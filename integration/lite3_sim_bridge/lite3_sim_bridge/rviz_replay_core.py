"""State and audit helpers for the Humble RViz replay adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class ReplayAuditState:
    """Track evidence-preserving conversions performed during one bag replay."""

    sample_count: int
    source_mode: str = "replay"
    require_live_lidar: bool = False
    require_voxel_snapshots: bool = True
    require_root_transform: bool = False
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
    live_lidar_publish_count: int = 0
    preloaded_snapshot_file: str | None = None
    current_pose_publish_count: int = 0
    root_transform_publish_count: int = 0

    def __post_init__(self) -> None:
        if self.source_mode not in ("replay", "live"):
            raise ValueError("source_mode must be replay or live")

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

    def accept_current_pose(self, *, root_transform_published: bool) -> None:
        self.current_pose_publish_count += 1
        self.root_transform_publish_count += int(root_transform_published)

    def reject_bspline(self) -> None:
        self.rejected_bspline_count += 1

    def accept_bbox_snapshot(self, snapshot_file: str) -> None:
        self.bbox_publish_count += 1
        self.bbox_snapshot_files.add(str(snapshot_file))

    def accept_voxel_snapshot(
        self,
        snapshot_file: str,
        raw_point_count: int,
        inflated_point_count: int,
        live_point_count: int = 0,
    ) -> None:
        checked_raw_count = int(raw_point_count)
        checked_inflated_count = int(inflated_point_count)
        checked_live_count = int(live_point_count)
        if checked_raw_count <= 0 or checked_inflated_count <= 0:
            raise ValueError("replayed voxel clouds must be non-empty")
        if checked_live_count < 0:
            raise ValueError("replayed live LiDAR count must not be negative")
        if self.require_live_lidar and checked_live_count <= 0:
            raise ValueError("required replayed live LiDAR cloud must be non-empty")
        self.voxel_publish_count += 1
        self.live_lidar_publish_count += int(checked_live_count > 0)
        self.voxel_point_counts[str(snapshot_file)] = {
            "raw": checked_raw_count,
            "inflated": checked_inflated_count,
            "live_lidar": checked_live_count,
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
            "current_pose_matches_body_path": (
                self.current_pose_publish_count == self.body_pose_count
            ),
        }
        if self.require_root_transform:
            checks["root_transform_matches_body_path"] = (
                self.root_transform_publish_count == self.body_pose_count
            )
        if self.require_voxel_snapshots:
            checks.update(
                {
                    "sliding_bounds_observed": self.bbox_publish_count > 0,
                    "voxel_snapshots_observed": self.voxel_publish_count > 0,
                    "voxel_snapshots_nonempty": bool(self.voxel_point_counts)
                    and all(
                        counts["raw"] > 0
                        and counts["inflated"] > 0
                        and (
                            not self.require_live_lidar
                            or counts["live_lidar"] > 0
                        )
                        for counts in self.voxel_point_counts.values()
                    ),
                    "live_lidar_observed_when_required": (
                        not self.require_live_lidar
                        or self.live_lidar_publish_count > 0
                    ),
                }
            )
        published_topics = [
            "/review/lite3_actual_path",
            "/review/lite3_current_pose",
            "/review/scan_planned_path",
            "/review/sliding_map_bbox",
            "/review/occupancy",
            "/review/occupancy_inflate",
        ]
        if self.live_lidar_publish_count > 0:
            published_topics.append("/review/live_lidar")
        if self.root_transform_publish_count > 0:
            published_topics.append("/tf:world_to_TORSO")
        if self.source_mode == "live":
            claim_boundary = (
                "ROS 2 Foxy live visualization adapter; the SCAN planned path is "
                "sampled from each received /planning/bspline message, while the "
                "actual path, current pose, and robot-root transform come from "
                "/quad_0/body_pose in the same run; no planning, simulator stepping, "
                "or post-render path drawing is performed"
            )
        else:
            claim_boundary = (
                "ROS 2 Humble replay-only visualization adapter; source Foxy "
                "live LiDAR, voxel coordinates, and sliding-bound geometry are "
                f"republished from {self.voxel_publish_count} Foxy-decoded snapshots "
                "without spatial decimation; the display stream is temporally "
                "downsampled from the source topics, and no planning or simulator "
                "computation is performed on macOS"
            )
        return {
            "schema_version": 2,
            "status": "PASS" if all(checks.values()) else "FAIL",
            "claim_boundary": claim_boundary,
            "source_mode": self.source_mode,
            "source_topics": [
                "/quad_0/cloud",
                "/quad_0/body_pose",
                "/planning/bspline",
            ],
            "published_topics": published_topics,
            "checks": checks,
            "require_live_lidar": self.require_live_lidar,
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
            "live_lidar_publish_count": self.live_lidar_publish_count,
            "current_pose_publish_count": self.current_pose_publish_count,
            "root_transform_publish_count": self.root_transform_publish_count,
            "preloaded_snapshot_file": self.preloaded_snapshot_file,
            "voxel_point_counts": {
                key: self.voxel_point_counts[key]
                for key in sorted(self.voxel_point_counts)
            },
        }
