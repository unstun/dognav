#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
RUN_ROOT=${SCAN_V8_RUN_ROOT:-/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human}
CAUSAL_RUNNER=${SCAN_V8_CAUSAL_RUNNER:-$RUN_ROOT/run_remote_causal_immediate_walk_preview.sh}
BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge
RESULT_DIR=$RUN_ROOT/results/$RUN_ID

export SCAN_ENTRYPOINT=$0
export SCAN_ENABLE_VOXEL_CAPTURE=1
export SCAN_VOXEL_CAPTURE_PERIOD_SECONDS=${SCAN_VOXEL_CAPTURE_PERIOD_SECONDS:-0.1}

bash "$CAUSAL_RUNNER" "$@"

for required in \
  "$RESULT_DIR/voxel_snapshots" \
  "$RESULT_DIR/voxel_frames.jsonl" \
  "$RESULT_DIR/voxel_capture_summary.json" \
  "$RESULT_DIR/voxel_rosbag_info.txt" \
  "$RESULT_DIR/closed_loop_review_overlay.mp4" \
  "$RESULT_DIR/isaac/run_identity.json"; do
  if [[ ! -e $required ]]; then
    echo "voxel review input missing: $required" >&2
    exit 66
  fi
done

for topic in \
  /grid_map/occupancy \
  /grid_map/occupancy_inflate \
  /grid_map/sliding_map_bbox; do
  topic_line=$(grep -F "Topic: $topic |" "$RESULT_DIR/voxel_rosbag_info.txt" || true)
  topic_count=$(sed -E 's/.*Count: ([0-9]+).*/\1/' <<<"$topic_line")
  if [[ -z $topic_line || ! $topic_count =~ ^[0-9]+$ ]] || (( topic_count < 1 )); then
    echo "voxel topic missing or empty in rosbag: $topic" >&2
    exit 70
  fi
done

# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export PYTHONPATH=$BRIDGE${PYTHONPATH:+:$PYTHONPATH}
python -u -m lite3_sim_bridge.voxel_review \
  --snapshot-dir "$RESULT_DIR/voxel_snapshots" \
  --metadata "$RESULT_DIR/voxel_frames.jsonl" \
  --summary "$RESULT_DIR/voxel_capture_summary.json" \
  --run-identity "$RESULT_DIR/isaac/run_identity.json" \
  --output "$RESULT_DIR/voxel_3d_review.mp4" \
  --sidecar "$RESULT_DIR/voxel_3d_review_metadata.json" \
  --fps 10.0

ffmpeg -y -loglevel error \
  -i "$RESULT_DIR/closed_loop_review_overlay.mp4" \
  -i "$RESULT_DIR/voxel_3d_review.mp4" \
  -filter_complex \
  '[0:v]scale=640:360[isaac];[1:v]scale=640:360[voxel];[isaac][voxel]hstack=inputs=2[review]' \
  -map '[review]' -c:v libx264 -pix_fmt yuv420p -r 17 -shortest \
  "$RESULT_DIR/isaac_voxel_3d_side_by_side.mp4"

ffprobe -v error \
  -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames \
  -show_entries format=duration \
  -of json "$RESULT_DIR/voxel_3d_review.mp4" \
  >"$RESULT_DIR/voxel_3d_review_probe.json"
ffprobe -v error \
  -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames \
  -show_entries format=duration \
  -of json "$RESULT_DIR/isaac_voxel_3d_side_by_side.mp4" \
  >"$RESULT_DIR/isaac_voxel_3d_side_by_side_probe.json"

sha256sum \
  "$0" \
  "$CAUSAL_RUNNER" \
  "$BRIDGE/lite3_sim_bridge/voxel_capture_node.py" \
  "$BRIDGE/lite3_sim_bridge/voxel_review.py" \
  "$RESULT_DIR/voxel_frames.jsonl" \
  "$RESULT_DIR/voxel_capture_summary.json" \
  "$RESULT_DIR/voxel_3d_review_metadata.json" \
  "$RESULT_DIR/voxel_3d_review.mp4" \
  "$RESULT_DIR/isaac_voxel_3d_side_by_side.mp4" \
  >"$RESULT_DIR/voxel_3d_review_sha256.txt"

printf 'native SCAN voxel review complete: %s\n' "$RUN_ID"
