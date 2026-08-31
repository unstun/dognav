#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 RESULT_DIR" >&2
  exit 64
fi

RESULT_DIR=$1
MASTER=$RESULT_DIR/office_review_third_person_rviz_4k.mp4
STANDARD_TRANSFER=$RESULT_DIR/office_review_third_person_rviz_4k_transfer.mp4
ARTIFACT_STEM=office_review_third_person_rviz_4k_transfer_under10mb_v2
OUTPUT=$RESULT_DIR/$ARTIFACT_STEM.mp4
PROBE=$RESULT_DIR/${ARTIFACT_STEM}_ffprobe.json
VALIDATION=$RESULT_DIR/${ARTIFACT_STEM}_validation.json
SHA256=$RESULT_DIR/${ARTIFACT_STEM}_sha256.txt
CONTACT_SHEET=$RESULT_DIR/${ARTIFACT_STEM}_contact_sheet.jpg
ENCODING_LOG=$RESULT_DIR/${ARTIFACT_STEM}_encoding.log
SSIM_LOG=$RESULT_DIR/${ARTIFACT_STEM}_ssim.log
MAX_BYTES=10000000
TARGET_PAYLOAD_BYTES=9200000
WIDTH=1280
HEIGHT=360
MINIMUM_SSIM=0.95

for required in "$MASTER" "$STANDARD_TRANSFER"; do
  if [[ ! -f $required || -L $required ]]; then
    echo "required immutable source video is missing or not a regular file: $required" >&2
    exit 66
  fi
done
for output in "$OUTPUT" "$PROBE" "$VALIDATION" "$SHA256" "$CONTACT_SHEET" "$ENCODING_LOG" "$SSIM_LOG"; do
  if [[ -e $output || -L $output ]]; then
    echo "refusing to overwrite under-10MB evidence: $output" >&2
    exit 73
  fi
done

for command in ffmpeg ffprobe python3 sha256sum; do
  command -v "$command" >/dev/null || {
    echo "required command is unavailable: $command" >&2
    exit 69
  }
done

MASTER_HASH_BEFORE=$(sha256sum "$MASTER" | cut -d' ' -f1)
STANDARD_HASH_BEFORE=$(sha256sum "$STANDARD_TRANSFER" | cut -d' ' -f1)
MASTER_DURATION=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$MASTER")
TARGET_KBPS=$(python3 - "$MASTER_DURATION" "$TARGET_PAYLOAD_BYTES" <<'PY'
import math
import sys

duration = float(sys.argv[1])
target_bytes = int(sys.argv[2])
if duration <= 0.0:
    raise SystemExit("master duration must be positive")
print(max(128, math.floor(target_bytes * 8.0 / duration / 1000.0)))
PY
)

TEMP_DIR=$(mktemp -d)
cleanup() {
  rm -f "$TEMP_DIR"/passlog-*
  rmdir "$TEMP_DIR" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
PASSLOG=$TEMP_DIR/passlog

{
  printf 'ffmpeg_version=%s\n' "$(ffmpeg -version | head -1)"
  printf 'target_video_bitrate_kbps=%s\n' "$TARGET_KBPS"
  printf 'pass1='
  printf '%q ' ffmpeg -hide_banner -loglevel error -y -i "$MASTER" -map 0:v:0 -an \
    -vf "scale=$WIDTH:$HEIGHT:flags=lanczos" -c:v libx264 -preset slow \
    -b:v "${TARGET_KBPS}k" -pass 1 -passlogfile "$PASSLOG" -profile:v high \
    -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 \
    -colorspace bt709 -r 25 -f mp4 /dev/null
  printf '\npass2='
  printf '%q ' ffmpeg -hide_banner -loglevel error -n -i "$MASTER" -map 0:v:0 -an \
    -vf "scale=$WIDTH:$HEIGHT:flags=lanczos" -c:v libx264 -preset slow \
    -b:v "${TARGET_KBPS}k" -pass 2 -passlogfile "$PASSLOG" -profile:v high \
    -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 \
    -colorspace bt709 -r 25 -movflags +faststart "$OUTPUT"
  printf '\n'
} >"$ENCODING_LOG"

ffmpeg -hide_banner -loglevel error -y -i "$MASTER" -map 0:v:0 -an \
  -vf "scale=$WIDTH:$HEIGHT:flags=lanczos" -c:v libx264 -preset slow \
  -b:v "${TARGET_KBPS}k" -pass 1 -passlogfile "$PASSLOG" -profile:v high \
  -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 \
  -colorspace bt709 -r 25 -f mp4 /dev/null
ffmpeg -hide_banner -loglevel error -n -i "$MASTER" -map 0:v:0 -an \
  -vf "scale=$WIDTH:$HEIGHT:flags=lanczos" -c:v libx264 -preset slow \
  -b:v "${TARGET_KBPS}k" -pass 2 -passlogfile "$PASSLOG" -profile:v high \
  -pix_fmt yuv420p -color_range tv -color_primaries bt709 -color_trc bt709 \
  -colorspace bt709 -r 25 -movflags +faststart "$OUTPUT"

ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames,nb_read_frames,color_range,color_space,color_transfer,color_primaries \
  -show_entries format=duration,size -of json "$OUTPUT" >"$PROBE"
ffmpeg -hide_banner -loglevel error -xerror -i "$OUTPUT" -map 0:v:0 -f null -
ffmpeg -hide_banner -i "$MASTER" -i "$OUTPUT" \
  -lavfi "[0:v]scale=$WIDTH:$HEIGHT:flags=lanczos[reference];[reference][1:v]ssim" \
  -f null - 2>"$SSIM_LOG"
ffmpeg -hide_banner -loglevel error -y -i "$OUTPUT" \
  -vf "fps=1/20,scale=$WIDTH:$HEIGHT:flags=lanczos,tile=3x1" \
  -frames:v 1 "$CONTACT_SHEET"

MASTER_HASH_AFTER=$(sha256sum "$MASTER" | cut -d' ' -f1)
STANDARD_HASH_AFTER=$(sha256sum "$STANDARD_TRANSFER" | cut -d' ' -f1)
OUTPUT_HASH=$(sha256sum "$OUTPUT" | cut -d' ' -f1)
printf '%s  %s\n%s  %s\n%s  %s\n' \
  "$MASTER_HASH_AFTER" "$(basename "$MASTER")" \
  "$STANDARD_HASH_AFTER" "$(basename "$STANDARD_TRANSFER")" \
  "$OUTPUT_HASH" "$(basename "$OUTPUT")" >"$SHA256"

python3 - \
  "$MASTER" "$STANDARD_TRANSFER" "$OUTPUT" "$PROBE" "$SSIM_LOG" \
  "$VALIDATION" "$MASTER_HASH_BEFORE" "$MASTER_HASH_AFTER" \
  "$STANDARD_HASH_BEFORE" "$STANDARD_HASH_AFTER" "$OUTPUT_HASH" \
  "$TARGET_KBPS" "$MAX_BYTES" "$MINIMUM_SSIM" <<'PY'
import json
from pathlib import Path
import re
import subprocess
import sys

(
    master_path,
    standard_path,
    output_path,
    probe_path,
    ssim_log_path,
    validation_path,
) = map(Path, sys.argv[1:7])
(
    master_hash_before,
    master_hash_after,
    standard_hash_before,
    standard_hash_after,
    output_hash,
) = sys.argv[7:12]
target_kbps = int(sys.argv[12])
max_bytes = int(sys.argv[13])
minimum_ssim = float(sys.argv[14])

def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
            "-show_entries",
            "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames,nb_read_frames,color_range,color_space,color_transfer,color_primaries",
            "-show_entries", "format=duration,size", "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    stream = payload["streams"][0]
    fmt = payload["format"]
    return {
        "codec_name": stream.get("codec_name"),
        "profile": stream.get("profile"),
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "pixel_format": stream.get("pix_fmt"),
        "frame_rate": stream.get("r_frame_rate"),
        "frame_count": int(stream.get("nb_read_frames") or stream.get("nb_frames") or 0),
        "duration_seconds": float(fmt.get("duration", 0.0)),
        "size_bytes": int(fmt.get("size", path.stat().st_size)),
        "color_range": stream.get("color_range"),
        "color_space": stream.get("color_space"),
        "color_transfer": stream.get("color_transfer"),
        "color_primaries": stream.get("color_primaries"),
    }

master = probe(master_path)
candidate = json.loads(probe_path.read_text(encoding="utf-8"))
stream = candidate["streams"][0]
fmt = candidate["format"]
candidate_probe = {
    "codec_name": stream.get("codec_name"),
    "profile": stream.get("profile"),
    "width": int(stream.get("width", 0)),
    "height": int(stream.get("height", 0)),
    "pixel_format": stream.get("pix_fmt"),
    "frame_rate": stream.get("r_frame_rate"),
    "frame_count": int(stream.get("nb_read_frames") or stream.get("nb_frames") or 0),
    "duration_seconds": float(fmt.get("duration", 0.0)),
    "size_bytes": int(fmt.get("size", output_path.stat().st_size)),
    "color_range": stream.get("color_range"),
    "color_space": stream.get("color_space"),
    "color_transfer": stream.get("color_transfer"),
    "color_primaries": stream.get("color_primaries"),
}
matches = re.findall(r"All:([0-9.]+)", ssim_log_path.read_text(encoding="utf-8"))
if not matches:
    raise SystemExit("SSIM log does not contain an All score")
ssim = float(matches[-1])
checks = {
    "strictly_below_10000000_bytes": candidate_probe["size_bytes"] < max_bytes,
    "full_decode_succeeded": True,
    "frame_count_matches_master": candidate_probe["frame_count"] == master["frame_count"],
    "duration_matches_master": abs(candidate_probe["duration_seconds"] - master["duration_seconds"]) <= 1.0 / 25.0,
    "resolution_is_labeled_1280x360_delivery": [candidate_probe["width"], candidate_probe["height"]] == [1280, 360],
    "frame_rate_matches_master": candidate_probe["frame_rate"] == master["frame_rate"] == "25/1",
    "h264_high_yuv420p_bt709": candidate_probe["codec_name"] == "h264"
        and candidate_probe["profile"] == "High"
        and candidate_probe["pixel_format"] == "yuv420p"
        and candidate_probe["color_space"] == "bt709"
        and candidate_probe["color_transfer"] == "bt709"
        and candidate_probe["color_primaries"] == "bt709",
    "ssim_at_least_minimum": ssim >= minimum_ssim,
    "master_hash_unchanged": master_hash_before == master_hash_after,
    "existing_transfer_hash_unchanged": standard_hash_before == standard_hash_after,
}
passed = all(checks.values())
payload = {
    "schema_version": 1,
    "artifact": output_path.name,
    "purpose": "Full-duration directly playable review delivery copy strictly below 10000000 bytes; the 4K master and standard transfer remain immutable.",
    "source": master_path.name,
    "resolution_policy": "Explicitly labeled 1280x360 delivery copy preserving the 32:9 dual-panel order; the 3840x1080 master is the visual authority.",
    "target_video_bitrate_kbps": target_kbps,
    "probe": candidate_probe,
    "quality": {"ssim_against_same_resolution_lanczos_reference": ssim, "minimum_ssim": minimum_ssim},
    "sha256": {
        "master": master_hash_after,
        "existing_transfer": standard_hash_after,
        "under_10mb_transfer": output_hash,
    },
    "checks": checks,
    "manual_review": "pending contact-sheet and direct-video inspection",
    "status": "AUTOMATED_PASS_MANUAL_REVIEW_PENDING" if passed else "FAIL",
    "claim_boundary": "Delivery validation only; this does not add navigation, AC54, AC55, formal-candidate, non-flat, training, or real-robot evidence.",
}
validation_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if not passed:
    raise SystemExit("under-10MB transfer validation failed")
PY

printf 'under-10MB transfer: %s\n' "$OUTPUT"
printf 'validation: %s\n' "$VALIDATION"
