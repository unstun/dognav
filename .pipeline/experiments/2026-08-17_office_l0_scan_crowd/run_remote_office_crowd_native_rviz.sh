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
RVIZ_STARTUP_TIMEOUT_SECONDS=${SCAN_RVIZ_STARTUP_TIMEOUT_SECONDS:-2400}
REQUIRE_TERMINAL_GATE=${SCAN_NATIVE_RVIZ_REQUIRE_TERMINAL_GATE:-1}
REQUIRE_PEDESTRIAN_MOTION_GATE=${SCAN_NATIVE_RVIZ_REQUIRE_PEDESTRIAN_MOTION_GATE:-$REQUIRE_TERMINAL_GATE}

if ! [[ $DURATION_SECONDS =~ ^[1-9][0-9]*$ ]]; then
  echo "duration must be a positive integer" >&2
  exit 64
fi
if ! [[ $RVIZ_STARTUP_TIMEOUT_SECONDS =~ ^[1-9][0-9]*$ ]]; then
  echo "SCAN_RVIZ_STARTUP_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 64
fi
if [[ $REQUIRE_TERMINAL_GATE != 0 && $REQUIRE_TERMINAL_GATE != 1 ]]; then
  echo "SCAN_NATIVE_RVIZ_REQUIRE_TERMINAL_GATE must be 0 or 1" >&2
  exit 64
fi
if [[ $REQUIRE_PEDESTRIAN_MOTION_GATE != 0 && $REQUIRE_PEDESTRIAN_MOTION_GATE != 1 ]]; then
  echo "SCAN_NATIVE_RVIZ_REQUIRE_PEDESTRIAN_MOTION_GATE must be 0 or 1" >&2
  exit 64
fi

RUN_ROOT=/home/sun/machine-dog-nav-runs/2026-08-17_office_l0_scan_crowd
FOXY_WORKSPACE=${SCAN_FOXY_WORKSPACE:-/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human/foxy_ws}
OFFICE_DRIVER=${SCAN_OFFICE_DRIVER:-$RUN_ROOT/run_remote_office_crowd.sh}
RESULT_DIR=$RUN_ROOT/results/$RUN_ID
DISPLAY_NAME=${SCAN_RVIZ_DISPLAY:-:0}
XAUTHORITY_PATH=${SCAN_RVIZ_XAUTHORITY:-/run/user/1000/gdm/Xauthority}
RVIZ_IMAGE=${SCAN_RVIZ_IMAGE:-localhost/machine-dog-nav/foxy-scan-rviz:20260818}
BRIDGE_ROOT=${SCAN_BRIDGE:-$RUN_ROOT/integration/lite3_sim_bridge}
export PYTHONPATH=$BRIDGE_ROOT${PYTHONPATH:+:$PYTHONPATH}
RVIZ_CONFIG=$FOXY_WORKSPACE/src/lite3_sim_bridge/config/foxy_native_scan_review.rviz
CAPTURE_PATH=$RESULT_DIR/native_scan_rviz3d_5070ti.mp4
SYNC_CAPTURE_PATH=$RESULT_DIR/native_scan_rviz3d_5070ti_sim_time.mp4
SYNC_METADATA_PATH=$RESULT_DIR/native_scan_rviz3d_sim_time_metadata.json
TERMINAL_VALIDATION_PATH=$RESULT_DIR/office_review_terminal_validation.json
MOTION_AUDIT_PATH=$RESULT_DIR/office_pedestrian_motion_audit.json
COMBINED_PATH=$RESULT_DIR/office_review_third_person_rviz_4k.mp4
COMBINED_FFPROBE_PATH=$RESULT_DIR/office_review_third_person_rviz_4k_ffprobe.json
COMBINED_VALIDATION_PATH=$RESULT_DIR/office_review_third_person_rviz_4k_validation.json
TRANSFER_PATH=$RESULT_DIR/office_review_third_person_rviz_4k_transfer.mp4
TRANSFER_FFPROBE_PATH=$RESULT_DIR/office_review_third_person_rviz_4k_transfer_ffprobe.json
TRANSFER_VALIDATION_PATH=$RESULT_DIR/office_review_third_person_rviz_4k_transfer_validation.json
TRANSFER_SHA256_PATH=$RESULT_DIR/office_review_third_person_rviz_4k_transfer_sha256.txt
COMPRESSION_MANIFEST_PATH=$RESULT_DIR/video_compression_manifest.json
LIVE_POINTCLOUD_AUDIT_PATH=$RESULT_DIR/live_pointcloud_continuity_audit.json
CAPTURE_TIMELINE_PATH=$RESULT_DIR/native_scan_rviz3d_capture_timeline.jsonl
REVIEW_AUDIT_PATH=$RESULT_DIR/native_rviz_review_audit.json
DELIVERY_RELIABILITY_SOURCE=$BRIDGE_ROOT/lite3_sim_bridge/delivery_reliability.py
RUN_DRIVER_LOG=$RUN_ROOT/results/${RUN_ID}.driver.log

for required in \
  "$OFFICE_DRIVER" \
  "$RUN_ROOT/acceptance_thresholds_office_crowd.json" \
  "$RUN_ROOT/integration/lite3_sim_bridge/lite3_sim_bridge/rviz_time_sync.py" \
  "$DELIVERY_RELIABILITY_SOURCE" \
  "$FOXY_WORKSPACE/install/setup.bash" \
  "$RVIZ_CONFIG" \
  "$XAUTHORITY_PATH" \
  /tmp/.X11-unix/X0; do
  if [[ ! -e $required ]]; then
    echo "required native RViz input is missing: $required" >&2
    exit 66
  fi
done
if [[ -e $RESULT_DIR || -L $RESULT_DIR ]]; then
  echo "result directory already exists; preserve it and use a new run id: $RESULT_DIR" >&2
  exit 73
fi
if [[ -e $RUN_DRIVER_LOG || -L $RUN_DRIVER_LOG ]]; then
  echo "driver log already exists; preserve it and use a new run id: $RUN_DRIVER_LOG" >&2
  exit 73
fi
if ! podman image exists "$RVIZ_IMAGE"; then
  echo "native RViz image is missing: $RVIZ_IMAGE" >&2
  exit 66
fi

run_pid=
capture_pid=
timeline_pid=
cleanup() {
  if [[ -n ${timeline_pid:-} ]] && kill -0 "$timeline_pid" 2>/dev/null; then
    kill -TERM "$timeline_pid" 2>/dev/null || true
    wait "$timeline_pid" 2>/dev/null || true
  fi
  if [[ -n ${capture_pid:-} ]] && kill -0 "$capture_pid" 2>/dev/null; then
    kill -INT "$capture_pid" 2>/dev/null || true
    wait "$capture_pid" 2>/dev/null || true
  fi
  if [[ -n ${run_pid:-} ]] && kill -0 "$run_pid" 2>/dev/null; then
    kill -TERM "$run_pid" 2>/dev/null || true
    wait "$run_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

SCAN_NATIVE_RVIZ_ENABLED=1 \
SCAN_NATIVE_RVIZ_PRESTART_GATE=1 \
SCAN_NATIVE_RVIZ_DISPLAY="$DISPLAY_NAME" \
SCAN_NATIVE_RVIZ_XAUTHORITY="$XAUTHORITY_PATH" \
SCAN_NATIVE_RVIZ_IMAGE="$RVIZ_IMAGE" \
SCAN_NATIVE_RVIZ_CONFIG_REL=src/lite3_sim_bridge/config/foxy_native_scan_review.rviz \
SCAN_OFFICIAL_HUMAN_ANIMATION_MODE=phase_conditioned \
SCAN_OFFICE_PEDESTRIAN_MOTION_MODE=background_ping_pong \
SCAN_OFFICE_PEDESTRIAN_TURNAROUND_HOLD_SECONDS=0.6 \
bash "$OFFICE_DRIVER" \
  "$RUN_ID" "$DURATION_SECONDS" "$TELEMETRY_PORT" "$COMMAND_PORT" \
  >"$RUN_DRIVER_LOG" 2>&1 &
run_pid=$!

result_ready=0
for _ in $(seq 1 900); do
  if [[ -d $RESULT_DIR ]]; then
    result_ready=1
    break
  fi
  if ! kill -0 "$run_pid" 2>/dev/null; then
    break
  fi
  sleep 0.25
done
if (( result_ready != 1 )); then
  set +e
  wait "$run_pid"
  run_code=$?
  set -e
  run_pid=
  echo "office run exited before creating its result directory (exit $run_code)" >&2
  if (( run_code != 0 )); then
    exit "$run_code"
  fi
  exit 70
fi

rviz_window_id=
rviz_wait_steps=$((RVIZ_STARTUP_TIMEOUT_SECONDS * 4))
for _ in $(seq 1 "$rviz_wait_steps"); do
  rviz_window_id=$(DISPLAY="$DISPLAY_NAME" XAUTHORITY="$XAUTHORITY_PATH" \
    xwininfo -root -tree 2>/dev/null \
    | awk '/\("rviz2" "rviz2"\)/ && / - RViz"/ {print $1; exit}')
  if [[ -n $rviz_window_id ]]; then
    break
  fi
  if ! kill -0 "$run_pid" 2>/dev/null; then
    break
  fi
  sleep 0.25
done
if [[ -z $rviz_window_id ]]; then
  wait "$run_pid" || true
  run_pid=
  echo "native RViz window did not appear from the SCAN container" >&2
  exit 70
fi

window_info=$(DISPLAY="$DISPLAY_NAME" XAUTHORITY="$XAUTHORITY_PATH" \
  xwininfo -id "$rviz_window_id")
window_x=$(awk -F: '/Absolute upper-left X/ {gsub(/ /, "", $2); print $2}' <<<"$window_info")
window_y=$(awk -F: '/Absolute upper-left Y/ {gsub(/ /, "", $2); print $2}' <<<"$window_info")
window_width=$(awk -F: '/Width/ {gsub(/ /, "", $2); print $2; exit}' <<<"$window_info")
window_height=$(awk -F: '/Height/ {gsub(/ /, "", $2); print $2; exit}' <<<"$window_info")
capture_width=$((window_width - window_width % 2))
capture_height=$((capture_width * 9 / 16))
capture_height=$((capture_height - capture_height % 2))
if (( capture_height > window_height )); then
  capture_height=$((window_height - window_height % 2))
fi

{
  printf 'display=%s\n' "$DISPLAY_NAME"
  printf 'rviz_window_id=%s\n' "$rviz_window_id"
  printf 'capture_x=%s\n' "$window_x"
  printf 'capture_y=%s\n' "$window_y"
  printf 'capture_width=%s\n' "$capture_width"
  printf 'capture_height=%s\n' "$capture_height"
  printf '%s\n' "$window_info"
} >"$RESULT_DIR/native_scan_rviz3d_window.txt"
podman image inspect --format '{{.Id}}' "$RVIZ_IMAGE" \
  >"$RESULT_DIR/native_scan_rviz3d_image_id.txt"
sha256sum "$RVIZ_CONFIG" \
  >"$RESULT_DIR/native_scan_rviz3d_config_sha256.txt"

capture_start_epoch_ns=$(date +%s%N)
ffmpeg -hide_banner -loglevel warning -n \
  -f x11grab \
  -draw_mouse 0 \
  -framerate 25 \
  -video_size "${capture_width}x${capture_height}" \
  -i "${DISPLAY_NAME}.0+${window_x},${window_y}" \
  -vf scale=1920:1080:flags=lanczos \
  -an \
  -c:v h264_nvenc \
  -preset p7 \
  -tune hq \
  -rc vbr \
  -cq 16 \
  -b:v 0 \
  -profile:v high \
  -pix_fmt yuv420p \
  -color_range tv \
  -color_primaries bt709 \
  -color_trc bt709 \
  -colorspace bt709 \
  -movflags +faststart \
  "$CAPTURE_PATH" \
  >"$RESULT_DIR/native_scan_rviz3d_ffmpeg.log" 2>&1 &
capture_pid=$!

PYTHONPATH="$RUN_ROOT/integration/lite3_sim_bridge${PYTHONPATH:+:$PYTHONPATH}" \
python3 -u -m lite3_sim_bridge.rviz_time_sync observe \
  --camera-trace "$RESULT_DIR/camera_trace.jsonl" \
  --output-timeline "$CAPTURE_TIMELINE_PATH" \
  --capture-start-epoch-ns "$capture_start_epoch_ns" \
  --producer-pid "$run_pid" \
  --poll-seconds 0.005 \
  >"$RESULT_DIR/native_scan_rviz3d_timeline.log" 2>&1 &
timeline_pid=$!

voxel_ready=0
for _ in $(seq 1 900); do
  if [[ -s $RESULT_DIR/voxel_frames.jsonl ]]; then
    voxel_ready=1
    break
  fi
  if ! kill -0 "$run_pid" 2>/dev/null; then
    break
  fi
  sleep 0.1
done
if (( voxel_ready != 1 )); then
  wait "$run_pid" || true
  run_pid=
  echo "native SCAN occupancy evidence did not appear" >&2
  exit 70
fi

set +e
wait "$run_pid"
run_code=$?
set -e
run_pid=
sleep 2
set +e
wait "$timeline_pid"
timeline_code=$?
set -e
timeline_pid=
kill -INT "$capture_pid" 2>/dev/null || true
set +e
wait "$capture_pid"
capture_code=$?
set -e
capture_pid=

cp "$RUN_DRIVER_LOG" "$RESULT_DIR/native_scan_rviz3d_run_driver.log"
nvidia-smi --query-gpu=name,driver_version,memory.total \
  --format=csv,noheader \
  >"$RESULT_DIR/native_scan_rviz3d_gpu_identity.txt"

if (( run_code != 0 )); then
  echo "office run failed with exit code $run_code" >&2
  exit "$run_code"
fi
if (( capture_code != 0 && capture_code != 130 && capture_code != 255 )); then
  echo "native RViz capture failed with exit code $capture_code" >&2
  exit "$capture_code"
fi
if (( timeline_code != 0 )); then
  echo "native RViz timeline capture failed with exit code $timeline_code" >&2
  exit "$timeline_code"
fi
if [[ ! -s $CAPTURE_PATH ]]; then
  echo "native RViz capture is empty" >&2
  exit 70
fi
if [[ ! -s $REVIEW_AUDIT_PATH ]]; then
  echo "native RViz path/pose/URDF audit is missing" >&2
  exit 70
fi
python3 - "$REVIEW_AUDIT_PATH" <<'PY'
import json
import sys

audit = json.load(open(sys.argv[1], encoding="utf-8"))
required = (
    "body_path_has_multiple_poses",
    "bspline_observed",
    "current_pose_matches_body_path",
    "root_transform_matches_body_path",
    "live_lidar_audit_enabled",
    "live_lidar_observed_when_required",
    "all_received_live_lidar_nonempty",
    "live_lidar_stamps_strictly_increase",
    "live_lidar_simulator_gap_max_le_0_2_seconds",
)
if audit.get("status") != "PASS" or audit.get("source_mode") != "live":
    raise SystemExit("native RViz review audit did not pass")
if not all(audit.get("checks", {}).get(name) for name in required):
    raise SystemExit("native RViz review audit is missing a required live check")
if audit.get("require_live_lidar") is not True:
    raise SystemExit("native RViz live LiDAR audit was not required")
if int(audit.get("live_lidar_publish_count", 0)) <= 0:
    raise SystemExit("native RViz live LiDAR handled count is zero")
PY

# The raw RViz capture is wall-clock long because Isaac runs slower than real
# time. Select the native 5070 Ti frame observed for each camera-trace simulator
# timestamp so RViz, the preserved first view, and the external view share the
# same frame count and simulation-time sequence.
# shellcheck source=/dev/null
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export PYTHONPATH=$BRIDGE_ROOT${PYTHONPATH:+:$PYTHONPATH}
python3 - \
  "$RESULT_DIR/isaac/metrics.jsonl" \
  "$RESULT_DIR/isaac/run_identity.json" \
  "$MOTION_AUDIT_PATH" \
  "$REQUIRE_PEDESTRIAN_MOTION_GATE" <<'PY'
import json
import sys
from pathlib import Path

from lite3_sim_bridge.office_crowd_acceptance import (
    _load_jsonl,
    _pedestrian_motion_fidelity,
)

metrics_path, identity_path, output_path = map(Path, sys.argv[1:4])
require_full_motion_gate = sys.argv[4] == "1"
metrics_rows = _load_jsonl(metrics_path)
identity = json.loads(identity_path.read_text(encoding="utf-8"))
office = identity.get("office_crowd", {})
fidelity = _pedestrian_motion_fidelity(metrics_rows)
checks = {
    "safe_background_ping_pong_root_motion": office.get("pedestrian_motion_mode")
    == "background_ping_pong",
    "phase_conditioned_animation": office.get("official_human_animation_mode")
    == "phase_conditioned",
    "eight_people_observed": len(fidelity["pedestrian_names"]) == 8,
    "no_in_place_walk": fidelity["in_place_walk_fraction"] <= 0.01,
    "no_idle_sliding": fidelity["idle_while_moving_fraction"] <= 0.01,
}
duration_dependent_checks = {
    "root_motion_fraction": fidelity["root_moving_fraction"] >= 0.50,
    "continuous_crowd_motion": fidelity["timeline_any_root_motion_fraction"] >= 0.95,
}
if require_full_motion_gate:
    checks.update(duration_dependent_checks)
passed = all(checks.values())
payload = {
    "schema_version": 1,
    "status": "PASS" if passed else "FAIL",
    "claim_boundary": (
        "Automated root-motion and animation-coherence gate only; visible gait "
        "quality still requires Dr Sun's AC55 review."
        if require_full_motion_gate
        else "Short dual-view visual preflight only. Full-duration root-motion "
        "fractions are recorded but not gated; formal Office acceptance and "
        "human AC55 review are not evaluated by this run."
    ),
    "checks": checks,
    "fidelity": fidelity,
}
if not require_full_motion_gate:
    payload["non_gating_duration_observations"] = duration_dependent_checks
output_path.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
if not passed:
    raise SystemExit("Office pedestrian motion fidelity audit failed")
PY
python -u -m lite3_sim_bridge.rviz_time_sync synchronize \
  --source-video "$CAPTURE_PATH" \
  --timeline "$CAPTURE_TIMELINE_PATH" \
  --camera-trace "$RESULT_DIR/camera_trace.jsonl" \
  --reference-video "$RESULT_DIR/closed_loop_third_person_side.mp4" \
  --output-video "$SYNC_CAPTURE_PATH" \
  --output-metadata "$SYNC_METADATA_PATH" \
  >"$RESULT_DIR/native_scan_rviz3d_sync.log" 2>&1

python -u -m lite3_sim_bridge.delivery_reliability audit \
  --sensor-metrics "$RESULT_DIR/isaac/sensor_metrics.jsonl" \
  --native-audit "$REVIEW_AUDIT_PATH" \
  --rviz-config "$RVIZ_CONFIG" \
  --video "$SYNC_CAPTURE_PATH" \
  --output "$LIVE_POINTCLOUD_AUDIT_PATH" \
  >"$RESULT_DIR/live_pointcloud_continuity_audit.log" 2>&1

# A long visual review must show the complete route and a continuous terminal
# stop, not merely run for an arbitrary number of seconds. Reuse the frozen
# Office runtime projection so this supplemental gate has the same goal and
# two-second stop thresholds as the formal evaluator. A short visual preflight
# may explicitly skip only this terminal gate; all native RViz synchronization,
# pedestrian, and combined-video checks remain active.
if [[ $REQUIRE_TERMINAL_GATE == 1 ]]; then
  python3 - \
    "$RESULT_DIR/isaac/metrics.jsonl" \
    "$RESULT_DIR/isaac/sensor_metrics.jsonl" \
    "$RUN_ROOT/acceptance_thresholds_office_crowd.json" \
    "$TERMINAL_VALIDATION_PATH" <<'PY'
import json
import math
import sys
from pathlib import Path

from lite3_sim_bridge.office_crowd_acceptance import (
    _load_jsonl,
    _runtime_gate_metrics,
)

metrics_path, sensor_path, thresholds_path, output_path = map(Path, sys.argv[1:])
metrics_rows = _load_jsonl(metrics_path)
sensor_rows = _load_jsonl(sensor_path)
thresholds_payload = json.loads(thresholds_path.read_text(encoding="utf-8"))
limits = thresholds_payload["thresholds"]
goal_xy = [float(value) for value in thresholds_payload["goal_world_xy_m"]]
runtime = _runtime_gate_metrics(
    metrics_rows,
    sensor_rows,
    float(limits["stop_window_seconds"]),
)
final_xy = [float(value) for value in metrics_rows[-1]["root_pos_w"][:2]]
goal_error = math.dist(final_xy, goal_xy)
checks = {
    "minimum_simulation_duration": {
        "passed": runtime["simulation_duration_seconds"]
        >= float(limits["minimum_sim_duration_seconds"]),
        "actual_seconds": runtime["simulation_duration_seconds"],
        "minimum_seconds": float(limits["minimum_sim_duration_seconds"]),
    },
    "goal_xy": {
        "passed": goal_error <= float(limits["goal_xy_tolerance_m"]),
        "final_xy_m": final_xy,
        "goal_xy_m": goal_xy,
        "error_m": goal_error,
        "maximum_error_m": float(limits["goal_xy_tolerance_m"]),
    },
    "continuous_terminal_stop": {
        "passed": runtime["terminal_command_max_abs"]
        <= float(limits["stop_command_max_abs"])
        and runtime["terminal_planar_speed_max_mps"]
        <= float(limits["stop_planar_speed_max_mps"]),
        "window_seconds": float(limits["stop_window_seconds"]),
        "maximum_command_abs": runtime["terminal_command_max_abs"],
        "maximum_planar_speed_mps": runtime["terminal_planar_speed_max_mps"],
        "command_limit": float(limits["stop_command_max_abs"]),
        "planar_speed_limit_mps": float(limits["stop_planar_speed_max_mps"]),
    },
}
passed = all(check["passed"] for check in checks.values())
payload = {
    "schema_version": 1,
    "status": "PASS" if passed else "FAIL",
    "claim_boundary": (
        "Supplemental visual endpoint and terminal-stop gate; this does not "
        "replace formal Office acceptance or human AC55 review."
    ),
    "checks": checks,
}
output_path.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
if not passed:
    raise SystemExit("Office visual review did not reach and stop at the goal")
PY
else
  python3 - "$TERMINAL_VALIDATION_PATH" <<'PY'
import json
import sys
from pathlib import Path

output_path = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "status": "SKIPPED",
    "claim_boundary": (
        "Short dual-view visual preflight only. Goal arrival, continuous "
        "terminal stop, formal Office acceptance, and human AC55 review are "
        "not evaluated by this run."
    ),
    "checks": {},
}
output_path.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
fi

# Preserve every full-resolution entity as evidence, then provide the two views
# requested for review: high external third-person plus native 5070 Ti RViz.
ffmpeg -hide_banner -loglevel error -n \
  -i "$RESULT_DIR/closed_loop_third_person_side.mp4" \
  -i "$SYNC_CAPTURE_PATH" \
  -filter_complex \
  "[0:v]scale=1920:1080:flags=lanczos,setsar=1[side];[1:v]scale=1920:1080:flags=lanczos,setsar=1[rviz];[side][rviz]hstack=inputs=2[review]" \
  -map '[review]' -an \
  -c:v h264_nvenc -preset p7 -tune hq -rc vbr -cq 16 -b:v 0 \
  -profile:v high -pix_fmt yuv420p \
  -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -r 25 -shortest -movflags +faststart \
  "$COMBINED_PATH"

ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames,nb_read_frames \
  -show_entries format=duration,size \
  -of json "$COMBINED_PATH" \
  >"$COMBINED_FFPROBE_PATH"
python3 - \
  "$COMBINED_FFPROBE_PATH" \
  "$RESULT_DIR/camera_trace.jsonl" \
  "$COMBINED_VALIDATION_PATH" <<'PY'
import json
import sys
from pathlib import Path

probe_path, trace_path, output_path = map(Path, sys.argv[1:])
probe = json.loads(probe_path.read_text(encoding="utf-8"))
stream = probe["streams"][0]
trace_count = sum(1 for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip())
checks = {
    "resolution_dual_4k": [int(stream["width"]), int(stream["height"])] == [3840, 1080],
    "frame_rate_25fps": stream["r_frame_rate"] == "25/1",
    "frame_count_matches_trace": int(stream["nb_read_frames"]) == trace_count,
    "h264_yuv420p": stream["codec_name"] == "h264" and stream["pix_fmt"] == "yuv420p",
}
passed = all(checks.values())
payload = {
    "schema_version": 1,
    "status": "PASS" if passed else "FAIL",
    "layout": {
        "resolution": [3840, 1080],
        "panels": {
            "left": "high external side third-person view",
            "right": "native 5070 Ti SCAN RViz synchronized to simulator time",
        },
    },
    "trace_frame_count": trace_count,
    "checks": checks,
    "probe": probe,
}
output_path.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
if not passed:
    raise SystemExit("combined third-person and RViz video validation failed")
PY

python -u -m lite3_sim_bridge.delivery_reliability compress \
  --master "$COMBINED_PATH" \
  --transfer "$TRANSFER_PATH" \
  --ffprobe-output "$TRANSFER_FFPROBE_PATH" \
  --validation-output "$TRANSFER_VALIDATION_PATH" \
  --sha256-output "$TRANSFER_SHA256_PATH" \
  --manifest-output "$COMPRESSION_MANIFEST_PATH" \
  >"$RESULT_DIR/video_compression.log" 2>&1

ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames \
  -show_entries format=duration,size \
  -of json "$CAPTURE_PATH" \
  >"$RESULT_DIR/native_scan_rviz3d_ffprobe.json"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames \
  -show_entries format=duration,size \
  -of json "$SYNC_CAPTURE_PATH" \
  >"$RESULT_DIR/native_scan_rviz3d_sim_time_ffprobe.json"
sha256sum \
  "$0" \
  "$RUN_ROOT/integration/lite3_sim_bridge/lite3_sim_bridge/rviz_time_sync.py" \
  "$DELIVERY_RELIABILITY_SOURCE" \
  "$RVIZ_CONFIG" \
  "$RESULT_DIR/native_scan_rviz3d_image_id.txt" \
  "$RESULT_DIR/native_scan_rviz3d_window.txt" \
  "$RESULT_DIR/native_scan_rviz3d_ffprobe.json" \
  "$RESULT_DIR/native_scan_rviz3d_sim_time_ffprobe.json" \
  "$RESULT_DIR/native_rviz_robot_state.log" \
  "$REVIEW_AUDIT_PATH" \
  "$LIVE_POINTCLOUD_AUDIT_PATH" \
  "$CAPTURE_TIMELINE_PATH" \
  "$SYNC_METADATA_PATH" \
  "$TERMINAL_VALIDATION_PATH" \
  "$MOTION_AUDIT_PATH" \
  "$COMBINED_FFPROBE_PATH" \
  "$COMBINED_VALIDATION_PATH" \
  "$TRANSFER_FFPROBE_PATH" \
  "$TRANSFER_VALIDATION_PATH" \
  "$TRANSFER_SHA256_PATH" \
  "$COMPRESSION_MANIFEST_PATH" \
  "$CAPTURE_PATH" \
  "$SYNC_CAPTURE_PATH" \
  "$COMBINED_PATH" \
  "$TRANSFER_PATH" \
  >"$RESULT_DIR/native_scan_rviz3d_sha256.txt"

printf 'native RViz capture: %s\n' "$CAPTURE_PATH"
printf 'sim-time synchronized native RViz capture: %s\n' "$SYNC_CAPTURE_PATH"
printf 'combined third-person and RViz review: %s\n' "$COMBINED_PATH"
printf 'preferred compressed transfer review: %s\n' "$TRANSFER_PATH"
