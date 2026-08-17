#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT" >&2
  exit 64
fi

RUN_ROOT=/home/sun/machine-dog-nav-runs/2026-08-17_office_l0_scan_crowd
V8_ROOT=/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human

export SCAN_RUN_ROOT=$RUN_ROOT
export SCAN_ENTRYPOINT=$0
export SCAN_FOXY_WORKSPACE=$V8_ROOT/foxy_ws
export SCAN_V12_RUNTIME=$V8_ROOT/source/locomotion_v12/runtime_20260718_recovered
export SCAN_CHECKPOINT=$V8_ROOT/source/locomotion_v12/checkpoint/model_149999.pt
export SCAN_BRIDGE=$RUN_ROOT/integration/lite3_sim_bridge
export SCAN_ACCEPTANCE_CONFIG=$RUN_ROOT/acceptance_thresholds_office_crowd.json
export SCAN_ROBOT_ASSET=$V8_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface_isaac.urdf
export SCAN_CANONICAL_ROBOT_ASSET=$V8_ROOT/source/sensor_rig/urdf/lite3_pro_sensor_rig_real_with_interface.urdf
export SCAN_COURSE=office_l0_crowd
export SCAN_PLANNER_CONFIG_REL=src/plan_manage/config/foxy_isaac_office_crowd_planner.yaml
export SCAN_CONTROLLER_CONFIG_REL=src/plan_manage/config/foxy_isaac_office_crowd_controller.yaml
export SCAN_OFFICE_USD_PATH=$RUN_ROOT/results/office_l0_physics_wrapper01.usda
export SCAN_OFFICE_USD_SHA256=5ac29c16ab94a2a2e6bbde8cd7f3907d1e602164604f998070669fa176d9de47
export SCAN_OFFICE_ROUTE_PATH=$RUN_ROOT/results/office_l0_route_preflight07.json
export SCAN_OFFICE_ROUTE_SHA256=6e0db6f6803483fba846a515225aa167aaf7182fe645db11a5da02518cccf368
export SCAN_OFFICE_START_X=-15.625
export SCAN_OFFICE_START_Y=13.125
export SCAN_OFFICE_GOAL_X=-8.375
export SCAN_OFFICE_GOAL_Y=-0.625
export SCAN_OFFICIAL_HUMAN_ANIMATION_MODE=continuous_walk
export SCAN_MAX_VX=0.50
export SCAN_VIDEO_FPS=12
export SCAN_VIDEO_FRAME_STRIDE=5

bash "$RUN_ROOT/run_remote_closed_loop.sh" "$@"
