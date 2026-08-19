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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(ledger_path: Path, repository_root: Path) -> None:
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if payload.get("protocol_version") != "office-change-control-v1":
        raise ValueError("unexpected protocol_version")

    current = payload.get("current_working_revision")
    if not isinstance(current, dict):
        raise ValueError("current_working_revision must be an object")
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
        if run.get("revision") != revision and run.get("legacy_unversioned") is not True:
            raise ValueError(
                f"run {run_id} must map to the current revision or be explicitly legacy-unversioned"
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
