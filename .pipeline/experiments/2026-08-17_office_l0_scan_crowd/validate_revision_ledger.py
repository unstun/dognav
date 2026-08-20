#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from pathlib import Path


REVISION_PATTERN = re.compile(r"^office-r\d+\.\d+\.\d+(?:-[a-z0-9-]+)?$")
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(ledger_path: Path, repository_root: Path) -> None:
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError("schema_version must be 2")
    if payload.get("protocol_version") != "office-change-control-v2":
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
            if record.get("change_group") != "golden_dualview_delivery_reliability":
                raise ValueError(
                    f"revision {record_revision} must declare exactly the authorized change group"
                )
            if not record.get("planned_run_id"):
                raise ValueError(f"revision {record_revision}.planned_run_id is required")
            if not isinstance(record.get("rollback"), dict) or not record["rollback"]:
                raise ValueError(f"revision {record_revision}.rollback is required")
            for key in REQUIRED_PLANNED_REVISION_FIELDS:
                if not isinstance(record.get(key), list) or not record[key]:
                    raise ValueError(f"revision {record_revision}.{key} must be nonempty")
        revision_ids.append(record_revision)

    current = payload.get("current_working_revision")
    if not isinstance(current, dict):
        raise ValueError("current_working_revision must be an object")
    if current != revision_history[-1]:
        raise ValueError("current_working_revision must equal the final revision_history entry")
    revision = current.get("revision")
    if not isinstance(revision, str) or REVISION_PATTERN.fullmatch(revision) is None:
        raise ValueError("current revision does not match the Office revision format")
    for key in ("status", "source_commit", "source_commit_state", "change_group", "claim_boundary"):
        if not current.get(key):
            raise ValueError(f"current_working_revision.{key} is required")
    if not isinstance(current.get("frozen_invariants"), list) or not current["frozen_invariants"]:
        raise ValueError("current_working_revision.frozen_invariants must be nonempty")

    human_gate = payload.get("human_gate")
    if human_gate != {"gate": "AC55", "owner": "Dr Sun", "status": "pending"}:
        raise ValueError("AC55 must remain explicitly pending and owned by Dr Sun")
    if payload.get("accepted_revision") is not None or payload.get("formal_candidate") is not None:
        raise ValueError("this preflight ledger cannot name an accepted revision or formal candidate")

    experiment_root = repository_root / payload["source_of_truth"]
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
