#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
RUN_ROOT=${SCAN_V8_RUN_ROOT:-/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human}
CONTINUOUS_RUNNER=${SCAN_V8_CONTINUOUS_RUNNER:-$RUN_ROOT/run_remote_continuous_walk_preview.sh}
BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge

export SCAN_ENTRYPOINT=${SCAN_ENTRYPOINT:-$0}
export SCAN_DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER=run_start
export SCAN_DYNAMIC_OBSTACLE_WAIT_SECONDS=0.0
export SCAN_DYNAMIC_OBSTACLE_HOLD_SECONDS=0.0
export SCAN_DYNAMIC_OBSTACLE_X=${SCAN_DYNAMIC_OBSTACLE_X:--3.6}
export SCAN_DYNAMIC_OBSTACLE_END_X=${SCAN_DYNAMIC_OBSTACLE_END_X:--4.09}
export SCAN_DYNAMIC_OBSTACLE_START_Y=${SCAN_DYNAMIC_OBSTACLE_START_Y:-1.6}
export SCAN_DYNAMIC_OBSTACLE_END_Y=${SCAN_DYNAMIC_OBSTACLE_END_Y:-15.59}
export SCAN_DYNAMIC_OBSTACLE_SPEED=0.8

bash "$CONTINUOUS_RUNNER" "$@"

RESULT_DIR=$RUN_ROOT/results/$RUN_ID
# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export PYTHONPATH=$BRIDGE${PYTHONPATH:+:$PYTHONPATH}
python -u -m lite3_sim_bridge.immediate_walk_review \
  --metrics "$RESULT_DIR/isaac/metrics.jsonl" \
  --sensor-metrics "$RESULT_DIR/isaac/sensor_metrics.jsonl" \
  --ros-events "$RESULT_DIR/ros_events.jsonl" \
  --run-identity "$RESULT_DIR/isaac/run_identity.json" \
  --output "$RESULT_DIR/immediate_walk_audit.json"

sha256sum \
  "$0" \
  "$CONTINUOUS_RUNNER" \
  "$BRIDGE/lite3_sim_bridge/immediate_walk_review.py" \
  "$RESULT_DIR/immediate_walk_audit.json" \
  >"$RESULT_DIR/immediate_walk_audit_sha256.txt"

printf 'causal immediate-walk preview complete: %s\n' "$RUN_ID"
