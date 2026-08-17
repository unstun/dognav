#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
RUN_ROOT=${SCAN_V8_RUN_ROOT:-/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human}
BASE_RUNNER=${SCAN_V8_BASE_RUNNER:-$RUN_ROOT/run_remote_closed_loop.sh}

export SCAN_RUN_ROOT=$RUN_ROOT
export SCAN_ENTRYPOINT=${SCAN_ENTRYPOINT:-$0}
export SCAN_FOXY_WORKSPACE=$RUN_ROOT/foxy_ws
export SCAN_ACCEPTANCE_CONFIG=${SCAN_V8_ACCEPTANCE_CONFIG:-$RUN_ROOT/acceptance_thresholds_v8_official.json}
export SCAN_ROBOT_ASSET=$RUN_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface_isaac.urdf
export SCAN_CANONICAL_ROBOT_ASSET=$RUN_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface.urdf
export SCAN_COURSE=forest_gen_nav_v8_official_human
export SCAN_PLANNER_CONFIG_REL=src/plan_manage/config/foxy_isaac_forest_v7_dynamic_planner.yaml
export SCAN_CONTROLLER_CONFIG_REL=src/plan_manage/config/foxy_isaac_forest_v7_dynamic_controller.yaml
export SCAN_FOREST_GEN_ROOT=$RUN_ROOT/source/forest_gen
export SCAN_STRIPE_KIT_ROOT=$RUN_ROOT/source/STRIPE-kit
export SCAN_FOREST_ASSET_PATH=$SCAN_FOREST_GEN_ROOT/models
export SCAN_TERRAIN_FILTER_CELL_SIZE=${SCAN_TERRAIN_FILTER_CELL_SIZE:-0.30}
export SCAN_TERRAIN_FILTER_HEIGHT_THRESHOLD=${SCAN_TERRAIN_FILTER_HEIGHT_THRESHOLD:-0.22}
export SCAN_TERRAIN_FILTER_NEIGHBOR_CELLS=${SCAN_TERRAIN_FILTER_NEIGHBOR_CELLS:-1}
export SCAN_TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS=${SCAN_TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS:-2}
export SCAN_DYNAMIC_OBSTACLE_X=${SCAN_DYNAMIC_OBSTACLE_X:--2.7}
export SCAN_DYNAMIC_OBSTACLE_START_Y=${SCAN_DYNAMIC_OBSTACLE_START_Y:-2.0}
export SCAN_DYNAMIC_OBSTACLE_END_Y=${SCAN_DYNAMIC_OBSTACLE_END_Y:-4.8}
export SCAN_DYNAMIC_OBSTACLE_WAIT_SECONDS=${SCAN_DYNAMIC_OBSTACLE_WAIT_SECONDS:-0.0}
export SCAN_DYNAMIC_OBSTACLE_SPEED=${SCAN_DYNAMIC_OBSTACLE_SPEED:-0.8}
export SCAN_DYNAMIC_OBSTACLE_RADIUS=${SCAN_DYNAMIC_OBSTACLE_RADIUS:-0.30}
export SCAN_DYNAMIC_OBSTACLE_HEIGHT=${SCAN_DYNAMIC_OBSTACLE_HEIGHT:-1.70}
export SCAN_DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE=${SCAN_DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE:-0.02}
export SCAN_DYNAMIC_OBSTACLE_HOLD_FRACTION=${SCAN_DYNAMIC_OBSTACLE_HOLD_FRACTION:-0.35714285714285715}
export SCAN_DYNAMIC_OBSTACLE_HOLD_SECONDS=${SCAN_DYNAMIC_OBSTACLE_HOLD_SECONDS:-2.5}
export SCAN_OFFICIAL_HUMAN_ANIMATION_MODE=continuous_walk
export SCAN_MAX_VX=1.0
export SCAN_VIDEO_FPS=17
export SCAN_VIDEO_FRAME_STRIDE=3

bash "$BASE_RUNNER" "$@"

RESULT_DIR=$RUN_ROOT/results/$RUN_ID
BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge
# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export PYTHONPATH=$BRIDGE${PYTHONPATH:+:$PYTHONPATH}
python -u -m lite3_sim_bridge.trajectory_review \
  --raw-video "$RESULT_DIR/closed_loop.mp4" \
  --ros-events "$RESULT_DIR/ros_events.jsonl" \
  --metrics "$RESULT_DIR/isaac/metrics.jsonl" \
  --run-identity "$RESULT_DIR/isaac/run_identity.json" \
  --output-video "$RESULT_DIR/closed_loop_review_overlay.mp4" \
  --metadata "$RESULT_DIR/trajectory_review_metadata.json"

printf 'visual preview complete; acceptance intentionally not run: %s\n' "$RUN_ID"
