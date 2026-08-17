"""State and audit helpers for the Humble RViz replay adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class ReplayAuditState:
    """Track evidence-preserving conversions performed during one bag replay."""

    sample_count: int
    body_pose_count: int = 0
    rejected_body_pose_count: int = 0
    rejected_bspline_count: int = 0
    first_body_stamp_ns: int | None = None
    last_body_stamp_ns: int | None = None
    trajectory_point_counts: dict[int, int] = field(default_factory=dict)
    trajectory_start_stamps_ns: dict[int, int] = field(default_factory=dict)
    bbox_publish_count: int = 0
    bbox_snapshot_files: set[str] = field(default_factory=set)
    voxel_publish_count: int = 0
    voxel_point_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    preloaded_snapshot_file: str | None = None

    def accept_body_stamp(self, stamp_ns: int) -> bool:
        """Accept strictly increasing body stamps and reject replay regressions."""

        checked_stamp = int(stamp_ns)
        if self.last_body_stamp_ns is not None and checked_stamp <= self.last_body_stamp_ns:
            self.rejected_body_pose_count += 1
            return False
        if self.first_body_stamp_ns is None:
            self.first_body_stamp_ns = checked_stamp
        self.last_body_stamp_ns = checked_stamp
        self.body_pose_count += 1
        return True

    def accept_bspline(
        self, trajectory_id: int, point_count: int, start_stamp_ns: int
    ) -> None:
        """Record one successfully sampled source B-spline."""

        checked_count = int(point_count)
        if checked_count != self.sample_count:
            raise ValueError(
                f"sampled path has {checked_count} points; expected {self.sample_count}"
            )
        checked_id = int(trajectory_id)
        self.trajectory_point_counts[checked_id] = checked_count
        self.trajectory_start_stamps_ns[checked_id] = int(start_stamp_ns)

    def reject_bspline(self) -> None:
        self.rejected_bspline_count += 1

    def accept_bbox_snapshot(self, snapshot_file: str) -> None:
        self.bbox_publish_count += 1
        self.bbox_snapshot_files.add(str(snapshot_file))

    def accept_voxel_snapshot(
        self, snapshot_file: str, raw_point_count: int, inflated_point_count: int
    ) -> None:
        checked_raw_count = int(raw_point_count)
        checked_inflated_count = int(inflated_point_count)
        if checked_raw_count <= 0 or checked_inflated_count <= 0:
            raise ValueError("replayed voxel clouds must be non-empty")
        self.voxel_publish_count += 1
        self.voxel_point_counts[str(snapshot_file)] = {
            "raw": checked_raw_count,
            "inflated": checked_inflated_count,
        }

    def record_preloaded_snapshot(self, snapshot_file: str) -> None:
        self.preloaded_snapshot_file = str(snapshot_file)

    def summary(self) -> Mapping[str, object]:
        """Return a serializable audit that states the replay-only claim boundary."""

        trajectory_ids = sorted(self.trajectory_point_counts)
        checks = {
            "body_path_has_multiple_poses": self.body_pose_count > 1,
            "body_stamps_strictly_increase": self.rejected_body_pose_count == 0,
            "bspline_observed": bool(trajectory_ids),
            "bspline_sampling_errors_zero": self.rejected_bspline_count == 0,
            "all_bspline_paths_use_declared_sample_count": all(
                count == self.sample_count
                for count in self.trajectory_point_counts.values()
            ),
            "sliding_bounds_observed": self.bbox_publish_count > 0,
            "voxel_snapshots_observed": self.voxel_publish_count > 0,
            "voxel_snapshots_nonempty": bool(self.voxel_point_counts)
            and all(
                counts["raw"] > 0 and counts["inflated"] > 0
                for counts in self.voxel_point_counts.values()
            ),
        }
        return {
            "schema_version": 1,
            "status": "PASS" if all(checks.values()) else "FAIL",
            "claim_boundary": (
                "ROS 2 Humble replay-only visualization adapter; source Foxy "
                "voxel coordinates and sliding-bound geometry are republished from "
                "71 Foxy-decoded snapshots without spatial decimation; the display "
                "stream is temporally downsampled from the source topics, and no "
                "planning or simulator computation is performed on macOS"
            ),
            "source_topics": [
                "/quad_0/body_pose",
                "/planning/bspline",
            ],
            "published_topics": [
                "/review/lite3_actual_path",
                "/review/scan_planned_path",
                "/review/sliding_map_bbox",
                "/review/occupancy",
                "/review/occupancy_inflate",
            ],
            "checks": checks,
            "sample_count_per_trajectory": self.sample_count,
            "body_pose_count": self.body_pose_count,
            "rejected_body_pose_count": self.rejected_body_pose_count,
            "first_body_stamp_ns": self.first_body_stamp_ns,
            "last_body_stamp_ns": self.last_body_stamp_ns,
            "trajectory_ids": trajectory_ids,
            "trajectory_point_counts": {
                str(key): self.trajectory_point_counts[key] for key in trajectory_ids
            },
            "trajectory_start_stamps_ns": {
                str(key): self.trajectory_start_stamps_ns[key]
                for key in trajectory_ids
            },
            "rejected_bspline_count": self.rejected_bspline_count,
            "bbox_publish_count": self.bbox_publish_count,
            "bbox_snapshot_files": sorted(self.bbox_snapshot_files),
            "voxel_publish_count": self.voxel_publish_count,
            "preloaded_snapshot_file": self.preloaded_snapshot_file,
            "voxel_point_counts": {
                key: self.voxel_point_counts[key]
                for key in sorted(self.voxel_point_counts)
            },
        }
