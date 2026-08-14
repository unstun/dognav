#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
RUN_ROOT=${SCAN_V5_RUN_ROOT:-/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v5}
BASE_RUNNER=${SCAN_V5_BASE_RUNNER:-$RUN_ROOT/run_remote_closed_loop.sh}

export SCAN_RUN_ROOT=$RUN_ROOT
export SCAN_ENTRYPOINT=$0
export SCAN_FOXY_WORKSPACE=$RUN_ROOT/foxy_ws
export SCAN_ACCEPTANCE_CONFIG=${SCAN_V5_ACCEPTANCE_CONFIG:-$RUN_ROOT/acceptance_thresholds_v5_candidate.json}
export SCAN_ROBOT_ASSET=$RUN_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface_isaac.urdf
export SCAN_CANONICAL_ROBOT_ASSET=$RUN_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface.urdf
export SCAN_COURSE=forest_gen_nav
export SCAN_PLANNER_CONFIG_REL=src/plan_manage/config/foxy_isaac_forest_v5_planner.yaml
export SCAN_CONTROLLER_CONFIG_REL=src/plan_manage/config/foxy_isaac_controller.yaml
export SCAN_FOREST_GEN_ROOT=$RUN_ROOT/source/forest_gen
export SCAN_STRIPE_KIT_ROOT=$RUN_ROOT/source/STRIPE-kit
export SCAN_FOREST_ASSET_PATH=$SCAN_FOREST_GEN_ROOT/models
export SCAN_TERRAIN_FILTER_CELL_SIZE=${SCAN_TERRAIN_FILTER_CELL_SIZE:-0.30}
export SCAN_TERRAIN_FILTER_HEIGHT_THRESHOLD=${SCAN_TERRAIN_FILTER_HEIGHT_THRESHOLD:-0.22}
export SCAN_TERRAIN_FILTER_NEIGHBOR_CELLS=${SCAN_TERRAIN_FILTER_NEIGHBOR_CELLS:-1}
export SCAN_TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS=${SCAN_TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS:-2}
export SCAN_VIDEO_FPS=17
export SCAN_VIDEO_FRAME_STRIDE=3

bash "$BASE_RUNNER" "$@"

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
