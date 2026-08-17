"""Local-only TCP roles built on the shared v1 frame decoder."""

from dataclasses import dataclass
import select
import socket
import threading
import time
from typing import Callable, Optional, Tuple

from .command_state import CommandLimits, CommandSnapshot, LatestCommandState
from .protocol import (
    CommandV1,
    Frame,
    MessageType,
    ProtocolError,
    decode_command_payload,
    decode_frame,
    encode_command_payload,
    encode_frame,
    recv_frame,
    send_frame,
)


DEFAULT_TELEMETRY_PORT = 46000
DEFAULT_COMMAND_PORT = 46001


@dataclass(frozen=True)
class TransportStats:
    accepted_connections: int
    reconnects: int
    frames_received: int
    frames_sent: int
    protocol_errors: int
    io_errors: int
    last_protocol_error: Optional[str]
    coalesced_frames: int


class _StatsState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.accepted_connections = 0
        self.reconnects = 0
        self.frames_received = 0
        self.frames_sent = 0
        self.protocol_errors = 0
        self.io_errors = 0
        self.last_protocol_error = None  # type: Optional[str]
        self.coalesced_frames = 0

    def increment(self, field: str, count: int = 1) -> None:
        with self.lock:
            setattr(self, field, getattr(self, field) + count)

    def record_protocol_error(self, error: object) -> None:
        with self.lock:
            self.protocol_errors += 1
            self.last_protocol_error = str(error)

    def snapshot(self) -> TransportStats:
        with self.lock:
            return TransportStats(
                accepted_connections=self.accepted_connections,
                reconnects=self.reconnects,
                frames_received=self.frames_received,
                frames_sent=self.frames_sent,
                protocol_errors=self.protocol_errors,
                io_errors=self.io_errors,
                last_protocol_error=self.last_protocol_error,
                coalesced_frames=self.coalesced_frames,
            )


def _configure_connection(connection: socket.socket, timeout_seconds: float) -> None:
    connection.settimeout(timeout_seconds)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


class TelemetryPublisherServer:
    """Isaac-side single-client server for sensor and status frames."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = DEFAULT_TELEMETRY_PORT,
        io_timeout_seconds: float = 0.2,
    ) -> None:
        self._host = host
        self._port = port
        self._io_timeout_seconds = io_timeout_seconds
        self._listener = None  # type: Optional[socket.socket]
        self._connection = None  # type: Optional[socket.socket]
        self._connection_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._accept_thread = None  # type: Optional[threading.Thread]
        self._stats = _StatsState()

    @property
    def endpoint(self) -> Tuple[str, int]:
        if self._listener is None:
            raise RuntimeError("telemetry server is not started")
        host, port = self._listener.getsockname()[:2]
        return str(host), int(port)

    def start(self) -> None:
        if self._listener is not None:
            raise RuntimeError("telemetry server is already started")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self._host, self._port))
        listener.listen(1)
        listener.settimeout(self._io_timeout_seconds)
        self._listener = listener
        self._accept_thread = threading.Thread(
            target=self._accept_loop, name="lite3-telemetry-accept", daemon=True
        )
        self._accept_thread.start()

    def _accept_loop(self) -> None:
        assert self._listener is not None
        while not self._stop_event.is_set():
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                if not self._stop_event.is_set():
                    self._stats.increment("io_errors")
                break
            _configure_connection(connection, self._io_timeout_seconds)
            with self._connection_lock:
                previous = self._connection
                self._connection = connection
            if previous is not None:
                previous.close()
                self._stats.increment("reconnects")
            self._stats.increment("accepted_connections")

    def publish(self, frame_bytes: bytes) -> bool:
        frame = decode_frame(frame_bytes)
        if frame.header.message_type not in (
            MessageType.SENSOR_FRAME_V1,
            MessageType.STATUS_V1,
            MessageType.HEARTBEAT_V1,
        ):
            raise ProtocolError("telemetry stream received a command frame")
        with self._connection_lock:
            connection = self._connection
        if connection is None:
            return False
        try:
            send_frame(connection, frame_bytes)
        except (OSError, EOFError):
            self._stats.increment("io_errors")
            with self._connection_lock:
                if self._connection is connection:
                    self._connection = None
            connection.close()
            return False
        self._stats.increment("frames_sent")
        return True

    def stats(self) -> TransportStats:
        return self._stats.snapshot()

    def stop(self) -> None:
        self._stop_event.set()
        with self._connection_lock:
            connection = self._connection
            self._connection = None
        if connection is not None:
            connection.close()
        if self._listener is not None:
            self._listener.close()
            self._listener = None
        if self._accept_thread is not None:
            self._accept_thread.join(timeout=1.0)
            self._accept_thread = None


class CommandReceiverServer:
    """Isaac-side command receiver with one shared fail-closed state owner."""

    def __init__(
        self,
        command_state: LatestCommandState,
        host: str = "127.0.0.1",
        port: int = DEFAULT_COMMAND_PORT,
        io_timeout_seconds: float = 0.2,
        on_update: Optional[Callable[[CommandSnapshot], None]] = None,
    ) -> None:
        self._command_state = command_state
        self._host = host
        self._port = port
        self._io_timeout_seconds = io_timeout_seconds
        self._on_update = on_update
        self._listener = None  # type: Optional[socket.socket]
        self._connection = None  # type: Optional[socket.socket]
        self._connection_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None  # type: Optional[threading.Thread]
        self._stats = _StatsState()

    @property
    def endpoint(self) -> Tuple[str, int]:
        if self._listener is None:
            raise RuntimeError("command server is not started")
        host, port = self._listener.getsockname()[:2]
        return str(host), int(port)

    def start(self) -> None:
        if self._listener is not None:
            raise RuntimeError("command server is already started")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self._host, self._port))
        listener.listen(1)
        listener.settimeout(self._io_timeout_seconds)
        self._listener = listener
        self._thread = threading.Thread(
            target=self._run, name="lite3-command-receiver", daemon=True
        )
        self._thread.start()

    def _run(self) -> None:
        assert self._listener is not None
        has_accepted = False
        while not self._stop_event.is_set():
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                if not self._stop_event.is_set():
                    self._stats.increment("io_errors")
                break
            _configure_connection(connection, self._io_timeout_seconds)
            with self._connection_lock:
                self._connection = connection
            self._stats.increment("accepted_connections")
            if has_accepted:
                self._stats.increment("reconnects")
            has_accepted = True
            self._receive_connection(connection)
            with self._connection_lock:
                if self._connection is connection:
                    self._connection = None
            connection.close()
            if not self._stop_event.is_set():
                self._command_state.mark_disconnected()

    def _receive_connection(self, connection: socket.socket) -> None:
        while not self._stop_event.is_set():
            try:
                frames = [recv_frame(connection)]
                while len(frames) < 256:
                    readable, _, _ = select.select([connection], [], [], 0.0)
                    if not readable:
                        break
                    frames.append(recv_frame(connection))
            except socket.timeout:
                continue
            except ProtocolError as error:
                self._stats.record_protocol_error(error)
                return
            except (EOFError, OSError):
                return
            updates = []
            try:
                received_monotonic_ns = time.monotonic_ns()
                for frame in frames:
                    if frame.header.message_type == MessageType.HEARTBEAT_V1:
                        if frame.payload:
                            raise ProtocolError(
                                "heartbeat frame must have an empty payload"
                            )
                        continue
                    if frame.header.message_type != MessageType.CMD_VEL_V1:
                        raise ProtocolError(
                            "command stream received a non-command frame"
                        )
                    updates.append(
                        (
                            decode_command_payload(frame.payload),
                            frame.header.sequence,
                            frame.header.timestamp_ns,
                            received_monotonic_ns,
                        )
                    )
                snapshot = (
                    None
                    if not updates
                    else self._command_state.update_batch(updates)
                )
            except ProtocolError as error:
                self._stats.record_protocol_error(error)
                return
            self._stats.increment("frames_received", len(frames))
            self._stats.increment("coalesced_frames", max(0, len(updates) - 1))
            if snapshot is not None and self._on_update is not None:
                self._on_update(snapshot)

    def snapshot(self, now_monotonic_ns: Optional[int] = None) -> CommandSnapshot:
        now = time.monotonic_ns() if now_monotonic_ns is None else now_monotonic_ns
        return self._command_state.snapshot(now)

    def stats(self) -> TransportStats:
        return self._stats.snapshot()

    def stop(self) -> None:
        self._stop_event.set()
        with self._connection_lock:
            connection = self._connection
            self._connection = None
        if connection is not None:
            connection.close()
        if self._listener is not None:
            self._listener.close()
            self._listener = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None


class FrameStreamClient:
    """Foxy-side reconnectable client for one framed stream."""

    def __init__(self, host: str, port: int, timeout_seconds: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._socket = None  # type: Optional[socket.socket]

    def connect(self) -> None:
        self.close()
        connection = socket.create_connection(
            (self._host, self._port), timeout=self._timeout_seconds
        )
        _configure_connection(connection, self._timeout_seconds)
        self._socket = connection

    def receive(self) -> Frame:
        if self._socket is None:
            raise ConnectionError("stream client is not connected")
        try:
            return recv_frame(self._socket)
        except (EOFError, OSError, ProtocolError):
            self.close()
            raise

    def send(self, frame_bytes: bytes) -> None:
        if self._socket is None:
            raise ConnectionError("stream client is not connected")
        try:
            send_frame(self._socket, frame_bytes)
        except (OSError, ProtocolError):
            self.close()
            raise

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None


class CommandClient:
    """Foxy-side sequence and saturation owner for CMD_VEL_V1 frames."""

    def __init__(
        self,
        host: str,
        port: int,
        limits: CommandLimits,
        timeout_seconds: float = 1.0,
        initial_sequence: int = 0,
    ) -> None:
        if initial_sequence < 0:
            raise ValueError("initial_sequence must be non-negative")
        self._stream = FrameStreamClient(host, port, timeout_seconds)
        self._limits = limits
        self._sequence = initial_sequence

    @property
    def sequence(self) -> int:
        return self._sequence

    def connect(self) -> None:
        self._stream.connect()

    def send_command(
        self, command: CommandV1, timestamp_ns: Optional[int] = None
    ) -> CommandV1:
        checked = self._limits.clamp(command)
        self._sequence += 1
        timestamp = time.monotonic_ns() if timestamp_ns is None else timestamp_ns
        frame_bytes = encode_frame(
            MessageType.CMD_VEL_V1,
            sequence=self._sequence,
            timestamp_ns=timestamp,
            payload=encode_command_payload(checked),
        )
        self._stream.send(frame_bytes)
        return checked

    def close(self) -> None:
        self._stream.close()
