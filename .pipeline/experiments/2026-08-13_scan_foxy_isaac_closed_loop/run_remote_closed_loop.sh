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
FOXY_RVIZ_REPLAY_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/rviz_replay_node.py
FOXY_RVIZ_REPLAY_CORE_SOURCE=$FOXY_WORKSPACE/src/lite3_sim_bridge/lite3_sim_bridge/rviz_replay_core.py
FOXY_NATIVE_RVIZ_LAUNCH=$FOXY_WORKSPACE/src/lite3_sim_bridge/launch/native_rviz_review.launch.py
FOXY_VOXEL_ROSBAG_QOS=$FOXY_WORKSPACE/src/lite3_sim_bridge/config/voxel_rosbag_qos.yaml
TRAJECTORY_REVIEW_SOURCE=$BRIDGE/lite3_sim_bridge/trajectory_review.py
VOXEL_REVIEW_SOURCE=$BRIDGE/lite3_sim_bridge/voxel_review.py
ISAAC_ADAPTER_CORE_SOURCE=$BRIDGE/lite3_sim_bridge/isaac_adapter_core.py
OFFICIAL_HUMAN_BAKER_SOURCE=$BRIDGE/lite3_sim_bridge/bake_official_human_animation.py
OFFICIAL_HUMAN_CONTRACT_SOURCE=$BRIDGE/lite3_sim_bridge/official_human_contract.py
MID360_PATTERN_SOURCE=$BRIDGE/lite3_sim_bridge/mid360_pattern.py
CONTAINER_NAME=scan-foxy-$RUN_ID
CONTAINER_IMAGE=localhost/machine-dog-nav/foxy-scan:20260813
ROS_RUNTIME_SECONDS=${SCAN_ROS_RUNTIME_SECONDS:-$((DURATION_SECONDS * 6 + 120))}
VIDEO_FPS=${SCAN_VIDEO_FPS:-25}
VIDEO_FRAME_STRIDE=${SCAN_VIDEO_FRAME_STRIDE:-2}
OFFICE_REVIEW_ENABLED=${SCAN_OFFICE_REVIEW_ENABLED:-0}
OFFICE_REVIEW_CAMERA_SIDE=${SCAN_OFFICE_REVIEW_CAMERA_SIDE:-left}
OFFICE_REVIEW_CAMERA_LATERAL_DISTANCE=${SCAN_OFFICE_REVIEW_CAMERA_LATERAL_DISTANCE:-3.0}
OFFICE_REVIEW_CAMERA_TRAILING_BIAS=${SCAN_OFFICE_REVIEW_CAMERA_TRAILING_BIAS:-1.5}
OFFICE_REVIEW_CAMERA_HEIGHT=${SCAN_OFFICE_REVIEW_CAMERA_HEIGHT:-2.0}
OFFICE_REVIEW_CAMERA_FOCAL_LENGTH_MM=${SCAN_OFFICE_REVIEW_CAMERA_FOCAL_LENGTH_MM:-18.14756}
OFFICE_REVIEW_CAMERA_LOOK_AHEAD=${SCAN_OFFICE_REVIEW_CAMERA_LOOK_AHEAD:-1.0}
OFFICE_REVIEW_CAMERA_LOOK_HEIGHT_OFFSET=${SCAN_OFFICE_REVIEW_CAMERA_LOOK_HEIGHT_OFFSET:-0.15}
OFFICE_REVIEW_CAMERA_SMOOTHING_RATE=${SCAN_OFFICE_REVIEW_CAMERA_SMOOTHING_RATE:-4.0}
OFFICE_REVIEW_CAMERA_MAX_EYE_SPEED=${SCAN_OFFICE_REVIEW_CAMERA_MAX_EYE_SPEED:-8.0}
OFFICE_REVIEW_CAMERA_MAX_TARGET_SPEED=${SCAN_OFFICE_REVIEW_CAMERA_MAX_TARGET_SPEED:-8.0}
OFFICE_REVIEW_OVERVIEW_DISTANCE=${SCAN_OFFICE_REVIEW_OVERVIEW_DISTANCE:-6.5}
OFFICE_REVIEW_OVERVIEW_AZIMUTH=${SCAN_OFFICE_REVIEW_OVERVIEW_AZIMUTH:-35.0}
OFFICE_REVIEW_OVERVIEW_HEIGHT=${SCAN_OFFICE_REVIEW_OVERVIEW_HEIGHT:-4.5}
OFFICE_REVIEW_OVERVIEW_LOOK_AHEAD=${SCAN_OFFICE_REVIEW_OVERVIEW_LOOK_AHEAD:-2.0}
OFFICE_REVIEW_OVERVIEW_LOOK_HEIGHT_OFFSET=${SCAN_OFFICE_REVIEW_OVERVIEW_LOOK_HEIGHT_OFFSET:-0.20}
OFFICE_REVIEW_OVERVIEW_SMOOTHING_RATE=${SCAN_OFFICE_REVIEW_OVERVIEW_SMOOTHING_RATE:-3.0}
OFFICE_REVIEW_OVERVIEW_MAX_EYE_SPEED=${SCAN_OFFICE_REVIEW_OVERVIEW_MAX_EYE_SPEED:-6.0}
OFFICE_REVIEW_OVERVIEW_MAX_TARGET_SPEED=${SCAN_OFFICE_REVIEW_OVERVIEW_MAX_TARGET_SPEED:-6.0}
OFFICE_REVIEW_LIGHTING_PROFILE=${SCAN_OFFICE_REVIEW_LIGHTING_PROFILE:-high_contrast}
OFFICE_REVIEW_DOME_LIGHT_INTENSITY=${SCAN_OFFICE_REVIEW_DOME_LIGHT_INTENSITY:-1000.0}
OFFICE_REVIEW_EXPOSURE=${SCAN_OFFICE_REVIEW_EXPOSURE:-0.0}
MAX_VX=${SCAN_MAX_VX:-0.75}
PLANNER_FLOOR_FILTER_MAX_Z=${SCAN_PLANNER_FLOOR_FILTER_MAX_Z:-0.05}
LIDAR_PATTERN_MODE=${SCAN_LIDAR_PATTERN_MODE:-uniform}
LIDAR_PATTERN_CSV=${SCAN_LIDAR_PATTERN_CSV:-}
LIDAR_MIN_RANGE=${SCAN_LIDAR_MIN_RANGE:-0.10}
LIDAR_MAX_RANGE=${SCAN_LIDAR_MAX_RANGE:-12.0}
LIDAR_ARGS=(
  --lidar-pattern-mode "$LIDAR_PATTERN_MODE"
  --lidar-min-range "$LIDAR_MIN_RANGE"
  --lidar-max-range "$LIDAR_MAX_RANGE"
)
LIDAR_INPUTS=()
ROBOT_ARGS=()
ROBOT_INPUTS=()
FOREST_ARGS=()
DYNAMIC_ARGS=()
OFFICE_ARGS=()
OFFICE_REVIEW_ARGS=()
OFFICE_REVIEW_INPUTS=()
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
OFFICE_PEDESTRIAN_MOTION_MODE=${SCAN_OFFICE_PEDESTRIAN_MOTION_MODE:-single_pass}
OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS=${SCAN_OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS:-0.6}
ENABLE_VOXEL_CAPTURE=${SCAN_ENABLE_VOXEL_CAPTURE:-0}
VOXEL_CAPTURE_PERIOD_SECONDS=${SCAN_VOXEL_CAPTURE_PERIOD_SECONDS:-0.1}
VISUAL_REVIEW_ONLY=${SCAN_VISUAL_REVIEW_ONLY:-0}
RECORD_ROSBAG=${SCAN_RECORD_ROSBAG:-1}
NATIVE_RVIZ_ENABLED=${SCAN_NATIVE_RVIZ_ENABLED:-0}
NATIVE_RVIZ_PRESTART_GATE=${SCAN_NATIVE_RVIZ_PRESTART_GATE:-0}
NATIVE_RVIZ_DISPLAY=${SCAN_NATIVE_RVIZ_DISPLAY:-:0}
NATIVE_RVIZ_XAUTHORITY=${SCAN_NATIVE_RVIZ_XAUTHORITY:-/run/user/1000/gdm/Xauthority}
NATIVE_RVIZ_IMAGE=${SCAN_NATIVE_RVIZ_IMAGE:-localhost/machine-dog-nav/foxy-scan-rviz:20260818}
NATIVE_RVIZ_CONFIG_REL=${SCAN_NATIVE_RVIZ_CONFIG_REL:-src/plan_manage/launch/default.rviz}
NATIVE_RVIZ_CONFIG=$FOXY_WORKSPACE/$NATIVE_RVIZ_CONFIG_REL
NATIVE_RVIZ_ROBOT_ASSET=${SCAN_CANONICAL_ROBOT_ASSET:-}
NATIVE_RVIZ_ROBOT_ASSET_ROOT=
NATIVE_RVIZ_ROBOT_ASSET_CONTAINER=
NATIVE_RVIZ_INPUTS=()
NATIVE_RVIZ_PODMAN_ARGS=()
if [[ ! $MAX_VX =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]] \
  || ! awk -v value="$MAX_VX" 'BEGIN { exit !(value > 0.0) }'; then
  echo "SCAN_MAX_VX must be a positive decimal" >&2
  exit 64
fi
case "$LIDAR_PATTERN_MODE" in
  uniform)
    if [[ -n $LIDAR_PATTERN_CSV ]]; then
      echo "SCAN_LIDAR_PATTERN_CSV is valid only for livox_mid360 mode" >&2
      exit 64
    fi
    ;;
  livox_mid360)
    if [[ -z $LIDAR_PATTERN_CSV || ! -f $LIDAR_PATTERN_CSV ]]; then
      echo "livox_mid360 requires a regular SCAN_LIDAR_PATTERN_CSV file" >&2
      exit 66
    fi
    LIDAR_ARGS+=(--lidar-pattern-csv "$LIDAR_PATTERN_CSV")
    LIDAR_INPUTS+=("$LIDAR_PATTERN_CSV")
    ;;
  *)
    echo "unsupported SCAN_LIDAR_PATTERN_MODE: $LIDAR_PATTERN_MODE" >&2
    exit 64
    ;;
esac
if [[ $OFFICE_REVIEW_ENABLED != 0 && $OFFICE_REVIEW_ENABLED != 1 ]]; then
  echo "SCAN_OFFICE_REVIEW_ENABLED must be 0 or 1" >&2
  exit 64
fi
if [[ $ENABLE_VOXEL_CAPTURE != 0 && $ENABLE_VOXEL_CAPTURE != 1 ]]; then
  echo "SCAN_ENABLE_VOXEL_CAPTURE must be 0 or 1" >&2
  exit 64
fi
if [[ $VISUAL_REVIEW_ONLY != 0 && $VISUAL_REVIEW_ONLY != 1 ]]; then
  echo "SCAN_VISUAL_REVIEW_ONLY must be 0 or 1" >&2
  exit 64
fi
if [[ $RECORD_ROSBAG != 0 && $RECORD_ROSBAG != 1 ]]; then
  echo "SCAN_RECORD_ROSBAG must be 0 or 1" >&2
  exit 64
fi
if [[ $RECORD_ROSBAG == 0 && $VISUAL_REVIEW_ONLY != 1 ]]; then
  echo "SCAN_RECORD_ROSBAG=0 is allowed only with SCAN_VISUAL_REVIEW_ONLY=1" >&2
  exit 64
fi
if [[ $VISUAL_REVIEW_ONLY == 1 ]] \
  && [[ $OFFICE_REVIEW_ENABLED != 1 || $RECORD_ROSBAG != 0 ]]; then
  echo "visual-review-only mode requires Office review and SCAN_RECORD_ROSBAG=0" >&2
  exit 64
fi
if [[ $NATIVE_RVIZ_ENABLED != 0 && $NATIVE_RVIZ_ENABLED != 1 ]]; then
  echo "SCAN_NATIVE_RVIZ_ENABLED must be 0 or 1" >&2
  exit 64
fi
if [[ $NATIVE_RVIZ_PRESTART_GATE != 0 && $NATIVE_RVIZ_PRESTART_GATE != 1 ]]; then
  echo "SCAN_NATIVE_RVIZ_PRESTART_GATE must be 0 or 1" >&2
  exit 64
fi
if [[ $NATIVE_RVIZ_PRESTART_GATE == 1 && $NATIVE_RVIZ_ENABLED != 1 ]]; then
  echo "SCAN_NATIVE_RVIZ_PRESTART_GATE=1 requires native RViz" >&2
  exit 64
fi
if [[ ! $VOXEL_CAPTURE_PERIOD_SECONDS =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]] \
  || ! awk -v value="$VOXEL_CAPTURE_PERIOD_SECONDS" 'BEGIN { exit !(value > 0.0) }'; then
  echo "SCAN_VOXEL_CAPTURE_PERIOD_SECONDS must be a positive decimal" >&2
  exit 64
fi
if [[ $NATIVE_RVIZ_ENABLED == 1 ]]; then
  for required in "$NATIVE_RVIZ_XAUTHORITY" /tmp/.X11-unix/X0 \
    "$NATIVE_RVIZ_CONFIG" "$NATIVE_RVIZ_ROBOT_ASSET" \
    "$FOXY_RVIZ_REPLAY_SOURCE" "$FOXY_RVIZ_REPLAY_CORE_SOURCE" \
    "$FOXY_NATIVE_RVIZ_LAUNCH"; do
    if [[ ! -e $required ]]; then
      echo "native RViz input is missing: $required" >&2
      exit 66
    fi
  done
  if ! podman image exists "$NATIVE_RVIZ_IMAGE"; then
    echo "native RViz image is missing: $NATIVE_RVIZ_IMAGE" >&2
    exit 66
  fi
  CONTAINER_IMAGE=$NATIVE_RVIZ_IMAGE
  NATIVE_RVIZ_ROBOT_ASSET_ROOT=$(dirname "$(dirname "$NATIVE_RVIZ_ROBOT_ASSET")")
  NATIVE_RVIZ_ROBOT_ASSET_CONTAINER=/robot_asset/urdf/$(basename "$NATIVE_RVIZ_ROBOT_ASSET")
  NATIVE_RVIZ_INPUTS+=(
    "$NATIVE_RVIZ_CONFIG"
    "$NATIVE_RVIZ_ROBOT_ASSET"
    "$FOXY_RVIZ_REPLAY_SOURCE"
    "$FOXY_RVIZ_REPLAY_CORE_SOURCE"
    "$FOXY_NATIVE_RVIZ_LAUNCH"
  )
  NATIVE_RVIZ_PODMAN_ARGS+=(
    -e ENABLE_NATIVE_RVIZ=1
    -e NATIVE_RVIZ_CONFIG_CONTAINER="/workspace/$NATIVE_RVIZ_CONFIG_REL"
    -e NATIVE_RVIZ_ROBOT_ASSET_CONTAINER="$NATIVE_RVIZ_ROBOT_ASSET_CONTAINER"
    -e DISPLAY="$NATIVE_RVIZ_DISPLAY"
    -e XAUTHORITY=/tmp/.Xauthority
    -e QT_X11_NO_MITSHM=1
    -e LIBGL_ALWAYS_SOFTWARE=1
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw
    -v "$NATIVE_RVIZ_XAUTHORITY:/tmp/.Xauthority:ro"
    -v "$NATIVE_RVIZ_ROBOT_ASSET_ROOT:/robot_asset:ro"
  )
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
      --office-pedestrian-motion-mode "$OFFICE_PEDESTRIAN_MOTION_MODE"
      --office-pedestrian-turnaround-hold-seconds "$OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS"
    )
    if [[ $OFFICE_REVIEW_ENABLED == 1 ]]; then
      OFFICE_REVIEW_INPUTS=("$BRIDGE/lite3_sim_bridge/office_review_presentation.py")
      OFFICE_REVIEW_ARGS=(
        --office-review-presentation
        --office-review-material
        --office-review-third-person-side-video-path "$OUTPUT_DIR/closed_loop_third_person_side.mp4"
        --office-review-overview-video-path "$OUTPUT_DIR/closed_loop_overview.mp4"
        --office-review-camera-trace-path "$OUTPUT_DIR/camera_trace.jsonl"
        --office-review-material-audit-path "$OUTPUT_DIR/office_review_material_audit.json"
        --office-review-dashboard-video-path "$OUTPUT_DIR/office_review_dashboard.mp4"
        --office-review-dashboard-metadata-path "$OUTPUT_DIR/office_review_dashboard_metadata.json"
        --office-review-validation-report-path "$OUTPUT_DIR/office_review_validation_report.json"
        --office-review-effective-input-path "$OUTPUT_DIR/effective_input.txt"
        --office-review-launcher-path "$ENTRYPOINT"
        --office-review-camera-side "$OFFICE_REVIEW_CAMERA_SIDE"
        --office-review-camera-lateral-distance "$OFFICE_REVIEW_CAMERA_LATERAL_DISTANCE"
        --office-review-camera-trailing-bias "$OFFICE_REVIEW_CAMERA_TRAILING_BIAS"
        --office-review-camera-height "$OFFICE_REVIEW_CAMERA_HEIGHT"
        --office-review-camera-focal-length-mm "$OFFICE_REVIEW_CAMERA_FOCAL_LENGTH_MM"
        --office-review-camera-look-ahead "$OFFICE_REVIEW_CAMERA_LOOK_AHEAD"
        --office-review-camera-look-height-offset "$OFFICE_REVIEW_CAMERA_LOOK_HEIGHT_OFFSET"
        --office-review-camera-smoothing-rate "$OFFICE_REVIEW_CAMERA_SMOOTHING_RATE"
        --office-review-camera-max-eye-speed "$OFFICE_REVIEW_CAMERA_MAX_EYE_SPEED"
        --office-review-camera-max-target-speed "$OFFICE_REVIEW_CAMERA_MAX_TARGET_SPEED"
        --office-review-overview-distance "$OFFICE_REVIEW_OVERVIEW_DISTANCE"
        --office-review-overview-azimuth-offset-deg "$OFFICE_REVIEW_OVERVIEW_AZIMUTH"
        --office-review-overview-height "$OFFICE_REVIEW_OVERVIEW_HEIGHT"
        --office-review-overview-look-ahead "$OFFICE_REVIEW_OVERVIEW_LOOK_AHEAD"
        --office-review-overview-look-height-offset "$OFFICE_REVIEW_OVERVIEW_LOOK_HEIGHT_OFFSET"
        --office-review-overview-smoothing-rate "$OFFICE_REVIEW_OVERVIEW_SMOOTHING_RATE"
        --office-review-overview-max-eye-speed "$OFFICE_REVIEW_OVERVIEW_MAX_EYE_SPEED"
        --office-review-overview-max-target-speed "$OFFICE_REVIEW_OVERVIEW_MAX_TARGET_SPEED"
        --office-review-lighting-profile "$OFFICE_REVIEW_LIGHTING_PROFILE"
        --office-review-dome-light-intensity "$OFFICE_REVIEW_DOME_LIGHT_INTENSITY"
        --office-review-exposure "$OFFICE_REVIEW_EXPOSURE"
      )
    fi
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

if [[ $OFFICE_REVIEW_ENABLED == 1 && $COURSE != office_l0_crowd ]]; then
  echo "SCAN_OFFICE_REVIEW_ENABLED=1 is only valid for office_l0_crowd" >&2
  exit 64
fi
if [[ $COURSE == office_l0_crowd ]]; then
  if [[ $OFFICE_PEDESTRIAN_MOTION_MODE != single_pass \
    && $OFFICE_PEDESTRIAN_MOTION_MODE != background_ping_pong \
    && $OFFICE_PEDESTRIAN_MOTION_MODE != ping_pong ]]; then
    echo "unsupported SCAN_OFFICE_PEDESTRIAN_MOTION_MODE: $OFFICE_PEDESTRIAN_MOTION_MODE" >&2
    exit 64
  fi
  if [[ ! $OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]] \
    || ! awk -v value="$OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS" 'BEGIN { exit !(value > 0.0) }'; then
    echo "SCAN_OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS must be a positive decimal" >&2
    exit 64
  fi
  if [[ $OFFICE_PEDESTRIAN_MOTION_MODE != single_pass \
    && $OFFICIAL_HUMAN_ANIMATION_MODE != phase_conditioned ]]; then
    echo "ping-pong Office pedestrians require phase-conditioned animation" >&2
    exit 64
  fi
fi

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
  "$MID360_PATTERN_SOURCE" \
  "${LIDAR_INPUTS[@]}" \
  "${OFFICE_REVIEW_INPUTS[@]}" \
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
  printf 'ros_runtime_seconds=%s\n' "$ROS_RUNTIME_SECONDS"
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
  printf 'lidar_pattern_mode=%s\n' "$LIDAR_PATTERN_MODE"
  printf 'lidar_pattern_csv=%s\n' "$LIDAR_PATTERN_CSV"
  printf 'lidar_min_range_m=%s\n' "$LIDAR_MIN_RANGE"
  printf 'lidar_max_range_m=%s\n' "$LIDAR_MAX_RANGE"
  printf 'office_pedestrian_motion_mode=%s\n' "$OFFICE_PEDESTRIAN_MOTION_MODE"
  printf 'office_pedestrian_turnaround_hold_seconds=%s\n' "$OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS"
  printf 'video_fps=%s\n' "$VIDEO_FPS"
  printf 'video_frame_stride=%s\n' "$VIDEO_FRAME_STRIDE"
  printf 'office_review_enabled=%s\n' "$OFFICE_REVIEW_ENABLED"
  printf 'office_review_camera_side=%s\n' "$OFFICE_REVIEW_CAMERA_SIDE"
  printf 'office_review_camera_lateral_distance=%s\n' "$OFFICE_REVIEW_CAMERA_LATERAL_DISTANCE"
  printf 'office_review_camera_trailing_bias=%s\n' "$OFFICE_REVIEW_CAMERA_TRAILING_BIAS"
  printf 'office_review_camera_height=%s\n' "$OFFICE_REVIEW_CAMERA_HEIGHT"
  printf 'office_review_camera_focal_length_mm=%s\n' "$OFFICE_REVIEW_CAMERA_FOCAL_LENGTH_MM"
  printf 'office_review_camera_look_ahead=%s\n' "$OFFICE_REVIEW_CAMERA_LOOK_AHEAD"
  printf 'office_review_camera_look_height_offset=%s\n' "$OFFICE_REVIEW_CAMERA_LOOK_HEIGHT_OFFSET"
  printf 'office_review_camera_smoothing_rate=%s\n' "$OFFICE_REVIEW_CAMERA_SMOOTHING_RATE"
  printf 'office_review_camera_max_eye_speed=%s\n' "$OFFICE_REVIEW_CAMERA_MAX_EYE_SPEED"
  printf 'office_review_camera_max_target_speed=%s\n' "$OFFICE_REVIEW_CAMERA_MAX_TARGET_SPEED"
  printf 'office_review_overview_distance=%s\n' "$OFFICE_REVIEW_OVERVIEW_DISTANCE"
  printf 'office_review_overview_azimuth=%s\n' "$OFFICE_REVIEW_OVERVIEW_AZIMUTH"
  printf 'office_review_overview_height=%s\n' "$OFFICE_REVIEW_OVERVIEW_HEIGHT"
  printf 'office_review_overview_look_ahead=%s\n' "$OFFICE_REVIEW_OVERVIEW_LOOK_AHEAD"
  printf 'office_review_overview_look_height_offset=%s\n' "$OFFICE_REVIEW_OVERVIEW_LOOK_HEIGHT_OFFSET"
  printf 'office_review_overview_smoothing_rate=%s\n' "$OFFICE_REVIEW_OVERVIEW_SMOOTHING_RATE"
  printf 'office_review_overview_max_eye_speed=%s\n' "$OFFICE_REVIEW_OVERVIEW_MAX_EYE_SPEED"
  printf 'office_review_overview_max_target_speed=%s\n' "$OFFICE_REVIEW_OVERVIEW_MAX_TARGET_SPEED"
  printf 'office_review_lighting_profile=%s\n' "$OFFICE_REVIEW_LIGHTING_PROFILE"
  printf 'office_review_dome_light_intensity=%s\n' "$OFFICE_REVIEW_DOME_LIGHT_INTENSITY"
  printf 'office_review_exposure=%s\n' "$OFFICE_REVIEW_EXPOSURE"
  printf 'max_vx=%s\n' "$MAX_VX"
  printf 'enable_voxel_capture=%s\n' "$ENABLE_VOXEL_CAPTURE"
  printf 'voxel_capture_period_seconds=%s\n' "$VOXEL_CAPTURE_PERIOD_SECONDS"
  printf 'visual_review_only=%s\n' "$VISUAL_REVIEW_ONLY"
  printf 'record_rosbag=%s\n' "$RECORD_ROSBAG"
  printf 'native_rviz_enabled=%s\n' "$NATIVE_RVIZ_ENABLED"
  printf 'native_rviz_prestart_gate=%s\n' "$NATIVE_RVIZ_PRESTART_GATE"
  printf 'native_rviz_display=%s\n' "$NATIVE_RVIZ_DISPLAY"
  printf 'native_rviz_image=%s\n' "$CONTAINER_IMAGE"
  printf 'native_rviz_config_rel=%s\n' "$NATIVE_RVIZ_CONFIG_REL"
  printf 'native_rviz_robot_asset=%s\n' "$NATIVE_RVIZ_ROBOT_ASSET"
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
  "${OFFICE_REVIEW_INPUTS[@]}" \
  "$ISAAC_ADAPTER_CORE_SOURCE" \
  "$OFFICIAL_HUMAN_BAKER_SOURCE" \
  "$OFFICIAL_HUMAN_CONTRACT_SOURCE" \
  "$MID360_PATTERN_SOURCE" \
  "${LIDAR_INPUTS[@]}" \
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
  "${NATIVE_RVIZ_INPUTS[@]}" \
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
  "$CONTAINER_IMAGE" \
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
  "${OFFICE_REVIEW_ARGS[@]}" \
  "${LIDAR_ARGS[@]}" \
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

if [[ $NATIVE_RVIZ_PRESTART_GATE == 1 ]]; then
  kill -STOP "$ISAAC_PID"
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
  -e VISUAL_REVIEW_ONLY="$VISUAL_REVIEW_ONLY" \
  -e RECORD_ROSBAG="$RECORD_ROSBAG" \
  -v "$FOXY_WORKSPACE:/workspace" \
  -v "$OUTPUT_DIR:/evidence" \
  "${NATIVE_RVIZ_PODMAN_ARGS[@]}" \
  "$CONTAINER_IMAGE" \
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

    RVIZ_PID=
    REVIEW_PID=
    if [[ ${ENABLE_NATIVE_RVIZ:-0} == 1 ]]; then
      export XDG_RUNTIME_DIR=/tmp/runtime-root
      mkdir -p "$XDG_RUNTIME_DIR"
      chmod 700 "$XDG_RUNTIME_DIR"
      (
        trap - INT TERM
        exec ros2 launch lite3_sim_bridge native_rviz_review.launch.py \
          robot_urdf_path:="$NATIVE_RVIZ_ROBOT_ASSET_CONTAINER" \
          audit_path:=/evidence/native_rviz_review_audit.json
      ) >/evidence/native_rviz_robot_state.log 2>&1 &
      REVIEW_PID=$!
      (
        trap - INT TERM
        exec rviz2 -d "$NATIVE_RVIZ_CONFIG_CONTAINER"
      ) >/evidence/native_scan_rviz3d_rviz.log 2>&1 &
      RVIZ_PID=$!
    fi

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

    BAG_PID=
    BAG_CODE=0
    if [[ $RECORD_ROSBAG == 1 ]]; then
      BAG_TOPICS=(
        /quad_0/body_pose /quad_0/lidar_pose /quad_0/cloud
        /quad_0/cmd_vel /quad_0/joint_states /planning/bspline
        /review/scan_planned_path /review/lite3_actual_path
        /review/lite3_current_pose /robot_description /tf /tf_static
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
    else
      printf "%s\n" \
        "visual_review_only=1; rosbag intentionally disabled; not formal acceptance evidence" \
        >/evidence/rosbag.disabled.txt
    fi

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
    if [[ -n $BAG_PID ]]; then
      stop_with_int "$BAG_PID"
      BAG_CODE=$?
    fi
    if [[ -n $RVIZ_PID ]]; then
      kill -TERM "$RVIZ_PID" 2>/dev/null || true
      wait "$RVIZ_PID" 2>/dev/null || true
    fi
    if [[ -n $REVIEW_PID ]]; then
      stop_with_int "$REVIEW_PID" >/dev/null 2>&1 || true
    fi
    printf "%s" "$LAUNCH_CODE" >/evidence/foxy_launch.exit
    if [[ $RECORD_ROSBAG == 1 ]]; then
      printf "%s" "$BAG_CODE" >/evidence/rosbag.exit
    fi
    if [[ $ENABLE_VOXEL_CAPTURE == 1 ]]; then
      printf "%s" "$CAPTURE_CODE" >/evidence/voxel_capture.exit
      if [[ $RECORD_ROSBAG == 1 ]]; then
        ros2 bag info /evidence/rosbag >/evidence/voxel_rosbag_info.txt
      fi
      python3 -c '"'"'import json; assert json.load(open("/evidence/voxel_capture_summary.json"))["status"] == "PASS"'"'"'
    fi
    if [[ ${ENABLE_NATIVE_RVIZ:-0} == 1 ]]; then
      test -s /evidence/native_rviz_review_audit.json
      python3 -c '"'"'import json; audit=json.load(open("/evidence/native_rviz_review_audit.json")); assert audit["status"] == "PASS"; assert audit["source_mode"] == "live"; assert audit["checks"]["root_transform_matches_body_path"]'"'"'
    fi
    test -f /evidence/ros_summary.json
    if [[ $RECORD_ROSBAG == 1 ]]; then
      test -f /evidence/rosbag/metadata.yaml
    else
      test -s /evidence/rosbag.disabled.txt
    fi
    if (( LAUNCH_CODE != 0 )); then
      echo "ROS launch exited unexpectedly: $LAUNCH_CODE" >&2
      exit 1
    fi
    if [[ $RECORD_ROSBAG == 1 ]] && (( BAG_CODE != 0 && BAG_CODE != 2 )); then
      echo "rosbag recorder exited unexpectedly: $BAG_CODE" >&2
      exit 1
    fi
    if (( CAPTURE_CODE != 0 )); then
      echo "voxel capture exited unexpectedly: $CAPTURE_CODE" >&2
      exit 1
    fi
  ' &
container_pid=$!

if [[ $NATIVE_RVIZ_PRESTART_GATE == 1 ]]; then
  prestart_ready=0
  for _ in $(seq 1 600); do
    if podman container exists "$CONTAINER_NAME" 2>/dev/null \
      && podman exec "$CONTAINER_NAME" bash -lc '
        source /opt/ros/foxy/setup.bash
        ros2 node list 2>/dev/null | grep -qx /lite3_native_rviz_review
        ros2 topic info /quad_0/cloud 2>/dev/null \
          | grep -Eq "Subscription count: [1-9][0-9]*"
      '; then
      prestart_ready=1
      break
    fi
    if ! kill -0 "$container_pid" 2>/dev/null \
      || ! kill -0 "$ISAAC_PID" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done
  {
    printf 'prestart_gate=1\n'
    printf 'subscription_ready=%s\n' "$prestart_ready"
    printf 'source_topic=/quad_0/cloud\n'
    printf 'source_mode=live\n'
  } >"$OUTPUT_DIR/native_rviz_prestart_gate.txt"
  kill -CONT "$ISAAC_PID" 2>/dev/null || true
  if (( prestart_ready != 1 )); then
    podman stop --time 5 "$CONTAINER_NAME" >/dev/null 2>&1 || true
    wait "$container_pid" || true
    wait "$ISAAC_PID" || true
    set -e
    echo "native RViz live-cloud subscription was not ready before Isaac" >&2
    exit 70
  fi
fi

wait "$container_pid"
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

if ! python3 - "$OUTPUT_DIR/isaac/qualification_report.json" <<'PY'
import json
import sys

report_path = sys.argv[1]
with open(report_path, encoding="utf-8") as handle:
    report = json.load(handle)
if report.get("status") != "PASS":
    raise SystemExit(
        f"Isaac qualification report is not PASS: {report.get('status')!r}"
    )
PY
then
  echo "Isaac qualification report rejected the run" >&2
  exit 1
fi

if [[ $OFFICE_REVIEW_ENABLED == 1 ]]; then
  sha256sum \
    "$OUTPUT_DIR/closed_loop.mp4" \
    "$OUTPUT_DIR/closed_loop_third_person_side.mp4" \
    "$OUTPUT_DIR/closed_loop_overview.mp4" \
    "$OUTPUT_DIR/office_review_dashboard.mp4" \
    "$OUTPUT_DIR/camera_trace.jsonl" \
    "$OUTPUT_DIR/office_review_material_audit.json" \
    "$OUTPUT_DIR/office_review_dashboard_metadata.json" \
    "$OUTPUT_DIR/office_review_validation_report.json" \
    "$OUTPUT_DIR/office_review_ros_events_snapshot.jsonl" \
    >"$OUTPUT_DIR/office_review_output_sha256.txt"
fi
