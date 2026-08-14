#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID CAPTURE_VIDEO TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ID=$1
CAPTURE_VIDEO=$2
TELEMETRY_PORT=$3
COMMAND_PORT=$4
RUN_ROOT=/home/sun/machine-dog-nav-runs/2026-08-14_forest_lite3_v12_preview
RUNTIME=$RUN_ROOT/source/locomotion_v12/runtime_20260718_recovered
CHECKPOINT=$RUN_ROOT/source/locomotion_v12/checkpoint/model_149999.pt
SENSOR_RIG=$RUN_ROOT/source/sensor_rig
FOREST_GEN=$RUN_ROOT/source/forest_gen
STRIPE_KIT=$RUN_ROOT/source/STRIPE-kit
BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge
OUTPUT_DIR=$RUN_ROOT/results/$RUN_ID
LOG_DIR=$RUN_ROOT/logs/$RUN_ID

if [[ ! $RUN_ID =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "run id must contain only lowercase letters, digits, underscore, or dash" >&2
  exit 64
fi
if [[ $CAPTURE_VIDEO != 0 && $CAPTURE_VIDEO != 1 ]]; then
  echo "CAPTURE_VIDEO must be 0 or 1" >&2
  exit 64
fi
for port in "$TELEMETRY_PORT" "$COMMAND_PORT"; do
  if [[ ! $port =~ ^[0-9]+$ ]] || (( port < 1024 || port > 65535 )); then
    echo "ports must be integers within [1024, 65535]" >&2
    exit 64
  fi
done
if [[ $TELEMETRY_PORT == "$COMMAND_PORT" ]]; then
  echo "telemetry and command ports must differ" >&2
  exit 64
fi

ISAAC_URDF=$SENSOR_RIG/urdf/lite3_pro_sensor_rig_real_with_interface_isaac.urdf
CANONICAL_URDF=$SENSOR_RIG/urdf/lite3_pro_sensor_rig_real_with_interface.urdf
FOREST_MODELS=$FOREST_GEN/models
for required in \
  "$CHECKPOINT" \
  "$RUNTIME/source/rsl_rl/rsl_rl/env/vec_env.py" \
  "$RUNTIME/source/robot_lab/robot_lab/tasks/lite3/env_cfg.py" \
  "$ISAAC_URDF" \
  "$CANONICAL_URDF" \
  "$FOREST_GEN/forest_gen/scene.py" \
  "$STRIPE_KIT/stripe_kit/terrain.py" \
  "$FOREST_MODELS/Pine_1.usdz" \
  "$BRIDGE/lite3_sim_bridge/run_isaac_v12_fallback.py"; do
  if [[ ! -f $required ]]; then
    echo "required input missing: $required" >&2
    exit 66
  fi
done
if [[ -e $OUTPUT_DIR || -e $LOG_DIR ]]; then
  echo "run output already exists; refusing to overwrite: $RUN_ID" >&2
  exit 73
fi

FOREST_COMMIT=$(git -C "$FOREST_GEN" rev-parse HEAD)
STRIPE_COMMIT=$(git -C "$STRIPE_KIT" rev-parse HEAD)
if [[ $FOREST_COMMIT != a75fb28c7b896e2a67e2d889b804732d33c56e0c ]]; then
  echo "forest_gen commit mismatch: $FOREST_COMMIT" >&2
  exit 65
fi
if [[ $STRIPE_COMMIT != ce97eed40d9fc4927c4856eda6a17204d01087db ]]; then
  echo "STRIPE-kit commit mismatch: $STRIPE_COMMIT" >&2
  exit 65
fi

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"
sha256sum \
  "$0" \
  "$CHECKPOINT" \
  "$ISAAC_URDF" \
  "$CANONICAL_URDF" \
  "$BRIDGE/lite3_sim_bridge/run_isaac_lite3.py" \
  "$BRIDGE/lite3_sim_bridge/run_isaac_v12_fallback.py" \
  "$BRIDGE/lite3_sim_bridge/isaac_adapter_core.py" \
  "$FOREST_GEN/forest_gen/scene.py" \
  "$STRIPE_KIT/stripe_kit/terrain.py" \
  >"$OUTPUT_DIR/input_sha256.txt"
{
  printf 'forest_gen=%s\n' "$FOREST_COMMIT"
  printf 'stripe_kit=%s\n' "$STRIPE_COMMIT"
  git -C "$FOREST_GEN" status --porcelain --untracked-files=no | sed 's/^/forest_gen_status=/'
  git -C "$STRIPE_KIT" status --porcelain --untracked-files=no | sed 's/^/stripe_kit_status=/'
} >"$OUTPUT_DIR/upstream_git_state.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total \
  --format=csv,noheader >"$OUTPUT_DIR/gpu_identity.txt"

VIDEO_ARGS=()
if [[ $CAPTURE_VIDEO == 1 ]]; then
  VIDEO_ARGS=(
    --video-path "$OUTPUT_DIR/forest_lite3_v12.mp4"
    --video-fps 17
    --video-frame-stride 3
  )
fi

source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH="$BRIDGE:$RUNTIME/source/rsl_rl:$RUNTIME/source/robot_lab:$FOREST_GEN:$STRIPE_KIT${PYTHONPATH:+:$PYTHONPATH}"

cd "$RUNTIME"
set +e
python -u -m lite3_sim_bridge.run_isaac_v12_fallback \
  --mode qualification \
  --course forest_gen \
  --output-dir "$OUTPUT_DIR/isaac" \
  --checkpoint "$CHECKPOINT" \
  --vendored-rsl-rl "$RUNTIME/source/rsl_rl" \
  --robot-asset "$ISAAC_URDF" \
  --canonical-robot-asset "$CANONICAL_URDF" \
  --source-commit 8c3fdffa84b85be0704a10ea5b2533817d543822 \
  --forest-gen-root "$FOREST_GEN" \
  --stripe-kit-root "$STRIPE_KIT" \
  --forest-asset-path "$FOREST_MODELS" \
  --forest-size 32 \
  --forest-margin 10 \
  --forest-seed 14 \
  --telemetry-port "$TELEMETRY_PORT" \
  --command-port "$COMMAND_PORT" \
  --max-step-wall-seconds 12.0 \
  "${VIDEO_ARGS[@]}" \
  >"$LOG_DIR/isaac.log" 2>&1
RUN_CODE=$?
set -e
REPORT=$OUTPUT_DIR/isaac/qualification_report.json
if [[ ! -f $REPORT ]]; then
  echo "missing core qualification report; overriding launcher exit with 90" \
    >>"$LOG_DIR/isaac.log"
  RUN_CODE=90
elif [[ $(jq -r '.status' "$REPORT") != PASS ]]; then
  echo "core qualification report is not PASS; overriding launcher exit with 91" \
    >>"$LOG_DIR/isaac.log"
  RUN_CODE=91
fi
printf '%s\n' "$RUN_CODE" >"$LOG_DIR/isaac.exit"

find "$OUTPUT_DIR" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum \
  >"$OUTPUT_DIR/output_sha256.txt"
printf 'isaac=%s\n' "$RUN_CODE"
exit "$RUN_CODE"
