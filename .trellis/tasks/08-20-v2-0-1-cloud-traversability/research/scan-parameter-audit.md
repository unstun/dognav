# SCAN Traversability Parameter Audit

## Sources and boundary

- Local Foxy port configuration:
  `integration/scan_planner_foxy_ws/src/plan_manage/config/foxy_isaac_office_crowd_planner.yaml`
- Local map inflation implementation:
  `integration/scan_planner_foxy_ws/src/plan_env/src/grid_map.cpp`
- Local goal/route height handling:
  `integration/scan_planner_foxy_ws/src/plan_manage/src/scan_replan_fsm.cpp`
- Official upstream parameter file, verified against `main` on 2026-08-20 and
  pinned to commit `348e8a590a50a5a6bbab8d8c6dcfd171f009be26`:
  <https://github.com/wuyi2121/SCAN-Planner/blob/348e8a590a50a5a6bbab8d8c6dcfd171f009be26/src/planner/plan_manage/launch/advanced_param.xml>
- Official paper, especially Sections III, IV-B, IV-C, and V-B:
  <https://arxiv.org/html/2606.19555v1>

This note audits geometric SCAN parameters. It does not establish Lite3 V12
locomotion feasibility values.

## Where the values come from

The official SCAN README states that the released defaults are tuned for
Unitree Go2 and must be adjusted for another robot platform. The values are not
all determined from a robot datasheet:

1. **Measured from the protected robot assembly:** cylinder radius/offset,
   nominal body-center height, upper body/sensor extent, and transforms.
2. **Qualified with the locomotion controller:** maximum step up/down, maximum
   slope up/down, tracking error, and safe speed. These depend on the policy,
   gait, terrain, and command speed, not only physical dimensions.
3. **Tuned from sensor/planner evidence:** grid resolution, terrain-fit cell
   size/support, occupancy probabilities, optimization clearance, and planning
   horizon. These depend on point density, map behavior, compute budget, and
   failure policy.

Available local Lite3 evidence includes:

- current-Pro brochure dimensions `610 x 370 x 450 mm`;
- an official high-resolution fixed-standing model derivative with overall
  bounds `596.837 x 425.463 x 372.658 mm` (the width includes the standing leg
  geometry and is not directly a SCAN body-cylinder diameter);
- a registered factory stand-up height target of `0.33 m`;
- V12 command-takeover qualification with minimum root height
  `0.3010728061 m`;
- the Office acceptance range `0.25--0.45 m`.

No durable record found in this audit derives the current Office values
`double_cylinder_radius=0.40`, `double_cylinder_offset=0.18`, and
`body_height=0.40` from a pinned Lite3 protected-assembly envelope plus V12
qualification. They must therefore be treated as provisional conservative
integration values until the derivation and tests are recorded.

For Lite3, the protected assembly must include the torso and navigation
hardware that can collide, especially the MID-360/sensor structure. It must not
blindly use the whole standing-leg bounding box, because SCAN's twin cylinders
model the protected body envelope while the locomotion controller owns leg
motion.

## Required calibration parameters

## First borrowed-parameter baseline decision

Dr Sun decided on 2026-08-20 to begin with the official upstream SCAN values
instead of waiting for a complete Lite3 calibration. The reference profile must
be named `upstream_go2_reference`, remain separate from the Office profile, and
carry the claim `borrowed upstream Go2 parameters; not Lite3-qualified`.

The official upstream parameter file provides these directly relevant values:

| Parameter | Official Go2-tuned value |
| --- | ---: |
| `grid_map.double_cylinder_radius` | `0.25 m` |
| `grid_map.double_cylinder_offset` | `0.18 m` |
| `grid_map.obstacles_inflation_z_up` | `0.10 m` |
| `grid_map.obstacles_inflation_z_down` | `0.10 m` |
| `grid_map.body_height` | `0.40 m` |
| `grid_map.resolution` | `0.05 m` |
| sliding map size | `10 x 10 x 5 m` |
| `grid_map.max_ray_length` | `5.0 m` |
| `manager.max_vel` | `0.75 m/s` |
| `manager.max_acc` | `0.5 m/s^2` |
| `manager.max_jerk` | `4.0 m/s^3` |
| `manager.planning_horizon` | `3.5 m` |
| `optimization.dist0` | `0.20 m` |

Upstream does not expose explicit `max_slope_up`, `max_slope_down`,
`max_step_down`, terrain-fit support, or unknown-terrain policy parameters.
Those must not be invented or presented as borrowed upstream values. The paper
only defines an implicit maximum traversable step concept through the vertical
body clearance and assumes a supplied 3D ground-following route.

Recommendation for the first probe: borrow the upstream collision geometry
only, keep the existing Lite3-qualified command ceiling `0.50 m/s` and Office
map/horizon frozen, and label the result as a controlled compatibility probe.
This isolates the geometric change and avoids simultaneously increasing speed
from `0.50` to `0.75 m/s`.

### 1. Robot body and collision envelope

| Meaning | Local parameter | Current Office value | Official upstream default | How it must be set |
| --- | --- | ---: | ---: | --- |
| Horizontal cylinder radius | `grid_map.double_cylinder_radius` | `0.40 m` | `0.25 m` | Half body/sensor width plus lateral sway and safety margin; verify against the pinned Lite3 assembly. |
| Front/rear cylinder offset | `grid_map.double_cylinder_offset` | `0.18 m` | `0.18 m` | Choose so the union of two cylinders covers body and mounted hardware over yaw. |
| Nominal body-center height | `grid_map.body_height` | `0.40 m` | `0.40 m` | Use the actual locomotion root/body center above local terrain, not an arbitrary waypoint height. |
| Obstacle inflation upward | `grid_map.obstacles_inflation_z_up` | `0.10 m` | `0.10 m` | This implements the body's lower clearance in the local map. Under the paper model, `d_step = body_center_height - z_up_inflation`. |
| Obstacle inflation downward | `grid_map.obstacles_inflation_z_down` | `0.40 m` | `0.10 m` | This covers the body's upper extent and mounted hardware when checking overhangs. Measure from body center to the highest protected point plus margin. |
| Rebound safety distance | `optimization.dist0` | `0.20 m` | `0.20 m` | Minimum optimization clearance after inflation; keep frozen initially, then verify in narrow-passage tests. |

The current nominal combination implies an implicit paper-style geometric step
height of approximately `0.40 - 0.10 = 0.30 m`, but this is not yet a qualified
Lite3 V12 limit. It is meaningful only if the SCAN route Z really represents a
body center approximately `0.40 m` above the local terrain.

### 2. Route height and terrain envelope

| Meaning | Current setting | Required contract |
| --- | --- | --- |
| Preset waypoint Z | All Office waypoints use `0.85 m` | Route samples must use `terrain_z + qualified_body_center_height`; fixed `0.85 m` must not stand in for terrain. |
| Manual goal Z | Clamped to the initial odometry Z | For non-flat routes, receive or derive the local target terrain/body height instead of freezing the initial height. |
| Reference-path Z | Input path Z plus `grid_map.body_height` | Retain this convention, but specify that input path Z is ground/terrain height and validate it. |
| Map lower anchor | `grid_map.ground_height = 0.0 m` | Keep only as a map-boundary anchor; do not use it as the traversed surface on slopes. |
| Terrain cell size | Existing geometry filter default `0.30 m` | Tune against map resolution, foot/body scale, and MID-360 density; test at cell boundaries. |
| Terrain/obstacle separation | Existing height threshold `0.22 m` | Must be lower than or explicitly related to the qualified step/obstacle boundary; validate ramps and step edges. |
| Neighborhood support | Radius `1` cell, minimum `2` populated cells | Define sparse-cell behavior; recommendation is conservative retention/blocking, not automatic traversability. |

The current Office acceptance file allows root height `0.25--0.45 m`, while
the planner's preset route uses `0.85 m`. The implementation must first define
one body-center Z convention and add a runtime assertion/report for the
route-to-odometry height residual.

### 3. Traversability limits that are missing as explicit SCAN parameters

These should be added as a small, auditable adapter contract rather than hidden
inside unrelated thresholds:

| Proposed meaning | Proposed parameter | Fail-closed behavior |
| --- | --- | --- |
| Maximum uphill surface angle | `traversability.max_slope_up_deg` | Mark cell/edge non-traversable when exceeded. |
| Maximum downhill surface angle | `traversability.max_slope_down_deg` | Mark cell/edge non-traversable when exceeded. |
| Maximum upward discontinuity | `traversability.max_step_up_m` | Reject an edge exceeding the qualified value. |
| Maximum downward discontinuity/drop | `traversability.max_step_down_m` | Reject an edge exceeding the qualified value. |
| Terrain-fit quality | `traversability.max_height_residual_m` | Unknown/block when local terrain fit is unreliable. |
| Minimum terrain observations | `traversability.min_support_points` | Unknown/block when support is insufficient. |
| Body-height tracking residual | `traversability.max_route_height_error_m` | Stop/fail the probe when planned Z and odometry/local terrain disagree. |
| Unknown-terrain policy | `traversability.unknown_is_blocked` | Default `true` for the first bounded integration. |

The upstream paper provides a geometric `d_step` concept and a supplied 3D
ground-following route. It does not provide Lite3 V12-specific values for slope,
drop, friction, footholds, or stability. Those values require pinned locomotion
evidence or bounded qualification probes.

### 4. Map and trajectory parameters to freeze first

These affect results but should not be tuned simultaneously with the initial
traversability repair:

- `grid_map.resolution = 0.05 m`
- local map size `16 x 16 x 5 m`
- local update range `6 x 6 x 2.5 m`
- `grid_map.max_ray_length = 5.0 m`
- `manager.max_vel = 0.50 m/s`
- `manager.max_acc = 0.5 m/s^2`
- `manager.max_jerk = 4.0 m/s^3`
- controller `max_vx = 0.50 m/s`, `max_vy = 0.35 m/s`,
  `max_vyaw = 1.0 rad/s`

Keeping these frozen makes a flat/slope/step comparison attributable to the
terrain contract rather than simultaneous planner retuning.

## Recommended calibration order

1. Measure/pin the Lite3 assembly collision envelope and nominal body-center
   height.
2. Fix the route-Z convention and prove it matches odometry plus local terrain.
3. Derive the initial step threshold from locomotion evidence; map it back to
   SCAN's upward obstacle inflation.
4. Qualify slope-up, slope-down, step-up, and step-down independently in short
   simulation probes.
5. Only then tune terrain filter resolution/support and, if needed, planner
   speed or clearance.

For slope and step qualification, increase one terrain variable at a time at a
frozen command speed, repeat each level, and choose a declared operating bound
below the last repeatable pass. The first pass remains simulation-only; it does
not establish a real-robot limit.
