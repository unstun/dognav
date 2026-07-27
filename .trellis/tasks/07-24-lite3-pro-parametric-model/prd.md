# Lite3 LiDAR High-Fidelity Printable Replica

## Current Authorized J17A Front-Pair Revision (2026-07-27)

Dr Sun rejected the four-receiver chassis proxy and confirmed that the two
front shallow chassis holes are the intended screw interface. Their B-rep
centres are `64.999999659 mm` apart; each feature has a `diameter 2.5 mm`
central opening and a shallow `diameter 8.0 mm` cylindrical recess.

The original J17A front pair is `diameter 4.5 mm` through with
`diameter 8.0 mm` counterbores at `67.882250994 mm` pitch. The authorized
minimum correction preserves the manufacturer J17A source and creates the
separately named derived component
`J17A_FRONT_PAIR_65MM_ADAPTED_REV_B_NOT_OFFICIAL_CAD`. Only the two original
front stepped holes are filled and relocated onto the two chassis axes. Their
diameters are preserved, and the rear J17A pair is unchanged.

The entire J17A/J20A/S410/Mid-360 stack is translated rigidly by
`[-0.151878610, -3.128370000, +40.923512315] mm` in world `[X, Y, Z]` so the
new holes are coaxial and the carrier reaches numerical surface contact. No
new base is designed. The source J17A and the rejected Rev A proxy remain
preserved and hidden. Dr Sun authorized execution on 2026-07-27. The accepted
state is frozen locally as a complete editable F3D archive and a lightweight
adapted-J17A STEP; the active Fusion tab itself remains `Untitled`.

This is model-only alignment. The different diameters are not themselves a
mismatch: the J17A `diameter 8 mm` counterbore seats the screw head, its
`diameter 4.5 mm` through-hole provides shaft clearance, and the chassis
`diameter 2.5 mm` central opening is the receiving/pilot feature identified by
Dr Sun. The screw axis and head-seat relationship are therefore represented.
The exact thread designation, usable engagement, torque, material,
anti-rotation, tool access, and load path still require physical or
manufacturer confirmation. Only the front pair is aligned; the rear pair is
not claimed as installed.

## Rejected Receiver-Proxy Revision (2026-07-27)

Dr Sun authorized modifying the model to repair the mounting discrepancy.
Official installation-video close-up review confirms that the J17A four-hole
installation group is the `diameter 4.50 mm` through and `diameter 8 mm`
counterbored `67.88225 mm` square. The two circled Experience-body features
are instead `diameter 2.5 mm` shell through-holes with `diameter 4.55 mm`
annular inserts on a `65.00172 mm` pitch. They are not the J17A receiver group,
so scaling J17A or forcing its holes onto that pair is forbidden.

The approved minimum model correction preserves the official J17A, J20A,
S410, and Mid-360 geometry. It hides, but does not overwrite, the original
Experience top-shell body and substitutes one derived B-rep copy with four
hidden receiver proxies exactly coaxial with the unchanged J17A installation
holes. This derived shell is labeled
`interface_receiver_proxy_not_official_cad`; its receiver diameter, pilot,
depth, thread, material, and load path are not manufacturer-published Venture
geometry.

The complete sensor pose is captured in Fusion before the new component is
added so later timeline features cannot reset the external occurrences to
their source origins. The Fusion document remains unsaved pending visual
review. Dr Sun subsequently rejected this interpretation because it bypassed
the actual two front small-hole screw axes. Rev A is retained only as hidden
negative evidence and is not awaiting review.

## Superseded Interface Gate (2026-07-27)

There is no accepted installation baseline. Dr Sun rejected the
forward-30-mm Fusion placement because the J17A robot-side mounting features
do not align with the visible front chassis features. The B-rep interface
audit initially selected the wrong `4 x M3`, `110 x 86 mm` J17A feature. The
correct official-video-identified installation group is four
`diameter 4.50 mm` through holes with `diameter 8 mm` counterbores on a
`67.88225 mm` square. No corresponding full pattern exists on the supplied
Exploration/Experience robot body at `0.5 mm` tolerance.

This is a source-interface mismatch. Installation modeling is frozen pending
matching Lite3 Venture/LiDAR chassis/interface CAD or an official manufacturer
adapter/base CAD. Do not continue translating the bracket and do not design a
custom base under that instruction. R91-R99 supersede this freeze only for the
explicit two-front-hole J17A model correction. Fusion remains unsaved.

## Rejected Authorized Baseline (2026-07-27, Post-Reboot)

Dr Sun replaced the earlier adapter/D435 workstream with a smaller visual
baseline that must be correct before any new bracket is designed:

- use the user-provided full Lite3 STEP as the opaque robot context; the
  visible robot child is named `Lite3体验版总装.STEP`, so it must not be
  relabeled Lite3 Pro;
- hide the separate Exploration backload branch and add no industrial PC;
- install only the manufacturer J17A, J20A, S410, and Livox Mid-360 CAD;
- use B-rep geometry throughout the current Fusion scene; no robot or sensor
  mesh substitute is accepted;
- treat source/world `+Z` as the robot head/front, orient the Mid-360 optical
  window toward the head, and reject any occurrence transform whose rotation
  determinant is not `+1`;
- add no yellow/custom adapter, base, bridge, or support;
- omit D435 until its true CAD is translated in a separate clean Fusion
  session; do not import the heavy SolidWorks source into this already large
  scene;
- keep the Fusion document unsaved until Dr Sun visually accepts the basic
  direction and placement.

The rejected result is appearance and packaging evidence only. Rigid
translations were used to remove numerical solid intersections and establish
contact between source parts, but there is no verified robot-side hole match,
fastener receiver, thread engagement, cable route, or load path. It must not be
described as bolt-on, fit-validated, factory assembly CAD, or ready for
fabrication.

## Archived Current State (2026-07-26)

There is no accepted replica or printable assembly. Dr Sun rejected the latest
multiview candidate because the Interface position was unsupported and the
surrounding bracket/fastener geometry was invented without a real connection
chain. All modeling is frozen at R53-R58 until manufacturer factory-assembly
CAD/drawings or physical Lite3 LiDAR measurement/scan data are archived.

## Goal

Create the most faithful printable static replica that can be justified from
public primary evidence for the requested Lite3 laser configuration with a
real Livox Mid-360 mounted forward and downward.

The deliverable has two coordinated scales:

- a 1:1 millimetre master preserving official proportions and dimensions;
- a 1:4 static display kit sized for a common desktop printer.

This is a physical appearance replica, not factory manufacturing CAD, a
functional robot, a replacement structural part, or proof of hardware fit.

## Corrected Boundary

Dr Sun rejected the first appearance reconstruction on 2026-07-24 because it
was not sufficiently real. Its outputs remain an explicitly rejected visual
draft and are not accepted as the printable result.

Public source review found:

- DEEP Robotics publishes high-resolution Lite3 URDF/DAE visual assets under
  BSD-3-Clause;
- the official V1.0.7 manual and product imagery identify the Lite3 LiDAR
  appearance and the `610 x 370 x 496 mm` standing envelope, but do not publish
  complete assembly CAD; regulatory/launch evidence shows that historical
  configuration used a cylindrical scanner rather than the requested
  Mid-360;
- the public robot assets omit the LiDAR, depth-camera, and interface-box
  geometry;
- Livox publishes the official Mid-360 STEP and product imagery;
- DEEP Robotics publishes the official Lite3 Venture J17A sensor carrier,
  J20A 15-degree Mid-360 base, and S410 protective-guard STEP/drawings for its
  FAST-LIVO2 extension, plus an official installation video that fixes the
  visible relationship among those parts, D435, BZ20, and the rear AGX;
- Intel RealSense publishes the D435i SolidWorks source and its official
  `90 x 25 x 25 mm` product envelope. Its official `realsense-ros` package
  also publishes the detailed `d435.dae` visual mesh used by the D435i URDF;
- no public complete factory Lite3 LiDAR assembly STEP, manufacturing CAD, or
  print-ready STL was found;
- the official manual labels the visible top enclosure `Interface` and
  separately lists `NVIDIA Jetson Xavier NX` as the AI computer, but does not
  publish an internal assembly drawing that locates the Xavier NX inside that
  enclosure;
- the official visual meshes are not print-ready: they contain open,
  non-manifold, intersecting, and disconnected shells.

The requested target is the official Lite3 LiDAR assembly shown in the
V1.0.7 manual: a forward/downward Mid-360-style radar, front D435i, black
guard, compact local carrier, and long rear `Interface` enclosure. The
separate Lite3 Venture FAST-LIVO2 extension, its BZ20/rear-AGX layout, and the
custom Pro-to-J17A adapter are rejected detours rather than the target.

The chassis, legs, Mid-360, and D435 visual geometry may inherit official
source geometry. J17A, J20A, and S410 may be reused only as
`related_source_candidate` geometry where the manual silhouette supports
them; their FAST-LIVO2 provenance does not prove factory V1.0.7 identity or
hidden fit. The long Interface enclosure and all unpublished registration
remain evidence-scored reconstructions. The D435 print body must remain a
separately labeled watertight reconstruction of the official visual mesh.

## Requirements

- R1. Preserve every official input byte-for-byte under `references/upstream/`.
- R2. Put the corrected printable work under
  `references/derived/2026-07-24_lite3-lidar-printable-replica/`; do not
  overwrite or silently relabel the rejected visual draft.
- R3. Use the official high-resolution URDF/DAE chassis and leg meshes as the
  exterior reference at scale 1.0.
- R4. Convert every printable component to a closed, consistently oriented,
  non-self-intersecting manifold mesh. Overlapping visual shells alone do not
  satisfy printability.
- R5. Preserve visible source detail subject to declared reconstruction
  resolution. Record the source-to-print surface deviation.
- R6. Reconstruct the requested V1.0.7 factory-visible LiDAR equipment with
  separate named parts: image-derived long Interface enclosure,
  related-source-candidate J17A carrier, official Mid-360 optical
  window/body/connector, related-source-candidate J20A adapter and S410 guard,
  official-source D435 visual body, source-derived D435 printable body, and
  only source-backed or explicitly image-estimated fastener references. BZ20,
  the rear AGX assembly, and the user's different industrial PC are not the
  official-LiDAR appearance target.
- R7. Maintain four evidence classes for every dimension:
  `official_nominal`, `source_model`, `image_estimate`, and
  `print_adaptation`.
- R8. Generate a 1:1 master in millimetres and a 1:4 print kit. The 1:4 kit
  must not be produced by blindly scaling minimum wall thickness, pin
  clearances, or fragile details.
- R9. For the 1:4 FDM profile, use at least 0.8 mm free-standing wall/detail
  thickness, at least 2.4 mm assembly pins, and 0.20 mm radial clearance unless
  a documented test coupon justifies another value.
- R10. Deliver a static standing replica. Do not imply working joints,
  load-bearing structure, drivetrain replication, electronics, or robot
  actuation.
- R11. Provide separate print parts and an assembled reference. Parts must have
  stable identifiers and documented orientation/assembly order.
- R12. Export at least:
  - 1:1 watertight reference STL or 3MF;
  - 1:4 printable part STLs;
  - assembled 1:4 reference STL;
  - editable build source and parameter file;
  - slicer-independent geometry validation;
  - a slicer report or command-line slice for the declared FDM profile;
  - source comparison and print-layout renders.
- R13. Verify every output hash and perform a second clean build comparison.
- R14. Label outputs `printable_static_replica`. The labels
  `factory_cad`, `manufacturing_exact`, `functional_robot`, and
  `fit_validated` are forbidden.
- R15. No real-robot actuation, drilling, machining, hardware installation, or
  claim of safe structural use is authorized.
- R16. Per Dr Sun's 2026-07-24 visual correction, the Mid-360 must sit at the
  front and tilt 15 degrees toward robot `+X` (the head), so the mounting plane
  descends toward the front and the sensor body axis is
  `[sin(15 deg), 0, cos(15 deg)]`. Rearward tilt is forbidden. The front
  D435i must follow the official J17A camera-mount direction rather than a
  separately invented tilt.
- R17. Per Dr Sun's 2026-07-24 redesign request, the Mid-360 printable exterior
  must seat above the J20A mounting plane without solid interpenetration. The
  official 48 x 36 mm mounting-hole pattern must remain unobstructed, the
  Mid-360 must not intersect the S410 guard, and a separately identified hidden
  print bridge must provide one-piece 1:4 connectivity instead of relying on
  accidental component overlap. Record Boolean intersection volumes, sampled
  guard/connector clearances, and the longitudinal front/rear field-of-view
  envelope in the build report.
- R18. Per Dr Sun's 2026-07-25 installation correction, the lowest payload
  base must no longer be a solid plate underneath the industrial PC. It must
  use the official Lite3 Pro/LiDAR four-M3 payload pattern
  (`74 x 94 mm` centre spacing), leave all four holes open, and route two side
  rails plus J17A crossbars around an explicitly reported industrial-PC
  exclusion envelope. The D435i print part must locate to the official J17A
  camera-mount faces rather than sockets cut into the robot torso.
  Industrial-PC size, saddle geometry, D435i mounting adaptation, and physical
  clearances remain `image_estimate` or `print_adaptation`; the result is not a
  load-rated or fit-validated real bracket.
- R19. Per Dr Sun's 2026-07-25 body-fidelity correction, the official
  high-resolution URDF/DAE exterior and the watertight printable
  reconstruction must remain two explicit geometry tracks. The official raw
  exterior must drive the 1:1 visual/CAD-reference assembly and the primary
  appearance renders. The separately labeled printable body may use bounded
  smoothing after watertight reconstruction, but it must retain manifold,
  source-deviation, slicer, and hash evidence. The open official visual shells
  must never be labeled print-ready, and the voxel-reconstructed shell must
  never be presented as the original SolidWorks/CAD surface.
- R20. Per Dr Sun's 2026-07-25 assembly correction, the upper equipment must
  form an inspectable chain: official Lite3 `74 x 94 mm` four-M3 payload
  interface -> dual-rail base -> source-model J17A `110 x 86 mm` four-hole
  interface -> J20A/Mid-360/S410, with D435i located on J17A's two 20-degree
  downward camera faces. Both sets of four base holes must remain open. The
  installed industrial PC is a replaceable parameterized placeholder, not a
  reason to copy the published AGX Orin base.
- R21. Per Dr Sun's 2026-07-25 mechanical-reasonableness review, the
  industrial-PC placeholder must not be fused into the printable upper module.
  It must remain a separate print part located by lower side guides and held
  visibly from above by two removable pressure bars whose holes align with the
  slotted saddles. The sensor carrier moves 10 mm forward to provide at least
  10 mm IPC-to-crossbar plan clearance, and the hidden Mid-360 seating bridge
  must preserve at least the 1:4 profile's 0.8 mm equivalent hole-edge
  material. These changes improve inspectable assembly logic without asserting
  a load-rated real bracket.
- R22. Per Dr Sun's 2026-07-25 Jetson-position correction, the visible
  top enclosure must be identified as the official `Interface`, not as a
  published Jetson enclosure. The exterior registration must follow the
  official front/rear views, remain collision-free with the local radar
  mounts and torso, and report the Xavier NX location as unpublished.
  The Venture J17A must not determine or appear in the factory-replica upper
  assembly. No visible NVIDIA development-kit geometry may be exported.
- R23. Per Dr Sun's 2026-07-25 no-bottom-plate correction, the official visual
  track must not contain a spanning deck or carrier plate beneath the
  Interface/radar assembly. The Interface may expose only its local feet and
  the radar only local annular mounting points. Any connectivity required only
  for the printable upper module must be hidden from the official visual track
  and explicitly labeled `print_adaptation`.
- R24. Per Dr Sun's 2026-07-25 depth-camera-fidelity correction, the official
  visual track must use the pinned Intel RealSense `d435.dae` geometry used by
  the official D435i URDF. Hand-authored camera bodies, bezels, apertures, and
  cosmetic lens inserts are forbidden. The printable D435 body must be derived
  from that same official mesh, remain a separate watertight track, and record
  its source hash, rigid source-to-robot transform, reconstruction resolution,
  topology, and surface deviation. Only explicitly declared mounting
  adaptations may be added.
- R25. Historical rejected requirement only. The 2026-07-26 two-piece camera
  bracket, carrier plate, blind-bore receiver yoke, and eight-fastener chain
  proved that a plausible printable mechanism could be modeled and sliced,
  but Dr Sun rejected it because it was not a replica of the factory-visible
  Lite3 LiDAR support. Those shapes are forbidden in current outputs. Their
  geometry and slicer results remain rejection evidence, not acceptance.
- R26. Per Dr Sun's 2026-07-26 replica-identity correction, rebuilding the
  D435i support requires a source-first evidence gate. Every visible support
  face, tab, rail, plate, boss, and fastener must trace to the official Lite3
  LiDAR manual/product imagery or to a source model whose identity with the
  factory part has been demonstrated. The related Venture J17A drawing may
  constrain a candidate only; its 45 mm camera pattern and similar short tabs
  do not prove factory V1.0.7 identity. Long rails, a deep carrier plate,
  receiver yoke, and an eight-screw external assembly are forbidden because no
  primary factory evidence supports them. Geometry hidden in all primary views
  remains `unknown` and must be omitted from the official visual track rather
  than invented. Any necessary print-only support must be hidden, separately
  labeled `print_adaptation`, and absent from official-appearance renders.
  Mesh/slicer success is downstream of, and cannot override, this identity
  gate.
- R27. Historical rejected detour. The requested
  true-Mid-360 model is the official Lite3 Venture FAST-LIVO2 extension, not
  the historical regulatory/launch cylindrical-LiDAR revision. The visible
  sensor stack must use the unchanged official J17A, J20A, S410, and Mid-360
  source geometry. This identity choice does not claim that the same lower
  mounting pattern fits Lite3 Pro without adaptation.
- R28. The D435 must use the pinned real-source visual mesh, seat directly on
  the two short 20-degree J17A faces, and expose only the two source-backed M3
  axes on 45 mm centres. The former 17 mm standoff, long rails, deep carrier
  plate, receiver yoke, and eight-fastener chain are forbidden.
- R29. The white enclosure immediately behind J17A must use the official
  `1T21-BZ20` STEP geometry with its inspected `108 x 96 x 30 mm` envelope.
  It is separate from the rear AGX compute device and from the user's
  different industrial PC. The generic `160 x 92 x 46.8 mm`
  `FACTORY_INTERFACE` placeholder, its reported J17A collision, the resulting
  36 mm forward sensor shift, and the large hidden adapter are rejected.
- R30. The Lite3 Pro conversion may change only the hidden lower
  J17A-to-robot attachment region. It must preserve the source-backed visible
  stack and reach the official Pro `74 x 94 mm` four-M3 pattern without
  entering the user's actual industrial-PC, connector, or cable keep-out
  volumes. No Pro base may be finalized from the old `180 x 76 x 40 mm`
  placeholder; actual IPC CAD or measured envelope, mounting holes, connector
  faces, and cable bend zones are required first.
- R31. Per Dr Sun's 2026-07-26 real-assembly correction, the reviewed BZ20
  appearance candidate is not a mechanical assembly. Its four rendered J17A
  fastener references used the stale X coordinates
  `[72.676, 182.676] mm`, while the current rigid J17A source transform places
  the actual four robot-side M3 axes at
  `X=[82.851997, 192.851997] mm`, `Y=+/-43 mm`, and the lower J17A seating
  plane at `Z=446.0 mm`. Those stale fastener references must be removed from
  all current assembly evidence.
- R32. The lower conversion must be a real two-interface adapter, not a
  floating axis diagram. Its robot-side interface uses the official Pro
  centre `[20, 0] mm`, X-by-Y pattern `74 x 94 mm`, and four top-installed M3
  screws into explicit robot threaded-receiver proxies. Its sensor-side
  interface uses the four actual J17A M3 axes from R31 and four
  underside-installed, recessed M3 screws into the source-model J17A threaded
  holes. Clearance bores, counterbores, bearing faces, receiver envelopes,
  modeled engagement, bottom clearance, and tool paths must be distinct
  inspectable geometry.
- R33. The adapter must have a physically executable order:
  `J17A to adapter while inverted -> adapter/J17A subassembly to Lite3 Pro ->
  robot-side screws from above -> BZ20 or user IPC installed last`.
  No fastener head may become inaccessible before its installation step.
  Candidate screw lengths must be standard nominal lengths and must be checked
  against modeled adapter thickness and source receiver depth. The unpublished
  Lite3 Pro thread depth remains an explicit physical-verification gate rather
  than being invented.
- R34. The adapter may use only two narrow, fixed side trusses with local
  mounting pads and columns. It must leave the centre open, contain no sliding
  rail, pressure clamp, spanning deck, or fake IPC support, and report
  numerical clearance from the official BZ20 source solid and the Lite3 body.
  It is a `print_adaptation` for proving the sensor-to-robot assembly chain.
  Final fit around Dr Sun's different industrial PC remains blocked on the
  real IPC envelope, mounting holes, connector faces, and cable bend zones.
- R35. The real-assembly candidate must deliver a named editable FreeCAD
  assembly, a STEP and STL for the adapter, separate fastener/receiver
  components, and assembled, exploded, underside, and section views. Contact
  and engagement must be validated numerically; visual coincidence alone is
  insufficient.

R18-R35 record successive historical redesigns and rejected detours. Their
non-conflicting source-fidelity rules remain useful, but R36-R43 supersede
every earlier target-identity, visible-part, placement, or base-layout clause
that conflicts with the V1.0.7 manual target. In particular, R22-R23 do not
forbid a clearly labeled related-source J17A comparison candidate, and
R27-R35 do not authorize the rejected FAST-LIVO2/BZ20/AGX assembly.

- R36. Per Dr Sun's 2026-07-26 target-identity correction, the current target
  is the official Lite3 LiDAR V1.0.7 manual assembly, not the Venture
  FAST-LIVO2 extension. The target contains the long `Interface` enclosure and
  must not contain BZ20, the rear AGX support, a fake Jetson, a custom Pro
  truss, long rails, or a spanning lower deck.
- R37. The four losslessly extracted manual assets
  `lite3-lidar-v107-{front-render,side-render,rear-line-art,front-line-art}-original.png`
  are the primary visual registration evidence. Every visible support feature
  in the official-appearance candidate must trace to one of those views or be
  omitted.
- R38. The Mid-360, J20A, and S410 rotations remain rigid, but the rejected
  custom transform that raised the guard to approximately `524 mm` is
  forbidden. The new candidate must re-register the stack to the published
  `496 mm` standing envelope and report the resulting image-estimated
  transform.
- R39. The D435 visual must use the pinned official RealSense mesh. Its
  placement must be registered to the V1.0.7 front and side silhouettes; the
  former synthetic body, 17 mm artificial standoff, long carrier plate,
  receiver yoke, and eight-fastener chain remain forbidden.
- R40. The Interface is an image-derived approximately
  `233 x 92 x 46 mm` enclosure pending physical measurement. Its front and
  underside must reproduce the visible shallow relief. That relief must not be
  enlarged into a hidden collision patch. The official side view independently
  constrains a visible separation between the carrier and Interface, so the
  complete related-source sensor stack may be rigidly re-registered to that
  silhouette; it must not be moved solely to clear a guessed enclosure. The
  local mounting feet must bridge the image-registered gap to the Lite3 top
  deck instead of floating above it. Enclosure dimensions, relief, feet,
  ports, seams, and the sensor-stack registration remain `image_estimate`,
  never `official_nominal`.
- R41. J17A, J20A, and S410 may be used only as
  `related_source_candidate` geometry. Their published FAST-LIVO2 identity
  must remain in the manifest; visual similarity does not promote them to
  factory V1.0.7 CAD.
- R42. The official-appearance baseline must be built in a new evidence
  directory and compared from front, side, rear, and isometric views before
  changing the main printable generator. It must report solid separation
  between Interface, carrier, and local supports, retain no rejected
  FAST-LIVO2 compute parts, and remain unaccepted until Dr Sun visually
  approves it.
- R43. The current evidence manifest must use the hardware-evidence guide's
  explicit roles: `official_visual`, `related_source_candidate`,
  `image_estimate`, and, where needed, a separately named source-derived
  display, collision, or print layer. A placement transform belongs in its own
  declared parameter record and must not be encoded by relabeling an official
  visual mesh as factory assembly CAD.
- R44-R47. Historical rejected requirements only. They authorized four
  profiled J17A supports, four bored Interface feet, two invented fastener
  chains, hidden receiver proxies, and mechanism renders. Dr Sun rejected that
  result on 2026-07-26 because it solved a guessed mounting problem instead of
  reproducing the factory-visible assembly. These requirements must not govern
  the replica track.
- R48. The replacement track is a **visible-geometry replica**. It may contain
  only a part, surface, fastener head, gap, or relative placement that is
  directly visible in a cited official image/line drawing or comes from pinned
  manufacturer component geometry.
- R49. The factory-visible local carrier must be reconstructed as the compact
  thin plate and short block/post arrangement seen below the Mid-360/D435
  assembly. A long rail, profiled body-following support, invented receiver,
  or hidden load path is forbidden in normal replica geometry.
- R50. Interface and sensor placement must be registered from shared landmarks
  across official front, rear, side, and oblique views. No component may be
  translated solely to eliminate collision with an image-estimated enclosure.
- R51. Unpublished underside geometry remains absent or explicitly unresolved.
  Any later feature needed only for printing or attachment must live in a
  separately named `print_adaptation` track and remain excluded from official
  appearance renders until the visible replica is accepted.
- R52. The rejected baseline directory remains immutable rejection evidence.
  The visible replica must be generated in a new directory and must not inherit
  its profiled supports, receiver proxies, invented screw chains, or `35 mm`
  clearance-driven correction.
- R53. Dr Sun rejected the multiview candidate on 2026-07-26. Its rearward
  Interface registration and its lower plate, unequal posts, tilted plate,
  D435 rear support, guard straps, and visible fastener heads are unsupported
  image reconstructions. They are rejection evidence, not the current
  official-replica track.
- R54. Image registration, overall-height matching, collision avoidance, and
  visible separation may describe a visual hypothesis, but none of them may
  establish the factory Interface position, bracket dimensions, mounting-hole
  axes, contact surfaces, or mechanical connection.
- R55. A bracket may be called assembled only when every supported part has a
  source-backed or physically measured contact datum, hole/fastener axis,
  receiver, and onward load path. Missing factory geometry remains
  `unresolved`; it must not be filled with a plausible-looking plate, post,
  rail, support, screw head, or hidden receiver.
- R56. The geometry restart is evidence-gated. It requires either a
  manufacturer-supplied factory LiDAR assembly CAD/drawing or measurements/
  scan data from a physical Lite3 LiDAR edition. Until one of those inputs is
  archived, no new complete upper assembly may be generated.
- R57. The public-source audit completed on 2026-07-26 found separate official
  Lite3 body geometry, Mid-360 and D435 component geometry, and Lite3 Venture
  FAST-LIVO2 extension parts, but no public complete factory Lite3 LiDAR
  assembly CAD, STEP, URDF, hole layout, or assembly transform.
- R58. The main printable generator, print kit, industrial-PC base, and all
  rejected candidate generators remain frozen. Rejected artifacts are retained
  unchanged as negative evidence and must not be presented as current output.
- R59. The 2026-07-27 authorized target is the Lite3 Pro/LiDAR nominal payload
  interface plus the unchanged official Lite3 Venture FAST-LIVO2 sensor stack,
  not the factory V1.0.7 upper assembly.
- R60. The current assembly must omit BZ20, AGX, the user industrial PC, and
  every image-estimated Interface enclosure.
- R61. The fit review must compare the Pro/LiDAR `74 x 94 mm` four-M3 pattern
  with the source J17A `110 x 86 mm` four-hole pattern and must not claim direct
  bolt-on compatibility when the axes do not coincide.
- R62. Any Pro-to-J17A geometry must be a separately named `print_adaptation`
  with an open centre, explicit fastener access, and no modification of the
  official J17A/J20A/S410/Mid-360 geometry.
- R63. Superseded context rule. The user-provided real B-rep assembly replaces
  the local official Lite3 visual derivative in the primary Fusion preview.
  The old visual mesh may remain hidden or appear only in a labeled alignment
  diagnostic.
- R64. Fabrication and real-robot installation remain blocked until the
  physical robot variant, hole spacing, usable thread depth, top-surface datum,
  and cable keep-outs are measured.
- R65. Preserve the downloaded STEP byte-for-byte with its hash, AP214/B-rep
  structure, assembly names, unknown-license boundary, and unresolved
  Exploration-versus-Experience variant identity.
- R66. Hide the separate exploration backload module and add no external
  industrial computer. Manufacturer-native internal robot parts remain
  unchanged and must not be described as a newly installed IPC.
- R67. Do not relabel the downloaded chassis Lite3 Pro. A missing `74 x 94 mm`
  match means the existing yellow adapter is only a nominal Pro placement
  candidate on this body, not a verified bolt-on interface.
- R68. Keep the Fusion document unsaved until Dr Sun reviews the opaque real
  B-rep preview and the variant/interface boundary.
- R69. Current-baseline override. Where R59-R68 conflict with Dr Sun's latest
  instruction, the active Fusion scene contains only the real Lite3 B-rep,
  J17A, J20A, S410, and Mid-360. It contains no adapter/base/bridge, D435, BZ20,
  AGX, industrial PC, factory Interface reconstruction, or visible backload.
- R70. The robot head/front is source/world `+Z`, verified from the physical
  top view of the real assembly. Every occurrence transform must be a proper
  rigid transform with rotation determinant `+1`; reflections and mirrored
  carry-over from mesh placement pipelines are forbidden.
- R71. Every source part in the active scene must remain manufacturer B-rep
  geometry with zero mesh bodies. A visually similar tessellated replacement
  is not an accepted substitute for the current baseline.
- R72. Collision-driven seating correction is limited to a rigid translation
  along a source-backed vertical datum or the J20A 15-degree mount normal.
  Record the pre/post intersection volume and do not change part shape or call
  zero-distance contact a verified mechanical fit.
- R73. The approved numerical seating corrections are: J20A/S410/Mid-360
  upward `11.625 mm`; S410 outward `0.106515 mm` along the mount normal;
  Mid-360 outward `2.0015 mm` along the mount normal; and the complete stack
  upward `0.58375 mm` relative to the robot. Reuse is allowed only with the
  same pinned source files and frame convention.
- R74. D435 remains omitted until the true SolidWorks CAD is translated and
  inspected in a separate clean session. A D435 mesh, hand-authored proxy, or
  crash-prone direct import into the large current scene is forbidden.
- R75. The Fusion document remains unsaved and the task remains uncommitted and
  open until Dr Sun accepts the corrected B-rep screenshots.
- R76. Physical fit, robot-side holes, fasteners, thread depth, connector and
  cable clearance, service access, and load path remain unresolved. The
  current zero-intersection result is appearance/packaging evidence only.
- R77. Dr Sun rejected the first post-reboot longitudinal registration because
  the sensor stack appeared too far rearward relative to the official laser
  version. That transform and its `awaiting_visual_review` label are
  superseded; its screenshots remain rejection evidence only.
- R78. The replacement candidate moves the complete
  J17A/J20A/S410/Mid-360 assembly `30.0 mm` along robot `+Z` toward the head.
  The internal source-part transforms and rotations remain unchanged. This is
  an official-view-constrained visual registration, not a factory dimension.
- R79. Because the Lite3 front cover descends toward the head, the forward
  registration also moves the complete stack `2.4 mm` downward. It must report
  zero robot/J17A intersection and a non-floating numerical contact before
  visual review.
- R80. Dr Sun rejected the forward-30-mm candidate after the physical-top view
  showed that the J17A mounting features do not align with the visible front
  chassis features. Remove its `awaiting_visual_review` state; retain the
  screenshots and transform only as rejected evidence.
- R81. Corrected hole-role audit. The separate J17A `4 x M3`,
  `110 x 86 mm` pattern is not the direct-installation group shown in the
  official video. The installation group is the drawing's four
  `diameter 4.50 mm` through holes with `diameter 8 mm` counterbores; its B-rep
  centres form a `67.88225 x 67.88225 mm` square.
- R82. Treat the result as a source-interface mismatch, not as permission for
  another visual translation. The circled J17A front-row pitch is
  `67.88225 mm`, the circled robot pitch is approximately `65.00172 mm`, and
  their current longitudinal centre offset is `40.92332 mm`. Midpoint
  alignment would still leave each hole approximately `1.440265 mm` off-axis.
  Among `71` plausible robot circular-feature centres, the full fixed-
  orientation pattern still matches only `1/4` centres at `0.5 mm` tolerance.
  The J17A source is declared for `Lite3 Venture only`, while the supplied
  robot is an Exploration parent with an Experience robot child.
- R83. Freeze installation modeling until a matching Lite3 Venture/LiDAR
  chassis/interface CAD or official manufacturer adapter/base CAD is
  available. Do not design a custom base under the current instruction.
- R84. R83 is superseded only for the model-only receiver-proxy revision
  explicitly authorized by Dr Sun on 2026-07-27. It does not authorize a
  fabrication release, real-robot drilling, or a claimed factory Venture
  receiver reconstruction.
- R85. Preserve the official J17A body and its four installation-hole axes.
  Do not scale J17A, move its holes, or reinterpret the circled Experience
  `diameter 2.5 mm` shell features as the Venture receiver pattern.
- R86. Preserve the original Experience top-shell B-rep. The modified preview
  must use a separately named derived shell and must classify every added
  boss, pilot, and receiver feature as
  `interface_receiver_proxy_not_official_cad`.
- R87. The derived receiver axes must coincide with all four J17A
  `67.88225 mm`-square installation axes within `0.01 mm`. The proxy must
  remain one valid B-rep solid, contain zero mesh bodies, and introduce no
  positive J17A or other-body solid intersection.
- R88. Capture the complete external sensor pose before adding timeline
  geometry. J17A, J20A, S410, and Mid-360 must retain determinant-`+1`
  rotations and the reviewed whole-stack `+30.0 mm` front / `-2.4 mm`
  vertical correction.
- R89. Receiver outer diameter, pilot diameter, hidden depth, thread form,
  material, strength, tool access, and load path remain explicit proxy or
  unresolved fields. Numerical axis coincidence does not promote the derived
  shell into official factory CAD or fit-validated hardware.
- R90. Keep the Fusion document unsaved until Dr Sun visually accepts this
  receiver-proxy direction.
- R91. Dr Sun rejected R84-R90's receiver-proxy direction on 2026-07-27.
  Preserve Rev A as hidden negative evidence; it is not current geometry and
  its checked internal metrics cannot satisfy the replacement revision.
- R92. The replacement target is the two front shallow chassis-hole axes:
  `diameter 2.5 mm` central openings inside shallow `diameter 8.0 mm`
  cylindrical recesses at `64.999999659 mm` centre pitch.
- R93. Preserve the manufacturer J17A source body byte-for-byte and hide it in
  the preview. All authorized hole edits must be made in a separately named
  derived component classified
  `user_authorized_model_correction_not_official_cad`.
- R94. Fill and relocate only the two original J17A front stepped holes onto
  the exact chassis target axes. Preserve their `diameter 4.5 mm` through and
  `diameter 8.0 mm` counterbore dimensions. Do not change the rear J17A pair.
- R95. Move J17A, J20A, S410, and Mid-360 as one rigid stack by
  `[-0.151878610, -3.128370000, +40.923512315] mm` in world `[X, Y, Z]`.
  Preserve all source-part rotations with determinant `+1`, and capture the
  pose before adding timeline geometry.
- R96. The derived J17A must be one valid solid B-rep with zero mesh bodies.
  Both adapted axes must match the chassis axes within `0.01 mm`.
- R97. Exact checks must find no positive solid intersection between the robot,
  adapted J17A, J20A, S410, and Mid-360. Surface contact is allowed only as
  contact/packaging evidence.
- R98. Do not infer a real screw contract from geometric coaxiality. The
  `diameter 8 mm` J17A counterbore is the head seat, the `diameter 4.5 mm`
  J17A bore is shaft clearance, and the `diameter 2.5 mm` chassis opening is
  the receiving/pilot feature; these diameters are not required to be equal.
  Preserve that intended relationship. Exact thread identity, engagement
  depth, material, torque, anti-rotation, service access, and load path remain
  unresolved. The unchanged rear pair is not an installed interface.
- R99. Keep the Fusion document unsaved until Dr Sun visually accepts the
  Rev B hole alignment and full-stack position. After acceptance, freeze a
  complete local F3D archive and a separately re-importable adapted-J17A STEP
  before any further modeling.

## Acceptance Criteria

- [x] AC1. The official source hashes remain unchanged and the corrected work
  is isolated from the rejected visual draft.
- [x] AC2. The 1:1 master uses the official high-resolution chassis/leg
  geometry and records its reconstruction resolution and surface deviation.
- [x] AC3. Every delivered STL is manifold, closed, consistently oriented, and
  free of degenerate faces.
- [x] AC4. The 1:1 assembled reference is ground-aligned. Length and width
  remain within the declared official-body tolerance; the S410-equipped
  assembled height is checked separately against an explicitly non-official
  `525 mm` image-estimated variant target rather than relabeling the factory
  `496 mm` LiDAR-version height.
- [ ] AC5. Superseded historical FAST-LIVO2 appearance criterion; it cannot
  accept the current V1.0.7 official-LiDAR target.
- [x] AC6. The Mid-360/J17A/J20A/S410 identities and D435i nominal envelope and
  visual mesh are tied to official source files; every estimated placement or
  surrounding Lite3 dimension is explicitly marked `image_estimate`, and no
  complete factory V1.0.7 assembly identity is asserted.
- [x] AC7. The 1:4 kit fits within a documented desktop-printer build volume
  and meets the declared minimum feature and clearance rules.
- [x] AC8. The separate print parts have assembly keys, pins, or fasteners and an
  unambiguous assembly map.
- [x] AC9. A real slicer accepts every declared print part and produces a
  non-empty toolpath estimate without geometry-repair errors.
- [ ] AC10. The second clean build reproduces parameters, part names, geometry
  metrics, and deterministic hashes where the format permits. This must be
  rerun after the latest official-D435 correction.
- [x] AC11. Comparison renders show the official evidence, repaired master,
  print kit, part seams, and any deliberately thickened print features.
- [ ] AC12. Dr Sun visually accepts the corrected replica before it is
  committed or the task is closed.
- [x] AC13. The redesigned upper module reports zero Mid-360/J20A and
  Mid-360/S410 Boolean overlap, positive hidden-bridge engagement with both
  printable bodies, one connected upper-module solid, preserved mounting-hole
  clearance, and non-zero connector-to-guard clearance.
- [x] AC14. Historical dual-rail revision only: the rebuilt upper module had no
  solid base below the declared industrial-PC footprint, preserved both the
  open Lite3 `74 x 94 mm` four-hole M3 pattern and the J17A `110 x 86 mm`
  crossbar holes, reported positive IPC plan clearances, and mounted the
  separate D435i part to the official J17A
  camera interface rather than to the torso. This criterion is superseded for
  current outputs by AC17-AC19.
- [ ] AC15. The primary full-robot reference uses the smooth official
  high-resolution Lite3 exterior and is visually recognizable as Lite3. The
  printable body is separately labeled, remains manifold and sliceable after
  any smoothing, and is shown in an honest print-specific diagnostic rather
  than being substituted for the official CAD appearance.
- [x] AC16. Historical IPC-clamp revision only: the industrial-PC placeholder
  and its two top pressure bars were separate printable parts, the IPC had
  numerical-zero solid intersection with the upper module and pressure bars,
  both pressure bars remained separate closed components, IPC-to-crossbar
  clearance was at least 10 mm, the nearest Lite3/J17A hole ligament and
  hidden-bridge hole-edge material met the
  scale-aware minimum-feature rule, and all 19 print STLs pass geometry and
  real-slicer validation. Those parts are forbidden in current outputs by
  R22 and are superseded by AC17-AC19.
- [ ] AC17. Superseded historical Interface criterion. The generic
  `FACTORY_INTERFACE` identity was rejected after the official BZ20 and
  separate rear-AGX relationship was verified; this criterion cannot be
  checked for the current target.
- [ ] AC18. The replacement visual-reference assembly and primary renders
  contain no `UPPER_DECK_INTERFACE`, `PAYLOAD_BASE`, invented spanning
  LiDAR-carrier plate, or fake Jetson. They show only the unchanged source
  J17A stack and separate official BZ20 shell. Dr Sun must visually accept the
  silhouette.
- [x] AC19. The visual-reference GLB contains `D435I_CAMERA` from the pinned
  official RealSense mesh and excludes `FRONT_CAMERA_BAR`,
  `D435I_FRONT_BEZEL`, and `CAMERA_LENSES`. The source-derived D435 print
  master is one closed, consistently wound component at the declared 0.35 mm
  reconstruction pitch, with master-to-source p99 deviation below 0.5 mm.
  The build report records the source hash, source bounds, rigid transform, and
  camera collision evidence. Because the official mesh is open, its physical
  separation must use a declared surface-clearance method, while exact Boolean
  collision volume must use the source-derived watertight print proxy; the two
  methods must not be conflated.
- [ ] AC20. Rejected historical criterion. The two-piece
  `CAMERA_MOUNT_BRACKET`, `CAMERA_CARRIER_PLATE`,
  `CAMERA_RECEIVER_YOKE`, and eight-fastener design passed 125 geometry checks
  and 20/20 slicer checks, but failed the replica-identity review. It is not an
  accepted camera mount and this criterion cannot be checked.
- [ ] AC21. The camera-mount evidence matrix separates direct factory-visible
  facts, related-source candidates, negative evidence, and hidden unknowns.
  Dr Sun must accept that evidence boundary before replacement geometry is
  rebuilt. The replacement official-appearance render must contain none of the
  rejected long rails, deep carrier plate, receiver yoke, or invented
  eight-screw assembly; every visible new feature must cite its source.
- [ ] AC22. Superseded historical criterion. The full-standing appearance comparison uses the official Lite3
  exterior plus unchanged official FAST-LIVO2 source parts, shows the real
  D435 directly on J17A, and contains none of the rejected rails, carrier
  plate, receiver yoke, fake Jetson, or large hidden adapter. Dr Sun must
  visually accept the comparison.
- [x] AC23. The corrected BZ20 layout uses the unchanged official
  `108 x 96 x 30 mm` source solid, reports its image-estimated rigid transform,
  reports `0.0 mm3` BZ20/J17A intersection, and preserves positive BZ20- and
  D435-to-torso AABB clearances.
- [x] AC24. The rejected generic Interface/36 mm shift/hidden-adapter
  directories are explicitly marked superseded, and the main printable
  generator remains unchanged while the actual industrial-PC geometry is
  unavailable.
- [x] AC25. The MakerWorld 30-degree, `45 x 80 mm` bracket is recorded only as
  a nonofficial secondary reference with its unavailable raw-source boundary;
  none of its conflicting dimensions or eight-screw layout is promoted into
  the Lite3 replica.
- [ ] AC26. The four sensor-side screw axes coincide with the actual
  source-model J17A M3 void axes within `0.05 mm`; the stale
  `[72.676, 182.676] mm` references are absent. All four robot-side axes
  coincide with the official Pro `[20, 0] mm` centred `74 x 94 mm` pattern.
- [ ] AC27. The adapter has positive, zero-gap seating area at all four
  robot-side pads and all four J17A columns; it has one closed connected solid,
  an open centre, and no undeclared solid overlap with J17A, BZ20, or the
  source-derived Lite3 torso collision proxy.
- [ ] AC28. Four robot-side and four J17A-side screws each pass through their
  declared clearance bore and enter their declared receiver. The report records
  nominal screw length, bearing plane, adapter traversal, receiver engagement,
  remaining bottom clearance, head accessibility, and installation step for
  every fastener group.
- [ ] AC29. The real-assembly candidate exports a readable `.FCStd`, adapter
  `.STEP` and `.STL`, separate screw/receiver parts, and assembled, exploded,
  underside, and section renders. Dr Sun must visually accept this candidate
  before the main replica generator is changed.
- [ ] AC30. Rejected multiview criterion. The candidate included the requested
  long Interface, forward/downward Mid-360, guard, and D435 silhouette, but its
  Interface placement and mounting geometry were unsupported; it cannot accept
  the V1.0.7 identity.
- [ ] AC31. Historical metric only. The rejected candidate reached
  `496.003681 mm`, but matching the published overall height does not validate
  its Interface position, bracket geometry, or assembly.
- [ ] AC32. Historical metric only. The rejected candidate reported an `11 mm`
  visible Interface/carrier separation, but that image-estimated separation
  does not establish either part's factory transform or mechanical connection.
- [ ] AC33. Historical artifact only. Comparison sheets exist for the rejected
  candidate, but their existence is not replica acceptance.
- [ ] AC34. Superseded manifest criterion. The manifest must now identify the
  entire multiview candidate as rejected and must not call its invented
  surrounding geometry a current replica.
- [ ] AC35. No longer has a candidate to review. A future evidence-backed
  V1.0.7 baseline must be visually accepted before the main printable
  generator, print kit, or industrial-PC adaptation is changed.
- [x] AC36-AC38. Historical check evidence exists for the rejected engineered
  adaptation. These checks are explicitly non-accepting and do not count
  toward replica completion.
- [x] AC39. Dr Sun rejected the profiled-support/receiver-proxy candidate as an
  adaptation rather than a replica on 2026-07-26.
- [ ] AC40. Every visible mount feature in the replacement candidate maps to a
  cited official view or pinned manufacturer component; the evidence matrix
  contains no unsupported hidden bracket geometry.
- [ ] AC41. Official-view overlays confirm the compact thin carrier, short
  blocks/posts, Mid-360 down-tilt, D435 placement, and separate rear Interface
  relationship without a clearance-driven transform.
- [ ] AC42. Superseded by the second rejection. Although the renders omit
  earlier profiled supports and receiver proxies, the replacement plate,
  posts, camera support, guard straps, and fastener heads are themselves
  unsupported reconstructions.
- [ ] AC43. Dr Sun visually accepts the visible factory replica before any
  printable attachment base or user industrial-PC adaptation is designed.
- [x] AC44. The multiview candidate status and manifest record Dr Sun's
  2026-07-26 rejection, the unsupported Interface translation, the invented
  bracket/connection geometry, and the non-print-ready claim boundary.
- [x] AC45. The public-source audit distinguishes the official Lite3 body,
  factory LiDAR manual imagery, independent Mid-360/D435 component geometry,
  and the separate Venture FAST-LIVO2 extension; it records that no complete
  public factory LiDAR assembly CAD was found.
- [ ] AC46. A manufacturer factory-LiDAR assembly CAD/drawing or a physical
  measurement/scan package supplies the Interface datum, bracket contact
  surfaces, hole axes, fastener receivers, and assembly transform before
  geometry work resumes.
- [x] AC47. Historical, superseded Fusion review evidence showed the local
  Lite3 visual model, J17A/J20A/S410/Mid-360/D435, and a separately identified
  Pro-to-J17A adapter. R69 forbids reusing that scene as the current baseline.
- [x] AC48. The review records the `74 x 94 mm` versus `110 x 86 mm` pattern
  mismatch and distinguishes nominal CAD alignment from physical fit.
- [ ] AC49. The adapter is one connected valid solid with eight open fastener
  paths, accessible installation order, and no undeclared collision with the
  source J17A or declared Lite3 collision proxy.
- [ ] AC50. Dr Sun visually accepts the no-industrial-PC sensor-stack layout
  before a Fusion document, printable package, or real-hardware procedure is
  finalized.
- [x] AC51. The downloaded STEP is preserved byte-for-byte and verified as a
  real AP214 B-rep assembly rather than a mesh-only model.
- [x] AC52. Historical, superseded preview evidence used the real robot base,
  hid the separate exploration backload, and recorded the old adapter/body
  correction. The adapter and `0.2 mm` correction are absent from the current
  R69-R76 baseline.
- [ ] AC53. Dr Sun accepts the real-B-rep appearance and decides whether this
  Exploration/Experience chassis should replace the nominal Pro body target
  despite the absent `74 x 94 mm` pattern.
- [x] AC54. The current Fusion scene contains the full opaque Lite3 source
  assembly with `288` visible robot B-rep proxy bodies and zero robot mesh
  bodies. J17A, J20A, S410, and Mid-360 each use their pinned manufacturer CAD
  and report zero mesh bodies.
- [x] AC55. The physical-top view establishes source/world `+Z` as the head.
  J17A and every dependent sensor occurrence use determinant-`+1` proper
  rotations; the rejected mirrored J17A transform is absent.
- [x] AC56. Exact solid checks report `0 mm3` intersection for robot/J17A,
  J17A/J20A, J20A/S410, J20A/Mid-360, and S410/Mid-360. J17A/J20A minimum
  distance is `0 mm`; J20A/S410 is within numerical contact at
  `0.000000097 mm`.
- [x] AC57. The current scene contains no custom/yellow adapter or base, no
  D435, no BZ20, no AGX, no added industrial PC, no factory Interface
  reconstruction, and no visible Exploration backload.
- [x] AC58. Historical, rejected review evidence recorded the first post-reboot
  isometric, side, and physical-top views. Dr Sun rejected that registration
  because the sensor stack appeared too far rearward.
- [ ] AC59. Dr Sun visually accepts the corrected front direction, sensor
  orientation, and basic placement before the Fusion document is saved or any
  D435/bracket work resumes.
- [x] AC60. The complete source sensor assembly is rigidly translated
  `30.0 mm` toward robot `+Z` and `2.4 mm` downward without changing any
  internal source-part rotation or shape. All four external occurrence
  rotations retain determinant `+1`.
- [x] AC61. The forward candidate reports `0 mm3` intersection for
  robot/J17A, J17A/J20A, J20A/S410, J20A/Mid-360, and S410/Mid-360.
  Robot/J17A minimum distance is `0.006602556 mm`, treated as numerical
  contact rather than a verified fastener fit.
- [x] AC62. Three `1800 x 1200` screenshots record the forward-30-mm
  isometric, side, and physical-top views in a new
  evidence directory. Human review subsequently rejected this candidate.
- [x] AC63. The rejected directory contains a machine-readable mount-interface
  audit that explicitly corrects the earlier hole-group error. It records the
  J17A `67.88225 mm` square installation pattern, `71` robot candidate centres,
  circled-row pitches of `67.88225 mm` versus `65.00172 mm`, `0.5 mm`
  tolerance, and best result of `1/4` aligned centres.
- [x] AC64. Candidate status, validation report, design, implementation notes,
  and task state all classify the forward-30-mm transform as rejected for
  source-interface mismatch rather than current placement evidence.
- [ ] AC65. A matching Lite3 Venture/LiDAR chassis/interface CAD or official
  manufacturer adapter/base CAD is archived and its source identity is
  verified before installation modeling resumes.
- [ ] AC66. Superseded historical Rev A metric. Its derived shell was a valid
  solid and its invented four receivers were internally coaxial, but Dr Sun
  rejected the underlying interface interpretation.
- [ ] AC67. Superseded historical Rev A metric. Its zero-collision result does
  not accept the rejected receiver-proxy geometry.
- [ ] AC68. Rejected by Dr Sun. The Rev A receiver-proxy views are retained
  only as negative evidence.
- [x] AC69. The robot target pair is measured from the source B-rep as
  `64.999999659 mm` pitch with `diameter 2.5 mm` central openings and shallow
  `diameter 8.0 mm` recesses. Both adapted J17A axes match the target axes with
  maximum line residual `3.0838e-13 mm`.
- [x] AC70. The adapted J17A is one solid B-rep with one lump, one shell,
  `141` faces, `32.140771157 cm3` volume, and zero mesh bodies. The source J17A
  remains unchanged, preserved, and hidden; only the derived front pair moved.
- [x] AC71. Exact checks report zero positive intersection among the robot and
  all four sensor bodies, determinant `+1` for every occurrence rotation, a
  captured `Front_2x_Shallow_Holes_65mm_Aligned_Contact_Pose`, and no pending
  snapshot. Five `1800 x 1200` screenshots are hashed in the evidence report.
- [x] AC72. Dr Sun authorized execution of the Rev B coaxial front-pair model
  on 2026-07-27. The accepted state is frozen as a `126210700`-byte complete
  F3D archive and a `267046`-byte AP214 adapted-J17A STEP. The STEP cleanly
  imports as one valid closed solid with `141` faces. This acceptance does not
  authorize physical screw/receiver design or fabrication.

## Out Of Scope

- A working or articulated quadruped robot.
- Replacement shells or a load-rated, fit-validated real-robot payload bracket.
- Reverse engineering hidden electronics, wiring, bearings, fasteners,
  materials, or load paths.
- Claiming exact factory geometry where only images are public.
- 1:1 manufacturing or printing until a printer, material, build volume, and
  physical-purpose review are supplied.
