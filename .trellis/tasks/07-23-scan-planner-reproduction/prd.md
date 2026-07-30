# Reproduce SCAN-Planner Upstream

## Goal

Determine whether the selected SCAN-Planner revision can produce a traceable
closed-loop navigation result in its original upstream environment, and record
which parts of a complete quadruped navigation stack are present or absent.

The result should support a later human decision about whether SCAN-Planner is
worth adapting to ROS 2 and Lite3. It must not prematurely integrate upstream
source into project implementation paths.

## Background

- The selected canonical repository is
  `https://github.com/wuyi2121/SCAN-Planner`.
- The selected upstream revision is the default `main` commit
  `529f0ba43b7e79e6fff85a5777c786237f0f8f33` from 2026-07-16.
- The root repository is Apache-2.0 licensed. Individual ROS package manifests
  still contain incomplete metadata such as `<license>TODO</license>`.
- The upstream documented environment is Ubuntu 20.04 with ROS Noetic and a
  Catkin build. The documented quick start uses `rviz.launch` and `run.launch`.
- The current local host is Apple Silicon macOS 26.5.2. ROS Noetic is not
  installed. Docker CLI exists, but no Docker daemon was running when checked.
- The current physical Lite3 configuration has only a depth camera. Dr Sun
  wants to determine whether a public, printable Lite3-to-MID360 mounting model
  exists before considering a 3D LiDAR addition.
- The official Lite3 comparison manual identifies the depth-camera-only
  configuration as Lite3 Pro. Its payload interface is shared with the LiDAR
  version: four M3 threaded holes on a 74 mm by 94 mm rectangular pattern. The
  Pro payload allowance is 4 kg.
- Public DEEP Robotics user manuals contain actual dimensioned top-view
  interface drawings. The current Pro manual shows `4 x M3` threaded holes on
  a 74 mm by 94 mm rectangular centre pattern. The AI manual shows `6 x M3`
  plus `2 x M4` and provides the associated chain dimensions; the earlier
  combined manual explicitly maps that pattern to Venture and the 74 mm by
  94 mm pattern to Pro/LiDAR. The inspected PDFs and high-resolution page
  renders are archived under
  `references/upstream/2026-07-24_lite3-design-drawings/`.
- The official Motion Development Manual adds dimensioned body and leg
  drawings: 548 mm body length, 370 mm body width, 74/44 mm top/bottom offsets
  from the body origin, 124 mm left-right hip-centre spacing, 349 mm
  front-rear hip-centre spacing, 328 mm leg-plane spacing, 102 mm lateral leg
  offset, 200 mm upper leg, 210 mm lower leg, and 20 mm foot radius.
- These manual figures are design-reference drawings, not release-ready
  manufacturing drawings. They do not specify thread engagement depth,
  tolerances, materials, wall thickness, surface finish, or a complete datum
  scheme. Physical hole spacing and usable thread depth must therefore be
  measured before an adapter is fabricated.
- Livox publishes an official Mid-360 STEP model and FOV STEP model. The sensor
  is approximately 65 mm by 65 mm by 60 mm and 265 g, with four bottom M3
  mounting holes 5 mm deep.
- Mid-360 does not accept a normal RJ-45 cable at the sensor. It uses a
  12-pin M12 A-coded aviation connector carrying power, Ethernet, and optional
  synchronization signals. Livox's separately sold 1-to-3 splitter breaks this
  out into bare DC power leads, RJ-45 Ethernet, and a function lead; Livox
  classifies that splitter as suitable for testing/debugging and recommends a
  customized cable and connectors for higher-reliability deployments.
- Deep Robotics' Lite3 FAST-LIVO2 example shows the same breakout topology with
  its power branch terminated as XT30 and explicitly connects that XT30 to the
  Lite3 24 V XT30 port. Therefore a bench setup can start from the official
  Livox splitter plus a correctly wired robot-side power termination, while a
  moving outdoor Lite3 installation should use a reviewed, strain-relieved
  harness. The actual Lite3 port polarity and available power must be verified
  on the physical robot before energizing the LiDAR.
- A verified printable D435i-plus-Mid-360 sensor bracket is publicly available
  at `https://makerworld.com/en/models/1838891` under CC BY 4.0. The listing
  includes a tested print profile, a real assembled photograph, and the
  editable `D435i和MID360支架.sldprt` source. Its robot-side pattern is four M3
  holes on 45 mm by 80 mm centres, so it does not bolt directly to Lite3 Pro's
  74 mm by 94 mm interface.
- Deep Robotics Lab publishes five downloadable STEP solids for its
  Lite3-Venture FAST-LIVO2 hardware extension at
  `https://github.com/DeepRoboticsLab/fast-livo2-deep-robotics`. This is the
  closest Lite3-specific real-robot reference inspected, but the files are
  explicitly named for Lite3 Venture, not Lite3 Pro, and the external Drive
  folder does not state a separate hardware license.
- A current official-organization tree scan plus targeted searches of GitHub,
  GrabCAD, Sketchfab, Printables, Thingiverse, MakerWorld, Cults, CGTrader,
  3D ContentCentral, 3Dfindit, TraceParts, Onshape, and Zenodo found no public
  complete Lite3 engineering solid with the physical payload screw holes
  modeled. Direct searches on GrabCAD, 3D ContentCentral, 3Dfindit, and
  TraceParts explicitly returned no result; fuzzy MakerWorld and Thingiverse
  results were unrelated robots. This is a surveyed search result, not proof
  that no private or unindexed manufacturing CAD exists.
- The official Lite3 support-page download resolves to a product brochure, not
  CAD. The official product page states that a model is included in the
  developer package, but no public STEP, Parasolid, or native mechanical-CAD
  download was exposed on the inspected support and download pages.
- A third-party ROS 2 repository,
  `https://github.com/legubiao/quadruped_ros2_control`, commit
  `5434c5810d1a7fe223bcfd04550e9d3bfdd4b458`, contains a complete Lite3 visual
  model as a Blender-authored DAE. Direct geometry inspection and rendering
  showed a smooth top shell without the payload-interface holes. The mesh is
  non-watertight and split into many visual components, so it is not usable as
  manufacturing CAD even though it depicts a standing, complete robot.
- Tecmer advertises a Lite3-compatible docking product with M3/M4 top threads
  and claims openly provided STEP drawings at `https://tecmer.cn/`. The
  inspected public site and client bundle exposed no actual STEP file or
  download route, so this remains an unverified supplier lead rather than a
  found model.
- Two official Venture accessory files do contain real solid hole geometry.
  Fusion imported `1T21-J17A-lidar base.STEP` as one closed BRep solid and
  imported `1T21-BZ20-backload shell.STEP` as one closed BRep solid with 74
  faces, including 32 cylindrical faces. These are partial accessories rather
  than a complete robot body, and the inspection does not establish modeled
  helical threads or compatibility with the Lite3 Pro 74 mm by 94 mm interface.
- Deep Robotics Lab also publishes a BSD-3-Clause robot-model repository at
  `https://github.com/DeepRoboticsLab/deep_robotics_model`. Commit
  `18192847e16ab85c056440072fcc5844cef43856` contains a complete low-resolution
  Lite3 simulation model in URDF, MJCF, and USD forms with STL meshes. The
  repository README links a separate official high-resolution Lite3 URDF with
  DAE meshes. Both official variants contain the torso and four articulated
  legs but no LiDAR or depth-camera link. No official public full manufacturing
  CAD assembly of the commercial Lite3 LIDAR configuration was found.
- The high-resolution torso mesh visibly includes four body-shell fastener
  heads at approximately `(x, y)=(+/-102.5, +/-72.5)` mm, a 205 mm by 145 mm
  pattern. They are visual surface details in a non-watertight DAE mesh, not
  open or parametric threaded holes. The model does not contain the verified
  Lite3 Pro four-M3 74 mm by 94 mm payload-interface pattern or URDF mounting
  metadata, so these visible fasteners must not be used as payload-bracket
  dimensions.
- Dr Sun clarified on 2026-07-24 that the required baseline artifact is the
  complete Lite3 robot model, not the J17A LiDAR base. The pinned low- and
  high-resolution official model sets are stored under
  `references/upstream/2026-07-24_deep-robotics-model/` and packaged as
  `Lite3-official-models-18192847.zip`. This model is suitable for visualization
  and simulation reference, but its mesh geometry is not evidence of mounting
  tolerances, thread specifications, or Lite3 Pro physical fit.
- For direct consumption outside a URDF-aware viewer, the official
  high-resolution URDF and DAE assets were reproducibly assembled into
  fixed-pose `Lite3-official-high-res-factory-stand-fusion-y-up.glb` and
  `Lite3-official-high-res-factory-stand-fusion-y-up.stl` files. The pose uses
  the sibling locomotion repository's registered factory stand-up handoff
  target, `(HipX=0, HipY=-0.653535, Knee=1.27109)` radians on each leg. The
  assembly was ground-aligned from the URDF foot collision spheres and rotated
  from the source URDF's Z-up frame into Fusion's Y-up modeling frame. All four
  foot-contact heights are 0 with zero spread. Fusion imported the STL as one
  mesh body and visually confirmed a horizontal body with four downward legs
  on the modeling ground. This is a reproducible fixed pose, not a live-robot
  standing test, articulated replacement URDF, or official manufacturing CAD
  release.
- The complete derivative can be edited, but it should not be used as the
  mechanical-authoring source: its STL is a single 1,179,234-triangle mesh, and
  the separate high-resolution `torso.dae` is a non-watertight visualization
  mesh. The proposed modification path is therefore to preserve all official
  assets unchanged, create a separate parametric Lite3 Pro top-interface or
  adapter solid using the nominal four-M3 74 mm by 94 mm pattern, register that
  solid to the torso reference, and export both a full-robot visual derivative
  and an editable STEP/Fusion mechanical derivative. Until the physical robot
  is measured, this would be a nominal design-reference model rather than a
  fit-validated printable part.
- The Drive package is not a five-part printable assembly kit. It contains five
  separate STEP parts and only three component drawings, with no assembly STEP,
  exploded view, bill of materials, or complete fastener list. The drawings
  specify machined and anodized 6061-T6 aluminium for both LiDAR base plates
  (`1T21-J17A` and `1T21-J20A`) and welded, powder-coated 45 steel for the LiDAR
  protector (`1CA5-S410`). The official video explicitly identifies the
  `AGX-orin-base` as a 3D-printed part; the `1T21-BZ20` backload-shell material
  remains undocumented.
- The confirmed mechanical hierarchy is two independent assemblies around the
  Venture backload shell: the `AGX-orin-base` attaches under the AGX Orin and
  then to the robot, while the sensor assembly uses `1T21-J17A` as the
  robot-side base, `1T21-J20A` as the 15-degree Mid-360 adapter, and
  `1CA5-S410` as the four-foot protective cage. The `1T21-J20A` drawing matches
  the Mid-360's official 48 mm by 36 mm four-M3 mounting pattern and also
  provides four M5 attachment positions matching the protector. The official
  video demonstrates mounting the already-assembled sensor unit to the Venture
  with four robot-side screws, but it does not demonstrate assembling those
  three sensor parts or publish all screw lengths.
- No public, license-complete, direct-fit Lite3 Pro 74 mm by 94 mm printable
  mount was found. The evidence-backed reuse path is therefore the CC BY
  sensor bracket plus a measured Pro-to-45-by-80 adapter, or a reviewed
  derivative of the Deep Robotics Venture STEP parts. A public Go2 mount is not
  a substitute because its robot-side geometry is incompatible and its
  `LICENSE` file is only a TODO placeholder.
- The earlier J17A direct-edit investigation remains a sensor-mount reference,
  not the required Lite3 robot model. No J17A modification should proceed until
  the intended use of the complete Lite3 model and the required dimensional
  accuracy are confirmed. If STEP editing is later approved, the downloaded
  upstream STEP must remain byte-for-byte preserved and all edits must operate
  on a clearly named working copy with a reproducible script.
- Relevant Reddit workflows and vendor documentation converge on treating an
  imported STEP as a base or direct-modeling solid: preserve the source, heal
  or fill obsolete holes, add new sketches/cuts/bosses, visually compare the
  derivative, and export a new STEP. Fusion 360 and Shapr3D offer a more
  approachable manual GUI on macOS; FreeCAD offers the stronger local,
  open-source, Python-automation path; Onshape offers browser-based direct
  editing but requires uploading the model. FreeCAD 1.1.2 and Autodesk Fusion
  with an Education license are now installed on the local Apple Silicon Mac.
  FreeCAD's command-line CAD kernel successfully validates and tessellates all
  three Venture sensor-assembly STEP solids. Accessibility-driven GUI
  interaction caused FreeCAD measurement crashes, and Fusion closed
  unexpectedly while importing the J20A STEP through GUI automation.
- On 2026-07-24, Autodesk Fusion's official local MCP imported the unchanged
  J17A STEP without GUI automation or a crash. Fusion recognized one closed
  BRep solid with a 153.735 mm by 115.000 mm by 27.061 mm bounding box. The
  unsaved Fusion document was used only for inspection; the source remained at
  SHA-256
  `52f7f991e904d815d78265a6f695124f2f4bb24131b3500e07f44355ebe39490`.
  The source record and screenshot are under
  `references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/` and
  `.trellis/tasks/07-23-scan-planner-reproduction/evidence/`, respectively.
  This validates the Mac visualization and API-inspection path, not Lite3 Pro
  fit, printable strength, or real-robot safety.
- Livox recommends a flat metal mounting plate at least 3 mm thick with at
  least 10,000 square millimetres exposed to air, plus at least 10 mm airflow
  clearance around the sensor. Therefore an all-plastic direct-contact print is
  not an evidence-backed final mount; a printed Lite3 adapter plus metal
  heat-spreading plate is the safer starting architecture.
- The repository contains the local occupancy map, dynamic A* search, B-spline
  optimization, replanning FSM, CPU/GPU local sensing, procedural/PCD maps,
  Go2 visualization assets, a closed-loop path follower, and a planar
  kinematic simulator.
- The closed-loop follower publishes `geometry_msgs/Twist` on `cmd_vel`, which
  is structurally compatible with the public Lite3 ROS bridge.
- The planner supports exactly two obstacle-sensing modes:
  - `lidar`: `sensor_msgs/PointCloud2` plus a time-consistent
    `nav_msgs/Odometry` sensor pose;
  - `depth`: `sensor_msgs/Image` depth (`16UC1` or `32FC1`) approximately
    synchronized with a `nav_msgs/Odometry` sensor pose, plus calibrated
    `fx`, `fy`, `cx`, and `cy`.
- Both sensing modes also require a continuous
  `nav_msgs/Odometry` body pose for the sliding map and trajectory follower.
  Raw IMU alone is insufficient.
- The documented real-world defaults use a MID360-like 3D LiDAR or RealSense
  D435, `/LIO/clouds_lidar`, `/LIO/odom_imu`, and `/LIO/odom_vehicle`.
  The depth defaults filter observations to approximately 0.3--3.0 m.
- A raw 2D `sensor_msgs/LaserScan` and an RGB-only camera are not accepted by
  the current mapper without an additional conversion or perception layer.
- The included Go2 simulation is not a physics-based locomotion reproduction:
  `go2_kinematic_sim` integrates commanded planar velocity, while
  `go2_gait_publisher` animates joint states for visualization.
- Real-world operation requires external LIO, sensor drivers, calibration, and
  a robot driver. Reference-path mode also expects an external upper-level
  route source. The repository contains no automated tests, release, CI
  workflow, or pretrained model requirement.

## Requirements

- The independently verifiable current Lite3 LiDAR V1.0.7 visual reconstruction
  is planned in child task `07-24-lite3-pro-parametric-model`. That child
  consumes the official model and drawing evidence archived here but does not
  wait for the ROS Noetic planner reproduction.
- R1. Keep the upstream repository as a read-only reference under the dated
  `references/upstream/` layout; do not copy unreviewed source into project
  implementation paths.
- R2. Record canonical URL, license, pinned commit, default branch, upstream
  commands, dependencies, assumptions, and status in a tracked repository
  manifest.
- R3. Prefer the original `main` ROS Noetic path for the first reproduction.
  Do not mix the unofficial `ros2-community` port into the same evidence run.
- R4. Use the CPU LiDAR sensing backend and navigation mode 1 for the minimum
  first run unless evidence found during setup requires a narrower smoke test.
- R5. Preserve raw build and runtime output locally. Record exact environment
  versions and every local workaround.
- R6. A closed-loop run must include a start state, a reachable goal, generated
  planning output, bounded `cmd_vel`, pose progress, and a final outcome.
- R7. Visual evidence should show the actual upstream runtime state, not only
  a README animation or static repository asset.
- R8. Keep evidence labels exact: inspection is `surveyed`; only a successful
  upstream run with saved evidence is `reproduced`.
- R9. Do not start model training, real-robot actuation, or Lite3 integration.
- R10. Preserve all unrelated user-owned untracked research files.
- R11. Record whether a trustworthy printable Lite3-to-MID360 mount exists,
  including source, license, file format, robot/sensor compatibility, and any
  unresolved mechanical or field-of-view constraints. Do not treat an
  unverified decorative model as a safe hardware mount.
- R12. Use the pinned official complete Lite3 model as the visualization and
  spatial-reference baseline. If later mechanical adaptation proceeds, preserve
  the original robot-model and Venture STEP files unchanged, apply only
  approved changes to working copies through a reproducible CAD script, and
  verify mounting dimensions against physical measurements or an official
  engineering drawing.

## Acceptance Criteria

- [ ] AC1. A dated upstream reference directory contains the pinned source,
  completed manifest, comparison/assessment, and raw log paths.
- [ ] AC2. The environment record names OS, architecture, ROS distribution,
  compiler/CMake/Catkin versions, and whether execution was local, container,
  or remote.
- [ ] AC3. The pinned source either builds successfully with the original
  Catkin command, or the report contains the exact terminal failure and a
  source-backed blocker classification.
- [ ] AC4. If build succeeds, the original upstream simulation launches using
  CPU LiDAR sensing without modifying project implementation code.
- [ ] AC5. If runtime launches, one reachable navigation goal is issued and
  the evidence records planner output, nonzero bounded `cmd_vel`, pose
  progression, and stop/final state.
- [ ] AC6. The final assessment explicitly separates planner completeness from
  missing SLAM, physical locomotion, hardware driver, and Lite3 integration.
- [ ] AC7. Any upstream modification is captured as a minimal patch inside the
  reference record and is not silently applied to project code.
- [ ] AC8. No claim exceeds the strongest saved evidence state.
- [ ] AC9. Any generated mechanical derivative is traceable to an unchanged
  upstream STEP, a reproducible edit script, and a dimension-change record; a
  successful CAD export alone is not claimed as physical fit or load
  validation.

## Out of Scope

- ROS 2 porting or repair of the community ROS 2 branch.
- Lite3 navigation-to-locomotion integration.
- Real Go2 or Lite3 actuation.
- Formal benchmark comparison, model training, or algorithm redesign.
- Treating the visualization gait animation as a physics or locomotion result.

## Open Question

- Should the required first outcome be the full original ROS Noetic visual
  closed loop (recommended), or is a headless build-and-launch smoke sufficient
  for this task?
- Confirm whether the immediate use of the complete Lite3 model is
  a nominal full-robot visualization/simulation derivative or a physically
  printable payload-interface part. The recommended direction is a two-layer
  result: a separate parametric mechanical interface placed on the unchanged
  full-robot visual model.
- Measure the physical Lite3 Pro four-thread positions before treating a
  generated STEP or print as fit-validated.
