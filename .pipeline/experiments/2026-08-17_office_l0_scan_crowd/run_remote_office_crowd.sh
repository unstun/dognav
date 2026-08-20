#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
DURATION_SECONDS=$2

if ! [[ $DURATION_SECONDS =~ ^[1-9][0-9]*$ ]]; then
  echo "duration must be a positive integer" >&2
  exit 64
fi

RUN_ROOT=/home/sun/machine-dog-nav-runs/2026-08-17_office_l0_scan_crowd
V8_ROOT=/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human
CLOSED_LOOP_SCRIPT=${SCAN_CLOSED_LOOP_SCRIPT:-$RUN_ROOT/run_remote_closed_loop.sh}

export SCAN_RUN_ROOT=$RUN_ROOT
export SCAN_ENTRYPOINT=${SCAN_ENTRYPOINT:-$0}
export SCAN_FOXY_WORKSPACE=${SCAN_FOXY_WORKSPACE:-$V8_ROOT/foxy_ws}
export SCAN_V12_RUNTIME=$V8_ROOT/source/locomotion_v12/runtime_20260718_recovered
export SCAN_CHECKPOINT=$V8_ROOT/source/locomotion_v12/checkpoint/model_149999.pt
export SCAN_BRIDGE=${SCAN_BRIDGE:-$RUN_ROOT/integration/lite3_sim_bridge}
export SCAN_ACCEPTANCE_CONFIG=$RUN_ROOT/acceptance_thresholds_office_crowd.json
export SCAN_ROBOT_ASSET=$V8_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface_isaac.urdf
export SCAN_CANONICAL_ROBOT_ASSET=$V8_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface.urdf
export SCAN_COURSE=office_l0_crowd
export SCAN_PLANNER_CONFIG_REL=${SCAN_PLANNER_CONFIG_REL:-src/plan_manage/config/foxy_isaac_office_crowd_planner.yaml}
export SCAN_CONTROLLER_CONFIG_REL=src/plan_manage/config/foxy_isaac_office_crowd_controller.yaml
export SCAN_BRIDGE_CONFIG_REL=${SCAN_BRIDGE_CONFIG_REL:-src/lite3_sim_bridge/config/foxy_bridge.yaml}
export SCAN_CLOUD_PROFILE=${SCAN_CLOUD_PROFILE:-legacy_planner_v1}
export SCAN_REQUIRE_DUAL_CLOUD=${SCAN_REQUIRE_DUAL_CLOUD:-false}
export SCAN_OFFICE_USD_PATH=$RUN_ROOT/results/office_l0_physics_wrapper01.usda
export SCAN_OFFICE_USD_SHA256=5ac29c16ab94a2a2e6bbde8cd7f3907d1e602164604f998070669fa176d9de47
export SCAN_OFFICE_ROUTE_PATH=$RUN_ROOT/results/office_l0_route_preflight07.json
export SCAN_OFFICE_ROUTE_SHA256=6e0db6f6803483fba846a515225aa167aaf7182fe645db11a5da02518cccf368
export SCAN_OFFICE_START_X=-15.625
export SCAN_OFFICE_START_Y=13.125
export SCAN_OFFICE_GOAL_X=-8.375
export SCAN_OFFICE_GOAL_Y=-0.625
export SCAN_LIDAR_PATTERN_MODE=livox_mid360
export SCAN_LIDAR_PATTERN_CSV=$RUN_ROOT/references/upstream/2026-08-19_mid360_simulation/source/livox_laser_simulation/scan_mode/mid360.csv
export SCAN_LIDAR_MIN_RANGE=0.10
export SCAN_LIDAR_MAX_RANGE=40.0
export SCAN_OFFICIAL_HUMAN_ANIMATION_MODE=${SCAN_OFFICIAL_HUMAN_ANIMATION_MODE:-continuous_walk}
export SCAN_OFFICE_PEDESTRIAN_MOTION_MODE=${SCAN_OFFICE_PEDESTRIAN_MOTION_MODE:-single_pass}
export SCAN_OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS=${SCAN_OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS:-0.6}
export SCAN_MAX_VX=0.50
export SCAN_VIDEO_FPS=25
export SCAN_VIDEO_FRAME_STRIDE=2
# Three settled RTX renders are intentionally produced for every review view.
# This wall-clock allowance does not extend simulator time or ROS evidence time.
# Three temporally settled 2K renders per review view make each simulated
# second substantially slower than the original single-view capture.  Keep
# ROS alive long enough for the requested simulation duration instead of
# silently accepting a shortened presentation video.
export SCAN_ROS_RUNTIME_SECONDS=$((DURATION_SECONDS * 60 + 240))
export SCAN_OFFICE_REVIEW_ENABLED=1
export SCAN_OFFICE_REVIEW_CAMERA_SIDE=right
export SCAN_OFFICE_REVIEW_CAMERA_LATERAL_DISTANCE=3.5
export SCAN_OFFICE_REVIEW_CAMERA_TRAILING_BIAS=3.5
export SCAN_OFFICE_REVIEW_CAMERA_HEIGHT=8.0
export SCAN_OFFICE_REVIEW_CAMERA_FOCAL_LENGTH_MM=18.0
export SCAN_OFFICE_REVIEW_CAMERA_LOOK_AHEAD=0.75
export SCAN_OFFICE_REVIEW_CAMERA_LOOK_HEIGHT_OFFSET=0.10
export SCAN_OFFICE_REVIEW_CAMERA_SMOOTHING_RATE=1.5
export SCAN_OFFICE_REVIEW_CAMERA_MAX_EYE_SPEED=4.0
export SCAN_OFFICE_REVIEW_CAMERA_MAX_TARGET_SPEED=4.0
export SCAN_OFFICE_REVIEW_OVERVIEW_DISTANCE=1.5
export SCAN_OFFICE_REVIEW_OVERVIEW_AZIMUTH=90.0
export SCAN_OFFICE_REVIEW_OVERVIEW_HEIGHT=2.3
export SCAN_OFFICE_REVIEW_OVERVIEW_LOOK_AHEAD=0.35
export SCAN_OFFICE_REVIEW_LIGHTING_PROFILE=high_contrast
export SCAN_OFFICE_REVIEW_DOME_LIGHT_INTENSITY=650.0
export SCAN_OFFICE_REVIEW_EXPOSURE=-0.25
export SCAN_ENABLE_VOXEL_CAPTURE=1
export SCAN_VOXEL_CAPTURE_PERIOD_SECONDS=0.1
export SCAN_VISUAL_REVIEW_ONLY=${SCAN_VISUAL_REVIEW_ONLY:-0}
export SCAN_RECORD_ROSBAG=${SCAN_RECORD_ROSBAG:-1}

bash "$CLOSED_LOOP_SCRIPT" "$@"

RESULT_DIR=$RUN_ROOT/results/$RUN_ID
for required in \
  "$RESULT_DIR/voxel_snapshots" \
  "$RESULT_DIR/voxel_frames.jsonl" \
  "$RESULT_DIR/voxel_capture_summary.json" \
  "$RESULT_DIR/isaac/run_identity.json" \
  "$RESULT_DIR/closed_loop.mp4" \
  "$RESULT_DIR/closed_loop_third_person_side.mp4" \
  "$RESULT_DIR/closed_loop_overview.mp4"; do
  if [[ ! -e $required ]]; then
    echo "native SCAN review input missing: $required" >&2
    exit 66
  fi
done

# Render the exact native SCAN raw/inflated voxel snapshots. This is a
# robot-centric sliding occupancy map, not a reconstructed global SLAM cloud.
# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export PYTHONPATH=$SCAN_BRIDGE${PYTHONPATH:+:$PYTHONPATH}
python -u -m lite3_sim_bridge.voxel_review \
  --snapshot-dir "$RESULT_DIR/voxel_snapshots" \
  --metadata "$RESULT_DIR/voxel_frames.jsonl" \
  --summary "$RESULT_DIR/voxel_capture_summary.json" \
  --run-identity "$RESULT_DIR/isaac/run_identity.json" \
  --output "$RESULT_DIR/native_scan_voxel_review.mp4" \
  --sidecar "$RESULT_DIR/native_scan_voxel_review_metadata.json" \
  --fps 10.0 \
  --width 1920 \
  --height 1080

voxel_offset_seconds=$(python - "$RESULT_DIR/voxel_frames.jsonl" "$RESULT_DIR/camera_trace.jsonl" <<'PY'
import json
import sys

voxel = json.loads(open(sys.argv[1], encoding="utf-8").readline())
camera = json.loads(open(sys.argv[2], encoding="utf-8").readline())
offset = float(voxel["body_stamp_ns"]) / 1.0e9 - float(camera["sim_time_seconds"])
print(f"{max(0.0, offset):.9f}")
PY
)

ffmpeg -hide_banner -loglevel error -n \
  -i "$RESULT_DIR/closed_loop.mp4" \
  -i "$RESULT_DIR/closed_loop_third_person_side.mp4" \
  -i "$RESULT_DIR/closed_loop_overview.mp4" \
  -i "$RESULT_DIR/native_scan_voxel_review.mp4" \
  -filter_complex \
  "[0:v]scale=640:360,setsar=1[first];[1:v]scale=640:360,setsar=1[side];[2:v]scale=640:360,setsar=1[overview];[first][side][overview]hstack=inputs=3[top];[3:v]scale=1280:720,setsar=1,tpad=start_duration=${voxel_offset_seconds}:start_mode=add:stop_mode=clone:stop_duration=2,pad=1920:720:320:0:black[voxels];[top][voxels]vstack=inputs=2[dashboard]" \
  -map '[dashboard]' -an -c:v libx264 -profile:v high -preset medium -crf 16 \
  -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 \
  -colorspace bt709 -r 25 -shortest -movflags +faststart \
  "$RESULT_DIR/office_review_native_scan_dashboard.mp4"

sha256sum \
  "$0" \
  "$SCAN_BRIDGE/lite3_sim_bridge/voxel_capture_node.py" \
  "$SCAN_BRIDGE/lite3_sim_bridge/voxel_review.py" \
  "$RESULT_DIR/voxel_frames.jsonl" \
  "$RESULT_DIR/voxel_capture_summary.json" \
  "$RESULT_DIR/native_scan_voxel_review_metadata.json" \
  "$RESULT_DIR/native_scan_voxel_review.mp4" \
  "$RESULT_DIR/office_review_native_scan_dashboard.mp4" \
  >"$RESULT_DIR/native_scan_review_sha256.txt"
