#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 RESULT_DIR [REPLAY_RATE]" >&2
  exit 64
fi

RESULT_DIR=$1
REPLAY_RATE=${2:-0.5}
START_DELAY_SECONDS=${RVIZ_REPLAY_START_DELAY_SECONDS:-10}
ROS_BAG_DIR=${RVIZ_REPLAY_ROSBAG_DIR:-$RESULT_DIR/rosbag}
ENVIRONMENT_ROOT=/opt/homebrew/Caskroom/miniforge/base/envs/machine-dog-nav-humble-rviz
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPOSITORY_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
OVERLAY_SETUP=$REPOSITORY_ROOT/.pipeline/experiments/2026-08-16_scan_forest_v8_voxel_review/robostack_humble_rviz/humble_overlay/install/setup.bash
RVIZ_CONFIG=$REPOSITORY_ROOT/integration/lite3_sim_bridge/config/humble_voxel_replay.rviz
AUDIT_PATH=$RESULT_DIR/rviz_replay_audit.json

if ! [[ $REPLAY_RATE =~ ^[0-9]+([.][0-9]+)?$ ]] || [[ $REPLAY_RATE == 0 || $REPLAY_RATE == 0.0 ]]; then
  echo "REPLAY_RATE must be a positive decimal" >&2
  exit 64
fi
if ! [[ $START_DELAY_SECONDS =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "RVIZ_REPLAY_START_DELAY_SECONDS must be a non-negative decimal" >&2
  exit 64
fi
for required in \
  "$ROS_BAG_DIR/metadata.yaml" \
  "$RESULT_DIR/voxel_frames.jsonl" \
  "$RESULT_DIR/voxel_snapshots" \
  "$ENVIRONMENT_ROOT/setup.sh" \
  "$OVERLAY_SETUP" \
  "$RVIZ_CONFIG"; do
  if [[ ! -e $required ]]; then
    echo "required RViz replay input is missing: $required" >&2
    exit 66
  fi
done
if [[ -e $AUDIT_PATH || -L $AUDIT_PATH ]]; then
  echo "RViz replay audit already exists; preserve it and use a fresh result directory: $AUDIT_PATH" >&2
  exit 73
fi

export PATH=$ENVIRONMENT_ROOT/bin:/usr/bin:/bin:/usr/sbin:/sbin
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
set +u
# shellcheck source=/dev/null
source "$ENVIRONMENT_ROOT/setup.sh"
# shellcheck source=/dev/null
source "$OVERLAY_SETUP"
set -u
export PYTHONPATH=$REPOSITORY_ROOT/integration/lite3_sim_bridge${PYTHONPATH:+:$PYTHONPATH}

rviz_pid=
replay_pid=
cleanup() {
  if [[ -n $replay_pid ]] && kill -0 "$replay_pid" 2>/dev/null; then
    kill -INT "$replay_pid" 2>/dev/null || true
    wait "$replay_pid" 2>/dev/null || true
  fi
  if [[ -n $rviz_pid ]] && kill -0 "$rviz_pid" 2>/dev/null; then
    kill -TERM "$rviz_pid" 2>/dev/null || true
    wait "$rviz_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

"$ENVIRONMENT_ROOT/bin/rviz2" -d "$RVIZ_CONFIG" &
rviz_pid=$!
"$ENVIRONMENT_ROOT/bin/python" -m lite3_sim_bridge.rviz_replay_node --ros-args \
  -p audit_path:="$AUDIT_PATH" \
  -p voxel_metadata_path:="$RESULT_DIR/voxel_frames.jsonl" \
  -p voxel_snapshot_dir:="$RESULT_DIR/voxel_snapshots" \
  -p preload_first_snapshot:=true \
  -p require_live_lidar:=true &
replay_pid=$!

sleep "$START_DELAY_SECONDS"
if ! kill -0 "$rviz_pid" 2>/dev/null || ! kill -0 "$replay_pid" 2>/dev/null; then
  echo "RViz or replay adapter exited before rosbag playback" >&2
  exit 70
fi

"$ENVIRONMENT_ROOT/bin/ros2" bag play "$ROS_BAG_DIR" --rate "$REPLAY_RATE"
sleep 2
kill -INT "$replay_pid"
wait "$replay_pid"
replay_pid=

"$ENVIRONMENT_ROOT/bin/python" - "$AUDIT_PATH" <<'PY'
import json
import sys

audit = json.load(open(sys.argv[1], encoding="utf-8"))
if audit.get("status") != "PASS":
    raise SystemExit("RViz replay audit did not pass")
if not audit.get("checks", {}).get("live_lidar_observed_when_required"):
    raise SystemExit("RViz replay did not publish the required live LiDAR layer")
print(json.dumps({
    "status": audit["status"],
    "voxel_publish_count": audit["voxel_publish_count"],
    "live_lidar_publish_count": audit["live_lidar_publish_count"],
    "trajectory_ids": audit["trajectory_ids"],
}, sort_keys=True))
PY
