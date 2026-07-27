# Implementation Plan: Lite3 LiDAR High-Fidelity Printable Replica

## Current J17A Front-Pair Adaptation Implementation (2026-07-27)

1. Measure the two front shallow chassis features directly from the source
   B-rep: `diameter 2.5 mm` central openings, shallow `diameter 8.0 mm`
   recesses, and `64.999999659 mm` centre pitch.
2. Preserve the manufacturer J17A body. In a temporary Fusion document,
   validate a derived-body workflow that heals the two original front stepped
   holes and re-cuts them without stale B-rep references.
3. Translate J17A/J20A/S410/Mid-360 rigidly by
   `[-0.151878610, -3.128370000, +40.923512315] mm` in world `[X, Y, Z]`,
   preserving every internal transform and determinant-`+1` rotation.
4. Capture
   `Front_2x_Shallow_Holes_65mm_Aligned_Contact_Pose` before adding new
   timeline geometry.
5. Create
   `J17A_FRONT_PAIR_65MM_ADAPTED_REV_B_NOT_OFFICIAL_CAD`, fill only the two
   source front holes, and cut the preserved `diameter 4.5 mm` through /
   `diameter 8.0 mm` counterbores on the exact robot axes. Leave the rear pair
   unchanged.
6. Hide the unchanged source J17A and rejected Rev A proxy; restore the
   original robot top shell and display the adapted J17A with J20A, S410, and
   Mid-360.
7. Verify axis residual, B-rep topology, rotation determinants, numerical
   contact, all pairwise solid intersections, snapshot state, and screenshot
   hashes. Leave Fusion unsaved for Dr Sun's review.

Measured Rev B results:

- target pitch: `64.999999659 mm`;
- adapted-axis maximum line residual: `3.083798808770177e-13 mm`;
- adapted J17A: one solid B-rep, one lump, one shell, `141` faces,
  `32.140771157 cm3`, zero mesh bodies;
- source J17A remains `31.805746881 cm3` and is hidden unchanged;
- adapted-J17A/robot-shell minimum distance: numerical zero/contact;
- all robot/adapted-J17A and sensor/sensor exact intersections: `0.0 mm3`;
- all four occurrence rotation determinants: `+1`;
- two snapshots, no pending snapshot;
- five `1800 x 1200` review screenshots;
- Fusion document `Untitled`: modified and unsaved.

After Dr Sun authorized execution:

- Fusion exported the complete editable assembly to
  `lite3-j17a-front-pair-65mm-rev-b.f3d`
  (`126210700` bytes,
  SHA-256 `889b3b6cd8487b600a37d1ce4b29868ee356cc55debf380bdca3554fbc2be46e`);
- Fusion exported the adapted component to
  `j17a-front-pair-65mm-adapted-rev-b.step`
  (`267046` bytes,
  SHA-256 `debede467637c5bca850ace215e3c5946517b1b985e79af798926cabca51c7bb`);
- the F3D container passed archive integrity checks for every member supported
  by the generic archive tester;
- a clean FreeCAD import of the STEP reports one valid closed solid, one shell,
  `141` faces, and `32140.875563 mm3` volume.

The current implementation represents the intended screw path: the
`diameter 8 mm` J17A counterbore is the head seat, the `diameter 4.5 mm`
J17A bore is shaft clearance, and the `diameter 2.5 mm` chassis opening is the
receiving/pilot feature. The unequal diameters are expected. Exact thread,
screw length, engagement, material, torque, anti-rotation, access, and load
path remain outside the validated claim.

## Rejected Receiver-Proxy Implementation (2026-07-27)

1. Re-check the official installation close-up and distinguish the four large
   J17A installation holes from the unrelated Experience-body shell inserts.
2. Preserve the official J17A/J20A/S410/Mid-360 B-reps and restore the reviewed
   `+30.0 mm` front / `-2.4 mm` vertical whole-stack pose.
3. Capture that external occurrence pose in one Fusion position snapshot
   before creating new timeline geometry.
4. Copy only the Experience top-shell body into
   `LITE3_VENTURE_RECEIVER_PROXY_REV_A`; keep the original body intact and
   hidden in the preview.
5. Add four hidden receiver proxies on the actual J17A counterbore axes. Use
   `8.0 mm` outside diameter, `6.0 mm` hidden depth, and `3.3 mm` pilot only as
   explicit nonofficial proxy parameters.
6. Verify one solid B-rep, zero mesh bodies, all four centre residuals below
   `0.01 mm`, zero new body collision, determinant-`+1` source-part rotations,
   and no pending position snapshot.
7. Export top, diagnostic top, isometric, and side review images while leaving
   the Fusion document unsaved.

Measured Rev A results:

- four-axis maximum residual:
  `7.105427357601002e-13 mm`;
- derived-shell/J17A intersection: `0.0 mm3`;
- derived-shell/J17A minimum distance: `0.006602556 mm`;
- receiver-boss intersection with other existing bodies: none;
- derived shell: one solid B-rep, one lump, one shell, `1729` faces,
  `435.649838 cm3`, zero mesh bodies;
- J17A source volume remains `31.805746881 cm3`;
- the Fusion document is `Untitled`, modified, and unsaved.

Dr Sun rejected Rev A because it bypassed the actual two front small-hole
screw axes. The component remains hidden as negative evidence; its internal
metrics do not satisfy the Rev B acceptance gate.

## Current User-Authorized Workstream (2026-07-27)

1. Preserve and hash the full user-provided Lite3 STEP and the manufacturer
   J17A, J20A, S410, and Mid-360 sources.
2. Import the full opaque Lite3 B-rep in Fusion, keep the visible Experience
   robot child, and hide the separate Exploration backload.
3. Establish robot head/front as source/world `+Z` from a physical-top chassis
   view before placing sensors.
4. Install only J17A, J20A, S410, and Mid-360 manufacturer B-reps. Assert zero
   mesh bodies and determinant-`+1` occurrence rotations.
5. Add no custom/yellow adapter, base, bridge, D435, BZ20, AGX, industrial PC,
   or factory Interface reconstruction.
6. Register the complete sensor assembly from official visible landmarks.
   After Dr Sun rejected the first position as too far rearward, move the
   complete assembly `30.0 mm` toward robot `+Z` and `2.4 mm` down while
   preserving all internal source-part transforms.
7. Record B-rep counts, source hashes, transforms, pre/post collision metrics,
   exclusions, and the unresolved physical-fit boundary.
8. Present corrected isometric, side, and top screenshots to Dr Sun while the
   Fusion document remains unsaved.
9. If Dr Sun accepts the basic placement, save a named Fusion version. Handle
   the true D435 CAD later in a separate clean session before designing any
   robot-side base.

## Archived Current State (2026-07-26)

Implementation is frozen at an evidence-acquisition gate. There is no accepted
official-LiDAR geometry candidate and no accepted printable assembly.

Dr Sun rejected the latest multiview candidate because its Interface position
was image-estimated and moved rearward without a factory datum, while its lower
plate, unequal posts, tilted plate, D435 rear support, guard straps, and
fastener heads were invented without a real contact/fastener/receiver chain.
The reported `496.003681 mm` height and `11 mm` separation are historical
self-consistency metrics only.

Public-source review found no complete factory Lite3 LiDAR assembly CAD, STEP,
URDF, hole layout, or assembly transform. The official Lite3 body, Mid-360,
D435, and Lite3 Venture FAST-LIVO2 extension parts remain separate evidence
classes. No generator may combine them into a claimed factory replica.

The next executable modeling input must be either manufacturer factory-LiDAR
assembly CAD/drawings or a physical measurement/scan package. Until then,
preserve rejected artifacts, keep the main printable generator unchanged, and
do not generate another complete upper assembly.

## Requirement Change

Dr Sun rejected the first visual reconstruction and required the most realistic
model that can actually be 3D printed. The corrected implementation does not
promote or reuse the rejected full visual STL as a printable result.

## Ordered Checklist

1. Preserve and relabel the first output as a rejected visual draft.
2. Record the new printable-replica requirements and reset acceptance gates.
3. Audit the official high-resolution DAE components for open edges,
   non-manifold edges, disconnected shells, self-intersections, and source
   dimensions.
4. Benchmark watertight reconstruction at multiple resolutions and reject any
   method that silently loses major shells or detail.
5. Implement a reproducible source-to-master conversion script and parameter
   file under
   `references/derived/2026-07-24_lite3-lidar-printable-replica/`.
6. Generate watertight 1:1 torso, hip, thigh, and shank master components.
7. Reassemble the official factory-standing pose from the pinned URDF without
   changing source scale.
8. Replace the coarse upper draft with official Mid-360, J20A and S410 source
   geometry while keeping surrounding Lite3 placement evidence-scored.
9. Generate a 1:1 static assembled reference and verify the declared envelope.
10. Produce the 1:4 FDM kit with side-specific parts, hidden keys/pins, minimum
    thickness, and print clearance.
11. Generate an assembled 1:4 reference and print-layout renders.
12. Run independent manifold/topology validation and clean re-import.
13. Slice every print part with an installed or task-contained real slicer
    profile; record toolpath, estimated time/material, and any warnings.
14. Run a second clean build and compare parameters, names, metrics, and
    deterministic hashes.
15. Run Trellis validation, `trellis-check`, update the relevant specification,
    and present renders plus direct files to Dr Sun.
16. Commit and close only after Dr Sun visually accepts the corrected model.
17. Replace nominal-pattern-only sensor registration with a collision-free
    seating contract: offset the reconstructed Mid-360 master along the J20A
    normal, preserve the source hole rectangle, add a deliberate hidden print
    bridge, and validate component intersections, clearances, field of view and
    upper-module connectivity.
18. Historical, superseded: separate the industrial-PC placeholder from the upper-module Boolean,
    add two removable pressure bars aligned with the slotted saddles, move the
    sensor stack forward for service and hole-ligament clearance, enforce the
    scale-aware hidden-bridge edge rule, and regenerate the 19-part kit.
19. Historical, superseded: replace the remaining visual interpenetrations with a complete visible
    collision matrix, source-hole-axis registration, open-bore J17A stand-offs,
    source-axis connector sleeves, and an outboard D435i mounting path.
20. Historical, superseded: correct the Jetson/Interface evidence boundary: export the official-view
    `FACTORY_INTERFACE` exterior only, record the Xavier NX location as
    unpublished, search the closest collision-free exterior registration, and
    regenerate the renders for human review.
21. Historical, superseded: remove the rejected spanning factory carrier and deck from the official
    visual track. Retain only local open-bore mounts and keep any FDM
    connectivity webs hidden inside the print-only upper module.
22. Historical source correction only: replace the estimated D435i shell, bezel, apertures, and lens inserts with
    the pinned official RealSense ROS visual mesh. Build a separate watertight
    print body from the same source, retain only the declared mounting lugs,
    and add source/transform/deviation validation plus camera close-up renders.
    The subsequently added lugs/brackets are rejected.
23. Historical rejected detour: split the historical cylindrical factory-LiDAR identity from the requested
    official true-Mid-360 FAST-LIVO2 extension and freeze the latter as the
    visible target.
24. Historical FAST-LIVO2 work: restore the unchanged J17A/J20A/S410/Mid-360 stack and seat the pinned
    D435 directly on J17A with only its two source-backed M3 axes.
25. Historical rejected detour: replace the wrong generic Interface placeholder with the official BZ20
    source solid, keep the rear AGX/user industrial PC separate, and render a
    full-standing official-source comparison.
26. Keep the main printable generator and Pro adapter frozen until Dr Sun
    accepts the appearance candidate and actual user-IPC CAD/measurements are
    available.
27. Correct the identity target to the official Lite3 LiDAR V1.0.7 manual
    assembly and freeze BZ20, AGX, and the custom Pro truss as rejected tracks.
28. Losslessly extract the manual front, side, front-line-art, and
    rear-line-art assets; inspect the official perception manual and
    navigation repository for sensor identity and mechanical-data boundaries.
29. Repose the official high-resolution Lite3 URDF to the manual standing
    silhouette before registering the upper assembly to the `496 mm` height.
30. Build a new evidence-only long-Interface baseline with the real Mid-360,
    real D435 direct mount and two M3 axes, related-source J17A/J20A/S410
    candidates, and an explicit Interface/carrier relief.
31. Export a readable FreeCAD assembly, render four-direction comparisons,
    and run targeted identity, source-hash, envelope, contact, collision, and
    artifact validation.
32. Keep the main printable generator and user-IPC base frozen until Dr Sun
    visually accepts the V1.0.7 baseline.
33. Reject the collision-masking Interface cut after the official side view
    shows a separate carrier and Interface front face.
34. Historical rejected action: move the complete related-source sensor stack rigidly `35 mm` farther
    toward robot `+X`, leaving the image-derived Interface fixed.
35. Historical rejected action: add four bored Interface feet plus four source-axis J17A local supports,
    with explicit upward/downward M3 fasteners and replaceable hidden receiver
    proxies.
36. Historical rejected action: render normal, transparent-mechanism, and underside views and require zero
    carrier/Interface/support overlap before visual review.

## Current Findings

### 2026-07-25 Zero-Collision Revision

- The official manual labels the visible top enclosure `Interface` and only
  lists `NVIDIA Jetson Xavier NX` separately under configuration. It does not
  locate the AI computer inside the visible enclosure. The previous
  `FACTORY_XAVIER_NX_INTERFACE` identity was therefore rejected.
- The `448.865 mm3` collision produced by moving the Interface toward its
  official visual position proved that the Venture J17A carrier was the wrong
  factory-layout constraint. The revised factory track removes J17A from the
  visible and printable upper assembly, uses a compact image-estimated forward
  carrier, and places the `160 x 92 x 46 mm` Interface at
  `[15.0, 0.0, 451.8] mm`.
- The first carrier-post revision had `17.556 mm3` of visible carrier/J20A
  overlap. Lowering the posts below the tilted adapter exterior produces 28/28
  numerical-zero visible collision pairs while retaining one connected
  printable upper component.
- Dr Sun rejected the subsequently visible lower plate. The plate-free
  revision removes `UPPER_DECK_INTERFACE` and `PAYLOAD_BASE` from the official
  exterior, replaces `FACTORY_LIDAR_CARRIER` with four local annular
  `FACTORY_LIDAR_MOUNTS`, and confines two narrow connectivity webs to the
  print-only upper Boolean.

- Official STEP cylindrical axes replace the former J17A circular-opening
  centre registration. The J20A X=1.558875 mm hole row aligns to the J17A
  X=-22.691125 mm counterbore row.
- The base rises 1.5 mm above the watertight torso. The sensor assembly uses
  the minimum tested 25.0 mm vertical lift that clears both torso and base.
- J17A/J20A, J20A/S410, Mid-360/J20A, Mid-360/S410, J17A/D435i, base/torso,
  and every other pair among the nine declared visible bodies report at most
  0.001 mm3 intersection. All 36 pairs pass; the maximum residual is numerical
  noise at 9.53e-12 mm3.
- The former large hidden radar bridge is removed. Four annular stand-offs
  preserve the J17A base holes, two annular sleeves follow the J17A/J20A bolt
  row, and four follow the J20A/S410 guard axes. The printable upper module is
  one connected component.
- The D435i body moves 14 mm outward along J17A's official 20-degree camera
  axis. Its two print pins now span the resulting gap to J17A rather than
  embedding the camera body in the carrier.
- The complete primary zero-cache build and validation pass with zero
  failures. PrusaSlicer 2.9.6 produces non-empty toolpaths for 19/19 parts.
  The independent zero-cache build matches 33/34 hashes; the sole 3MF byte
  difference has an equivalent imported geometry signature.
- The refreshed master and print-kit ZIP files pass `unzip -t`. The task stays
  `in_progress` until Dr Sun visually accepts the revised renders.

- Official current documentation and the official model repository were
  rechecked on 2026-07-24.
- No public complete Lite3 LiDAR assembly STEP, manufacturing CAD, or
  print-ready STL was found. The Mid-360, J20A and S410 component CAD is
  public and is used directly within the stated variant boundary.
- High-resolution source topology:
  - torso: 299,349 processed faces, 18,192 boundary edges, 21 non-manifold
    edges;
  - hip: 75,402 processed faces, 6 boundary edges, 3 non-manifold edges;
  - thigh: 117,514 processed faces, 264 boundary edges, 24 non-manifold edges;
  - shank: 27,050 processed faces, 6 boundary edges, 2 non-manifold edges.
- Generic mesh-hole repair was rejected because it collapsed valid component
  shells.
- Manifold and quadric simplification were also rejected for the official
  master meshes because binary STL round-trip introduced coincident-vertex
  non-manifold edges. The final masters retain indexed marching-cubes topology
  without simplification.
- Torso voxel reconstruction succeeded at 2.0, 1.5, and 1.0 mm master pitch.
  The selected bridged 1.0 mm torso contains 1,777,070 faces. Selected final
  smoothed-master-to-source P99 deviations are 1.035 mm for the torso,
  0.494 mm for the hip, 0.741 mm for the thigh, and 0.742 mm for the shank.
- The upright revision before Dr Sun's latest placement correction had a 1:1
  standing envelope of
  `611.468 x 373.450 x 495.990 mm`, within the declared 5 mm per-axis tolerance
  of the official `610 x 370 x 496 mm`.
- The 1:4 kit contains 17 STLs: one torso, twelve side-specific leg parts, one
  upper module, one D435i part, four lens inserts in one STL, and fourteen
  loose pins in one STL.
- The torso and upper/camera parts now have real hidden print interfaces:
  twelve loose leg pins, two integrated upper-module pins and pocket, and two
  integrated camera-bar pins, all with 0.20 mm nominal radial clearance.
- `validation_report.json` passes post-export topology and import checks for
  all masters, print parts, and reference formats.
- PrusaSlicer 2.9.6 produced non-empty G-code for 17/17 parts with zero blocking
  or geometry-repair diagnostics. Known Voronoi numerical fallbacks remain
  recorded in `slice_report.json`.
- Dr Sun rejected the upright and then the rearward-slanted revisions on
  2026-07-24. The accepted implementation direction is a real Livox Mid-360
  mounted at the front with a 15-degree forward/downward tilt.
- The manufacturer Mid-360 STEP is preserved at SHA-256
  `b93e9b51282ed319b6aa755e76a132c0eb03306da5f3b9676bcabf2e2ae25f02`.
  The official source contains 7 solids, 23 shells, and 1715 faces. Its
  optical window, housing exterior, base and connector are tessellated
  separately for truthful reference coloring.
- The official Lite3 Venture J20A base is preserved at SHA-256
  `341b08ca08526e5ee0e9fbeca0bfda9d9970062c6605e979adc52b31955c9bc9`;
  its drawing and STEP establish the 15-degree mounting plane.
- The official S410 guard is preserved at SHA-256
  `7fd23a776b45c7d8571ef77ba9e8b05520eced0b97f62487ba03f88bbc9df810`.
- Source-axis conversion plus the J20A angle produces robot-frame sensor axis
  `[0.258819, 0, 0.965926]`, which points toward robot `+X` and up. In side
  view the mounting plane therefore descends toward the robot head; the real
  connector is yawed rearward toward the interface enclosure.
- The official sensor components remain distinct in the visual-reference GLB.
  The printable 3MF instead contains watertight body and upper-module objects.
  The printable upper module fuses a 0.4 mm voxel-sealed Mid-360 master, J20A,
  S410, a hidden seating bridge and the U-shaped payload base into one manifold
  part. Decorative payload fastener heads are omitted so the four robot holes
  stay open.
- The current standing envelope is
  `612.379 x 372.658 x 496.142 mm`; ground error is 0.0 mm and every axis is
  within the declared 5 mm envelope tolerance.
- The final zero-cache Mid-360 master has 441,708 faces and a
  master-to-source P99 surface distance of 0.4083 mm. The larger
  source-to-master tail remains recorded because the official STEP also
  contains internal/open shells that are not retained as printable exterior.
- Geometry round-trip validation passes for all 9 master STLs, 17 print STLs,
  and all declared reference formats. The explicit placement check records
  sensor axis `[0.258819, 0, 0.965926]`.
- PrusaSlicer 2.9.6 initially exposed a Voronoi error on the real cooling-fin
  gaps. Disabling generic `gap_fill` and `thin_walls` compensation removed the
  error without weakening the declared 1.0 mm scaled minimum sensor feature.
  Final slicing produces non-empty G-code for 17/17 parts with zero blocking
  diagnostics and zero recorded non-blocking numerical fallbacks.
- The second zero-cache build reproduces all source/parameter hashes, geometry
  metrics, part names, and 30/31 output hashes exactly. The 3MF XML byte stream
  differs, while both imported 3MF scenes have identical object counts,
  vertex/face counts, bounds, and volumes.
- The pre-J17A packages passed `unzip -t`, but their recorded hashes were
  superseded by the 2026-07-25 J17A/D435i/dual-rail rebuild. Do not distribute
  the earlier package bytes.
- `trellis-update-spec` review found no applicable backend, frontend, harness,
  API, or cross-layer contract. The source-frame transform, component variant
  boundary, collision-free seating audit, print-only bridge, dual visual/print
  body tracks, STL float32 post-Boolean simplification, and slicer settings
  remain task-specific and are recorded here and in the artifact README rather
  than promoted into a durable project code-spec.
- A post-build mechanical audit found that the first forward-tilted printable
  registration still contained `9376.8 mm3` of Mid-360/J20A solid overlap.
  Mid-360/S410 did not intersect, but the closest sampled full-scale clearance
  was below 1 mm. Dr Sun requested a redesign rather than accepting the visual
  tilt alone.
- The redesigned registration moves the reconstructed Mid-360 master 3.0 mm
  outward along the J20A normal and uses a 44 x 5 x 30 mm hidden bridge centered
  1.5 mm above the source mounting plane. Exact Boolean audit now reports
  `0.0 mm3` Mid-360/J20A overlap and `0.0 mm3` Mid-360/S410 overlap. The bridge
  engages Mid-360 by `1692.9 mm3` and J20A by `3962.0 mm3`.
- The four-hole rectangle remains 48 x 36 mm with 3.5 mm J20A through holes.
  The hidden bridge leaves 0.25 mm and 1.25 mm edge clearance to the respective
  hole boundaries. The upper module round-trips as one connected watertight
  component after unverified cosmetic guard bolts were removed.
- Deterministic bidirectional vertex sampling reports 0.753 mm minimum
  Mid-360/S410 clearance and 10.674 mm connector/S410 clearance. These are
  geometry audit values for the static replica, not tolerance or vibration
  validation.
- The 15-degree forward tilt maps Livox's published `-7 to 52 degree` vertical
  field of view to approximate longitudinal envelopes of `-22 to 37 degrees`
  in front and `8 to 67 degrees` behind. This is an orientation audit, not a
  full ray-occlusion simulation.
- The redesigned zero-cache build and validation pass. PrusaSlicer accepts
  17/17 parts with non-empty G-code and zero blocking diagnostics. A second
  independent zero-cache build matches 30/31 output hashes exactly; the 3MF
  byte stream differs while its geometry signature remains equivalent.
- A fresh isolated Python environment exposed undeclared runtime dependencies
  used by trimesh export and voxel reconstruction. `networkx`, `lxml`, and
  `scikit-image` are now pinned in `requirements.txt`.
- Dr Sun's 2026-07-25 correction identifies the previously reconstructed
  `interface enclosure` as the existing industrial PC and rejects the solid
  deck beneath it. The verified rebuild replaces that deck with an
  industrial-PC-clearing U-shaped base on the official `74 x 94 mm` four-M3
  Lite3 payload pattern. The front camera also needs a visible mechanical path
  to that base; its print sockets moved from `TORSO` to the upper module.
- The new base consists of two 14 mm-wide side rails and a front support pad.
  Its four open printable clearance holes are 3.5 mm diameter on the official
  `74 x 94 mm` pattern. Against the image-estimated `180 x 76 mm` industrial-PC
  plan envelope, exact audit reports `0.0 mm3` exclusion intersection, 2.0 mm
  lateral rail clearance and 15.0 mm longitudinal front-pad clearance.
- The earlier separate camera part used two estimated outboard support arms.
  Dr Sun's later official-assembly correction supersedes that geometry with a
  D435i nominal envelope and two mounting lugs aligned to the official J17A
  camera faces.
- Moving the bottom plate invalidated one legacy display-model upper pin; both
  upper pins were moved onto the side rails, after which both the 1:1 upper
  master and 1:4 upper print part round-trip as one connected watertight
  component.
- The first post-redesign comparison incorrectly compared a diagnostic
  master-reuse build to a zero-cache build and failed at 10/31 exact hashes.
  It was not accepted. The main output and an empty `rebuild-check` output were
  then both rebuilt with zero cache. Final comparison passes at 30/31 exact
  hashes, with the sole 3MF byte difference geometry-equivalent.
- That earlier validation pass applied to the superseded U-base/camera-arm
  revision. The J17A/D435i assembly and dual-hole-pattern correction require a
  new clean build, validation, slice, and render cycle before the current
  revision can be called validated.
- Dr Sun's 2026-07-25 body-fidelity correction identified that the primary
  standing renders were using the voxel-reconstructed watertight print body.
  Direct comparison against the official high-resolution DAE assembly confirms
  that the pose and overall dimensions were close, but the print reconstruction
  introduced visible terrace bands and a swollen, non-SolidWorks appearance.
  The implementation must therefore split official visual-reference geometry
  from printable geometry; shader changes alone are not an acceptable fix.
- The completed body correction now exports the smooth official
  high-resolution URDF/DAE world links in
  `lite3_lidar_1_1_reference.glb`; those open source shells are explicitly
  `print_ready: false`. The same-stem 1:1 3MF uses independently validated
  watertight printable objects and is explicitly `print_ready: true`.
- The print body uses 50 iterations of topology-preserving Taubin smoothing.
  Full-scale p99 vertex displacements are 0.455 mm for the torso, 0.231 mm for
  the hip, 0.356 mm for the thigh and 0.360 mm for the shank. Absolute volume
  changes remain below 0.065%; at 1:4 the largest p99 displacement is
  0.114 mm, below the declared 0.20 mm layer height.
- The first post-smoothing diagnostic exposed 9 STL boundary edges on
  `HL_HIP` after float32 export even though the in-memory Manifold3D Boolean
  was closed. A 0.0001 mm post-cut manifold simplification removes numerical
  slivers; all four hip STLs now round-trip with zero boundary and
  non-manifold edges.
- The final primary build and a fresh
  `rebuild-check-body-fidelity` zero-cache build both pass geometry validation
  with zero failures. PrusaSlicer accepts 17/17 parts with non-empty G-code and
  zero diagnostics. The two builds match 30/31 output hashes exactly; the
  non-byte-deterministic 3MF remains geometry-equivalent.
- Official FAST-LIVO2 hardware review added the J17A carrier STEP/drawing and
  registered its source-model `110 x 86 mm` four-hole base interface. J17A's
  two front camera faces share the axis `[0.939693, 0, -0.342020]`, equivalent
  to 20 degrees downward toward robot `+X`, with 45 mm centre spacing.
- Official Intel RealSense evidence added the D435i SolidWorks source and
  datasheet. The current printable camera body follows the official
  `90 x 25 x 25 mm` nominal envelope; its four optical apertures and printable
  locating pins remain explicitly estimated/adapted because the proprietary
  SLDPRT was preserved but not translated into local manufacturing geometry.
- The lowest base now uses two 14 mm longitudinal rails, two J17A crossbars,
  four slotted industrial-PC saddles, and no solid centre plate. Its current
  IPC placeholder is `180 x 76 x 40 mm` and remains replaceable parameters,
  not a measured fit.
- The assembly path is now explicit in geometry and reports: open Lite3
  `74 x 94 mm` four-M3 holes -> dual-rail base -> open J17A `110 x 86 mm`
  crossbar holes -> J17A/J20A/Mid-360/S410; the D435i locates to J17A. The
  diagnostic master-reuse build reports numerical-zero intersection at both
  four-hole probe sets, `0.0 mm3` base/IPC exclusion intersection, 2.0 mm
  lateral IPC clearance, and 3.676 mm longitudinal clearance to the first
  sensor crossbar.
- Removing the rejected synthetic camera bar exposes the official high-detail
  source standing length of `596.837 mm`, 13.163 mm below the nominal 610 mm
  brochure envelope. The X acceptance tolerance is therefore 15 mm while Y/Z
  remain 5 mm; source scale stays 1.0 and no fake geometry is added to force
  the brochure number.
- The final primary zero-cache build passes validation with zero failures.
  PrusaSlicer 2.9.6 accepts all `17/17` print parts with non-empty G-code,
  zero blocking diagnostics, and no recorded geometry-repair fallback.
- A fresh independent `rebuild-check-j17a-ipc-base` zero-cache build also
  passes validation with zero failures. The comparison matches `31/32` output
  hashes and sizes exactly; the sole 3MF byte-stream difference imports with
  an equivalent geometry signature.
- Refreshed FreeCAD renders separate the dark industrial-PC placeholder from
  the light dual-rail base, show the empty centre below the IPC, expose both
  four-hole patterns, and show the four-aperture D435i front aligned to J17A.
- Refreshed deliverable archives pass `unzip -t`:
  - 1:1 master package SHA-256:
    `85c6c492ec8b1c0fdf64cf30eeb308c9fc3e0170bb9dc9ab24ed5d749ff3fcfa`;
  - 1:4 print kit SHA-256:
    `8464d5e781c13faa1cc638e153f7eb5188d86de1f65eb956dd5afffcf65fdae1`.
- `trellis-check` found no package-spec conflict and all targeted syntax/JSON,
  geometry, slicer, and comparison checks pass. `trellis-update-spec` found no
  backend, frontend, harness, API, infra, or cross-layer contract suitable for
  promotion; the hardware-specific parameter contract remains in the task
  design and artifact README.
- The 2026-07-25 mechanical-reasonableness revision removes the industrial-PC
  placeholder from the `UPPER_LIDAR_MODULE` Boolean. `INDUSTRIAL_PC.stl` is one
  closed part and `INDUSTRIAL_PC_TOP_CLAMPS.stl` contains two closed removable
  pressure bars with four holes aligned to the existing saddle slots.
- Rails and crossbars are 6 mm thick, the J17A/sensor stack is shifted 10 mm
  forward, IPC-to-first-crossbar plan clearance is above 10 mm, and the nearest
  Lite3/J17A hole ligament is above the scale-aware 3.2 mm full-scale floor.
  The narrowed hidden Mid-360 bridge preserves 3.25 mm to both mounting-hole
  boundaries, equivalent to 0.8125 mm at 1:4.
- The primary zero-cache rebuild reports 19 print parts and passes independent
  mesh validation with zero failures. PrusaSlicer 2.9.6 accepts all 19/19
  parts with non-empty toolpaths and zero blocking diagnostics. Refreshed
  FreeCAD top and isometric renders show the dark IPC as a separate object
  under two orange removable pressure bars.
- A fresh `rebuild-check-ipc-clamps` zero-cache build also passes geometry and
  19/19 slicer validation. The comparison matches 33/34 output hashes and
  sizes exactly; the sole 3MF byte-stream difference imports with an equivalent
  multi-object geometry signature.

### 2026-07-25 Official D435i Geometry Correction

- The preceding nominal-envelope D435 body, hand-authored front bezel, four
  estimated apertures, and `CAMERA_LENSES` STL were rejected by Dr Sun as not
  being a real depth-camera model. Those statements and artifacts are
  superseded by this correction.
- The official `realsense-ros` repository was pinned at commit
  `60c850958d651130fc2cc3d10efb37ff5be93da5`. Its
  `_d435i.urdf.xacro` includes the D435 definition whose aluminum case uses
  `meshes/d435.dae`.
- The preserved DAE has SHA-256
  `42f3b66f47a1f8f425a2e4dc07c1d9c283183167d8441f520a15623d98f9bf78`,
  231,127 faces, and audited bounds
  `89.9143 x 25.0000 x 25.0547 mm`. It is open visual geometry and remains
  explicitly non-print-ready.
- `D435I_CAMERA` in the visual-reference GLB now uses that official mesh
  directly. The printable proxy is excluded from the visual track, and the
  former synthetic bezel and lens nodes are absent.
- `d435i_sensor_master_1_1.stl` is reconstructed from the official mesh at
  0.35 mm voxel pitch. It is one watertight, consistently wound component with
  master-to-source p99 distance `0.3571 mm`. The larger reverse-direction tail
  is retained because the official mesh includes open and internal detail that
  is not preserved as a closed print exterior.
- `front_camera_bar_master_1_1.stl` and `FRONT_CAMERA_BAR.stl` add only two
  declared print mounting lugs/pins. The visual and print tracks share one
  recorded rigid source-to-robot transform.
- The current visible collision matrix has 21/21 numerical-zero pairs. The
  D435 entries use the explicitly declared source-derived watertight collision
  proxy because the official DAE is open. The official visual mesh itself has
  `11.8757 mm` sampled minimum clearance to the factory mounts. The print body
  and camera arms report zero Boolean intersection; sampled arm-to-guard
  minimum clearance is `10.3699 mm`.
- Targeted validation passes
  `d435i.official_visual_and_source_derived_print_tracks`. The only current
  full-report failure is the expected missing body-smoothing diagnostic caused
  by deliberately reusing the already validated Lite3/Mid-360 masters during
  this rapid camera-only rebuild.
- PrusaSlicer 2.9.6 accepts the current 17/17 print parts with non-empty
  toolpaths, zero warnings, and zero geometry-repair diagnostics. The new
  `FRONT_CAMERA_BAR` slice estimates 11 minutes 4 seconds and 1.22 g under the
  declared generic PLA profile.
- A full zero-cache rebuild, clean-build comparison, and package refresh remain
  pending visual acceptance.
- `trellis-update-spec` promoted the reusable evidence boundary into
  `.trellis/spec/guides/hardware-geometry-evidence-guide.md`: official visual,
  source-derived collision proxy, source-derived print body, and print
  adaptation must remain separately named, and open visual meshes must not be
  treated as solid Boolean CAD.

### 2026-07-26 D435i Mechanical Bracket And Fastener Correction

- Dr Sun rejected the preceding camera lugs/pins because they did not establish
  a mechanically inspectable fit or show how the depth camera was screwed to
  the robot-side structure. The 2026-07-25 statements about camera lugs,
  integrated camera pins, camera sockets, 17 print parts, and pending
  body-smoothing evidence are superseded by this correction.
- Intel D400-series datasheet Rev 017 Figure 10-9 provides the camera-side
  contract: two rear M3 mounting points on 45 mm centres, maximum 3 mm thread
  insertion, and 0.4 Nm recommended combined torque for the two M3 points.
  The carrier-side axes remain sourced from the pinned J17A geometry; a
  complete factory Lite3 LiDAR camera-bracket drawing is not public.
- `FRONT_CAMERA_BAR` is now the source-derived D435 print body only. It is
  cropped at the official rear plane and contains two blind print-clearance
  holes on the official 45 mm axes. Floating support cylinders, mounting lugs,
  integrated camera pins, and upper-module camera sockets are absent.
- `CAMERA_MOUNT_BRACKET` contains the camera-side plate and four longitudinal
  rails. `CAMERA_CARRIER_PLATE` is a separate carrier-side mating plate.
  `CAMERA_FASTENERS` contains eight explicit components: two camera-side M3x6,
  two carrier-side M3x6, and four lateral M3x8 fastener references.
- The assembly order is executable: install the two camera-side axial screws,
  install the two carrier-side axial screws, mate the two bracket halves, then
  close the four lateral screws. A rejected one-piece dual-end plate blocked
  access to the opposing axial screw pairs and was not retained.
- With a 3.2 mm plate and 0.6 mm mating pad, modeled M3x6 insertion is 2.2 mm,
  below Intel's 3 mm maximum. The 17 mm stand-off leaves 3.4 mm between
  opposing axial screw heads. At 1:4, holes and screw shafts are enlarged to
  preserve 0.20 mm radial clearance and the 0.8 mm minimum printable feature.
- Both bracket halves round-trip as one watertight connected component with
  zero boundary and non-manifold edges. The fastener bundle contains eight
  connected components in both master and print tracks.
- A final mechanical review rejected the first two-piece result even though its
  screws were visible: the carrier plate remained approximately 6.48 mm from
  the upper structure, so both carrier-side screws terminated in open space.
  That revision is superseded and is not accepted as an assembled mount.
- The correction adds `CAMERA_RECEIVER_YOKE`: two 12 mm receiver bosses with
  3.0 mm blind bores and 4 x 4 mm struts anchored into the official-source
  S410 geometry. The print yoke is Boolean-integrated into
  `UPPER_LIDAR_MODULE`; it does not add a twenty-first loose print part.
  Carrier screws enter the blind bores by 2.2 mm, the carrier-to-receiver face
  gap is 0.02 mm, and the 1:4 receiver radial wall is 0.9 mm.
- The clean zero-cache build passes 125 independent checks with zero failures.
  The ten-component visible relationship matrix contains 45 pairs. The sole
  declared positive pair is receiver-yoke-to-S410 engagement at 43.9378 mm3;
  the other 44 relationships are numerical zero. Camera-to-bracket,
  bracket-to-carrier, carrier-to-receiver, and every undeclared
  bracket/receiver-to-adapter/interface/torso relationship are numerical zero.
- Deterministic sampled minimum guard clearance is 5.1947 mm for the
  camera-side bracket and 1.0735 mm for the carrier plate. The official open
  D435 visual retains 14.6350 mm minimum sampled clearance to the factory
  mounts.
- Integrating the receiver yoke into the high-resolution upper Boolean
  produced two enclosed negative shells of 89.9598 and 89.9651 mm3. The export
  keeps the single positive exterior component and records/discards only those
  negative internal shells; the resulting upper STL is one connected,
  watertight, positive-volume component.
- Receiver construction exposed a latent helper defect:
  `rectangular_beam_between` orthogonalized a NumPy view in place and therefore
  mutated the caller-owned camera width axis. The helper now copies that axis
  before normalization; the screw and receiver arrays remain on their
  source-derived 45 mm pattern.
- The current kit contains 20 print STLs. PrusaSlicer 2.9.6 produces non-empty
  toolpaths for 20/20 parts with zero blocking diagnostics or recorded repair
  fallback. The slicer worker cap is four threads after an otherwise
  reproducible transient signal-5 failure at eight threads.
- The reusable hardware evidence guide now requires an explicit fastener
  count, receiver, insertion limit, service access, assembly sequence,
  separation of intended fastener engagement from undeclared solid collision,
  and honest display-model/load boundary.

### 2026-07-26 Replica Identity Rejection

- Dr Sun rejected the entire two-piece camera bracket, carrier plate,
  receiver-yoke, and eight-fastener revision. Although it passed 125 checks and
  20/20 slicer runs, it was an original print mechanism rather than a replica
  of the factory-visible Lite3 LiDAR support.
- `CAMERA_MOUNT_BRACKET`, `CAMERA_CARRIER_PLATE`,
  `CAMERA_RECEIVER_YOKE`, and the associated eight-screw layout are now
  superseded and forbidden in the next official-appearance output.
- The passed mesh, clearance, receiver-engagement, and slicer results are
  retained only as rejection history. They must not be used to claim the
  camera mount is correct, accepted, or replicated.
- Primary official evidence shows the D435i immediately in front of and below
  the radar on a compact local support. It does not show long rails, a deep
  carrier plate, a rear receiver yoke, or the invented eight-screw chain.
- The DEEP Robotics J17A drawing is a real one-piece base with short angled
  camera faces and a 45 mm pattern, but it is published for the related Lite3
  Venture FAST-LIVO2 extension. It remains a candidate comparison source, not
  factory Lite3 LiDAR V1.0.7 geometry.
- The current manufacturer Lite3 gallery was acquired and hashed. It lists an
  `激光版` but its eleven gallery/detail assets show only the generic body and
  provide no camera-bracket close-up or hidden mounting CAD.
- The evidence boundary and view-by-view matrix are recorded in
  `research/official-lidar-camera-mount-evidence.md`. Replacement modeling is
  paused until that boundary is reviewed; unknown hidden geometry will be
  omitted instead of invented.

### 2026-07-26 Rejected FAST-LIVO2 Source-Backed Reset

- The chosen true-Mid-360 target is the official Lite3 Venture FAST-LIVO2
  extension. The historical FCC/launch cylindrical-LiDAR revision remains a
  separate factory configuration and is not the current geometry target.
- The direct-camera candidate moves the pinned real-source D435 by
  `[-15.974775, 0.0, 5.814342] mm` from the rejected 17 mm-standoff position
  and seats it on the two 20-degree J17A faces. Sampled camera/J17A minimum
  distance is `0.0002 mm`; only the two 45 mm-centre M3 axes remain.
- The official BZ20 STEP was inspected as one closed solid with a
  `108 x 96 x 30 mm` envelope. The official AGX Orin base STEP is a separate
  upright rear support, not a rail or lower plate beneath J17A.
- `prepare_official_bz20_layout_candidate.py` removes the generic
  `160 x 92 x 46.8 mm` Interface placeholder, the 36 mm sensor shift, the
  large hidden Pro adapter, and all invented camera mechanisms. It keeps the
  official sensor transform unchanged and places BZ20 by the declared
  image-estimated translation `[2.652557, 4.498856, 330.462585] mm`.
- The corrected candidate reports `0.0 mm3` BZ20/J17A Boolean intersection,
  `2.5 mm` BZ20-to-torso AABB gap, and `8.293274 mm` D435-to-torso AABB gap.
  The official visual torso/D435 meshes are open, so those torso relations are
  explicitly AABB checks rather than false solid-Boolean claims.
- The official full-standing Lite3 exterior is ground-normalized by
  `2.501525 mm`; its torso-top datum then agrees with the placement candidate
  within `0.001 mm`. Fresh front, side, top, isometric, source-part, and bottom
  views were rendered, and
  `evidence/official-bz20-layout-candidate/official-video-vs-source-cad.png`
  compares them against official frames 284 and 296.
- The old clearance-shift and hidden-adapter evidence directories now contain
  explicit rejection status files. The direct-camera directory warns that only
  its D435/J17A relationship remains valid; its generic Interface collision is
  superseded.
- The surveyed MakerWorld bracket is a nonofficial 30-degree, `45 x 80 mm`,
  eight-sensor-screw design. Its raw SLDPRT download reported
  `闭源文件无法下载。`; it is recorded as a secondary reference and contributes
  no geometry to this candidate.
- The main printable generator, part count, slicer package, and Pro base remain
  unchanged. The user's industrial-PC geometry is not available, so a custom
  J17A-to-Pro base cannot yet be modeled or fit-validated without guessing.

### 2026-07-26 Real-Assembly Restart

- Dr Sun correctly rejected the BZ20 layout as an assembly. The J17A was
  visually positioned above the body, while the black cylinders were only
  fastener-axis references and entered no modeled receiver.
- The candidate also mixed datums: its four references used
  `X=[72.676, 182.676] mm`, but direct inspection of the official J17A STEP
  and its current rigid transform places the real robot-side M3 voids at
  `X=[82.851997, 192.851997] mm`, `Y=+/-43 mm`,
  `Z=446..448.5 mm`. Ray probes pass through the latter axes and intersect
  unrelated material at the stale axes.
- Build a new evidence-only real-assembly candidate before touching the main
  generator. It must use a one-piece open-centre side-truss adapter, true
  robot/J17A bores and counterbores, four candidate M3x8 robot screws, four
  candidate M3x20 J17A screws, and explicit Lite3 receiver proxies.
- Export the candidate as FreeCAD, STEP, STL, and separate fastener parts;
  render assembled, exploded, underside, and section views.
- Validate transformed hole-axis coincidence, seating contact, fastener
  traversal/engagement/bottom clearance, assembly order, connectedness,
  BZ20/body/J17A collision, and absence of a centre deck or fake IPC.
- The new candidate proves only the sensor-to-robot chain. Final outline and
  fit around Dr Sun's different industrial PC remain gated by measured IPC
  geometry.

### 2026-07-26 Official V1.0.7 Baseline Reset

- The target is now the factory-visible Lite3 LiDAR V1.0.7 manual assembly,
  not the separate Venture FAST-LIVO2 extension.
- Four embedded manual assets were losslessly extracted and hashed. The
  official Perception Development Manual confirms Xavier NX, D435i, Livox
  startup, and `mid360_ws`, but no mechanical CAD or extrinsics. The official
  `Lite3_Navigation` snapshot also contains no URDF, mesh, static transform,
  or factory sensor extrinsic.
- The official high-resolution URDF was rebuilt at
  `hip_y=-0.68 rad`, `knee=1.48 rad`. The complete baseline envelope is
  `604.784973 x 372.657928 x 496.0 mm`, compared with the published
  `610 x 370 x 496 mm`.
- The sensor stack transform is `[55.0, 0.0, -28.132935] mm`. The S410 guard
  reaches `496.0 mm` exactly.
- The official D435 direct-mount mesh and its two 45 mm-centre M3 evidence axes
  move rigidly with J17A. Their inherited sampled surface contact is
  `0.0002 mm`; the former 17 mm artificial standoff and all synthetic camera
  brackets are absent.
- The lossless manual side view re-registration updates the image-derived
  Interface to `233 x 92 x 46 mm`. Its four `7.899495 mm` bored feet now
  bridge from the `399.867065 mm` Interface underside to the
  `391.967571 mm` source-body deck datum; the former approximately `5 mm`
  visible suspension is rejected.
- The prior J17A registration overlapped the Interface body envelope by about
  `34 mm` along robot X and used an enclosure cut to mask that error. The
  corrected rigid sensor registration moves `35 mm` forward, leaves the
  Interface fixed, and produces `0.0 mm3` Interface/J17A and
  Interface/local-support overlap.
- The J17A STEP/drawing resolves four `M3` axes on a `110 x 86 mm` pattern.
  Four profiled local supports now expose an upward M3 path into J17A and a
  separately accessible downward M3 path into replaceable body receiver
  proxies. Their sampled minimum body clearance is `0.250008 mm`; the
  Interface feet use a separate four-M3 mounting chain.
- A black D435 front-face display layer is derived from front-facing triangles
  of the pinned RealSense mesh. It changes only appearance and adds no
  synthetic camera body or manufacturing geometry.
- The evidence directory contains a readable
  `lite3_lidar_v107_baseline_candidate.FCStd`, Interface STL, full and upper
  assembly renders, and four official-versus-CAD comparison sheets.
- The manifest now classifies manufacturer meshes as `official_visual`,
  J17A/J20A/S410 as `related_source_candidate`, the Interface as
  `image_estimate`, and the D435 face display layer separately as
  `source_derived_visual_material_layer`.
- `trellis-update-spec` adds a reusable seating/contact gate: every claimed
  pad must report its supporting datum and gap, while zero-gap contact without
  a receiver or load path remains appearance evidence only.
- `validate_official_lidar_v107_baseline.py` passes `27/27` checks. This is an
  appearance baseline, not factory CAD, manufacturing-exact geometry, or a
  fit-validated industrial-PC adapter.

## Review State

The latest post-reboot candidate is
`evidence/factory-step-lite3-real-brep-sensor-stack-forward-30mm-candidate/`.
It moves the complete source stack `30.0 mm` toward robot `+Z` and `2.4 mm`
down after Dr Sun rejected the preceding longitudinal registration as too far
rearward. The full opaque robot and J17A/J20A/S410/Mid-360 B-reps remain
unchanged; all five declared solid intersections are zero, robot/J17A minimum
distance is `0.006602556 mm`, and all four external rotations have determinant
`+1`.

Dr Sun rejected this candidate because the J17A mounting features do not align
with the visible front chassis features. The first audit selected the wrong
J17A `4 x M3`, `110 x 86 mm` hole group. Official drawing and installation-
video evidence identify the correct group as four `diameter 4.50 mm` through
holes with `diameter 8 mm` counterbores on a `67.88225 mm` square.

The circled J17A front-row pitch is `67.88225 mm`; the circled robot row is
approximately `65.00172 mm` and its centre is currently `40.92332 mm` farther
toward robot `+Z`. Translating to a common midpoint would still leave each
hole approximately `1.440265 mm` off-axis. Among `71` plausible robot
circular-feature centres, the full fixed-orientation group matches only
`1/4` at `0.5 mm` tolerance. Its status is
`rejected_interface_mismatch`, and `mount_interface_audit.json` records the
check.

Do not move the source stack again. The next implementation step is source
acquisition and identity verification for either a matching Lite3
Venture/LiDAR chassis/interface CAD or an official manufacturer adapter/base
CAD. A custom base is not authorized. The Fusion document remains unsaved and
unchanged.

Dr Sun rejected the latest full-standing candidate on 2026-07-26 because it
was still an engineered adaptation rather than a factory-visible replica. Its
four profiled supports, bored Interface feet, two provisional M3 chains,
hidden receiver proxies, and `35 mm` clearance-driven sensor translation must
not be carried into the replacement visual track. The historical `27/27`
result validates only the rejected candidate's own geometry assertions.

The replacement work starts from the official front/rear line art and current
official oblique photograph. It will trace only the compact thin local carrier,
short visible blocks/posts, visible fastener heads, Mid-360/D435/guard, and
Interface relationship. Hidden robot receivers are unresolved rather than
modeled. It is not yet the main printable model.

The rejected replacement implementation remains archived at
`evidence/official-lidar-v107-multiview-replica-candidate/`. It imports the
manufacturer Mid-360 exterior and pinned official D435 visual mesh, but imports
no J17A/J20A/S410 bracket geometry. The lower plate, four unequal posts,
15-degree upper plate, camera rear support, guard straps, visible heads, and
Interface exterior were reconstructed from official views without enough
mechanical evidence. The render/manifest checks reported a `496.003681 mm`
guard top and `11 mm` visible Interface-to-carrier separation, but Dr Sun
rejected the Interface placement and the entire invented mounting chain on
2026-07-26. This candidate is not a replica, not an assembly, not factory CAD,
and not print-ready.

The previous two-piece/yoke/eight-fastener design, BZ20/AGX target detour,
generic Interface collision, 36 mm sensor shift, and large hidden adapter are
rejected regardless of their former mesh/slicer results. The task remains
`in_progress`, uncommitted, and unclosed. AC31-AC34 and AC42 have been reset
because they described only the newly rejected candidate. No visual-review
candidate, main-generator replacement, Pro/user-IPC base, final part count,
clean-build comparison, or package refresh is accepted.
