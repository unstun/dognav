#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
DURATION_SECONDS=$2
TELEMETRY_PORT=$3
COMMAND_PORT=$4
ENTRYPOINT=${SCAN_ENTRYPOINT:-$0}

if [[ ! $RUN_ID =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "run id must contain only lowercase letters, digits, underscore, or dash" >&2
  exit 64
fi
if [[ ! $DURATION_SECONDS =~ ^[0-9]+$ ]] || (( DURATION_SECONDS < 1 )); then
  echo "duration must be a positive integer" >&2
  exit 64
fi
for port in "$TELEMETRY_PORT" "$COMMAND_PORT"; do
  if [[ ! $port =~ ^[0-9]+$ ]] || (( port < 1024 || port > 65535 )); then
    echo "ports must be integers within [1024, 65535]" >&2
    exit 64
  fi
done

RUN_ROOT=${SCAN_RUN_ROOT:-/home/sun/machine-dog-nav-runs/2026-08-13_scan_foxy_isaac}
FOXY_WORKSPACE=${SCAN_FOXY_WORKSPACE:-$RUN_ROOT/foxy_ws_clean3}
LOG_DIR=$RUN_ROOT/logs/$RUN_ID
OUTPUT_DIR=$RUN_ROOT/results/$RUN_ID
RUNTIME=${SCAN_V12_RUNTIME:-$RUN_ROOT/source/locomotion_v12/runtime_20260718_recovered}
CHECKPOINT=${SCAN_CHECKPOINT:-$RUN_ROOT/source/locomotion_v12/checkpoint/model_149999.pt}
BRIDGE=${SCAN_BRIDGE:-$RUN_ROOT/integration/lite3_sim_bridge}
ACCEPTANCE_CONFIG=${SCAN_ACCEPTANCE_CONFIG:-$RUN_ROOT/acceptance_thresholds.json}
COURSE=${SCAN_COURSE:-single_box}
PLANNER_CONFIG_REL=${SCAN_PLANNER_CONFIG_REL:-src/plan_manage/config/foxy_isaac_planner.yaml}
CONTROLLER_CONFIG_REL=${SCAN_CONTROLLER_CONFIG_REL:-src/plan_manage/config/foxy_isaac_controller.yaml}
PLANNER_CONFIG=$FOXY_WORKSPACE/$PLANNER_CONFIG_REL
CONTROLLER_CONFIG=$FOXY_WORKSPACE/$CONTROLLER_CONFIG_REL
CONTROLLER_SOURCE=$FOXY_WORKSPACE/src/plan_manage/src/closed_loop_controller.cpp
PROGRESS_SOURCE=$FOXY_WORKSPACE/src/plan_manage/include/plan_manage/trajectory_progress.h
FSM_SOURCE=$FOXY_WORKSPACE/src/plan_manage/src/scan_replan_fsm.cpp
FSM_HEADER=$FOXY_WORKSPACE/src/plan_manage/include/plan_manage/scan_replan_fsm.h
GRID_MAP_SOURCE=$FOXY_WORKSPACE/src/plan_env/src/grid_map.cpp
OCCLUSION_SHADOW_SOURCE=$FOXY_WORKSPACE/src/plan_env/include/plan_env/occlusion_shadow.h
FOXY_LAUNCH_SOURCE=$FOXY_WORKSPACE/src/plan_manage/launch/foxy_isaac_closed_loop.launch.py
FOXY_BRIDGE_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/foxy_bridge_node.py
FOXY_TRANSPORT_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/transport.py
FOXY_PROTOCOL_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/protocol.py
FOXY_COMMAND_STATE_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/command_state.py
FOXY_MONITOR_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/acceptance_monitor_node.py
FOXY_VOXEL_CAPTURE_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/voxel_capture_node.py
FOXY_VOXEL_ROSBAG_QOS=$FOXY_WORKSPACE/src/lite3_sim_bridge/config/voxel_rosbag_qos.yaml
TRAJECTORY_REVIEW_SOURCE=$BRIDGE/lite3_sim_bridge/trajectory_review.py
VOXEL_REVIEW_SOURCE=$BRIDGE/lite3_sim_bridge/voxel_review.py
ISAAC_ADAPTER_CORE_SOURCE=$BRIDGE/lite3_sim_bridge/isaac_adapter_core.py
OFFICIAL_HUMAN_BAKER_SOURCE=$BRIDGE/lite3_sim_bridge/bake_official_human_animation.py
OFFICIAL_HUMAN_CONTRACT_SOURCE=$BRIDGE/lite3_sim_bridge/official_human_contract.py
CONTAINER_NAME=scan-foxy-$RUN_ID
ROS_RUNTIME_SECONDS=$((DURATION_SECONDS * 6 + 120))
VIDEO_FPS=${SCAN_VIDEO_FPS:-25}
VIDEO_FRAME_STRIDE=${SCAN_VIDEO_FRAME_STRIDE:-2}
MAX_VX=${SCAN_MAX_VX:-0.75}
PLANNER_FLOOR_FILTER_MAX_Z=${SCAN_PLANNER_FLOOR_FILTER_MAX_Z:-0.05}
ROBOT_ARGS=()
ROBOT_INPUTS=()
FOREST_ARGS=()
DYNAMIC_ARGS=()
OFFICE_ARGS=()
FOREST_PYTHONPATH=
TERRAIN_FILTER_CELL_SIZE=
TERRAIN_FILTER_HEIGHT_THRESHOLD=
TERRAIN_FILTER_NEIGHBOR_CELLS=
TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS=
DYNAMIC_OBSTACLE_X=
DYNAMIC_OBSTACLE_END_X=
DYNAMIC_OBSTACLE_START_Y=
DYNAMIC_OBSTACLE_END_Y=
DYNAMIC_OBSTACLE_WAIT_SECONDS=
DYNAMIC_OBSTACLE_SPEED=
DYNAMIC_OBSTACLE_RADIUS=
DYNAMIC_OBSTACLE_HEIGHT=
DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE=
DYNAMIC_OBSTACLE_HOLD_FRACTION=
DYNAMIC_OBSTACLE_HOLD_SECONDS=
DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER=${SCAN_DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER:-first_nonzero_body_command}
OFFICIAL_HUMAN_CACHE=
OFFICIAL_HUMAN_CACHE_CONTENT_SHA256=
OFFICIAL_HUMAN_ANIMATION_MODE=${SCAN_OFFICIAL_HUMAN_ANIMATION_MODE:-phase_conditioned}
ENABLE_VOXEL_CAPTURE=${SCAN_ENABLE_VOXEL_CAPTURE:-0}
VOXEL_CAPTURE_PERIOD_SECONDS=${SCAN_VOXEL_CAPTURE_PERIOD_SECONDS:-0.1}
if [[ ! $MAX_VX =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]] \
  || ! awk -v value="$MAX_VX" 'BEGIN { exit !(value > 0.0) }'; then
  echo "SCAN_MAX_VX must be a positive decimal" >&2
  exit 64
fi
if [[ $ENABLE_VOXEL_CAPTURE != 0 && $ENABLE_VOXEL_CAPTURE != 1 ]]; then
  echo "SCAN_ENABLE_VOXEL_CAPTURE must be 0 or 1" >&2
  exit 64
fi
if [[ ! $VOXEL_CAPTURE_PERIOD_SECONDS =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]] \
  || ! awk -v value="$VOXEL_CAPTURE_PERIOD_SECONDS" 'BEGIN { exit !(value > 0.0) }'; then
  echo "SCAN_VOXEL_CAPTURE_PERIOD_SECONDS must be a positive decimal" >&2
  exit 64
fi
if [[ -n ${SCAN_ROBOT_ASSET:-} || -n ${SCAN_CANONICAL_ROBOT_ASSET:-} ]]; then
  if [[ -z ${SCAN_ROBOT_ASSET:-} || -z ${SCAN_CANONICAL_ROBOT_ASSET:-} ]]; then
    echo "both SCAN_ROBOT_ASSET and SCAN_CANONICAL_ROBOT_ASSET are required" >&2
    exit 64
  fi
  ROBOT_ARGS=(
    --robot-asset "$SCAN_ROBOT_ASSET"
    --canonical-robot-asset "$SCAN_CANONICAL_ROBOT_ASSET"
  )
  ROBOT_INPUTS=("$SCAN_ROBOT_ASSET" "$SCAN_CANONICAL_ROBOT_ASSET")
fi

case "$COURSE" in
  flat|single_box)
    ;;
  office_l0_crowd)
    for office_var in SCAN_OFFICE_USD_PATH SCAN_OFFICE_USD_SHA256 \
      SCAN_OFFICE_ROUTE_PATH SCAN_OFFICE_ROUTE_SHA256 \
      SCAN_OFFICE_START_X SCAN_OFFICE_START_Y \
      SCAN_OFFICE_GOAL_X SCAN_OFFICE_GOAL_Y; do
      if [[ -z ${!office_var:-} ]]; then
        echo "office course requires $office_var" >&2
        exit 66
      fi
    done
    OFFICE_ARGS=(
      --office-usd-path "$SCAN_OFFICE_USD_PATH"
      --office-usd-sha256 "$SCAN_OFFICE_USD_SHA256"
      --office-route-path "$SCAN_OFFICE_ROUTE_PATH"
      --office-route-sha256 "$SCAN_OFFICE_ROUTE_SHA256"
      --office-start-xy "$SCAN_OFFICE_START_X" "$SCAN_OFFICE_START_Y"
      --office-goal-xy "$SCAN_OFFICE_GOAL_X" "$SCAN_OFFICE_GOAL_Y"
    )
    ;;
  forest_gen|forest_gen_nav|forest_gen_nav_v6|forest_gen_nav_v7_dynamic|forest_gen_nav_v8_human|forest_gen_nav_v8_official_human)
    FOREST_GEN_ROOT=${SCAN_FOREST_GEN_ROOT:-}
    STRIPE_KIT_ROOT=${SCAN_STRIPE_KIT_ROOT:-}
    FOREST_ASSET_PATH=${SCAN_FOREST_ASSET_PATH:-}
    for forest_path in "$FOREST_GEN_ROOT" "$STRIPE_KIT_ROOT" "$FOREST_ASSET_PATH"; do
      if [[ -z $forest_path || ! -d $forest_path ]]; then
        echo "forest course requires existing SCAN_FOREST_GEN_ROOT, SCAN_STRIPE_KIT_ROOT, and SCAN_FOREST_ASSET_PATH" >&2
        exit 66
      fi
    done
    FOREST_ARGS=(
      --forest-gen-root "$FOREST_GEN_ROOT"
      --stripe-kit-root "$STRIPE_KIT_ROOT"
      --forest-asset-path "$FOREST_ASSET_PATH"
    )
    FOREST_PYTHONPATH=$FOREST_GEN_ROOT:$STRIPE_KIT_ROOT
    if [[ $COURSE == forest_gen_nav || $COURSE == forest_gen_nav_v6 || $COURSE == forest_gen_nav_v7_dynamic || $COURSE == forest_gen_nav_v8_human || $COURSE == forest_gen_nav_v8_official_human ]]; then
      TERRAIN_FILTER_CELL_SIZE=${SCAN_TERRAIN_FILTER_CELL_SIZE:-0.30}
      TERRAIN_FILTER_HEIGHT_THRESHOLD=${SCAN_TERRAIN_FILTER_HEIGHT_THRESHOLD:-0.22}
      TERRAIN_FILTER_NEIGHBOR_CELLS=${SCAN_TERRAIN_FILTER_NEIGHBOR_CELLS:-1}
      TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS=${SCAN_TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS:-2}
      FOREST_ARGS+=(
        --terrain-filter-cell-size "$TERRAIN_FILTER_CELL_SIZE"
        --terrain-filter-height-threshold "$TERRAIN_FILTER_HEIGHT_THRESHOLD"
        --terrain-filter-neighbor-cells "$TERRAIN_FILTER_NEIGHBOR_CELLS"
        --terrain-filter-minimum-neighbor-cells "$TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS"
      )
    fi
    if [[ $COURSE == forest_gen_nav_v7_dynamic || $COURSE == forest_gen_nav_v8_human || $COURSE == forest_gen_nav_v8_official_human ]]; then
      if [[ $DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER != first_nonzero_body_command \
        && $DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER != run_start ]]; then
        echo "unsupported SCAN_DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER: $DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER" >&2
        exit 64
      fi
      DYNAMIC_OBSTACLE_X=${SCAN_DYNAMIC_OBSTACLE_X:--3.0}
      DYNAMIC_OBSTACLE_END_X=${SCAN_DYNAMIC_OBSTACLE_END_X:-$DYNAMIC_OBSTACLE_X}
      DYNAMIC_OBSTACLE_START_Y=${SCAN_DYNAMIC_OBSTACLE_START_Y:-1.2}
      DYNAMIC_OBSTACLE_END_Y=${SCAN_DYNAMIC_OBSTACLE_END_Y:-4.8}
      DYNAMIC_OBSTACLE_WAIT_SECONDS=${SCAN_DYNAMIC_OBSTACLE_WAIT_SECONDS:-0.2}
      DYNAMIC_OBSTACLE_SPEED=${SCAN_DYNAMIC_OBSTACLE_SPEED:-0.8}
      DYNAMIC_OBSTACLE_RADIUS=${SCAN_DYNAMIC_OBSTACLE_RADIUS:-0.30}
      if [[ $COURSE == forest_gen_nav_v8_official_human ]]; then
        DYNAMIC_OBSTACLE_HEIGHT=${SCAN_DYNAMIC_OBSTACLE_HEIGHT:-1.70}
      else
        DYNAMIC_OBSTACLE_HEIGHT=${SCAN_DYNAMIC_OBSTACLE_HEIGHT:-1.50}
      fi
      DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE=${SCAN_DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE:-0.02}
      DYNAMIC_OBSTACLE_HOLD_FRACTION=${SCAN_DYNAMIC_OBSTACLE_HOLD_FRACTION:-0.5}
      DYNAMIC_OBSTACLE_HOLD_SECONDS=${SCAN_DYNAMIC_OBSTACLE_HOLD_SECONDS:-0.0}
      DYNAMIC_ARGS=(
        --dynamic-obstacle-x "$DYNAMIC_OBSTACLE_X"
        --dynamic-obstacle-end-x "$DYNAMIC_OBSTACLE_END_X"
        --dynamic-obstacle-start-y "$DYNAMIC_OBSTACLE_START_Y"
        --dynamic-obstacle-end-y "$DYNAMIC_OBSTACLE_END_Y"
        --dynamic-obstacle-wait-seconds "$DYNAMIC_OBSTACLE_WAIT_SECONDS"
        --dynamic-obstacle-speed "$DYNAMIC_OBSTACLE_SPEED"
        --dynamic-obstacle-radius "$DYNAMIC_OBSTACLE_RADIUS"
        --dynamic-obstacle-height "$DYNAMIC_OBSTACLE_HEIGHT"
        --dynamic-obstacle-terrain-clearance "$DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE"
        --dynamic-obstacle-hold-fraction "$DYNAMIC_OBSTACLE_HOLD_FRACTION"
        --dynamic-obstacle-hold-seconds "$DYNAMIC_OBSTACLE_HOLD_SECONDS"
        --dynamic-obstacle-schedule-trigger "$DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER"
      )
    fi
    ;;
  *)
    echo "unsupported SCAN_COURSE: $COURSE" >&2
    exit 64
    ;;
esac

for required in \
  "$FOXY_WORKSPACE/install/setup.bash" \
  "$ENTRYPOINT" \
  "$CHECKPOINT" \
  "$BRIDGE/lite3_sim_bridge/run_isaac_v12_fallback.py" \
  "$BRIDGE/lite3_sim_bridge/acceptance.py" \
  "$BRIDGE/lite3_sim_bridge/transport.py" \
  "$PLANNER_CONFIG" \
  "$CONTROLLER_CONFIG" \
  "$CONTROLLER_SOURCE" \
  "$PROGRESS_SOURCE" \
  "$FSM_SOURCE" \
  "$FSM_HEADER" \
  "$GRID_MAP_SOURCE" \
  "$OCCLUSION_SHADOW_SOURCE" \
  "$FOXY_LAUNCH_SOURCE" \
  "$FOXY_BRIDGE_SOURCE" \
  "$FOXY_TRANSPORT_SOURCE" \
  "$FOXY_PROTOCOL_SOURCE" \
  "$FOXY_COMMAND_STATE_SOURCE" \
  "$FOXY_MONITOR_SOURCE" \
  "$FOXY_VOXEL_CAPTURE_SOURCE" \
  "$FOXY_VOXEL_ROSBAG_QOS" \
  "$TRAJECTORY_REVIEW_SOURCE" \
  "$VOXEL_REVIEW_SOURCE" \
  "$ISAAC_ADAPTER_CORE_SOURCE" \
  "$OFFICIAL_HUMAN_BAKER_SOURCE" \
  "$OFFICIAL_HUMAN_CONTRACT_SOURCE" \
  "${ROBOT_INPUTS[@]}" \
  "$FOXY_WORKSPACE/build/plan_env/libplan_env.a" \
  "$FOXY_WORKSPACE/build/scan_planner/scan_planner_node" \
  "$FOXY_WORKSPACE/build/scan_planner/closed_loop_controller" \
  "$ACCEPTANCE_CONFIG"; do
  if [[ ! -f $required ]]; then
    echo "required input missing: $required" >&2
    exit 66
  fi
done
if [[ -e $LOG_DIR || -e $OUTPUT_DIR ]]; then
  echo "run output already exists; refusing to overwrite: $RUN_ID" >&2
  exit 73
fi

mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# The official AnimationGraph cannot share the Direct GPU process safely in the
# pinned runtime.  Generate its ControlRig-retargeted pose cache in a bounded,
# isolated Isaac process before the physical Lite3 scene starts.
# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH="$BRIDGE:$RUNTIME/source/rsl_rl:$RUNTIME/source/robot_lab${FOREST_PYTHONPATH:+:$FOREST_PYTHONPATH}${PYTHONPATH:+:$PYTHONPATH}"
if [[ $COURSE == forest_gen_nav_v8_official_human || $COURSE == office_l0_crowd ]]; then
  if [[ $OFFICIAL_HUMAN_ANIMATION_MODE != phase_conditioned \
    && $OFFICIAL_HUMAN_ANIMATION_MODE != continuous_walk ]]; then
    echo "unsupported SCAN_OFFICIAL_HUMAN_ANIMATION_MODE: $OFFICIAL_HUMAN_ANIMATION_MODE" >&2
    exit 64
  fi
  OFFICIAL_HUMAN_CACHE=$OUTPUT_DIR/official_human_retarget_cache.npz
  OFFICIAL_HUMAN_MANIFEST=$OUTPUT_DIR/official_human_retarget_cache.json
  python -u -m lite3_sim_bridge.bake_official_human_animation \
    --output "$OFFICIAL_HUMAN_CACHE" \
    --manifest "$OFFICIAL_HUMAN_MANIFEST" \
    >"$LOG_DIR/official_human_bake.log" 2>&1
  if [[ ! -s $OFFICIAL_HUMAN_CACHE || ! -s $OFFICIAL_HUMAN_MANIFEST ]]; then
    echo "official Biped retarget cache generation failed" >&2
    exit 70
  fi
  OFFICIAL_HUMAN_CACHE_CONTENT_SHA256=$(python -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["cache_content_sha256"])' \
    "$OFFICIAL_HUMAN_MANIFEST")
  DYNAMIC_ARGS+=(
    --official-human-animation-cache "$OFFICIAL_HUMAN_CACHE"
    --official-human-animation-mode "$OFFICIAL_HUMAN_ANIMATION_MODE"
  )
  sha256sum "$OFFICIAL_HUMAN_CACHE" "$OFFICIAL_HUMAN_MANIFEST" \
    >"$OUTPUT_DIR/official_human_cache_sha256.txt"
fi

{
  printf 'duration_seconds=%s\n' "$DURATION_SECONDS"
  printf 'course=%s\n' "$COURSE"
  printf 'planner_config_rel=%s\n' "$PLANNER_CONFIG_REL"
  printf 'controller_config_rel=%s\n' "$CONTROLLER_CONFIG_REL"
  printf 'planner_floor_filter_max_z=%s\n' "$PLANNER_FLOOR_FILTER_MAX_Z"
  printf 'terrain_filter_cell_size=%s\n' "$TERRAIN_FILTER_CELL_SIZE"
  printf 'terrain_filter_height_threshold=%s\n' "$TERRAIN_FILTER_HEIGHT_THRESHOLD"
  printf 'terrain_filter_neighbor_cells=%s\n' "$TERRAIN_FILTER_NEIGHBOR_CELLS"
  printf 'terrain_filter_minimum_neighbor_cells=%s\n' "$TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS"
  printf 'dynamic_obstacle_x=%s\n' "$DYNAMIC_OBSTACLE_X"
  printf 'dynamic_obstacle_end_x=%s\n' "$DYNAMIC_OBSTACLE_END_X"
  printf 'dynamic_obstacle_start_y=%s\n' "$DYNAMIC_OBSTACLE_START_Y"
  printf 'dynamic_obstacle_end_y=%s\n' "$DYNAMIC_OBSTACLE_END_Y"
  printf 'dynamic_obstacle_wait_seconds=%s\n' "$DYNAMIC_OBSTACLE_WAIT_SECONDS"
  printf 'dynamic_obstacle_speed=%s\n' "$DYNAMIC_OBSTACLE_SPEED"
  printf 'dynamic_obstacle_radius=%s\n' "$DYNAMIC_OBSTACLE_RADIUS"
  printf 'dynamic_obstacle_height=%s\n' "$DYNAMIC_OBSTACLE_HEIGHT"
  printf 'dynamic_obstacle_terrain_clearance=%s\n' "$DYNAMIC_OBSTACLE_TERRAIN_CLEARANCE"
  printf 'dynamic_obstacle_hold_fraction=%s\n' "$DYNAMIC_OBSTACLE_HOLD_FRACTION"
  printf 'dynamic_obstacle_hold_seconds=%s\n' "$DYNAMIC_OBSTACLE_HOLD_SECONDS"
  printf 'dynamic_obstacle_schedule_trigger=%s\n' "$DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER"
  printf 'official_human_cache_content_sha256=%s\n' "$OFFICIAL_HUMAN_CACHE_CONTENT_SHA256"
  printf 'official_human_animation_mode=%s\n' "$OFFICIAL_HUMAN_ANIMATION_MODE"
  printf 'video_fps=%s\n' "$VIDEO_FPS"
  printf 'video_frame_stride=%s\n' "$VIDEO_FRAME_STRIDE"
  printf 'max_vx=%s\n' "$MAX_VX"
  printf 'enable_voxel_capture=%s\n' "$ENABLE_VOXEL_CAPTURE"
  printf 'voxel_capture_period_seconds=%s\n' "$VOXEL_CAPTURE_PERIOD_SECONDS"
} >"$OUTPUT_DIR/effective_input.txt"

sha256sum \
  "$0" \
  "$ENTRYPOINT" \
  "$OUTPUT_DIR/effective_input.txt" \
  "$ACCEPTANCE_CONFIG" \
  "$PLANNER_CONFIG" \
  "$CONTROLLER_CONFIG" \
  "$CONTROLLER_SOURCE" \
  "$PROGRESS_SOURCE" \
  "$FSM_SOURCE" \
  "$FSM_HEADER" \
  "$GRID_MAP_SOURCE" \
  "$OCCLUSION_SHADOW_SOURCE" \
  "$FOXY_LAUNCH_SOURCE" \
  "$BRIDGE/lite3_sim_bridge/run_isaac_v12_fallback.py" \
  "$ISAAC_ADAPTER_CORE_SOURCE" \
  "$OFFICIAL_HUMAN_BAKER_SOURCE" \
  "$OFFICIAL_HUMAN_CONTRACT_SOURCE" \
  "$BRIDGE/lite3_sim_bridge/acceptance.py" \
  "$BRIDGE/lite3_sim_bridge/command_state.py" \
  "$BRIDGE/lite3_sim_bridge/transport.py" \
  "$BRIDGE/lite3_sim_bridge/protocol.py" \
  "$BRIDGE/lite3_sim_bridge/foxy_bridge_node.py" \
  "$BRIDGE/lite3_sim_bridge/acceptance_monitor_node.py" \
  "$TRAJECTORY_REVIEW_SOURCE" \
  "$VOXEL_REVIEW_SOURCE" \
  "$FOXY_BRIDGE_SOURCE" \
  "$FOXY_TRANSPORT_SOURCE" \
  "$FOXY_PROTOCOL_SOURCE" \
  "$FOXY_COMMAND_STATE_SOURCE" \
  "$FOXY_MONITOR_SOURCE" \
  "$FOXY_VOXEL_CAPTURE_SOURCE" \
  "$FOXY_VOXEL_ROSBAG_QOS" \
  "${ROBOT_INPUTS[@]}" \
  "$FOXY_WORKSPACE/build/scan_planner/scan_planner_node" \
  "$FOXY_WORKSPACE/build/scan_planner/closed_loop_controller" \
  "$FOXY_WORKSPACE/build/plan_env/libplan_env.a" \
  >"$OUTPUT_DIR/input_sha256.txt"
if [[ -n $FOREST_PYTHONPATH ]]; then
  {
    printf 'forest_gen '
    git -C "$FOREST_GEN_ROOT" rev-parse HEAD
    printf 'stripe_kit '
    git -C "$STRIPE_KIT_ROOT" rev-parse HEAD
    git -C "$FOREST_GEN_ROOT" status --porcelain --untracked-files=no \
      | sed 's/^/forest_gen_status=/'
    git -C "$STRIPE_KIT_ROOT" status --porcelain --untracked-files=no \
      | sed 's/^/stripe_kit_status=/'
  } >"$OUTPUT_DIR/upstream_commits.txt"
fi
nvidia-smi --query-gpu=name,driver_version,memory.total \
  --format=csv,noheader >"$OUTPUT_DIR/gpu_identity.txt"
podman image inspect --format '{{.Id}}' \
  localhost/machine-dog-nav/foxy-scan:20260813 \
  >"$OUTPUT_DIR/container_image_id.txt"

ISAAC_PID=
cleanup() {
  if [[ -n ${ISAAC_PID:-} ]] && kill -0 "$ISAAC_PID" 2>/dev/null; then
    kill -TERM "$ISAAC_PID" 2>/dev/null || true
    wait "$ISAAC_PID" 2>/dev/null || true
  fi
  if podman container exists "$CONTAINER_NAME" 2>/dev/null; then
    podman stop --time 5 "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cd "$RUNTIME"
python -u -m lite3_sim_bridge.run_isaac_v12_fallback \
  --mode external \
  --course "$COURSE" \
  --duration-seconds "$DURATION_SECONDS" \
  --output-dir "$OUTPUT_DIR/isaac" \
  --checkpoint "$CHECKPOINT" \
  --vendored-rsl-rl "$RUNTIME/source/rsl_rl" \
  "${ROBOT_ARGS[@]}" \
  "${FOREST_ARGS[@]}" \
  "${DYNAMIC_ARGS[@]}" \
  "${OFFICE_ARGS[@]}" \
  --source-commit 8c3fdffa84b85be0704a10ea5b2533817d543822 \
  --telemetry-port "$TELEMETRY_PORT" \
  --command-port "$COMMAND_PORT" \
  --planner-floor-filter-max-z "$PLANNER_FLOOR_FILTER_MAX_Z" \
  --max-vx "$MAX_VX" \
  --acceptance-config "$ACCEPTANCE_CONFIG" \
  --video-path "$OUTPUT_DIR/closed_loop.mp4" \
  --video-fps "$VIDEO_FPS" \
  --video-frame-stride "$VIDEO_FRAME_STRIDE" \
  >"$LOG_DIR/isaac.log" 2>&1 &
ISAAC_PID=$!

ports_ready=0
for _ in $(seq 1 600); do
  if ss -ltn | grep -q ":$TELEMETRY_PORT " \
    && ss -ltn | grep -q ":$COMMAND_PORT "; then
    ports_ready=1
    break
  fi
  if ! kill -0 "$ISAAC_PID" 2>/dev/null; then
    break
  fi
  sleep 0.25
done
printf '%s\n' "$ports_ready" >"$LOG_DIR/ports_ready.txt"
if (( ports_ready != 1 )); then
  wait "$ISAAC_PID" || true
  echo "Isaac endpoints did not become ready" >&2
  exit 70
fi

set +e
podman run --rm --name "$CONTAINER_NAME" \
  --network=host \
  -e TELEMETRY_PORT="$TELEMETRY_PORT" \
  -e COMMAND_PORT="$COMMAND_PORT" \
  -e ROS_RUNTIME_SECONDS="$ROS_RUNTIME_SECONDS" \
  -e PLANNER_CONFIG_CONTAINER="/workspace/$PLANNER_CONFIG_REL" \
  -e CONTROLLER_CONFIG_CONTAINER="/workspace/$CONTROLLER_CONFIG_REL" \
  -e BRIDGE_MAX_VX="$MAX_VX" \
  -e ENABLE_VOXEL_CAPTURE="$ENABLE_VOXEL_CAPTURE" \
  -e VOXEL_CAPTURE_PERIOD_SECONDS="$VOXEL_CAPTURE_PERIOD_SECONDS" \
  -v "$FOXY_WORKSPACE:/workspace" \
  -v "$OUTPUT_DIR:/evidence" \
  localhost/machine-dog-nav/foxy-scan:20260813 \
  bash -lc '
    set +u
    source /opt/ros/foxy/setup.bash
    cd /workspace
    source install/setup.bash
    set -u

    stop_with_int() {
      local target_pid=$1
      local attempts=0
      kill -INT "$target_pid" 2>/dev/null || true
      while kill -0 "$target_pid" 2>/dev/null && (( attempts < 100 )); do
        sleep 0.1
        attempts=$((attempts + 1))
      done
      if kill -0 "$target_pid" 2>/dev/null; then
        kill -TERM "$target_pid" 2>/dev/null || true
        attempts=0
        while kill -0 "$target_pid" 2>/dev/null && (( attempts < 50 )); do
          sleep 0.1
          attempts=$((attempts + 1))
        done
      fi
      if kill -0 "$target_pid" 2>/dev/null; then
        kill -KILL "$target_pid" 2>/dev/null || true
      fi
      wait "$target_pid"
    }

    CAPTURE_PID=
    CAPTURE_CODE=0
    if [[ $ENABLE_VOXEL_CAPTURE == 1 ]]; then
      (
        trap - INT TERM
        exec python3 -m lite3_sim_bridge.voxel_capture_node --ros-args \
          -p output_dir:=/evidence/voxel_snapshots \
          -p metadata_path:=/evidence/voxel_frames.jsonl \
          -p summary_path:=/evidence/voxel_capture_summary.json \
          -p capture_period_seconds:="$VOXEL_CAPTURE_PERIOD_SECONDS"
      ) >/evidence/voxel_capture.log 2>&1 &
      CAPTURE_PID=$!
    fi

    BAG_TOPICS=(
      /quad_0/body_pose /quad_0/lidar_pose /quad_0/cloud
      /quad_0/cmd_vel /planning/bspline
    )
    BAG_OPTIONS=()
    if [[ $ENABLE_VOXEL_CAPTURE == 1 ]]; then
      BAG_TOPICS+=(
        /grid_map/occupancy /grid_map/occupancy_inflate
        /grid_map/sliding_map_bbox
      )
      BAG_OPTIONS+=(
        --qos-profile-overrides-path
        /workspace/src/lite3_sim_bridge/config/voxel_rosbag_qos.yaml
      )
    fi
    (
      trap - INT TERM
      exec ros2 bag record "${BAG_OPTIONS[@]}" -o /evidence/rosbag "${BAG_TOPICS[@]}"
    ) >/evidence/rosbag_stdout.log 2>&1 &
    BAG_PID=$!

    (
      trap - INT TERM
      exec ros2 launch scan_planner foxy_isaac_closed_loop.launch.py \
        telemetry_port:="$TELEMETRY_PORT" \
        command_port:="$COMMAND_PORT" \
        planner_config:="$PLANNER_CONFIG_CONTAINER" \
        controller_config:="$CONTROLLER_CONFIG_CONTAINER" \
        bridge_max_vx:="$BRIDGE_MAX_VX" \
        enable_monitor:=true \
        monitor_event_log:=/evidence/ros_events.jsonl \
        monitor_summary:=/evidence/ros_summary.json
    ) >/evidence/foxy_launch.log 2>&1 &
    LAUNCH_PID=$!

    elapsed=0
    max_wait=$ROS_RUNTIME_SECONDS
    while (( elapsed < max_wait )); do
      if [[ -f /evidence/isaac/qualification_report.json ]]; then
        sleep 2
        break
      fi
      sleep 1
      elapsed=$((elapsed + 1))
    done
    stop_with_int "$LAUNCH_PID"
    LAUNCH_CODE=$?
    if [[ -n $CAPTURE_PID ]]; then
      stop_with_int "$CAPTURE_PID"
      CAPTURE_CODE=$?
    fi
    stop_with_int "$BAG_PID"
    BAG_CODE=$?
    printf "%s" "$LAUNCH_CODE" >/evidence/foxy_launch.exit
    printf "%s" "$BAG_CODE" >/evidence/rosbag.exit
    if [[ $ENABLE_VOXEL_CAPTURE == 1 ]]; then
      printf "%s" "$CAPTURE_CODE" >/evidence/voxel_capture.exit
      ros2 bag info /evidence/rosbag >/evidence/voxel_rosbag_info.txt
      python3 -c '"'"'import json; assert json.load(open("/evidence/voxel_capture_summary.json"))["status"] == "PASS"'"'"'
    fi
    test -f /evidence/ros_summary.json
    test -f /evidence/rosbag/metadata.yaml
    if (( LAUNCH_CODE != 0 )); then
      echo "ROS launch exited unexpectedly: $LAUNCH_CODE" >&2
      exit 1
    fi
    if (( BAG_CODE != 0 && BAG_CODE != 2 )); then
      echo "rosbag recorder exited unexpectedly: $BAG_CODE" >&2
      exit 1
    fi
    if (( CAPTURE_CODE != 0 )); then
      echo "voxel capture exited unexpectedly: $CAPTURE_CODE" >&2
      exit 1
    fi
  '
container_code=$?
wait "$ISAAC_PID"
isaac_code=$?
set -e
ISAAC_PID=

printf '%s' "$container_code" >"$LOG_DIR/container.exit"
printf '%s' "$isaac_code" >"$LOG_DIR/isaac.exit"
printf 'container=%s isaac=%s\n' "$container_code" "$isaac_code"

if (( container_code != 0 || isaac_code != 0 )); then
  exit 1
fi
