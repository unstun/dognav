#!/usr/bin/env python3
"""Validate a Lite3 experiment archive note.

This is intentionally small and flexible: by default it catches only missing
minimum sections and obvious unfilled placeholders. Use --strict for full notes.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_FRONTMATTER = [
    "date",
    "experiment_id",
    "version_alias",
    "status",
    "source_of_truth",
]

REQUIRED_HEADINGS = [
    "## One-line identity",
    "## Minimum Facts",
    "## Artifact Map",
    "## Claim Boundary",
]

STRICT_HEADINGS = [
    "### Lineage",
    "### Terrain And Distribution",
    "### Commands",
    "### Metrics And Curves",
    "### Double-End Sync Gate",
]

PLACEHOLDER_PATTERNS = [
    r"<[^>\n]+>",
    r"\bTODO\b",
    r"\bTBD\b",
]

COMPLETE_STATUSES = {"archived", "complete", "completed"}
TRAINING_PHASES = {"training", "reproduction"}


def find_repo_root(path: Path) -> Path | None:
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def git_tracked(repo_root: Path, path: Path) -> bool:
    rel_path = path.relative_to(repo_root)
    if path.is_dir():
        result = subprocess.run(
            ["git", "ls-files", "--", str(rel_path)],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return bool(result.stdout.strip())

    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", str(rel_path)],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def has_file(root: Path, patterns: list[str]) -> bool:
    return any(path.is_file() for pattern in patterns for path in root.glob(pattern))


def validate_artifact_package(
    archive_path: Path,
    frontmatter: dict[str, str],
    errors: list[str],
) -> None:
    status = frontmatter.get("status", "").strip().lower()
    if status not in COMPLETE_STATUSES:
        return

    experiment_id = frontmatter.get("experiment_id", "").strip()
    if not experiment_id or experiment_id.startswith("<"):
        return

    repo_root = find_repo_root(archive_path.resolve())
    if repo_root is None:
        errors.append("cannot find git repo root for artifact gate")
        return

    artifact_root = repo_root / "artifacts" / experiment_id
    if not artifact_root.is_dir():
        errors.append(f"missing result package: artifacts/{experiment_id}/")
        return

    if not git_tracked(repo_root, artifact_root):
        errors.append(f"result package is not tracked by git: artifacts/{experiment_id}/")

    required_paths = [
        artifact_root / "README.md",
        artifact_root / "manifests",
    ]
    for path in required_paths:
        rel_path = path.relative_to(repo_root)
        if not path.exists():
            errors.append(f"missing result package item: {rel_path}")
        elif not git_tracked(repo_root, path):
            errors.append(f"result package item is not tracked by git: {rel_path}")

    phase = frontmatter.get("phase", "").strip().lower()
    if phase in TRAINING_PHASES:
        required_evidence = {
            "checkpoint": ["tracked_checkpoints/**/*.pt", "tracked_checkpoints/**/*.pth"],
            "run logs": [
                "tracked_logs/**/*stdout*",
                "tracked_logs/**/*stderr*",
                "tracked_logs/**/*.log",
                "tracked_logs/**/*.txt",
            ],
            "tensorboard": ["tensorboard/**/events.out.tfevents*"],
            "manifest": ["manifests/*.sha256", "manifests/*manifest*", "manifests/*command*"],
        }
    else:
        required_evidence = {
            "result media or plot": ["videos/**/*", "frames/**/*", "plots/**/*"],
            "manifest": ["manifests/*.sha256", "manifests/*manifest*", "manifests/*command*"],
        }

    for label, patterns in required_evidence.items():
        if not has_file(artifact_root, patterns):
            errors.append(f"missing result package evidence: {label}")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow template placeholders; useful only when checking template shape.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also require recommended detail sections for audit-heavy archives.",
    )
    args = parser.parse_args()

    if not args.archive.is_file():
        print(f"missing file: {args.archive}", file=sys.stderr)
        return 2

    text = args.archive.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    errors: list[str] = []

    for key in REQUIRED_FRONTMATTER:
        if key not in frontmatter or not frontmatter[key]:
            errors.append(f"missing frontmatter key: {key}")

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing section: {heading}")

    if args.strict:
        for heading in STRICT_HEADINGS:
            if heading not in text:
                errors.append(f"missing strict section: {heading}")

    if not args.allow_placeholders:
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, text):
                errors.append(f"unfilled placeholder pattern: {pattern}")

    validate_artifact_package(args.archive, frontmatter, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"archive ok: {args.archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
