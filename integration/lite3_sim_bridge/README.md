# Lite3 Simulation Bridge

This package owns the ROS-distribution-independent boundary between the ROS 2
Foxy SCAN planner and the Isaac Sim Lite3 runtime.

The transport uses two localhost-only TCP streams:

- telemetry: Isaac to Foxy (`SENSOR_FRAME_V1` and `STATUS_V1`);
- command: Foxy to Isaac (`CMD_VEL_V1`).

The wire envelope is network byte order and contains a magic value, protocol
version, message type, flags, header/payload lengths, sequence number,
monotonic timestamp, reserved field, and payload CRC32. Point samples are
packed as network-order `float32 x,y,z`. Pose quaternions use `(x,y,z,w)`.

The pure-Python protocol and command-state modules use only the standard
library and support Python 3.8, which is the Ubuntu 20.04 / ROS 2 Foxy baseline.
ROS and Isaac adapters import these modules rather than reimplementing the wire
contract.

This directory is project code. It is not part of the SCAN upstream snapshot.

The Foxy process runs `foxy_bridge_node`. The Isaac Sim 5.1 process has two
task-owned adapters:

- `run_isaac_lite3` evaluates the first V17 E3 locomotion candidate;
- `run_isaac_v12_fallback` runs the one allowed V12 `model_149999` fallback.

The V17 candidate was rejected by the fixed command-response gate. V12 passed
zero, forward, lateral, yaw, watchdog-zero, contact-support, and finite-policy
checks, and is the only adapter used by the accepted closed loop. Both adapters
use simulator-truth pose and an Isaac Lab multi-mesh ray-cast LiDAR; neither is
represented as real MID-360 or LIO data.

The formal fixed-course outcome and exact claim boundary are recorded in
`.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/REPORT.md`.
