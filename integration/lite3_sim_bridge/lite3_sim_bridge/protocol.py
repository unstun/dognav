"""Binary protocol shared by the Foxy and Isaac bridge processes.

All fixed-width values use network byte order. Sensor point bytes are packed as
network-order ``float32 x,y,z`` triples. Quaternions use ``(x,y,z,w)``.
"""

from dataclasses import dataclass
from enum import IntEnum
import math
import socket
import struct
from typing import Iterable, Optional, Sequence, Tuple
import zlib


MAGIC = b"L3NV"
PROTOCOL_VERSION = 1
MAX_PAYLOAD_BYTES = 16 * 1024 * 1024
MAX_POINT_COUNT = 1_000_000
POINT_STRIDE_BYTES = 12
POINT_FORMAT_XYZ_F32_BE = 1

# magic, version, message type, flags, header bytes, payload bytes, sequence,
# timestamp ns, reserved, payload crc32
HEADER_STRUCT = struct.Struct("!4sBBHIIQQII")
HEADER_SIZE = HEADER_STRUCT.size
SENSOR_PREFIX_STRUCT = struct.Struct("!14d32sIHBB")
COMMAND_STRUCT = struct.Struct("!3f")
STATUS_STRUCT = struct.Struct("!4fIIIII")


class MessageType(IntEnum):
    SENSOR_FRAME_V1 = 1
    STATUS_V1 = 2
    CMD_VEL_V1 = 3
    HEARTBEAT_V1 = 4


class StatusFlag(IntEnum):
    CONTACT_SUPPORTED = 1 << 0
    COLLISION = 1 << 1
    TERMINATED = 1 << 2
    RESET_OCCURRED = 1 << 3
    NAN_DETECTED = 1 << 4


class ProtocolError(ValueError):
    """Raised when bytes violate the v1 wire contract."""


class SequenceTracker:
    """Single owner for increasing sequence validation and gap accounting."""

    def __init__(self) -> None:
        self._last_sequence = None  # type: Optional[int]
        self._gap_count = 0

    @property
    def last_sequence(self):  # type: () -> Optional[int]
        return self._last_sequence

    @property
    def gap_count(self) -> int:
        return self._gap_count

    def observe(self, sequence: int) -> int:
        _require_uint("sequence", sequence, 64)
        if self._last_sequence is not None and sequence <= self._last_sequence:
            raise ProtocolError("sequence is not increasing")
        gap = 0
        if self._last_sequence is not None and sequence > self._last_sequence + 1:
            gap = sequence - self._last_sequence - 1
            self._gap_count += gap
        self._last_sequence = sequence
        return gap


@dataclass(frozen=True)
class Header:
    message_type: MessageType
    flags: int
    payload_length: int
    sequence: int
    timestamp_ns: int
    payload_crc32: int


@dataclass(frozen=True)
class Frame:
    header: Header
    payload: bytes


@dataclass(frozen=True)
class CommandV1:
    vx: float
    vy: float
    wz: float


@dataclass(frozen=True)
class SensorFrameV1:
    body_position: Tuple[float, float, float]
    body_quaternion_xyzw: Tuple[float, float, float, float]
    sensor_position: Tuple[float, float, float]
    sensor_quaternion_xyzw: Tuple[float, float, float, float]
    config_sha256: bytes
    point_count: int
    points_xyz_f32_be: bytes


@dataclass(frozen=True)
class StatusV1:
    physics_hz: float
    policy_hz: float
    sensor_hz: float
    bridge_latency_ms: float
    contact_count: int
    dropped_frames: int
    watchdog_events: int
    flags: int
    termination_code: int


def _require_uint(name: str, value: int, bits: int) -> None:
    maximum = (1 << bits) - 1
    if not isinstance(value, int) or value < 0 or value > maximum:
        raise ProtocolError("{} must be an unsigned {}-bit integer".format(name, bits))


def _require_finite(name: str, values: Sequence[float]) -> Tuple[float, ...]:
    converted = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in converted):
        raise ProtocolError("{} contains a non-finite value".format(name))
    return converted


def _require_pose(
    position: Sequence[float], quaternion_xyzw: Sequence[float], name: str
) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    if len(position) != 3 or len(quaternion_xyzw) != 4:
        raise ProtocolError("{} pose must contain 3 position and 4 quaternion values".format(name))
    checked_position = _require_finite(name + " position", position)
    checked_quaternion = _require_finite(name + " quaternion", quaternion_xyzw)
    norm = math.sqrt(sum(value * value for value in checked_quaternion))
    if abs(norm - 1.0) > 1.0e-3:
        raise ProtocolError("{} quaternion must be unit length".format(name))
    return checked_position, checked_quaternion


def encode_frame(
    message_type: MessageType,
    sequence: int,
    timestamp_ns: int,
    payload: bytes,
    flags: int = 0,
) -> bytes:
    """Encode one complete v1 frame."""

    try:
        checked_type = MessageType(message_type)
    except ValueError as exc:
        raise ProtocolError("unknown message type") from exc
    _require_uint("sequence", sequence, 64)
    _require_uint("timestamp_ns", timestamp_ns, 64)
    _require_uint("flags", flags, 16)
    if flags != 0:
        raise ProtocolError("v1 flags must be zero")
    if not isinstance(payload, bytes):
        raise ProtocolError("payload must be bytes")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ProtocolError("payload exceeds v1 limit")
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    header = HEADER_STRUCT.pack(
        MAGIC,
        PROTOCOL_VERSION,
        int(checked_type),
        flags,
        HEADER_SIZE,
        len(payload),
        sequence,
        timestamp_ns,
        0,
        checksum,
    )
    return header + payload


def decode_header(data: bytes, max_payload_bytes: int = MAX_PAYLOAD_BYTES) -> Header:
    """Validate and decode one fixed v1 header."""

    if len(data) != HEADER_SIZE:
        raise ProtocolError("header length mismatch")
    (
        magic,
        version,
        message_type,
        flags,
        header_length,
        payload_length,
        sequence,
        timestamp_ns,
        reserved,
        payload_crc32,
    ) = HEADER_STRUCT.unpack(data)
    if magic != MAGIC:
        raise ProtocolError("bad magic")
    if version != PROTOCOL_VERSION:
        raise ProtocolError("unsupported protocol version")
    if flags != 0:
        raise ProtocolError("unknown required flags")
    if header_length != HEADER_SIZE:
        raise ProtocolError("unsupported header length")
    if reserved != 0:
        raise ProtocolError("reserved header field must be zero")
    if payload_length > max_payload_bytes:
        raise ProtocolError("payload length exceeds configured limit")
    try:
        checked_type = MessageType(message_type)
    except ValueError as exc:
        raise ProtocolError("unknown message type") from exc
    return Header(
        message_type=checked_type,
        flags=flags,
        payload_length=payload_length,
        sequence=sequence,
        timestamp_ns=timestamp_ns,
        payload_crc32=payload_crc32,
    )


def decode_frame(data: bytes, max_payload_bytes: int = MAX_PAYLOAD_BYTES) -> Frame:
    """Decode exactly one complete frame and reject trailing bytes."""

    if len(data) < HEADER_SIZE:
        raise ProtocolError("truncated frame header")
    header = decode_header(data[:HEADER_SIZE], max_payload_bytes=max_payload_bytes)
    expected_length = HEADER_SIZE + header.payload_length
    if len(data) != expected_length:
        raise ProtocolError("frame length mismatch")
    payload = data[HEADER_SIZE:]
    if zlib.crc32(payload) & 0xFFFFFFFF != header.payload_crc32:
        raise ProtocolError("payload CRC32 mismatch")
    return Frame(header=header, payload=payload)


def recv_exact(sock: socket.socket, byte_count: int) -> bytes:
    """Read exactly ``byte_count`` bytes or raise ``EOFError``."""

    if byte_count < 0:
        raise ValueError("byte_count must be non-negative")
    chunks = []
    remaining = byte_count
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise EOFError("socket closed with {} bytes remaining".format(remaining))
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_frame(sock: socket.socket, max_payload_bytes: int = MAX_PAYLOAD_BYTES) -> Frame:
    """Receive one framed message from a stream socket."""

    header_bytes = recv_exact(sock, HEADER_SIZE)
    header = decode_header(header_bytes, max_payload_bytes=max_payload_bytes)
    payload = recv_exact(sock, header.payload_length)
    if zlib.crc32(payload) & 0xFFFFFFFF != header.payload_crc32:
        raise ProtocolError("payload CRC32 mismatch")
    return Frame(header=header, payload=payload)


def send_frame(sock: socket.socket, frame_bytes: bytes) -> None:
    """Send one already encoded frame."""

    # Decode before transmitting so callers cannot bypass the shared boundary.
    decode_frame(frame_bytes)
    sock.sendall(frame_bytes)


def pack_xyz_points(points: Iterable[Sequence[float]]) -> Tuple[int, bytes]:
    """Pack an iterable of XYZ triples into network-order float32 bytes."""

    flat = []
    count = 0
    for point in points:
        if len(point) != 3:
            raise ProtocolError("each point must contain x, y, z")
        checked = _require_finite("point", point)
        flat.extend(checked)
        count += 1
        if count > MAX_POINT_COUNT:
            raise ProtocolError("point count exceeds v1 limit")
    if not flat:
        return 0, b""
    return count, struct.pack("!{}f".format(len(flat)), *flat)


def unpack_xyz_points(point_count: int, data: bytes) -> Tuple[Tuple[float, float, float], ...]:
    """Decode network-order XYZ bytes. Intended for tests and small samples."""

    _validate_xyz_point_bytes(point_count, data)
    if point_count == 0:
        return tuple()
    values = struct.unpack("!{}f".format(point_count * 3), data)
    return tuple(
        (values[index], values[index + 1], values[index + 2])
        for index in range(0, len(values), 3)
    )


def xyz_f32_be_to_le(data: bytes) -> bytes:
    """Convert network-order float32 bytes to explicit little-endian ROS bytes."""

    if len(data) % 4 != 0:
        raise ProtocolError("float32 point bytes must be four-byte aligned")
    converted = bytearray(len(data))
    for offset in range(0, len(data), 4):
        converted[offset : offset + 4] = data[offset : offset + 4][::-1]
    return bytes(converted)


def _validate_xyz_point_bytes(point_count: int, data: bytes) -> None:
    """Validate a point buffer without expanding it into Python tuples."""

    _require_uint("point_count", point_count, 32)
    if point_count > MAX_POINT_COUNT:
        raise ProtocolError("point count exceeds v1 limit")
    expected = point_count * POINT_STRIDE_BYTES
    if len(data) != expected:
        raise ProtocolError("point byte length mismatch")
    for (value,) in struct.iter_unpack("!f", data):
        if not math.isfinite(value):
            raise ProtocolError("point payload contains a non-finite value")


def encode_sensor_payload(sensor: SensorFrameV1) -> bytes:
    body_position, body_quaternion = _require_pose(
        sensor.body_position, sensor.body_quaternion_xyzw, "body"
    )
    sensor_position, sensor_quaternion = _require_pose(
        sensor.sensor_position, sensor.sensor_quaternion_xyzw, "sensor"
    )
    if not isinstance(sensor.config_sha256, bytes) or len(sensor.config_sha256) != 32:
        raise ProtocolError("config_sha256 must contain 32 raw bytes")
    _require_uint("point_count", sensor.point_count, 32)
    if sensor.point_count > MAX_POINT_COUNT:
        raise ProtocolError("point count exceeds v1 limit")
    expected_point_bytes = sensor.point_count * POINT_STRIDE_BYTES
    if len(sensor.points_xyz_f32_be) != expected_point_bytes:
        raise ProtocolError("point byte length does not match point_count")
    # Validate all point values before they cross the trust boundary.
    _validate_xyz_point_bytes(sensor.point_count, sensor.points_xyz_f32_be)
    prefix = SENSOR_PREFIX_STRUCT.pack(
        *(body_position + body_quaternion + sensor_position + sensor_quaternion),
        sensor.config_sha256,
        sensor.point_count,
        POINT_STRIDE_BYTES,
        POINT_FORMAT_XYZ_F32_BE,
        0,
    )
    payload = prefix + sensor.points_xyz_f32_be
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ProtocolError("sensor payload exceeds v1 limit")
    return payload


def decode_sensor_payload(payload: bytes) -> SensorFrameV1:
    if len(payload) < SENSOR_PREFIX_STRUCT.size:
        raise ProtocolError("truncated sensor payload")
    unpacked = SENSOR_PREFIX_STRUCT.unpack(payload[: SENSOR_PREFIX_STRUCT.size])
    pose_values = unpacked[:14]
    config_sha256 = unpacked[14]
    point_count = unpacked[15]
    point_stride = unpacked[16]
    point_format = unpacked[17]
    reserved = unpacked[18]
    if point_stride != POINT_STRIDE_BYTES:
        raise ProtocolError("unsupported point stride")
    if point_format != POINT_FORMAT_XYZ_F32_BE:
        raise ProtocolError("unsupported point format")
    if reserved != 0:
        raise ProtocolError("reserved sensor field must be zero")
    point_bytes = payload[SENSOR_PREFIX_STRUCT.size :]
    _validate_xyz_point_bytes(point_count, point_bytes)
    body_position, body_quaternion = _require_pose(pose_values[0:3], pose_values[3:7], "body")
    sensor_position, sensor_quaternion = _require_pose(
        pose_values[7:10], pose_values[10:14], "sensor"
    )
    return SensorFrameV1(
        body_position=body_position,
        body_quaternion_xyzw=body_quaternion,
        sensor_position=sensor_position,
        sensor_quaternion_xyzw=sensor_quaternion,
        config_sha256=config_sha256,
        point_count=point_count,
        points_xyz_f32_be=point_bytes,
    )


def encode_command_payload(command: CommandV1) -> bytes:
    values = _require_finite("command", (command.vx, command.vy, command.wz))
    return COMMAND_STRUCT.pack(*values)


def decode_command_payload(payload: bytes) -> CommandV1:
    if len(payload) != COMMAND_STRUCT.size:
        raise ProtocolError("command payload length mismatch")
    values = COMMAND_STRUCT.unpack(payload)
    checked = _require_finite("command", values)
    return CommandV1(vx=checked[0], vy=checked[1], wz=checked[2])


def encode_status_payload(status: StatusV1) -> bytes:
    rates = _require_finite(
        "status rates",
        (status.physics_hz, status.policy_hz, status.sensor_hz, status.bridge_latency_ms),
    )
    for name, value in (
        ("contact_count", status.contact_count),
        ("dropped_frames", status.dropped_frames),
        ("watchdog_events", status.watchdog_events),
        ("flags", status.flags),
        ("termination_code", status.termination_code),
    ):
        _require_uint(name, value, 32)
    known_flags = sum(int(flag) for flag in StatusFlag)
    if status.flags & ~known_flags:
        raise ProtocolError("status contains unknown flags")
    return STATUS_STRUCT.pack(
        *(rates
          + (
              status.contact_count,
              status.dropped_frames,
              status.watchdog_events,
              status.flags,
              status.termination_code,
          ))
    )


def decode_status_payload(payload: bytes) -> StatusV1:
    if len(payload) != STATUS_STRUCT.size:
        raise ProtocolError("status payload length mismatch")
    unpacked = STATUS_STRUCT.unpack(payload)
    status = StatusV1(
        physics_hz=unpacked[0],
        policy_hz=unpacked[1],
        sensor_hz=unpacked[2],
        bridge_latency_ms=unpacked[3],
        contact_count=unpacked[4],
        dropped_frames=unpacked[5],
        watchdog_events=unpacked[6],
        flags=unpacked[7],
        termination_code=unpacked[8],
    )
    # Reuse the encoder as the single semantic validator.
    encode_status_payload(status)
    return status
