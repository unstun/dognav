#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from pathlib import Path


REVISION_PATTERN = re.compile(r"^office-[rv]\d+\.\d+\.\d+(?:-[a-z0-9-]+)?$")
RUN_STAGE_VALUES = {"smoke", "preflight", "dryrun", "candidate"}
RUN_STATUS_VALUES = {
    "failed",
    "rejected",
    "superseded",
    "human_preflight_review_pending",
    "formal_candidate_automated_passed",
    "human_accepted",
}
REQUIRED_PLANNED_REVISION_FIELDS = {
    "allowed_components",
    "expected_artifacts",
    "automated_gates",
    "unauthorized_actions",
}
GO2_REFERENCE_REVISION = "office-v2.0.1-go2-geometry-preflight"
GO2_REFERENCE_CHANGE_GROUP = "dual_cloud_transport_and_upstream_go2_geometry_reference"
GO2_REFERENCE_COMMIT = "348e8a590a50a5a6bbab8d8c6dcfd171f009be26"
GO2_REFERENCE_VALUES = {
    "grid_map.double_cylinder_radius": 0.25,
    "grid_map.double_cylinder_offset": 0.18,
    "grid_map.body_height": 0.4,
    "grid_map.obstacles_inflation_z_up": 0.1,
    "grid_map.obstacles_inflation_z_down": 0.1,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def validate(ledger_path: Path, repository_root: Path) -> None:
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 3:
        raise ValueError("schema_version must be 3")
    if payload.get("protocol_version") != "office-change-control-v3":
        raise ValueError("unexpected protocol_version")

    revision_history = payload.get("revision_history")
    if not isinstance(revision_history, list) or not revision_history:
        raise ValueError("revision_history must be a nonempty append-only list")
    revision_ids: list[str] = []
    for index, record in enumerate(revision_history):
        if not isinstance(record, dict):
            raise ValueError(f"revision_history[{index}] must be an object")
        record_revision = record.get("revision")
        if (
            not isinstance(record_revision, str)
            or REVISION_PATTERN.fullmatch(record_revision) is None
        ):
            raise ValueError(f"revision_history[{index}].revision is invalid")
        if record_revision in revision_ids:
            raise ValueError(f"duplicate revision: {record_revision}")
        expected_parent = None if index == 0 else revision_ids[-1]
        if record.get("parent_revision") != expected_parent:
            raise ValueError(
                f"revision {record_revision} parent must be {expected_parent!r}"
            )
        is_baseline = record.get("normalization_baseline") is True
        if is_baseline != (index == 0):
            raise ValueError("only the first revision may be the normalization baseline")
        for key in (
            "status",
            "source_commit",
            "source_commit_state",
            "canonical_branch",
            "artifact_state",
            "change_group",
            "claim_boundary",
        ):
            if not record.get(key):
                raise ValueError(f"revision {record_revision}.{key} is required")
        if re.fullmatch(r"[0-9a-f]{40}", str(record["source_commit"])) is None:
            raise ValueError(f"revision {record_revision}.source_commit must be full SHA-1")
        if not isinstance(record.get("frozen_invariants"), list) or not record[
            "frozen_invariants"
        ]:
            raise ValueError(f"revision {record_revision}.frozen_invariants must be nonempty")
        if not is_baseline:
            expected_change_group = (
                GO2_REFERENCE_CHANGE_GROUP
                if record_revision == GO2_REFERENCE_REVISION
                else "golden_dualview_delivery_reliability"
            )
            if record.get("change_group") != expected_change_group:
                raise ValueError(
                    f"revision {record_revision} must declare change_group "
                    f"{expected_change_group!r}"
                )
            if not record.get("planned_run_id"):
                raise ValueError(f"revision {record_revision}.planned_run_id is required")
            if not isinstance(record.get("rollback"), dict) or not record["rollback"]:
                raise ValueError(f"revision {record_revision}.rollback is required")
            for key in REQUIRED_PLANNED_REVISION_FIELDS:
                if not isinstance(record.get(key), list) or not record[key]:
                    raise ValueError(f"revision {record_revision}.{key} must be nonempty")
            if record_revision == GO2_REFERENCE_REVISION:
                for key in (
                    "allowed_files",
                    "frozen_parameters",
                    "borrowed_parameters",
                    "historical_evidence_baseline",
                    "failure_retention",
                ):
                    if not record.get(key):
                        raise ValueError(f"revision {record_revision}.{key} is required")
                borrowed = record["borrowed_parameters"]
                if borrowed.get("profile") != "upstream_go2_reference":
                    raise ValueError("Go2 reference profile name drifted")
                if borrowed.get("official_commit") != GO2_REFERENCE_COMMIT:
                    raise ValueError("Go2 official source commit drifted")
                if borrowed.get("values") != GO2_REFERENCE_VALUES:
                    raise ValueError("Go2 borrowed parameter inventory drifted")
                frozen = record["frozen_parameters"]
                expected_frozen = {
                    "manager_max_vel_mps": 0.5,
                    "manager_max_acc_mps2": 0.5,
                    "manager_max_jerk_mps3": 4.0,
                    "office_map_size_m": [16.0, 16.0, 5.0],
                    "office_local_update_range_m": [6.0, 6.0, 2.5],
                    "office_planning_horizon_m": 8.0,
                    "mid360_hz": 10.0,
                    "mid360_rays_per_scan": 20000,
                    "mid360_range_m": [0.1, 40.0],
                }
                for key, expected in expected_frozen.items():
                    if frozen.get(key) != expected:
                        raise ValueError(f"frozen parameter {key} drifted")
        revision_ids.append(record_revision)

    current = payload.get("current_working_revision")
    if current != revision_ids[-1]:
        raise ValueError("current_working_revision must name the final revision_history entry")
    if not isinstance(current, str) or REVISION_PATTERN.fullmatch(current) is None:
        raise ValueError("current revision does not match the Office revision format")

    human_gate = payload.get("human_gate")
    if human_gate != {"gate": "AC55", "owner": "Dr Sun", "status": "pending"}:
        raise ValueError("AC55 must remain explicitly pending and owned by Dr Sun")
    if payload.get("accepted_revision") is not None or payload.get("formal_candidate") is not None:
        raise ValueError("this preflight ledger cannot name an accepted revision or formal candidate")

    experiment_root = repository_root / payload["source_of_truth"]
    go2_record = revision_history[-1]
    if go2_record.get("revision") != GO2_REFERENCE_REVISION:
        raise ValueError("the Go2 reference revision must remain the history tail")
    baseline = go2_record["historical_evidence_baseline"]
    if _canonical_sha256(revision_history[:-1]) != baseline.get(
        "revision_history_before_canonical_sha256"
    ):
        raise ValueError("historical revision_history prefix drifted")
    runs = payload.get("runs", [])
    historical_run_count = baseline.get("runs_before_count")
    if not isinstance(historical_run_count, int) or historical_run_count < 0:
        raise ValueError("historical run count is missing or invalid")
    if len(runs) < historical_run_count:
        raise ValueError("historical run records were removed")
    if _canonical_sha256(runs[:historical_run_count]) != baseline.get(
        "runs_before_canonical_sha256"
    ):
        raise ValueError("historical run records drifted")

    protected_files = {
        "r2_0_1_revision_markdown_sha256": experiment_root
        / "revisions/office-r2.0.1-preflight.md",
        "r2_0_1_revision_manifest_sha256": experiment_root
        / "revisions/office-r2.0.1-preflight.manifest.json",
        "r2_0_1_recursive_manifest_sha256": experiment_root
        / "revisions/office-r2.0.1-preflight.local-recursive-sha256.txt",
        "r2_0_1_master_video_sha256": experiment_root
        / "results/office_crowd_r2_0_1_live_cloud_transfer_preflight06/office_review_third_person_rviz_4k.mp4",
        "r2_0_1_transfer_video_sha256": experiment_root
        / "results/office_crowd_r2_0_1_live_cloud_transfer_preflight06/office_review_third_person_rviz_4k_transfer.mp4",
    }
    for baseline_key, path in protected_files.items():
        expected = baseline.get(baseline_key)
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"historical evidence baseline {baseline_key} is malformed")
        if not path.is_file():
            raise ValueError(f"missing protected historical evidence: {path}")
        actual = _sha256(path)
        if actual != expected:
            raise ValueError(f"protected historical evidence drifted: {path}")

    run_ids: set[str] = set()
    for run in payload.get("runs", []):
        run_id = run.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("every run requires a nonempty run_id")
        if run_id in run_ids:
            raise ValueError(f"duplicate run_id: {run_id}")
        run_ids.add(run_id)
        if (
            run.get("revision") not in revision_ids
            and run.get("legacy_unversioned") is not True
        ):
            raise ValueError(
                f"run {run_id} must map to revision_history or be explicitly legacy-unversioned"
            )
        if run.get("stage") not in RUN_STAGE_VALUES:
            raise ValueError(f"run {run_id} has an invalid stage")
        if run.get("status") not in RUN_STATUS_VALUES:
            raise ValueError(f"run {run_id} has an invalid status")
        if run.get("immutable") is not True:
            raise ValueError(f"run {run_id} must be immutable")
        for evidence in run.get("evidence", []):
            relative_path = evidence.get("path")
            expected_hash = evidence.get("sha256")
            if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
                raise ValueError(f"run {run_id} has malformed evidence")
            evidence_path = experiment_root / relative_path
            if not evidence_path.is_file():
                raise ValueError(f"missing local evidence: {evidence_path}")
            actual_hash = _sha256(evidence_path)
            if actual_hash != expected_hash:
                raise ValueError(
                    f"evidence hash mismatch for {evidence_path}: {actual_hash} != {expected_hash}"
                )

    next_action = payload.get("next_action")
    if not isinstance(next_action, dict):
        raise ValueError("next_action must be an object")
    if next_action.get("full_run_authorized") is not False:
        raise ValueError("full_run_authorized must remain false before fresh approval")
    if next_action.get("formal_candidate_authorized") is not False:
        raise ValueError("formal_candidate_authorized must remain false before fresh approval")
    if next_action.get("flat_short_regression_authorized") is not True:
        raise ValueError("flat_short_regression_authorized must reflect Dr Sun approval")
    if next_action.get("nonflat_preflight_authorized") is not False:
        raise ValueError("nonflat_preflight_authorized must remain false before fresh approval")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Office revision ledger")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args()
    validate(args.ledger.resolve(), args.repository_root.resolve())
    print(f"PASS: {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
