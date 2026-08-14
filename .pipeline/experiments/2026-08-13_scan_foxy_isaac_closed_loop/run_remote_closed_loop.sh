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
RUNTIME=$RUN_ROOT/source/locomotion_v12/runtime_20260718_recovered
CHECKPOINT=$RUN_ROOT/source/locomotion_v12/checkpoint/model_149999.pt
BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge
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
FOXY_BRIDGE_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/foxy_bridge_node.py
FOXY_TRANSPORT_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/transport.py
FOXY_PROTOCOL_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/protocol.py
FOXY_COMMAND_STATE_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/command_state.py
CONTAINER_NAME=scan-foxy-$RUN_ID
ROS_RUNTIME_SECONDS=$((DURATION_SECONDS + 3))
VIDEO_FPS=${SCAN_VIDEO_FPS:-25}
VIDEO_FRAME_STRIDE=${SCAN_VIDEO_FRAME_STRIDE:-2}
PLANNER_FLOOR_FILTER_MAX_Z=${SCAN_PLANNER_FLOOR_FILTER_MAX_Z:-0.05}
ROBOT_ARGS=()
ROBOT_INPUTS=()
FOREST_ARGS=()
FOREST_PYTHONPATH=
TERRAIN_FILTER_CELL_SIZE=
TERRAIN_FILTER_HEIGHT_THRESHOLD=
TERRAIN_FILTER_NEIGHBOR_CELLS=
TERRAIN_FILTER_MINIMUM_NEIGHBOR_CELLS=
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
  forest_gen|forest_gen_nav)
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
    if [[ $COURSE == forest_gen_nav ]]; then
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
  "$FOXY_BRIDGE_SOURCE" \
  "$FOXY_TRANSPORT_SOURCE" \
  "$FOXY_PROTOCOL_SOURCE" \
  "$FOXY_COMMAND_STATE_SOURCE" \
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
  printf 'video_fps=%s\n' "$VIDEO_FPS"
  printf 'video_frame_stride=%s\n' "$VIDEO_FRAME_STRIDE"
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
  "$BRIDGE/lite3_sim_bridge/run_isaac_v12_fallback.py" \
  "$BRIDGE/lite3_sim_bridge/acceptance.py" \
  "$BRIDGE/lite3_sim_bridge/command_state.py" \
  "$BRIDGE/lite3_sim_bridge/transport.py" \
  "$BRIDGE/lite3_sim_bridge/protocol.py" \
  "$BRIDGE/lite3_sim_bridge/foxy_bridge_node.py" \
  "$FOXY_BRIDGE_SOURCE" \
  "$FOXY_TRANSPORT_SOURCE" \
  "$FOXY_PROTOCOL_SOURCE" \
  "$FOXY_COMMAND_STATE_SOURCE" \
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

# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH="$BRIDGE:$RUNTIME/source/rsl_rl:$RUNTIME/source/robot_lab${FOREST_PYTHONPATH:+:$FOREST_PYTHONPATH}${PYTHONPATH:+:$PYTHONPATH}"

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
  --source-commit 8c3fdffa84b85be0704a10ea5b2533817d543822 \
  --telemetry-port "$TELEMETRY_PORT" \
  --command-port "$COMMAND_PORT" \
  --planner-floor-filter-max-z "$PLANNER_FLOOR_FILTER_MAX_Z" \
  --acceptance-config "$ACCEPTANCE_CONFIG" \
  --video-path "$OUTPUT_DIR/closed_loop.mp4" \
  --video-fps "$VIDEO_FPS" \
  --video-frame-stride "$VIDEO_FRAME_STRIDE" \
  >"$LOG_DIR/isaac.log" 2>&1 &
ISAAC_PID=$!

ports_ready=0
for _ in $(seq 1 240); do
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

    (
      trap - INT TERM
      exec ros2 bag record -o /evidence/rosbag \
        /quad_0/body_pose /quad_0/lidar_pose /quad_0/cloud \
        /quad_0/cmd_vel /planning/bspline
    ) >/evidence/rosbag_stdout.log 2>&1 &
    BAG_PID=$!

    (
      trap - INT TERM
      exec ros2 launch scan_planner foxy_isaac_closed_loop.launch.py \
        telemetry_port:="$TELEMETRY_PORT" \
        command_port:="$COMMAND_PORT" \
        planner_config:="$PLANNER_CONFIG_CONTAINER" \
        controller_config:="$CONTROLLER_CONFIG_CONTAINER" \
        enable_monitor:=true \
        monitor_event_log:=/evidence/ros_events.jsonl \
        monitor_summary:=/evidence/ros_summary.json
    ) >/evidence/foxy_launch.log 2>&1 &
    LAUNCH_PID=$!

    sleep "$ROS_RUNTIME_SECONDS"
    stop_with_int "$LAUNCH_PID"
    LAUNCH_CODE=$?
    stop_with_int "$BAG_PID"
    BAG_CODE=$?
    printf "%s" "$LAUNCH_CODE" >/evidence/foxy_launch.exit
    printf "%s" "$BAG_CODE" >/evidence/rosbag.exit
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
