# SCAN ROS 2 Community Port: Foxy Selection Record

## Decision

Use the six planner packages from commit
`d0b921c9b05a6d291d144d60882b2e0e88d2c0e0` as the source for a project-owned
ROS 2 Foxy compatibility port. Keep the downloaded source tree unchanged and
put all compatibility changes in the separate integration overlay.

## Included

| Package | Role in the accepted loop |
|---|---|
| `scan_planner_msgs` | B-spline and planner-display message definitions |
| `plan_env` | Point-cloud occupancy map and pose-aware sliding map |
| `path_searching` | Dynamic A-star search |
| `bspline_opt` | B-spline trajectory optimization |
| `traj_utils` | Trajectory primitives and visualization |
| `scan_planner` | Planner node, replanning FSM, closed-loop controller, config and launch |

`scan_planner` currently declares simulator-only runtime dependencies. The
Foxy overlay must remove those declarations and must install/launch only the
planner node and closed-loop controller required by the accepted architecture.

## Excluded

The whole `src/simulator/` tree is excluded from the Foxy runtime. In
particular, `go2_description` depends on Gazebo Fortress, `ros_gz_sim`,
`ros_gz_bridge`, and `gz_ros2_control`, while the default planner launch still
starts `go2_kinematic_sim`. Neither path supplies the accepted Lite3 policy and
PhysX causal chain.

The project also excludes the visualization-only gait publisher and the
kinematic/open-loop controller executables from the acceptance launch. Their
source may remain in the port for traceability only if the build can exclude
them deterministically; otherwise they will be omitted with a recorded patch.

## Compatibility Boundary

The upstream branch documents Ubuntu 22.04 and ROS 2 Humble. The target is an
isolated Ubuntu 20.04 / ROS 2 Foxy environment. A successful result will be
called a project Foxy port, never an upstream Foxy release or upstream
reproduction.

The first build should preserve all algorithmic source unchanged and test the
existing C++17/ament code against Foxy. Compatibility patches are introduced
only in response to an exact build or runtime failure and remain reviewable
against the immutable snapshot.

## Reproducible Port Diff

Run the task-owned generator from the repository root:

```bash
bash references/upstream/2026-08-13_scan-planner-ros2-community/generate_foxy_port_patch.sh
```

It compares the six selected package directories in the immutable snapshot
against `integration/scan_planner_foxy_ws/src/`, excludes generated Python
bytecode, and writes
`foxy_port.patch`. The generated patch includes Foxy compatibility changes,
the project-owned closed-loop controller, Lite3 safety configuration, tests,
and launch files. The separate `integration/lite3_sim_bridge/` package has no
upstream counterpart and is reviewed as task-owned integration source.

## Evidence State

`surveyed`: archive integrity, license, README, package manifests, CMake files,
launch files, and planner source structure were inspected. No ROS build or
runtime has yet passed at this record point.
