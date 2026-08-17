"""Choose a conservative long Office L0 route from source collision bounds."""

from __future__ import annotations

import argparse
from collections import deque
import hashlib
import heapq
import json
import math
from pathlib import Path

import numpy as np


GRID_RESOLUTION_M = 0.25
ROBOT_INFLATION_M = 0.45
L0_BOUNDS = (-24.0, -27.0, 6.0, 60.0)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _neighbors(cell, shape):
    x, y = cell
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nxt = (x + dx, y + dy)
        if 0 <= nxt[0] < shape[0] and 0 <= nxt[1] < shape[1]:
            yield nxt


def _bfs(mask, start):
    queue = deque([start])
    distance = {start: 0}
    parent = {start: None}
    while queue:
        current = queue.popleft()
        for nxt in _neighbors(current, mask.shape):
            if not mask[nxt] or nxt in distance:
                continue
            distance[nxt] = distance[current] + 1
            parent[nxt] = current
            queue.append(nxt)
    return distance, parent


def _largest_component(mask):
    unseen = set(map(tuple, np.argwhere(mask)))
    largest = set()
    while unseen:
        seed = next(iter(unseen))
        distance, _ = _bfs(mask, seed)
        component = set(distance)
        unseen.difference_update(component)
        if len(component) > len(largest):
            largest = component
    return largest


def _world(cell):
    x0, y0, _, _ = L0_BOUNDS
    return (
        x0 + (cell[0] + 0.5) * GRID_RESOLUTION_M,
        y0 + (cell[1] + 0.5) * GRID_RESOLUTION_M,
    )


def _segment_clear(mask, a, b):
    steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
    for index in range(steps + 1):
        alpha = index / steps
        cell = (
            int(round(a[0] + alpha * (b[0] - a[0]))),
            int(round(a[1] + alpha * (b[1] - a[1]))),
        )
        if not (0 <= cell[0] < mask.shape[0] and 0 <= cell[1] < mask.shape[1]):
            return False
        if not mask[cell]:
            return False
    return True


def _point_segment_distance(point, start, end):
    point = np.asarray(point, dtype=float)
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    delta = end - start
    denominator = float(np.dot(delta, delta))
    if denominator <= 1.0e-12:
        return float(np.linalg.norm(point - start))
    alpha = float(np.clip(np.dot(point - start, delta) / denominator, 0.0, 1.0))
    return float(np.linalg.norm(point - (start + alpha * delta)))


def _segment_distance(first_start, first_end, second_start, second_end):
    minimum = math.inf
    for alpha in np.linspace(0.0, 1.0, 41):
        first_point = np.asarray(first_start) + alpha * (
            np.asarray(first_end) - np.asarray(first_start)
        )
        second_point = np.asarray(second_start) + alpha * (
            np.asarray(second_end) - np.asarray(second_start)
        )
        minimum = min(
            minimum,
            _point_segment_distance(first_point, second_start, second_end),
            _point_segment_distance(second_point, first_start, first_end),
        )
    return minimum


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collision-inventory", type=Path, required=True)
    parser.add_argument("--floor-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--route-length-m", type=float)
    args = parser.parse_args()
    inventory = json.loads(args.collision_inventory.read_text(encoding="utf-8"))
    floor_result = json.loads(args.floor_result.read_text(encoding="utf-8"))

    x0, y0, x1, y1 = L0_BOUNDS
    shape = (
        int(math.ceil((x1 - x0) / GRID_RESOLUTION_M)),
        int(math.ceil((y1 - y0) / GRID_RESOLUTION_M)),
    )
    floor = np.zeros(shape, dtype=bool)
    for row in floor_result["floor_rows"]:
        bx0, by0, _, bx1, by1, _ = row["bounds_xyzxyz_m"]
        ix0 = max(0, int(math.floor((bx0 - x0) / GRID_RESOLUTION_M)))
        iy0 = max(0, int(math.floor((by0 - y0) / GRID_RESOLUTION_M)))
        ix1 = min(shape[0], int(math.ceil((bx1 - x0) / GRID_RESOLUTION_M)))
        iy1 = min(shape[1], int(math.ceil((by1 - y0) / GRID_RESOLUTION_M)))
        floor[ix0:ix1, iy0:iy1] = True

    obstacles = np.zeros(shape, dtype=bool)
    human_obstacles = np.zeros(shape, dtype=bool)
    recorded_obstacles = []
    seen_bounds = set()
    excluded_tokens = (
        "Floor",
        "Carpet",
        "Ceiling",
        "GroundPlane",
        "Light",
        "Lamp",
        "SmokeDetector",
        "Sprinkler",
        "Pipe",
        "Ventilation",
        "CCTV",
    )
    for row in inventory["rows"]:
        if not row["collision_api"] or any(token in row["path"] for token in excluded_tokens):
            continue
        bx0, by0, bz0, bx1, by1, bz1 = row["bounds_xyzxyz_m"]
        if bz1 < 0.08 or bz0 > 1.80:
            continue
        key = tuple(round(value, 3) for value in row["bounds_xyzxyz_m"])
        if key in seen_bounds:
            continue
        seen_bounds.add(key)
        for target_mask, inflation in (
            (obstacles, ROBOT_INFLATION_M),
            (human_obstacles, 0.30),
        ):
            ix0 = max(0, int(math.floor((bx0 - inflation - x0) / GRID_RESOLUTION_M)))
            iy0 = max(0, int(math.floor((by0 - inflation - y0) / GRID_RESOLUTION_M)))
            ix1 = min(shape[0], int(math.ceil((bx1 + inflation - x0) / GRID_RESOLUTION_M)))
            iy1 = min(shape[1], int(math.ceil((by1 + inflation - y0) / GRID_RESOLUTION_M)))
            if ix1 > ix0 and iy1 > iy0:
                target_mask[ix0:ix1, iy0:iy1] = True
        recorded_obstacles.append(row["path"])

    free = floor & ~obstacles
    human_free = floor & ~human_obstacles
    component = _largest_component(free)
    if not component:
        raise RuntimeError("conservative Office grid has no connected free component")
    component_mask = np.zeros_like(free)
    for cell in component:
        component_mask[cell] = True
    first = next(iter(component))
    distance, _ = _bfs(component_mask, first)
    endpoint_a = max(distance, key=distance.get)
    distance, parent = _bfs(component_mask, endpoint_a)
    endpoint_b = max(distance, key=distance.get)
    cells = []
    current = endpoint_b
    while current is not None:
        cells.append(current)
        current = parent[current]
    cells.reverse()
    if args.route_length_m is not None:
        if args.route_length_m < 20.0:
            raise ValueError("requested Office route must remain at least 20 m")
        target_cells = int(round(args.route_length_m / GRID_RESOLUTION_M)) + 1
        if target_cells > len(cells):
            raise ValueError("requested Office route exceeds the connected path")
        cells = cells[:target_cells]
        endpoint_b = cells[-1]
    path_length = (len(cells) - 1) * GRID_RESOLUTION_M
    if path_length < 20.0:
        raise RuntimeError(f"longest conservative Office route is only {path_length:.2f} m")

    crossing_candidates = []
    for index in range(2, len(cells) - 2, 3):
        prev_cell, centre, next_cell = cells[index - 1], cells[index], cells[index + 1]
        tangent = np.asarray(next_cell, dtype=float) - np.asarray(prev_cell, dtype=float)
        normal = np.asarray([-tangent[1], tangent[0]], dtype=float)
        if np.linalg.norm(normal) < 1.0e-9:
            continue
        normal /= np.linalg.norm(normal)
        accepted = None
        for half_width_cells in range(8, 4, -1):
            a = tuple(np.rint(np.asarray(centre) - half_width_cells * normal).astype(int))
            b = tuple(np.rint(np.asarray(centre) + half_width_cells * normal).astype(int))
            if _segment_clear(human_free, a, b):
                accepted = (a, b)
                break
        if accepted is not None:
            crossing_candidates.append((index, accepted))
    crossing_routes = []
    used_indices = []
    for target_fraction in (0.45, 0.75):
        target_index = int(target_fraction * (len(cells) - 1))
        eligible = [
            candidate
            for candidate in crossing_candidates
            if all(abs(candidate[0] - used) >= 8 for used in used_indices)
        ]
        if not eligible:
            raise RuntimeError("fewer than two separated conservative pedestrian crossings")
        index, accepted = min(eligible, key=lambda candidate: abs(candidate[0] - target_index))
        used_indices.append(index)
        fraction = index / (len(cells) - 1)
        crossing_routes.append(
            {
                "name": f"crossing_{len(crossing_routes) + 1}",
                "start_xy_m": _world(accepted[0]),
                "end_xy_m": _world(accepted[1]),
                "nominal_path_fraction": fraction,
                "speed_mps": 0.8 + 0.1 * len(crossing_routes),
            }
        )

    from scipy.ndimage import distance_transform_edt

    path_mask = np.zeros_like(free)
    for cell in cells:
        path_mask[cell] = True
    distance_from_robot_path = distance_transform_edt(~path_mask) * GRID_RESOLUTION_M
    background_free = human_free & (distance_from_robot_path >= 2.0)
    background_routes = []
    selected_background_starts = []
    candidates = sorted(
        map(tuple, np.argwhere(background_free)),
        key=lambda cell: distance_from_robot_path[cell],
    )
    for seed in candidates:
        if any(
            math.dist(_world(seed), _world(existing)) < 5.5
            for existing in selected_background_starts
        ):
            continue
        distance, parent = _bfs(background_free, seed)
        endpoints = [
            cell for cell, steps in distance.items() if 8 <= steps <= 16
        ]
        if not endpoints:
            continue
        end = max(endpoints, key=lambda cell: distance[cell])
        start_world = _world(seed)
        end_world = _world(end)
        if any(
            _segment_distance(
                start_world,
                end_world,
                route["start_xy_m"],
                route["end_xy_m"],
            )
            < 1.2
            for route in crossing_routes
        ):
            continue
        selected_background_starts.append(seed)
        index = len(background_routes)
        background_routes.append(
            {
                "name": f"background_{index + 1}",
                "start_xy_m": start_world,
                "end_xy_m": end_world,
                "speed_mps": 0.6 + 0.1 * index,
                "minimum_robot_path_clearance_m": min(
                    distance_from_robot_path[seed], distance_from_robot_path[end]
                ),
            }
        )
        if len(background_routes) == 6:
            break
    if len(background_routes) != 6:
        raise RuntimeError("could not place six separated off-route background pedestrians")

    sparse_waypoints = []
    accumulated = 0.0
    next_waypoint_distance = 7.0
    for first_cell, second_cell in zip(cells, cells[1:]):
        accumulated += GRID_RESOLUTION_M
        if accumulated + 1.0e-9 >= next_waypoint_distance:
            sparse_waypoints.append((*_world(second_cell), 0.85))
            next_waypoint_distance += 7.0
    goal_xyz = (*_world(endpoint_b), 0.85)
    if not sparse_waypoints or sparse_waypoints[-1] != goal_xyz:
        sparse_waypoints.append(goal_xyz)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "office_l0_conservative_route_preflight_pass",
        "reviewed": False,
        "grid_resolution_m": GRID_RESOLUTION_M,
        "robot_inflation_m": ROBOT_INFLATION_M,
        "world_bounds_xyxy_m": L0_BOUNDS,
        "grid_shape": shape,
        "floor_cell_count": int(floor.sum()),
        "obstacle_cell_count": int(obstacles.sum()),
        "largest_free_component_cell_count": len(component),
        "recorded_obstacle_count": len(recorded_obstacles),
        "start_xy_m": _world(endpoint_a),
        "goal_xy_m": _world(endpoint_b),
        "path_length_m": path_length,
        "path_xy_m": [_world(cell) for cell in cells],
        "scan_sparse_waypoints_xyz_m": sparse_waypoints,
        "crossing_pedestrians": crossing_routes,
        "background_pedestrians": background_routes,
        "collision_inventory_sha256": _sha256(args.collision_inventory),
        "floor_result_sha256": _sha256(args.floor_result),
        "claim_boundary": [
            "source collision AABBs are conservatively inflated for scenario preflight only",
            "route and pedestrian truth may configure/evaluate the trial but cannot enter SCAN",
            "no source-mesh continuous sweep, articulated Lite3, sensor, pedestrian, or planning claim",
        ],
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 14), dpi=160)
    display = np.zeros((*shape, 3), dtype=np.uint8)
    display[floor] = (225, 225, 225)
    display[free] = (250, 250, 250)
    display[obstacles] = (35, 45, 55)
    ax.imshow(
        display.transpose(1, 0, 2),
        origin="lower",
        extent=(x0, x1, y0, y1),
    )
    path = np.asarray(payload["path_xy_m"])
    ax.plot(path[:, 0], path[:, 1], color="#08a0ff", linewidth=2.0, label="conservative route")
    for route in crossing_routes:
        points = np.asarray([route["start_xy_m"], route["end_xy_m"]])
        ax.plot(points[:, 0], points[:, 1], color="#ff9d00", linewidth=2.0)
    for route in background_routes:
        points = np.asarray([route["start_xy_m"], route["end_xy_m"]])
        ax.plot(points[:, 0], points[:, 1], color="#45c96b", linewidth=1.5)
    ax.scatter(*payload["start_xy_m"], c="#00c8ff", s=45, label="start")
    ax.scatter(*payload["goal_xy_m"], c="#ff3366", s=45, label="goal")
    ax.set_aspect("equal")
    ax.set_title(f"Office L0 conservative preflight | {path_length:.1f} m")
    ax.set_xlabel("world x [m]")
    ax.set_ylabel("world y [m]")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(args.preview)
    plt.close(fig)
    print(
        "OFFICE_L0_ROUTE="
        + json.dumps(
            {
                "status": payload["status"],
                "path_length_m": path_length,
                "start_xy_m": payload["start_xy_m"],
                "goal_xy_m": payload["goal_xy_m"],
                "pedestrian_count": len(crossing_routes) + len(background_routes),
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
