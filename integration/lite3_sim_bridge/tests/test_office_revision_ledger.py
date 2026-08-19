import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = (
    REPOSITORY_ROOT
    / ".pipeline"
    / "experiments"
    / "2026-08-17_office_l0_scan_crowd"
)
LEDGER_PATH = EXPERIMENT_ROOT / "revision_ledger.json"
VALIDATOR_PATH = EXPERIMENT_ROOT / "validate_revision_ledger.py"

SPEC = importlib.util.spec_from_file_location(
    "office_revision_ledger_validator",
    VALIDATOR_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load revision-ledger validator: {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class OfficeRevisionLedgerTest(unittest.TestCase):
    def _write_payload(self, payload: dict, directory: str) -> Path:
        path = Path(directory) / "revision_ledger.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_current_ledger_and_evidence_hashes_pass(self) -> None:
        VALIDATOR.validate(LEDGER_PATH, REPOSITORY_ROOT)

    def test_unauthorized_full_run_promotion_fails(self) -> None:
        payload = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        payload["next_action"]["full_run_authorized"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_payload(payload, directory)
            with self.assertRaisesRegex(ValueError, "full_run_authorized"):
                VALIDATOR.validate(path, REPOSITORY_ROOT)

    def test_evidence_hash_drift_fails(self) -> None:
        payload = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        payload["runs"][1]["evidence"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_payload(payload, directory)
            with self.assertRaisesRegex(ValueError, "evidence hash mismatch"):
                VALIDATOR.validate(path, REPOSITORY_ROOT)


if __name__ == "__main__":
    unittest.main()
