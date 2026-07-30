#!/usr/bin/env python3
"""Slice every declared Lite3 1:4 print part with PrusaSlicer."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
BUILD_ROOT = Path(os.environ.get("LITE3_PRINT_BUILD_ROOT", ROOT)).resolve()
SLICER = Path(
    os.environ.get(
        "LITE3_PRUSASLICER",
        "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
    )
)
CONFIG = ROOT / "slicer" / "PrusaSlicer_2.9.6_FDM_0.4mm.ini"
DATA_DIR = BUILD_ROOT / "slicer" / "prusaslicer-data"
GCODE_DIR = BUILD_ROOT / "slicer" / "gcode"
REPORT_PATH = BUILD_ROOT / "reports" / "slice_report.json"
PRINT_DIR = BUILD_ROOT / "models" / "print_1_4"

EXPECTED_PARTS = {
    "ASSEMBLY_PINS",
    "CAMERA_CARRIER_PLATE",
    "CAMERA_FASTENERS",
    "CAMERA_MOUNT_BRACKET",
    "FACTORY_INTERFACE",
    "FL_HIP",
    "FL_SHANK",
    "FL_THIGH",
    "FRONT_CAMERA_BAR",
    "FR_HIP",
    "FR_SHANK",
    "FR_THIGH",
    "HL_HIP",
    "HL_SHANK",
    "HL_THIGH",
    "HR_HIP",
    "HR_SHANK",
    "HR_THIGH",
    "TORSO",
    "UPPER_LIDAR_MODULE",
}

METADATA_PATTERNS = {
    "filament_used_mm": re.compile(r"^; filament used \[mm\] = (.+)$"),
    "filament_used_cm3": re.compile(r"^; filament used \[cm3\] = (.+)$"),
    "filament_used_g": re.compile(r"^; total filament used \[g\] = (.+)$"),
    "estimated_printing_time": re.compile(
        r"^; estimated printing time \(normal mode\) = (.+)$"
    ),
}

KNOWN_NONBLOCKING_FALLBACKS = (
    "Detected missing Voronoi vertex, input polygons will be rotated back and forth.",
    "Detected non-planar Voronoi diagram, input polygons will be rotated back and forth.",
    "Reversing even wall line causes it to be printed CCW instead of CW!",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_gcode(path: Path) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    extrusion_moves = 0
    layer_changes = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.rstrip("\n")
            if stripped.startswith(";LAYER_CHANGE"):
                layer_changes += 1
            if stripped.startswith(("G0 ", "G1 ")) and " E" in stripped:
                extrusion_moves += 1
            for name, pattern in METADATA_PATTERNS.items():
                match = pattern.match(stripped)
                if match:
                    metadata[name] = match.group(1)
    return {
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "layer_changes": layer_changes,
        "extrusion_moves": extrusion_moves,
        "metadata": metadata,
        "nonempty_toolpath": layer_changes > 0 and extrusion_moves > 0,
    }


def main() -> int:
    if not SLICER.is_file():
        raise FileNotFoundError(SLICER)
    if not CONFIG.is_file():
        raise FileNotFoundError(CONFIG)
    actual_parts = {path.stem for path in PRINT_DIR.glob("*.stl")}
    if actual_parts != EXPECTED_PARTS:
        raise ValueError(
            "Print part set mismatch: "
            f"missing={sorted(EXPECTED_PARTS - actual_parts)} "
            f"unexpected={sorted(actual_parts - EXPECTED_PARTS)}"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GCODE_DIR.mkdir(parents=True, exist_ok=True)
    for stale_gcode in GCODE_DIR.glob("*.gcode"):
        if stale_gcode.stem not in EXPECTED_PARTS:
            stale_gcode.unlink()
    version_result = subprocess.run(
        [str(SLICER), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    version_line = (version_result.stdout or version_result.stderr).splitlines()[0]

    parts: dict[str, Any] = {}
    failures: list[str] = []
    for index, name in enumerate(sorted(EXPECTED_PARTS), start=1):
        stl_path = PRINT_DIR / f"{name}.stl"
        gcode_path = GCODE_DIR / f"{name}.gcode"
        command = [
            str(SLICER),
            "--datadir",
            str(DATA_DIR),
            "--load",
            str(CONFIG),
            "--threads",
            # Four workers avoid a transient PrusaSlicer signal-5 exit seen
            # after the preceding 19 parts while retaining deterministic output.
            str(max(1, min(4, os.cpu_count() or 1))),
            "--loglevel",
            "2",
            "--export-gcode",
            "--output",
            str(gcode_path),
            str(stl_path),
        ]
        print(f"slice={index}/{len(EXPECTED_PARTS)} part={name}", flush=True)
        result = subprocess.run(command, capture_output=True, text=True)
        log = "\n".join(
            piece.strip()
            for piece in (result.stdout, result.stderr)
            if piece.strip()
        )
        warning_lines = [
            line
            for line in log.splitlines()
            if re.search(r"\b(warning|error|repair|empty)\b", line, re.I)
        ]
        nonblocking_fallback_lines = [
            line
            for line in warning_lines
            if any(message in line for message in KNOWN_NONBLOCKING_FALLBACKS)
        ]
        blocking_diagnostic_lines = [
            line
            for line in warning_lines
            if line not in nonblocking_fallback_lines
        ]
        part_report: dict[str, Any] = {
            "input_stl": str(stl_path),
            "input_sha256": sha256(stl_path),
            "gcode": str(gcode_path),
            "returncode": result.returncode,
            "warning_lines": warning_lines,
            "nonblocking_slicer_fallback_lines": nonblocking_fallback_lines,
            "blocking_diagnostic_lines": blocking_diagnostic_lines,
            "slicer_log": log,
        }
        if result.returncode == 0 and gcode_path.is_file():
            part_report.update(parse_gcode(gcode_path))
        else:
            part_report["nonempty_toolpath"] = False
        if (
            result.returncode != 0
            or blocking_diagnostic_lines
            or not part_report["nonempty_toolpath"]
        ):
            failures.append(name)
        parts[name] = part_report
        print(
            f"slice_result={name} returncode={result.returncode} "
            f"diagnostics={len(warning_lines)} "
            f"blocking={len(blocking_diagnostic_lines)} "
            f"nonempty={part_report['nonempty_toolpath']}",
            flush=True,
        )

    report = {
        "schema_version": 1,
        "artifact_label": "printable_static_replica",
        "slicer": version_line,
        "slicer_path": str(SLICER),
        "config": str(CONFIG),
        "config_sha256": sha256(CONFIG),
        "declared_part_count": len(EXPECTED_PARTS),
        "passed": not failures,
        "failed_parts": failures,
        "parts": parts,
        "claim_boundary": (
            "Successful command-line slicing proves non-empty FDM toolpaths "
            "under the declared generic profile. It does not prove physical "
            "fit, printer calibration, material performance, or surface finish."
        ),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"passed={report['passed']}", flush=True)
    print(f"failed_parts={','.join(failures)}", flush=True)
    print(f"report={REPORT_PATH}", flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
