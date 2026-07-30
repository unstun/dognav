# Lite3 LiDAR High-Fidelity Printable Replica

This directory builds a static 1:1/1:4 replica of the requested Lite3 laser
configuration. The visible reference uses manufacturer geometry wherever
public source files exist; the printable kit uses separately identified
watertight reconstructions and print adaptations.

## Evidence And Claim Boundary

The output label is `printable_static_replica`. It is not factory assembly CAD,
manufacturing-exact geometry, a working robot, a load-rated bracket, or proof
of physical fit.

The current geometry tracks are:

- Lite3 body and legs: official DEEP Robotics high-resolution URDF/DAE for the
  visible reference; a separate watertight reconstruction for printing.
- LiDAR: official Livox Mid-360 STEP, official DEEP Robotics J20A 15-degree
  adapter, and official S410 guard geometry.
- Top enclosure: a visible `DEEP Robotics Interface` exterior reconstructed
  from official views. The manual lists `NVIDIA Jetson Xavier NX` separately,
  but does not publish its location inside the robot; the report therefore
  records `ai_computer_location: not_published` and exports no visible Jetson
  development-kit model.
- Depth camera: the exact `d435.dae` visual mesh from the official
  `realsense-ros` package, pinned at commit
  `60c850958d651130fc2cc3d10efb37ff5be93da5`. The official
  `_d435i.urdf.xacro` includes the D435 visual definition that uses this mesh.
  Its audited source bounds are
  `89.9143 x 25.0000 x 25.0547 mm`.

The official D435 visual mesh is open and is therefore not labeled printable.
`d435i_sensor_master_1_1.stl` is a separate 0.35 mm voxel reconstruction from
that same official source. It is one watertight component; the current
master-to-source p99 surface distance is `0.3571 mm`. The mounted printable
`FRONT_CAMERA_BAR` trims only the voxel overgrowth at the official rear plane
and adds two print-clearance blind holes on the official 45 mm M3 axes. It is
not fused to the support. A separate two-piece camera bracket, eight explicit
fasteners, and a two-arm blind-bore receiver yoke provide the printable
assembly path into the S410/upper module. The former
hand-authored rounded box, front bezel, estimated apertures, lens inserts,
floating support cylinders, and integrated camera pins have been removed.

The J20A and S410 are published for the related Lite3 Venture FAST-LIVO2
extension. They are source-backed component geometry, not evidence that the
complete current assembly is the factory V1.0.7 LiDAR configuration.

## Environment

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The build and validation use the pinned dependencies in `requirements.txt`.

## Build And Validate

```bash
.venv/bin/python build_printable_replica.py
.venv/bin/python validate_printable_replica.py
```

Set `LITE3_PRINT_BUILD_ROOT` to build into a separate directory. Set
`LITE3_PRINT_REBUILD_ROOT` to that directory when running
`compare_clean_rebuild.py`.

The official STEP files are preserved unchanged. Regenerate their deterministic
tessellation cache with:

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c \
  "p='prepare_official_sensor_meshes.py'; \
   exec(compile(open(p,'rb').read(),p,'exec'), \
   {'__name__':'__main__','__file__':p})"
```

Primary files:

- `models/reference/lite3_lidar_1_1_reference.glb`: smooth visible reference
  with the official Lite3 exterior and official D435 mesh; it contains open
  source shells and is not print-ready.
- `models/reference/lite3_lidar_1_1_reference.3mf`: multi-object printable
  reference made from watertight geometry.
- `models/master_1_1/d435i_sensor_master_1_1.stl`: source-derived watertight
  D435 body before the mounting adaptation.
- `models/master_1_1/front_camera_bar_master_1_1.stl`: full-scale source-derived
  D435 print body with the two declared print-clearance blind holes.
- `models/master_1_1/camera_mount_bracket_master_1_1.stl`: source-aligned
  printable camera-side plate and four side rails.
- `models/master_1_1/camera_carrier_plate_master_1_1.stl`: separately
  printable carrier-side mating plate.
- `CAMERA_RECEIVER_YOKE` in the visual reference: two receiver bosses and
  struts that give the carrier-side screws real material to enter. Its
  print-adapted counterpart is Boolean-integrated into
  `UPPER_LIDAR_MODULE`, so it is not an additional loose STL.
- `models/master_1_1/camera_fasteners_master_1_1.stl`: eight explicit
  full-scale fastener references.
- `models/print_1_4/FRONT_CAMERA_BAR.stl`: oriented 1:4 printable camera part.
- `models/print_1_4/CAMERA_MOUNT_BRACKET.stl`: printable camera-side bracket.
- `models/print_1_4/CAMERA_CARRIER_PLATE.stl`: printable carrier-side plate.
- `models/print_1_4/CAMERA_FASTENERS.stl`: eight print-adapted screw models.
- `models/print_1_4/`: current 20-part print kit.
- `reports/build_report.json`: source hashes, transforms, topology, surface
  deviation, placement, collision, and output hashes.
- `reports/validation_report.json`: independent post-export mesh and contract
  checks.
- `reports/slice_report.json`: per-part PrusaSlicer evidence after slicing.

Do not refresh or distribute the package ZIP files until the current
zero-cache build, full validation, slicing, clean-build comparison, and human
visual review have all completed. Pre-correction ZIPs and comparison evidence
are retained under `packages/superseded/` and `reports/superseded/`.

## Real Slicer Check

The declared generic PLA profile is
`slicer/PrusaSlicer_2.9.6_FDM_0.4mm.ini`.

```bash
.venv/bin/python slice_print_parts.py
```

Generated G-code is printer-specific and ignored by Git. The JSON report keeps
the input hashes, non-empty toolpath evidence, estimated material/time, and
slicer diagnostics.

## Current 1:4 Print Architecture

The kit contains:

- one `TORSO`;
- twelve side-specific leg parts;
- one connected `UPPER_LIDAR_MODULE`;
- one separate `FACTORY_INTERFACE`;
- one source-derived `FRONT_CAMERA_BAR`;
- one `CAMERA_MOUNT_BRACKET`;
- one `CAMERA_CARRIER_PLATE`;
- one `CAMERA_FASTENERS` STL containing eight screws;
- one `ASSEMBLY_PINS` STL containing twelve leg pins and two spares.

The upper module seats into the torso using two integrated pins and a shallow
display-model pocket. Two blind-bore receiver arms are integrated into the
printable upper module through the S410 guard. The complete D435i mounting
chain is: D435i body -> two camera-side M3x6 screws -> camera-side plate and
rails -> four lateral M3x8 screws -> carrier plate -> two carrier-side M3x6
screws -> two 3.0 mm blind receiver bores -> receiver struts -> S410/upper
module. The receiver axes remain derived from the pinned J17A source geometry.
This order leaves both axial screw pairs accessible before the side joint
closes and prevents either carrier screw from terminating in open space. The
official visual track contains no spanning plate beneath the Interface and
radar. The receiver yoke and narrow webs needed for the 1:4 upper print are
explicit `print_adaptation` geometry.

The official camera-side constraints are two M3 mounting points on 45 mm
centres, 3 mm maximum thread insertion, and 0.4 Nm recommended combined
torque. With a 3.2 mm plate, 0.6 mm mating pad and M3x6 screw, the modeled
thread insertion is 2.2 mm. The 17 mm bracket stand-off leaves 3.4 mm between
the opposing axial screw heads. The carrier plate keeps a 0.02 mm modeled face
gap to the receiver bosses; the receiver bore is 3.0 mm deep and the modeled
carrier-screw insertion is 2.2 mm. The 1:4 print version enlarges holes and
screw shafts to retain 0.20 mm radial clearance and a 0.9 mm receiver radial
wall, above the 0.8 mm minimum feature.

The visible D435 and printable D435 use the same source-to-robot rigid
transform. The visual GLB contains `D435I_CAMERA` and excludes the printable
proxy `FRONT_CAMERA_BAR` as well as all former synthetic optics.
Because the official DAE is an open visual shell, its mount separation is
checked with deterministic sampled surface clearance (`14.6350 mm` minimum in
the current report). Exact Boolean collision volumes use the explicitly
declared watertight print proxy. The current ten-component visible relationship
matrix contains 45 pairs. The sole declared positive engagement is
`MID360_GUARD__CAMERA_RECEIVER_YOKE` at `43.9378 mm3`; the other 44 pairs are
numerical zero. Camera-to-bracket, bracket-to-carrier-plate,
carrier-plate-to-receiver-yoke, receiver-yoke-to-adapter, and all other
undeclared Boolean volumes are zero. Sampled minimum clearance to the
Mid-360 guard is `5.1947 mm` for the camera bracket and `1.0735 mm` for the
carrier plate.

## Print Profile

- scale: 1:4;
- process: FDM static display;
- nozzle: 0.4 mm;
- layer height: 0.20 mm;
- minimum free-standing feature: 0.8 mm;
- loose assembly pin diameter: 2.4 mm;
- nominal radial clearance: 0.20 mm;
- maximum declared part envelope: `220 x 220 x 250 mm`.

The Mid-360 printable master is reconstructed at 0.4 mm voxel pitch. It moves
3.0 mm outward along the J20A mounting normal to prevent reconstructed-solid
interpenetration. A hidden bridge connects the print bodies inside the
official `48 x 36 mm` hole rectangle. This offset and bridge are print
adaptations, not Livox manufacturing dimensions.

## Installation Boundary

Actual printer calibration, shrinkage, supports, and surface finish still
require a test print. Installation on a real Lite3 is not authorized or
fit-validated by this model. A functional bracket requires direct measurement
of the robot and installed computer, followed by fastener, cable, thermal,
static-load, and vibration review.
