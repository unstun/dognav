#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
RUN_ROOT=/home/sun/machine-dog-nav-runs/2026-08-13_scan_foxy_isaac_v3

export SCAN_RUN_ROOT=$RUN_ROOT
export SCAN_FOXY_WORKSPACE=$RUN_ROOT/foxy_ws
export SCAN_ACCEPTANCE_CONFIG=${SCAN_V3_ACCEPTANCE_CONFIG:-$RUN_ROOT/acceptance_thresholds_v3_candidate.json}
export SCAN_ROBOT_ASSET=$RUN_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface_isaac.urdf
export SCAN_CANONICAL_ROBOT_ASSET=$RUN_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface.urdf
export SCAN_VIDEO_FPS=17
export SCAN_VIDEO_FRAME_STRIDE=3

bash "$SCRIPT_DIR/run_remote_closed_loop.sh" "$@"

RUN_ID=$1
RESULT_DIR=$RUN_ROOT/results/$RUN_ID
export PYTHONPATH=$RUN_ROOT/integration/lite3_sim_bridge${PYTHONPATH:+:$PYTHONPATH}
python3 -u -m lite3_sim_bridge.acceptance \
  --thresholds "$SCAN_ACCEPTANCE_CONFIG" \
  --metrics "$RESULT_DIR/isaac/metrics.jsonl" \
  --sensor-metrics "$RESULT_DIR/isaac/sensor_metrics.jsonl" \
  --depth-metrics "$RESULT_DIR/isaac/depth_metrics.jsonl" \
  --isaac-report "$RESULT_DIR/isaac/qualification_report.json" \
  --run-identity "$RESULT_DIR/isaac/run_identity.json" \
  --runtime-composition "$RESULT_DIR/isaac/runtime_composition.json" \
  --depth-artifact-root "$RESULT_DIR/isaac" \
  --ros-summary "$RESULT_DIR/ros_summary.json" \
  --video "$RESULT_DIR/closed_loop.mp4" \
  --rosbag "$RESULT_DIR/rosbag" \
  --foxy-log "$RESULT_DIR/foxy_launch.log" \
  --output "$RESULT_DIR/acceptance_report.json"
