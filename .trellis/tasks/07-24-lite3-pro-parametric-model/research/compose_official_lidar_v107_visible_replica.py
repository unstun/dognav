#!/usr/bin/env python3
"""Compose official-source versus visible-replica review sheets."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image, ImageOps


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[2]
OUTPUT_ROOT = (
    TASK_ROOT / "evidence/official-lidar-v107-visible-replica-candidate"
)
MANUAL_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-24_lite3-design-drawings/derived"
)
OFFICIAL_MEDIA_ROOT = (
    REPO_ROOT
    / "references/upstream/2026-07-26_lite3-current-lidar-official-us-media"
    / "source/original"
)
BASE_COMPOSER = (
    TASK_ROOT / "research/compose_official_lidar_v107_comparison.py"
)


def load_composer():
    spec = importlib.util.spec_from_file_location(
        "official_lidar_v107_comparison_helpers",
        BASE_COMPOSER,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load comparison helpers from {BASE_COMPOSER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUTPUT_ROOT = OUTPUT_ROOT
    return module


def main() -> None:
    composer = load_composer()
    official_front = Image.open(
        MANUAL_ROOT / "lite3-lidar-v107-front-render-original.png"
    )
    official_side = Image.open(
        MANUAL_ROOT / "lite3-lidar-v107-side-render-original.png"
    )
    official_rear_line = Image.open(
        MANUAL_ROOT / "lite3-lidar-v107-rear-line-art-original.png"
    )
    official_studio = Image.open(
        OFFICIAL_MEDIA_ROOT / "lite3-lidar-current-studio-2048x2048.jpg"
    )
    candidate_front = Image.open(OUTPUT_ROOT / "full-standing-front.png")
    candidate_side = ImageOps.mirror(
        Image.open(OUTPUT_ROOT / "full-standing-side.png")
    )
    candidate_iso = Image.open(OUTPUT_ROOT / "full-standing-isometric.png")

    composer.pair_sheet(
        official_front,
        candidate_front,
        "Front identity: official V1.0.7 vs visible-only replica",
        "Official V1.0.7 manual",
        "Visible replica candidate",
        "official-vs-visible-replica-front.png",
    )
    composer.pair_sheet(
        official_side,
        candidate_side,
        "Side identity: carrier layers and rear Interface placement",
        "Official V1.0.7 manual",
        "Visible replica candidate (mirrored)",
        "official-vs-visible-replica-side.png",
    )
    composer.pair_sheet(
        official_rear_line,
        candidate_iso,
        "Rear-oblique identity: only source-visible geometry",
        "Official V1.0.7 line art",
        "Visible replica candidate",
        "official-vs-visible-replica-rear-oblique.png",
    )
    composer.pair_sheet(
        official_studio,
        candidate_iso,
        "Current official studio view vs visible-only replica",
        "Official current product image",
        "Visible replica candidate",
        "official-current-vs-visible-replica.png",
    )
    for name in (
        "official-vs-visible-replica-front.png",
        "official-vs-visible-replica-side.png",
        "official-vs-visible-replica-rear-oblique.png",
        "official-current-vs-visible-replica.png",
    ):
        print(f"comparison={OUTPUT_ROOT / name}")


if __name__ == "__main__":
    main()
