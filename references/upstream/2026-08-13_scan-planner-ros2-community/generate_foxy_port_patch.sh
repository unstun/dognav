#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(cd "$SCRIPT_DIR/../../.." && pwd)
UPSTREAM_ROOT=references/upstream/2026-08-13_scan-planner-ros2-community/source/SCAN-Planner/src/planner
PORT_ROOT=integration/scan_planner_foxy_ws/src
OUTPUT_PATH=${1:-$SCRIPT_DIR/foxy_port.patch}
if [[ $OUTPUT_PATH != /* ]]; then
  OUTPUT_PARENT=$(cd "$(dirname "$OUTPUT_PATH")" && pwd)
  OUTPUT_PATH=$OUTPUT_PARENT/$(basename "$OUTPUT_PATH")
fi
TEMP_PATH=$(mktemp "${OUTPUT_PATH}.XXXXXX")

cleanup() {
  if [[ -e $TEMP_PATH ]]; then
    rm -f "$TEMP_PATH"
  fi
}
trap cleanup EXIT

cd "$REPOSITORY_ROOT"

for package in \
  bspline_opt \
  path_searching \
  plan_env \
  plan_manage \
  scan_planner_msgs \
  traj_utils; do
  diff_code=0
  diff -ruN \
    --exclude=__pycache__ \
    --exclude='*.pyc' \
    "$UPSTREAM_ROOT/$package" \
    "$PORT_ROOT/$package" \
    >>"$TEMP_PATH" || diff_code=$?
  if (( diff_code != 0 && diff_code != 1 )); then
    exit "$diff_code"
  fi
done

mv "$TEMP_PATH" "$OUTPUT_PATH"
chmod 0644 "$OUTPUT_PATH"
trap - EXIT
