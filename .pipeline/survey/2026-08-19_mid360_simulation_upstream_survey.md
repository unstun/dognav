# MID-360 Simulation Upstream Survey

> Date: 2026-08-19
> Stage: experiment + analysis
> Status: surveyed, primary source acquired at a pinned commit, and the opt-in
> Isaac integration passed new sensor and Office plus SCAN preflight checks;
> the original upstream Gazebo demo has not been reproduced.

## Question and criteria

The Office demo currently labels a uniform 16-channel, 2-degree ray grid with a
12 m maximum range as a "MID-360-like geometric ray model". This survey checks
whether an open-source implementation provides a better source for:

1. an angle-versus-time scan pattern rather than an invented fixed-line grid;
2. physical minimum and maximum range;
3. scan frequency and point count;
4. ROS point-cloud and timestamp behavior;
5. a license that permits deliberate reuse; and
6. a clear separation between sensor range, SLAM processing range, and local
   planner/map range.

## Inspected repositories

### 1. Livox-SDK/livox_laser_simulation — primary scan-pattern reference

- Canonical repository: https://github.com/Livox-SDK/livox_laser_simulation
- Default branch: `main`
- Pinned commit: `1cce1073633a062b92e30243a4c2920e45551bb5`
- License: MIT
- Upstream environment: Ubuntu 18.04, ROS Melodic, Gazebo 9.x
- Original smoke command: `roslaunch livox_laser_simulation livox_simulation.launch`
- Relevant pinned files:
  - `scan_mode/mid360.csv`: https://github.com/Livox-SDK/livox_laser_simulation/blob/1cce1073633a062b92e30243a4c2920e45551bb5/scan_mode/mid360.csv
  - `urdf/livox_mid360.xacro`: https://github.com/Livox-SDK/livox_laser_simulation/blob/1cce1073633a062b92e30243a4c2920e45551bb5/urdf/livox_mid360.xacro

The pinned `mid360.csv` contains 800,000 time-ordered samples. Direct inspection
gives azimuth `0.000376--360.0 deg` and zenith `37.836--97.2123 deg`, equivalent
to elevation about `-7.2123--52.164 deg`. This is consistent with the physical
MID-360 field of view and is materially different from a fixed 16-channel grid.

The xacro uses a 10 Hz update rate, 0.002 m range resolution, 0.01 m Gaussian
range-noise standard deviation, and `mid360.csv`. Its `samples=24000` and
`laser_max_range=200.0` are simulator defaults, not evidence that the physical
MID-360 has a 200 m detection range. The repository README itself describes
these parameters as display/example parameters.

### 2. fratopa/Mid360_simulation_plugin — useful independent implementation, no reusable license

- Canonical repository: https://github.com/fratopa/Mid360_simulation_plugin
- Default branch: `main`
- Pinned commit: `aae8ee3a0f16e2f21c480da9b858dd702a2cd13a`
- License: not declared; GitHub reports no license and `package.xml` contains
  `<license>TODO</license>`
- Upstream environment: Ubuntu 20.04, ROS Noetic, Gazebo 11
- Original smoke command: `roslaunch livox_laser_simulation test_pattern.launch`
- Relevant pinned model:
  https://github.com/fratopa/Mid360_simulation_plugin/blob/aae8ee3a0f16e2f21c480da9b858dd702a2cd13a/livox_laser_simulation/models/sensors_only/model.sdf

The model uses minimum range 0.1 m, maximum range 40 m, 10 Hz, 20,000 samples
per scan, and an 800,000-row MID-360 angle-time CSV. It also claims to correct
motion distortion present in the original plugin. These settings support the
40 m and 10 Hz choice, but the missing license prevents copying its source or
CSV into this project without separate permission or provenance review.

### 3. hku-mars/MARSIM — planner-oriented approximation, not a physical contract

- Canonical repository: https://github.com/hku-mars/MARSIM
- Default branch: `ubuntu20`
- Pinned commit: `2a287bb196eb35375636c3aa6ac6c6be45ebb1f3`
- License: GPL-2.0
- Upstream environment: ROS 1 branches for Ubuntu 16.04--20.04; a separate
  ROS 2 branch is advertised
- Original MID-360 smoke command:
  `roslaunch test_interface single_drone_mid360_dynobs.launch`
- Relevant pinned launch:
  https://github.com/hku-mars/MARSIM/blob/2a287bb196eb35375636c3aa6ac6c6be45ebb1f3/test_interface/launch/single_drone.xml

MARSIM's MID-360 mode uses a 15 m sensing horizon, 10 Hz, 360-degree yaw,
90-degree vertical FOV, 1 m minimum ray length, and a `minicf` pattern. Those
values are useful for a lightweight local planning benchmark, but they do not
match the physical MID-360 range, blind zone, or vertical FOV. MARSIM therefore
supports keeping a short planner horizon, not replacing the sensor model.

### 4. hku-mars/FAST_LIO — SLAM front-end reference, not a sensor simulator

- Canonical repository: https://github.com/hku-mars/FAST_LIO
- Default branch: `main`
- Pinned commit: `7cc4175de6f8ba2edf34bab02a42195b141027e9`
- License: GPL-2.0
- Relevant pinned configuration:
  https://github.com/hku-mars/FAST_LIO/blob/7cc4175de6f8ba2edf34bab02a42195b141027e9/config/mid360.yaml

The MID-360 configuration uses `scan_line=4`, `blind=0.5`,
`fov_degree=360`, and `det_range=100.0`. Here `blind` is a preprocessing filter
and `det_range` is a mapping/estimation range. Neither value should be copied
into the Isaac ray caster as the physical MID-360 minimum or maximum range.

### 5. Livox-SDK/livox_ros_driver2 — official ROS transport reference

- Canonical repository: https://github.com/Livox-SDK/livox_ros_driver2
- Default branch: `master`
- Pinned commit: `4a1def929e5b59c7a8122d19fce6efba581ce9f7`
- License: MIT for the listed driver source, with bundled dependency notices
- Relevant pinned configuration:
  https://github.com/Livox-SDK/livox_ros_driver2/blob/4a1def929e5b59c7a8122d19fce6efba581ce9f7/config/MID360_config.json

The driver configuration establishes MID-360 transport, point format,
`pattern_mode`, and explicit extrinsics. It does not define a synthetic ray
range or scan grid, so it is a ROS message/timestamp reference rather than a
simulation-geometry source.

## Cross-source decision

No inspected repository provides one trustworthy all-in-one configuration.
The supported split is:

| Contract | Source to follow | Value or behavior |
|---|---|---|
| angle-time pattern | Livox MIT simulator | pinned `mid360.csv`, time-varying and non-repetitive |
| physical FOV | Livox pattern and product specification | horizontal 360 deg; elevation about -7 to 52 deg |
| blind zone | Livox product specification and MID-360 plugins | 0.1 m |
| conservative physical range | Livox product specification and fratopa model | 40 m at 10% reflectivity |
| scan rate | Livox simulator, driver behavior, and other MID-360 simulators | 10 Hz |
| nominal output density | Livox product specification | 200,000 first-return points/s, about 20,000 points per 0.1 s scan |
| ROS representation | `livox_ros_driver2` | preserve sensor timestamp, ordered per-point time where available, and explicit extrinsics |
| SLAM processing range | FAST_LIO configuration | separate mapping parameter; do not call 100 m the sensor range |
| local planning horizon | MARSIM/SCAN configuration | may remain much shorter than 40 m for compute and local replanning |

The official Livox product specification used to resolve conflicting simulator
defaults is https://www.livoxtech.com/cn/mid-360/specs: 0.1 m blind zone,
40 m at 10% reflectivity, 70 m at 80% reflectivity, 360 by 59 degree FOV,
200,000 first-return points/s, and a typical 10 Hz frame rate.

## Recommendation for machine-dog-nav

Use the MIT-licensed Livox `mid360.csv` as the primary upstream reference for a
new opt-in Isaac MID-360 pattern. Pair it with the conservative 40 m physical
cap and 0.1 m blind zone from the official hardware specification. Group the
time-ordered pattern into 0.1 s scans and preserve the sample timestamp; do not
continue the current uniform 16-channel approximation under a MID-360 label.

Keep SCAN's local occupancy/planning window independently bounded. A 40 m raw
sensor does not require displaying or inflating a 40 m local collision map.
Do not copy the official Gazebo example's 200 m maximum, MARSIM's 15 m horizon
or 90-degree vertical FOV, or FAST_LIO's 100 m `det_range` into the physical
sensor contract.

The pinned MIT Livox repository is now acquired under
`references/upstream/2026-08-19_mid360_simulation/source/` with its clean commit,
license, tree digest, and selected-file hashes recorded in
`repository_manifest.yaml`. The original Gazebo launch has not been reproduced.
The new Isaac integration passed `mid360_sensor_runtime_smoke03` and the fresh
five-second `office_crowd_mid360_preflight01`: both emitted 20,000 rays per
0.1-second scan from the pinned pattern, while the Office run recorded returns
to about 39.883 m and nonempty native SCAN occupancy. This establishes the
source-backed geometric sensor and short integration boundary only. A complete
Office run and human AC55 judgment remain pending, and any formal run must use a
new candidate while preserving candidate38/39 and every existing preflight.
