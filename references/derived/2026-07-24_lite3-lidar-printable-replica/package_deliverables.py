#!/usr/bin/env python3
"""Package the current verified Lite3 master and 1:4 print deliverables."""

from __future__ import annotations

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
PACKAGES = ROOT / "packages"

COMMON = (
    "README.md",
    "ASSEMBLY.md",
    "print_parameters.json",
    "requirements.txt",
    "build_printable_replica.py",
    "validate_printable_replica.py",
    "prepare_official_sensor_meshes.py",
    "prepare_render_meshes.py",
    "render_printable_replica.py",
    "compare_clean_rebuild.py",
    "slice_print_parts.py",
    "package_deliverables.py",
    "make_comparison_sheet.py",
    "make_print_details_sheet.py",
)

REPORTS = (
    "reports/build_report.json",
    "reports/validation_report.json",
    "reports/slice_report.json",
    "reports/rebuild_comparison.json",
)

MASTER_EVIDENCE = (
    "evidence/lite3-lidar-printable-comparison.png",
    "evidence/lite3-lidar-print-details.png",
    "evidence/visual-reference-isometric.png",
    "evidence/visual-reference-front.png",
    "evidence/visual-reference-rear.png",
    "evidence/visual-reference-left.png",
    "evidence/visual-reference-right.png",
    "evidence/visual-reference-top.png",
    "evidence/visual-reference-upper-isometric.png",
    "evidence/visual-reference-upper-top.png",
    "evidence/visual-reference-upper-front.png",
    "evidence/visual-reference-mid360-isometric.png",
    "evidence/visual-reference-mid360-side.png",
    "evidence/jetson-agx-orin-isometric.png",
    "evidence/jetson-agx-orin-front.png",
    "evidence/jetson-agx-orin-rear.png",
    "evidence/jetson-agx-orin-left.png",
    "evidence/jetson-agx-orin-right.png",
    "evidence/jetson-agx-orin-top.png",
    "evidence/body-diagnostic-current-printable-isometric.png",
    "evidence/body-diagnostic-official-source-isometric.png",
)

PRINT_EVIDENCE = (
    "evidence/lite3-lidar-printable-comparison.png",
    "evidence/lite3-lidar-print-details.png",
    "evidence/printable-layout-top.png",
    "evidence/printable-layout-isometric.png",
    "evidence/printable-assembly-isometric.png",
    "evidence/printable-assembly-left.png",
    "evidence/printable-assembly-upper-isometric.png",
    "evidence/visual-reference-isometric.png",
    "evidence/visual-reference-upper-isometric.png",
    "evidence/visual-reference-upper-top.png",
    "evidence/visual-reference-upper-front.png",
    "evidence/jetson-agx-orin-isometric.png",
    "evidence/jetson-agx-orin-front.png",
    "evidence/jetson-agx-orin-left.png",
    "evidence/jetson-agx-orin-top.png",
    "evidence/body-diagnostic-current-printable-isometric.png",
    "evidence/body-diagnostic-official-source-isometric.png",
)


def existing_paths(relative_paths: tuple[str, ...]) -> list[Path]:
    paths = [ROOT / relative_path for relative_path in relative_paths]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing package inputs: "
            + ", ".join(str(path.relative_to(ROOT)) for path in missing)
        )
    return paths


def write_package(name: str, paths: list[Path]) -> None:
    PACKAGES.mkdir(parents=True, exist_ok=True)
    output = PACKAGES / name
    temporary = PACKAGES / f".{name}.tmp"
    with zipfile.ZipFile(
        temporary,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=True,
    ) as archive:
        for path in sorted(set(paths)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    temporary.replace(output)
    print(f"package={output} size_bytes={output.stat().st_size}", flush=True)


def main() -> None:
    common = existing_paths(COMMON)
    reports = existing_paths(REPORTS)
    master_paths = [
        *common,
        *reports,
        *existing_paths(MASTER_EVIDENCE),
        *sorted((ROOT / "models/master_1_1").glob("*")),
        ROOT / "models/reference/lite3_lidar_1_1_reference.3mf",
        ROOT / "models/reference/lite3_lidar_1_1_reference.glb",
    ]
    print_paths = [
        *common,
        *reports,
        *existing_paths(PRINT_EVIDENCE),
        ROOT / "slicer/PrusaSlicer_2.9.6_FDM_0.4mm.ini",
        *sorted((ROOT / "models/print_1_4").glob("*")),
        ROOT / "models/reference/lite3_lidar_1_4_assembled_reference.stl",
        ROOT / "models/reference/lite3_lidar_1_4_assembled.glb",
        ROOT / "models/reference/lite3_lidar_1_4_print_layout.glb",
    ]
    write_package("lite3_lidar_1_1_master.zip", master_paths)
    write_package("lite3_lidar_1_4_print_kit.zip", print_paths)


if __name__ == "__main__":
    main()
