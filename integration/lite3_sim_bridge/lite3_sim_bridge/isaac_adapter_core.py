"""Isaac-independent helpers for the Lite3 physical simulation adapter."""

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class QualificationSegment:
    name: str
    duration_seconds: float
    command: Tuple[float, float, float]
    connected: bool = True

    def __post_init__(self) -> None:
        if not self.name or not math.isfinite(self.duration_seconds):
            raise ValueError("qualification segment needs a name and finite duration")
        if self.duration_seconds <= 0.0 or len(self.command) != 3:
            raise ValueError("qualification segment duration and command are invalid")
        if not all(math.isfinite(float(value)) for value in self.command):
            raise ValueError("qualification command must be finite")
        if not self.connected and any(float(value) != 0.0 for value in self.command):
            raise ValueError("a disconnected segment must declare a zero command")


DEFAULT_QUALIFICATION_SCHEDULE = (
    QualificationSegment("settle_zero", 1.0, (0.0, 0.0, 0.0)),
    QualificationSegment("forward", 2.0, (0.30, 0.0, 0.0)),
    QualificationSegment("lateral", 2.0, (0.0, 0.18, 0.0)),
    QualificationSegment("yaw", 2.0, (0.0, 0.0, 0.40)),
    QualificationSegment("stop_zero", 1.0, (0.0, 0.0, 0.0)),
    QualificationSegment("watchdog_disconnect", 0.75, (0.0, 0.0, 0.0), False),
)


def schedule_state(
    elapsed_seconds: float,
    schedule: Sequence[QualificationSegment] = DEFAULT_QUALIFICATION_SCHEDULE,
) -> Tuple[QualificationSegment, float]:
    """Return the active schedule segment and elapsed time inside it."""

    if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0.0:
        raise ValueError("elapsed_seconds must be finite and non-negative")
    if not schedule:
        raise ValueError("schedule must not be empty")
    cursor = 0.0
    for segment in schedule:
        boundary = cursor + segment.duration_seconds
        if elapsed_seconds < boundary:
            return segment, elapsed_seconds - cursor
        cursor = boundary
    return schedule[-1], schedule[-1].duration_seconds


def schedule_duration(
    schedule: Sequence[QualificationSegment] = DEFAULT_QUALIFICATION_SCHEDULE,
) -> float:
    if not schedule:
        raise ValueError("schedule must not be empty")
    return sum(segment.duration_seconds for segment in schedule)


def canonical_config_sha256(config: Mapping[str, object]) -> bytes:
    """Hash JSON-compatible configuration with deterministic serialization."""

    encoded = json.dumps(
        config, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).digest()


def quaternion_wxyz_to_xyzw(quaternion: Sequence[float]) -> Tuple[float, ...]:
    if len(quaternion) != 4:
        raise ValueError("quaternion must contain four values")
    values = tuple(float(value) for value in quaternion)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("quaternion must be finite")
    norm = math.sqrt(sum(value * value for value in values))
    if norm < 1.0e-12:
        raise ValueError("quaternion norm is zero")
    w, x, y, z = (value / norm for value in values)
    return x, y, z, w


def rotation_matrix_from_wxyz(quaternion: Sequence[float]) -> Tuple[Tuple[float, ...], ...]:
    """Return the local-to-world rotation for a normalized Isaac quaternion."""

    x, y, z, w = quaternion_wxyz_to_xyzw(quaternion)
    return (
        (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)),
        (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)),
        (2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)),
    )


def world_hits_to_sensor_points(
    world_hits: Iterable[Sequence[float]],
    sensor_position_world: Sequence[float],
    sensor_quaternion_wxyz: Sequence[float],
    minimum_range: float,
    maximum_range: float,
    minimum_world_z: Optional[float] = None,
) -> Tuple[Tuple[float, float, float], ...]:
    """Transform finite, height- and range-gated world hits into the sensor frame."""

    if len(sensor_position_world) != 3:
        raise ValueError("sensor position must contain three values")
    origin = tuple(float(value) for value in sensor_position_world)
    if not all(math.isfinite(value) for value in origin):
        raise ValueError("sensor position must be finite")
    if (
        not math.isfinite(minimum_range)
        or not math.isfinite(maximum_range)
        or minimum_range < 0.0
        or maximum_range <= minimum_range
    ):
        raise ValueError("range limits are invalid")
    if minimum_world_z is not None and not math.isfinite(minimum_world_z):
        raise ValueError("minimum world z must be finite when provided")
    rotation = rotation_matrix_from_wxyz(sensor_quaternion_wxyz)
    result = []
    for hit in world_hits:
        if len(hit) != 3:
            raise ValueError("each world hit must contain three values")
        values = tuple(float(value) for value in hit)
        if not all(math.isfinite(value) for value in values):
            continue
        if minimum_world_z is not None and values[2] <= minimum_world_z:
            continue
        dx, dy, dz = (values[index] - origin[index] for index in range(3))
        # Row-vector delta multiplied by R gives R^T * delta in column form.
        local = (
            dx * rotation[0][0] + dy * rotation[1][0] + dz * rotation[2][0],
            dx * rotation[0][1] + dy * rotation[1][1] + dz * rotation[2][1],
            dx * rotation[0][2] + dy * rotation[1][2] + dz * rotation[2][2],
        )
        distance = math.sqrt(sum(value * value for value in local))
        if minimum_range <= distance <= maximum_range:
            result.append(local)
    return tuple(result)


def local_minimum_obstacle_hits(
    world_hits: Iterable[Sequence[float]],
    sensor_position_world: Sequence[float],
    minimum_range: float,
    maximum_range: float,
    cell_size: float,
    height_threshold: float,
    neighbor_cells: int = 1,
    minimum_neighbor_cells: int = 2,
) -> Tuple[Tuple[Tuple[float, float, float], ...], Mapping[str, int]]:
    """Keep obstacle-like hits above a local terrain envelope.

    The filter deliberately consumes only rendered XYZ geometry and sensor
    position. It has no terrain-height, scene-prim, or obstacle-label input.
    Sparse cells are retained conservatively rather than being called ground.
    """

    if len(sensor_position_world) != 3:
        raise ValueError("sensor position must contain three values")
    origin = tuple(float(value) for value in sensor_position_world)
    if not all(math.isfinite(value) for value in origin):
        raise ValueError("sensor position must be finite")
    if (
        not math.isfinite(minimum_range)
        or not math.isfinite(maximum_range)
        or minimum_range < 0.0
        or maximum_range <= minimum_range
    ):
        raise ValueError("range limits are invalid")
    if not math.isfinite(cell_size) or cell_size <= 0.0:
        raise ValueError("terrain-filter cell size must be positive and finite")
    if not math.isfinite(height_threshold) or height_threshold <= 0.0:
        raise ValueError("terrain-filter height threshold must be positive and finite")
    if neighbor_cells < 0:
        raise ValueError("terrain-filter neighbor cell count must be non-negative")
    if minimum_neighbor_cells <= 0:
        raise ValueError("terrain-filter minimum neighbor cells must be positive")

    candidates = []
    cell_minimum_z: Dict[Tuple[int, int], float] = {}
    input_count = 0
    for hit in world_hits:
        input_count += 1
        if len(hit) != 3:
            raise ValueError("each world hit must contain three values")
        point = tuple(float(value) for value in hit)
        if not all(math.isfinite(value) for value in point):
            continue
        distance = math.dist(point, origin)
        if distance < minimum_range or distance > maximum_range:
            continue
        cell = (
            math.floor(point[0] / cell_size),
            math.floor(point[1] / cell_size),
        )
        candidates.append((point, cell))
        cell_minimum_z[cell] = min(point[2], cell_minimum_z.get(cell, point[2]))

    obstacle_hits = []
    filtered_ground_count = 0
    sparse_retained_count = 0
    for point, cell in candidates:
        local_minima = []
        for dx in range(-neighbor_cells, neighbor_cells + 1):
            for dy in range(-neighbor_cells, neighbor_cells + 1):
                neighbor = (cell[0] + dx, cell[1] + dy)
                if neighbor in cell_minimum_z:
                    local_minima.append(cell_minimum_z[neighbor])
        if len(local_minima) < minimum_neighbor_cells:
            obstacle_hits.append(point)
            sparse_retained_count += 1
            continue
        terrain_envelope_z = min(local_minima)
        if point[2] - terrain_envelope_z > height_threshold:
            obstacle_hits.append(point)
        else:
            filtered_ground_count += 1

    stats = {
        "input_hit_count": input_count,
        "finite_in_range_hit_count": len(candidates),
        "cell_count": len(cell_minimum_z),
        "filtered_ground_hit_count": filtered_ground_count,
        "obstacle_hit_count": len(obstacle_hits),
        "sparse_retained_hit_count": sparse_retained_count,
    }
    return tuple(obstacle_hits), stats


def point_to_segment_distance_2d(
    point: Sequence[float], start: Sequence[float], end: Sequence[float]
) -> float:
    """Return Euclidean distance from a 2-D point to a closed segment."""

    if len(point) != 2 or len(start) != 2 or len(end) != 2:
        raise ValueError("point and segment endpoints must be two-dimensional")
    px, py = (float(value) for value in point)
    sx, sy = (float(value) for value in start)
    ex, ey = (float(value) for value in end)
    if not all(math.isfinite(value) for value in (px, py, sx, sy, ex, ey)):
        raise ValueError("point and segment endpoints must be finite")
    dx = ex - sx
    dy = ey - sy
    length_squared = dx * dx + dy * dy
    if length_squared <= 1.0e-18:
        return math.hypot(px - sx, py - sy)
    projection = ((px - sx) * dx + (py - sy) * dy) / length_squared
    projection = max(0.0, min(1.0, projection))
    closest_x = sx + projection * dx
    closest_y = sy + projection * dy
    return math.hypot(px - closest_x, py - closest_y)


def assert_command_visible_in_critic(
    critic_observation: Sequence[float],
    command: Sequence[float],
    command_offset: int = 9,
    tolerance: float = 1.0e-6,
) -> Tuple[float, float, float]:
    """Check the V17 teacher critic's live command slice."""

    if len(command) != 3 or command_offset < 0:
        raise ValueError("command or command_offset is invalid")
    if len(critic_observation) < command_offset + 3:
        raise ValueError("critic observation is too short for the command slice")
    observed = tuple(float(value) for value in critic_observation[command_offset : command_offset + 3])
    expected = tuple(float(value) for value in command)
    if not all(math.isfinite(value) for value in observed + expected):
        raise ValueError("command comparison contains a non-finite value")
    if any(abs(left - right) > tolerance for left, right in zip(observed, expected)):
        raise ValueError(
            "live command is not visible in the critic observation: "
            f"observed={observed}, expected={expected}"
        )
    return observed
