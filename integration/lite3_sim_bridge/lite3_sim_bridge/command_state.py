"""Thread-safe latest-command state and fail-closed watchdog behavior."""

from dataclasses import dataclass
import math
import threading
from typing import Optional, Sequence, Tuple

from .protocol import CommandV1, ProtocolError, SequenceTracker


@dataclass(frozen=True)
class CommandLimits:
    max_vx: float = 0.75
    max_vy: float = 0.35
    max_wz: float = 1.0

    def __post_init__(self) -> None:
        values = (self.max_vx, self.max_vy, self.max_wz)
        if not all(math.isfinite(value) and value > 0.0 for value in values):
            raise ValueError("command limits must be finite and positive")

    def clamp(self, command: CommandV1) -> CommandV1:
        values = (command.vx, command.vy, command.wz)
        if not all(math.isfinite(value) for value in values):
            raise ProtocolError("command contains a non-finite value")
        return CommandV1(
            vx=max(-self.max_vx, min(self.max_vx, command.vx)),
            vy=max(-self.max_vy, min(self.max_vy, command.vy)),
            wz=max(-self.max_wz, min(self.max_wz, command.wz)),
        )


@dataclass(frozen=True)
class CommandSnapshot:
    command: CommandV1
    sequence: Optional[int]
    source_timestamp_ns: Optional[int]
    received_monotonic_ns: Optional[int]
    stale: bool
    reason: str
    watchdog_events: int
    sequence_gaps: int


class LatestCommandState:
    """Own the command sequence, timestamp validation, clamp and watchdog."""

    ZERO = CommandV1(0.0, 0.0, 0.0)

    def __init__(
        self,
        limits: CommandLimits,
        timeout_ns: int = 250_000_000,
        max_source_age_ns: int = 250_000_000,
        max_future_skew_ns: int = 25_000_000,
    ) -> None:
        for name, value in (
            ("timeout_ns", timeout_ns),
            ("max_source_age_ns", max_source_age_ns),
            ("max_future_skew_ns", max_future_skew_ns),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError("{} must be a non-negative integer".format(name))
        if timeout_ns == 0:
            raise ValueError("timeout_ns must be positive")
        self._limits = limits
        self._timeout_ns = timeout_ns
        self._max_source_age_ns = max_source_age_ns
        self._max_future_skew_ns = max_future_skew_ns
        self._lock = threading.Lock()
        self._command = self.ZERO
        self._sequence_tracker = SequenceTracker()
        self._source_timestamp_ns = None  # type: Optional[int]
        self._received_monotonic_ns = None  # type: Optional[int]
        self._stale = True
        self._reason = "no_command"
        self._watchdog_events = 0

    def update(
        self,
        command: CommandV1,
        sequence: int,
        source_timestamp_ns: int,
        received_monotonic_ns: int,
    ) -> CommandSnapshot:
        return self.update_batch(
            ((command, sequence, source_timestamp_ns, received_monotonic_ns),)
        )

    def update_batch(
        self,
        updates: Sequence[Tuple[CommandV1, int, int, int]],
    ) -> CommandSnapshot:
        """Atomically coalesce a received backlog to its fresh latest command.

        Every sequence is observed so an intentional latest-wins coalesce is
        not reported as packet loss. Intermediate source-stale commands are
        never applied. The newest command must still satisfy the unchanged
        freshness and future-skew limits, otherwise the whole batch fails.
        """

        if not updates:
            raise ValueError("command update batch must not be empty")
        checked_updates = []
        for command, sequence, source_timestamp_ns, received_monotonic_ns in updates:
            for name, value in (
                ("sequence", sequence),
                ("source_timestamp_ns", source_timestamp_ns),
                ("received_monotonic_ns", received_monotonic_ns),
            ):
                if not isinstance(value, int) or value < 0:
                    raise ProtocolError(
                        "{} must be a non-negative integer".format(name)
                    )
            age_ns = received_monotonic_ns - source_timestamp_ns
            if age_ns < -self._max_future_skew_ns:
                raise ProtocolError("command timestamp is too far in the future")
            checked_updates.append(
                (
                    self._limits.clamp(command),
                    sequence,
                    source_timestamp_ns,
                    received_monotonic_ns,
                    age_ns,
                )
            )
        if checked_updates[-1][4] > self._max_source_age_ns:
            raise ProtocolError("command timestamp is stale")

        with self._lock:
            previous_sequence = self._sequence_tracker.last_sequence
            for _, sequence, _, _, _ in checked_updates:
                if previous_sequence is not None and sequence <= previous_sequence:
                    raise ProtocolError("sequence is not increasing")
                previous_sequence = sequence
            for _, sequence, _, _, _ in checked_updates:
                self._sequence_tracker.observe(sequence)
            latest = checked_updates[-1]
            self._command = latest[0]
            self._source_timestamp_ns = latest[2]
            self._received_monotonic_ns = latest[3]
            self._stale = False
            self._reason = "active"
            return self._snapshot_locked()

    def snapshot(self, now_monotonic_ns: int) -> CommandSnapshot:
        if not isinstance(now_monotonic_ns, int) or now_monotonic_ns < 0:
            raise ValueError("now_monotonic_ns must be a non-negative integer")
        with self._lock:
            if (
                not self._stale
                and self._received_monotonic_ns is not None
                and now_monotonic_ns - self._received_monotonic_ns > self._timeout_ns
            ):
                self._command = self.ZERO
                self._stale = True
                self._reason = "watchdog_timeout"
                self._watchdog_events += 1
            return self._snapshot_locked()

    def mark_disconnected(self) -> CommandSnapshot:
        with self._lock:
            was_active = not self._stale
            self._command = self.ZERO
            self._stale = True
            self._reason = "disconnected"
            if was_active:
                self._watchdog_events += 1
            return self._snapshot_locked()

    def _snapshot_locked(self) -> CommandSnapshot:
        return CommandSnapshot(
            command=self._command,
            sequence=self._sequence_tracker.last_sequence,
            source_timestamp_ns=self._source_timestamp_ns,
            received_monotonic_ns=self._received_monotonic_ns,
            stale=self._stale,
            reason=self._reason,
            watchdog_events=self._watchdog_events,
            sequence_gaps=self._sequence_tracker.gap_count,
        )
