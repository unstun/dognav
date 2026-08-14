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

RUN_ROOT=/home/sun/machine-dog-nav-runs/2026-08-13_scan_foxy_isaac
FOXY_WORKSPACE=$RUN_ROOT/foxy_ws_clean3
LOG_DIR=$RUN_ROOT/logs/$RUN_ID
OUTPUT_DIR=$RUN_ROOT/results/$RUN_ID
RUNTIME=$RUN_ROOT/source/locomotion_v12/runtime_20260718_recovered
CHECKPOINT=$RUN_ROOT/source/locomotion_v12/checkpoint/model_149999.pt
BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge
ACCEPTANCE_CONFIG=$RUN_ROOT/acceptance_thresholds.json
PLANNER_CONFIG=$FOXY_WORKSPACE/src/plan_manage/config/foxy_isaac_planner.yaml
CONTROLLER_CONFIG=$FOXY_WORKSPACE/src/plan_manage/config/foxy_isaac_controller.yaml
CONTROLLER_SOURCE=$FOXY_WORKSPACE/src/plan_manage/src/closed_loop_controller.cpp
PROGRESS_SOURCE=$FOXY_WORKSPACE/src/plan_manage/include/plan_manage/trajectory_progress.h
FSM_SOURCE=$FOXY_WORKSPACE/src/plan_manage/src/scan_replan_fsm.cpp
FSM_HEADER=$FOXY_WORKSPACE/src/plan_manage/include/plan_manage/scan_replan_fsm.h
GRID_MAP_SOURCE=$FOXY_WORKSPACE/src/plan_env/src/grid_map.cpp
OCCLUSION_SHADOW_SOURCE=$FOXY_WORKSPACE/src/plan_env/include/plan_env/occlusion_shadow.h
CONTAINER_NAME=scan-foxy-$RUN_ID
ROS_RUNTIME_SECONDS=$((DURATION_SECONDS + 3))

for required in \
  "$FOXY_WORKSPACE/install/setup.bash" \
  "$CHECKPOINT" \
  "$BRIDGE/lite3_sim_bridge/run_isaac_v12_fallback.py" \
  "$BRIDGE/lite3_sim_bridge/transport.py" \
  "$PLANNER_CONFIG" \
  "$CONTROLLER_CONFIG" \
  "$CONTROLLER_SOURCE" \
  "$PROGRESS_SOURCE" \
  "$FSM_SOURCE" \
  "$FSM_HEADER" \
  "$GRID_MAP_SOURCE" \
  "$OCCLUSION_SHADOW_SOURCE" \
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

sha256sum \
  "$0" \
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
  "$BRIDGE/lite3_sim_bridge/transport.py" \
  "$BRIDGE/lite3_sim_bridge/protocol.py" \
  "$BRIDGE/lite3_sim_bridge/foxy_bridge_node.py" \
  "$FOXY_WORKSPACE/build/scan_planner/scan_planner_node" \
  "$FOXY_WORKSPACE/build/scan_planner/closed_loop_controller" \
  "$FOXY_WORKSPACE/build/plan_env/libplan_env.a" \
  >"$OUTPUT_DIR/input_sha256.txt"
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

source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH="$BRIDGE:$RUNTIME/source/rsl_rl:$RUNTIME/source/robot_lab${PYTHONPATH:+:$PYTHONPATH}"

cd "$RUNTIME"
python -u -m lite3_sim_bridge.run_isaac_v12_fallback \
  --mode external \
  --course single_box \
  --duration-seconds "$DURATION_SECONDS" \
  --output-dir "$OUTPUT_DIR/isaac" \
  --checkpoint "$CHECKPOINT" \
  --vendored-rsl-rl "$RUNTIME/source/rsl_rl" \
  --source-commit 8c3fdffa84b85be0704a10ea5b2533817d543822 \
  --telemetry-port "$TELEMETRY_PORT" \
  --command-port "$COMMAND_PORT" \
  --planner-floor-filter-max-z 0.05 \
  --acceptance-config "$ACCEPTANCE_CONFIG" \
  --video-path "$OUTPUT_DIR/closed_loop.mp4" \
  --video-fps 25 \
  --video-frame-stride 2 \
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
