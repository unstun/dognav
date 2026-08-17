"""Pure configuration and camera helpers for official Isaac scene previews."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SceneSpec:
    name: str
    relative_usd_paths: tuple[str, ...]


SCENES = {
    "warehouse": SceneSpec(
        name="warehouse",
        relative_usd_paths=(
            "Environments/Simple_Warehouse/warehouse_with_forklifts.usd",
            "Environments/Simple_Warehouse/warehouse.usd",
        ),
    ),
    "office": SceneSpec(
        name="office",
        relative_usd_paths=("Environments/Office/office.usd",),
    ),
    "hospital": SceneSpec(
        name="hospital",
        relative_usd_paths=("Environments/Hospital/hospital.usd",),
    ),
}

OFFICE_TOUR_CAMERA_WAYPOINTS = (
    ((4.0, -4.0, 2.8), (-2.0, 3.0, 0.85)),
    ((6.0, 3.0, 3.0), (-2.0, 3.0, 0.90)),
    ((2.0, 10.0, 2.8), (-2.0, 3.0, 0.85)),
    ((-8.0, 10.0, 2.8), (-2.0, 3.0, 0.85)),
    ((-10.0, 3.0, 2.8), (-2.0, 3.0, 0.85)),
    ((-8.0, 10.0, 2.8), (-2.0, 3.0, 0.85)),
    ((2.0, 10.0, 2.8), (-2.0, 3.0, 0.85)),
    ((6.0, 3.0, 3.0), (-2.0, 3.0, 0.90)),
    ((4.0, -4.0, 2.8), (-2.0, 3.0, 0.85)),
)

OFFICE_FLOOR_LEVELS = (
    ("B1", -3.3),
    ("L0", 0.0),
    ("L1", 3.3),
)


def candidate_uris(asset_root: str, scene: str) -> tuple[str, ...]:
    """Return ordered source URIs without accepting an unknown scene."""

    if scene not in SCENES:
        raise ValueError(f"unsupported scene: {scene}")
    root = asset_root.rstrip("/")
    return tuple(f"{root}/{path}" for path in SCENES[scene].relative_usd_paths)


def validate_bounds(values: Iterable[float]) -> tuple[float, ...]:
    """Validate one finite six-value world-aligned bounding box."""

    import math

    bounds = tuple(float(value) for value in values)
    if len(bounds) != 6 or not all(math.isfinite(value) for value in bounds):
        raise ValueError("scene bounds must contain six finite values")
    if any(bounds[index + 3] <= bounds[index] for index in range(3)):
        raise ValueError("scene bounds must have positive extent on every axis")
    return bounds


def overview_camera(bounds: Iterable[float]) -> dict[str, tuple[float, ...]]:
    """Derive a conservative oblique overview from a world-aligned bbox."""

    x0, y0, z0, x1, y1, z1 = validate_bounds(bounds)
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)
    horizontal = max(x1 - x0, y1 - y0, 8.0)
    vertical = max(z1 - z0, 3.0)
    target_z = z0 + min(max(1.5, 0.25 * vertical), 0.7 * vertical)
    return {
        "eye": (
            cx + 0.62 * horizontal,
            cy - 0.78 * horizontal,
            z1 + max(0.24 * horizontal, 0.8 * vertical),
        ),
        "target": (cx, cy, target_z),
    }


def scene_views(bounds: Iterable[float]) -> dict[str, dict[str, tuple[float, ...]]]:
    """Return exterior context plus two navigation-height interior views."""

    first = overview_camera(bounds)
    x0, y0, z0, x1, y1, z1 = validate_bounds(bounds)
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)
    horizontal = max(x1 - x0, y1 - y0, 8.0)
    vertical = max(z1 - z0, 3.0)
    return {
        "overview": first,
        "reverse": {
            "eye": (
                cx - 0.68 * horizontal,
                cy + 0.72 * horizontal,
                z1 + max(0.18 * horizontal, 0.65 * vertical),
            ),
            "target": first["target"],
        },
        "interior_long": {
            "eye": (cx, y0 + 0.12 * (y1 - y0), z0 + 1.45),
            "target": (cx, y1 - 0.12 * (y1 - y0), z0 + 1.15),
        },
        "interior_cross": {
            "eye": (x0 + 0.15 * (x1 - x0), cy, z0 + 1.45),
            "target": (x1 - 0.15 * (x1 - x0), cy, z0 + 1.15),
        },
    }


def office_tour_camera_pose(frame: int, frame_count: int):
    """Interpolate one smooth, deterministic reception-tour camera pose."""

    if frame_count < 2:
        raise ValueError("Office tour requires at least two frames")
    if frame < 0 or frame >= frame_count:
        raise ValueError("Office tour frame is outside the declared range")
    progress = frame * (len(OFFICE_TOUR_CAMERA_WAYPOINTS) - 1) / (frame_count - 1)
    segment = min(int(progress), len(OFFICE_TOUR_CAMERA_WAYPOINTS) - 2)
    alpha = progress - segment
    smooth = alpha * alpha * (3.0 - 2.0 * alpha)
    eye_a, target_a = OFFICE_TOUR_CAMERA_WAYPOINTS[segment]
    eye_b, target_b = OFFICE_TOUR_CAMERA_WAYPOINTS[segment + 1]
    eye = tuple(a + (b - a) * smooth for a, b in zip(eye_a, eye_b, strict=True))
    target = tuple(a + (b - a) * smooth for a, b in zip(target_a, target_b, strict=True))
    return eye, target


def nearest_office_floor(center_z: float) -> tuple[str, float]:
    """Assign one finite prim-centre height to the nearest authored floor."""

    import math

    if not math.isfinite(center_z):
        raise ValueError("Office prim centre height must be finite")
    return min(OFFICE_FLOOR_LEVELS, key=lambda item: abs(center_z - item[1]))


def office_global_camera_pose(
    bounds_xy: Iterable[float],
    floor_z: float,
    frame: int,
    frame_count: int,
):
    """Return a top-down-to-oblique camera sweep for one Office floor."""

    import math

    values = tuple(float(value) for value in bounds_xy)
    if len(values) != 4:
        raise ValueError("Office floor bounds must contain x0, y0, x1, y1")
    x0, y0, x1, y1 = values
    if not all(map(math.isfinite, values)) or x1 <= x0 or y1 <= y0:
        raise ValueError("Office floor bounds must be finite with positive extent")
    if frame_count < 2 or frame < 0 or frame >= frame_count:
        raise ValueError("Office floor camera frame is outside the declared range")
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)
    span = max(x1 - x0, y1 - y0, 12.0)
    target = (cx, cy, floor_z + 0.35)
    waypoints = (
        ((cx, cy, floor_z + 1.05 * span), target),
        ((cx + 0.55 * span, cy - 0.65 * span, floor_z + 0.58 * span), target),
        ((cx - 0.55 * span, cy + 0.65 * span, floor_z + 0.58 * span), target),
        ((cx, cy, floor_z + 1.05 * span), target),
    )
    progress = frame * (len(waypoints) - 1) / (frame_count - 1)
    segment = min(int(progress), len(waypoints) - 2)
    alpha = progress - segment
    smooth = alpha * alpha * (3.0 - 2.0 * alpha)
    eye_a, target_a = waypoints[segment]
    eye_b, target_b = waypoints[segment + 1]
    eye = tuple(a + (b - a) * smooth for a, b in zip(eye_a, eye_b, strict=True))
    look_at = tuple(a + (b - a) * smooth for a, b in zip(target_a, target_b, strict=True))
    return eye, look_at
