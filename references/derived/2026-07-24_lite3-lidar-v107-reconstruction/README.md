# Lite3 LiDAR V1.0.7 Visual Reconstruction

This directory contains a source-traceable visual reconstruction of the current
Lite3 LiDAR configuration shown in the official LiDAR User Manual V1.0.7-0.

The unchanged official factory-standing Lite3 mesh is used as the robot
baseline. Missing upper-body LiDAR equipment is authored as separate
parametric FreeCAD solids:

- upper interface enclosure;
- laser-radar core;
- cooling fins;
- protective hoop;
- front depth-camera/sensor bar;
- hidden mounting-reference plate.

## Claim Boundary

The authored upper module is an `appearance_reconstruction`. The complete robot
assembly is `visual_only`.

The official manual does not publish the exact laser-radar model, bracket
dimensions, installation datum, tolerances, internal enclosure construction,
materials, or fastener details. These artifacts are therefore not official
factory CAD, manufacturing CAD, a print-ready mount, or evidence of physical
fit.

## Sources

- Official robot model:
  `references/upstream/2026-07-24_deep-robotics-model/`
- Official LiDAR V1.0.7 manual and page renders:
  `references/upstream/2026-07-24_lite3-design-drawings/`
- Requirements and design:
  `.trellis/tasks/07-24-lite3-pro-parametric-model/`

Every input hash and every authored dimensional parameter is recorded in
`model_parameters.json`.

## Build

```bash
FREECAD_CMD=/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
"$FREECAD_CMD" -c \
  'import runpy; runpy.run_path("build_lite3_lidar_v107.py", run_name="__main__")'
```

To create an isolated second build:

```bash
LITE3_MODEL_BUILD_ROOT="$PWD/rebuild-check" \
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  -c 'import runpy; runpy.run_path("build_lite3_lidar_v107.py", run_name="__main__")'
```

## Validate

```bash
python3 validate_outputs.py --root .
python3 validate_outputs.py \
  --root . \
  --compare-root rebuild-check \
  --comparison-report reports/rebuild-comparison.json
```

## Render And Compare

The render command launches a task-owned FreeCAD process, applies the recorded
visual colors, writes the standard views, and exits without saving another
document:

```bash
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD \
  render_lite3_lidar_v107.py

python3 make_comparison_sheet.py
```

## Expected Artifacts

Primary outputs are generated under `models/` and `reports/`:

- `models/lite3_lidar_v107_reconstruction.FCStd`: editable assembly with the
  official base mesh plus six separately named authored components.
- `models/lite3_lidar_v107_upper_module.step`: the six authored closed BRep
  solids.
- `models/lite3_lidar_v107_upper_module.stl`: authored upper components for
  direct viewing, not print-validated.
- `models/lite3_lidar_v107_standing_visual.stl`: complete standing visual with
  separate overlapping shells.
- `reports/validation.json`: source hashes, object names, validity, dimensions,
  export hashes, and clean re-import results.
- `reports/rebuild-comparison.json`: independent-build geometry, parameter, and
  deterministic-output comparison.

The measured standing envelope is
`610.036682 x 372.657928 x 496.000000 mm`. The 2.657928 mm width difference
from the nominal 370 mm is retained because the official source mesh remains
at scale 1.0.

Rendered views and comparison evidence are stored under `evidence/`, including
`lite3-lidar-v107-comparison.png`, six full-assembly views, and three upper
module detail views. The two STL exports reproduce byte-for-byte across clean
builds. FCStd and STEP raw hashes can differ because they contain
container/header metadata, so their geometry and re-imported solids are
compared instead.
