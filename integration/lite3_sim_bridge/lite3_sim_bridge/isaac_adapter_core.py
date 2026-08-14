"""Isaac-independent helpers for the Lite3 physical simulation adapter."""

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping, Optional, Sequence, Tuple


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
