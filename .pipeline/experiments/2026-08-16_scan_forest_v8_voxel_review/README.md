# Native SCAN Voxel Review

This auxiliary review records SCAN's native raw and inflated occupancy topics
during the official-human immediate-walk scenario. It does not reconstruct
voxels from Isaac scene truth.

Required source topics:

- `/grid_map/occupancy` — raw occupied voxels;
- `/grid_map/occupancy_inflate` — collision-inflated voxels used by planning;
- `/grid_map/sliding_map_bbox` — current local map boundary;
- `/quad_0/body_pose` — simulator-stamped physical Lite3 pose;
- `/planning/bspline` — active SCAN trajectory.

The headless Foxy capture writes timestamped native PointCloud2 snapshots. A
deterministic postprocessor renders their original XYZ coordinates in a true
three-axis perspective view with a 180-degree camera orbit and 1:1 vertical
scale. Raw and inflated voxel centres, the 3D SCAN B-spline, and the physical
Lite3 trace share the same coordinate frame. A small XY inset is retained only
for planning correlation; it is not presented as the voxel view. The renderer
may deterministically subsample points for display performance, but hashes and
point counts always cover the complete captured snapshots.

The earlier top-down plus oblique-projection artifact is retained only as a
rejected presentation prototype. It must not be described as a 3D voxel video.
The selected output names are `voxel_3d_review.mp4` and
`isaac_voxel_3d_side_by_side.mp4`. Raw rosbag, snapshot metadata, point counts,
hashes, and source videos remain beside the derived artifact. This trial is
human-review evidence only and cannot modify the frozen V8 R2 acceptance result
or its upstream-reproduction label.

## Results

The first presentation prototype rendered a top-down panel beside an oblique
projection. Dr Sun correctly rejected it as not being a true 3-D voxel view.
Those artifacts remain negative presentation evidence only.

The first long true-3-D attempt at pedestrian start `(-3.6, 2.3) m` reached the
route endpoint and parked briefly, so its continuous-crossing gate failed. A
shorter same-route attempt then produced a real collision at simulator time
`2.37 s`: minimum synchronized surface clearance `-0.130 m` and maximum
non-foot contact `2703.57 N`. Both failures are preserved and not offered for
review.

Moving only the pedestrian start forward to `(-3.6, 3.0) m` retained the same
straight endpoint, `0.8 m/s` speed, run-start trigger, official human,
sensor path, SCAN algorithm, V12 checkpoint, and safety thresholds. Two
same-input short preflights passed with `0.593 m` and `0.673 m` minimum
robot-human surface clearance, zero contact, LiDAR detection, active-path
intrusion, and later geometrically distinct SCAN plans.

Two same-input 22-second wall-clock review runs then passed. Both rendered
`15.2 s`, 1280 x 720 H.264 voxel videos with 152 frames and continuous
constant-speed walking:

- `v8_official_voxel_3d_review02a`: `0.704 m` minimum clearance, zero contact,
  SCAN response `0.50 s`, 117 LiDAR detections, 466 raw occupancy messages and
  427 inflated occupancy messages;
- `v8_official_voxel_3d_review02b`: `0.704 m` minimum clearance, zero contact,
  SCAN response `0.20 s`, 132 LiDAR detections, and the same normalized
  effective input as review 02a.

The selected voxel-only SHA-256 values are
`397d69a114a6792e99f3fa9389a3c1e6c7676fe2e001e4725f2d7f32b0c62e1a`
and
`cb6a57237174883927c96f8c363e18a1f2bdff8bc6804a1f845e1112cbf04dc3`.
The selected run's complete rosbag and 71 native XYZ snapshot files are also
copied locally in the lossless `native_voxel_sources.tar.zst` archive. Its
SHA-256 passes locally, `zstd -t` succeeds, and the archive expands to
778,086,400 bytes. Automated evidence is ready, but AC45 remains open until Dr
Sun watches and accepts the voxel-only and synchronized Isaac/voxel videos.
