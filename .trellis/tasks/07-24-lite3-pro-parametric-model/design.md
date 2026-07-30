# Design: Lite3 LiDAR High-Fidelity Printable Replica

## Current-Pro Revision Design Correction (2026-07-29)

The purchased current Pro is a new robot-interface target.  The legacy
V1.0.7 `74 x 94 mm` rectangle, the Venture J17A robot-side interface, and the
Experience-derived V1 axes are three different evidence tracks; none may be
silently substituted for the physical current-Pro receiver set.

### Split architecture

The design is split at a serviceable interface:

1. **Reusable upper sensor module.**  Preserve the reviewed Mid-360, D435i,
   S410, J17A/J20A-derived geometry, source sensor axes, and off-robot assembly
   order.  This is not proof of robot fit.
2. **Current-Pro lower adapter.**  A new, separately named print adaptation
   will connect the reusable module to measured receivers on Dr Sun's robot.
   It remains replaceable and must not be fused to the upper module before the
   physical fit review.

The lower adapter must place the upper module in the vacant forward region
shown by the user photo and current official LiDAR visual.  It must not pass
under, cut, move, or visually hide the long compute enclosure to compensate for
unknown geometry.  The enclosure, its feet, front edge, ventilation, cable,
and driver access form one measured keep-out.

### Frozen and open parameters

Frozen source-backed upper-module parameters include the official sensor
models and their internal mounting axes.  Open current-Pro parameters are:

- every usable robot receiver X/Y coordinate and seating Z;
- thread designation, usable depth, recess, and candidate screw length;
- compute-enclosure front edge, width, height, feet, cable, ventilation, and
  service corridor;
- upper-module forward offset and adapter elevation;
- printable rail/web width, height, fillets, and minimum wall after the fit
  envelope is known.

The current official product image is permitted to establish only that the
sensor module belongs ahead of the enclosure.  It cannot supply any of these
numeric parameters.

### Physical measurement scaffold and compact layout (2026-07-30)

Ten physical tape-measure photographs now define a local, uncertainty-bearing
coordinate scaffold.  The midpoint of the two front small-hole axes is
`[0, 0, 0]`; their lateral coordinates are `Y=+/-32.5 mm`.  The visible centre
candidate is approximately `[-75, 0, 0] mm`, the nose edge is `X=+20 mm`, and
the nominal compute enclosure begins at `X=-100 mm`.  Its photo envelope is
approximately `200 x 100 x 50 mm`; the collision proxy expands this to
`X=[-305,-96]`, `Y=[-54,54]`, and `Z=[0,54] mm` in the early photo-only
revision.  Scan Rev B supersedes the lateral collision bounds with
`Y=[-57,+60] mm` and supplies the two-recess nominal polygon described below.

This scaffold deliberately separates **visible axes** from **receivers**.  The
front pair has a two-view photo-measured pitch, but its thread and usable depth
are null.  The centre feature is only a visible candidate axis; its mounting
role, thread, depth, material, and onward load path are unknown.  Therefore the
current accepted receiver count is zero.

The retained V1/J17A-derived upper carrier is approximately `153.7 mm` long,
while the measured nose-to-expanded-enclosure zone is approximately `116 mm`.
Direct reuse would require about `37.7 mm` of overhang or enclosure overlap.
The current design direction is instead a compact `110 x 115 mm` planning
surface with the S410/Mid-360 source geometry centred at approximately
`X=-37.5 mm` and the D435i official `90 x 25 x 25 mm` envelope at the front.
The source-geometry layout leaves `6.0 mm` to the expanded enclosure and
`2.5 mm` to the measured nose edge.

The planning surface has zero thickness and no holes.  It is a packaging test,
not the lower adapter.  Receiver bores, structural ribs, cable routing, optical
directions, tool corridors, material, and print orientation follow only after
human placement review and the physical receiver contract.

### Physical scan reference and coordinate correction (2026-07-30)

The user-provided GLB is a textured room scan, not an isolated CAD model.  Its
raw bounds include the floor and unrelated objects, so whole-scene PCA is not a
valid robot orientation method.  The scan pipeline first crops the physical
Lite3 region, then fits the dense flat top of the long compute enclosure.  The
enclosure fit gives a robot long-axis yaw of `160.777014948 deg`; corrected
physical photographs identify the rounded empty nose as the positive front
end.  The resulting right-handed scan frame is `+X front`, `+Y left`, and
`+Z up`.

This scan frame is temporary and intentionally does **not** replace the R127
mount frame.  Its X/Y origin is the compute-enclosure top centroid because that
surface is dense and stable in the scan.  The final lower-adapter frame still
requires translation to the front small-hole midpoint after those receiver
axes are confirmed.  Keeping the two frames distinct prevents a convenient
scan datum from becoming a false fastener datum.

The 0.1-to-99.9-percentile enclosure-top span is approximately
`199.585 x 108.618 mm`, which corroborates metre-scaled GLB coordinates and the
physical enclosure measurements.  The oriented point reference, textured OBJ,
and 3 mm clustered STL support visual and collision work only.  Scan texture,
mesh noise, and occlusion are not precise enough to authorize small-hole
centres, diameters, threads, or structural use.

The compute enclosure's nominal footprint is also non-rectangular.  At its
front end, two side recesses begin near mount-frame `X=-130 mm` and run roughly
`30 mm` to the `X=-100 mm` front face.  The left exterior steps from about
`Y=+55.879` to `+44 mm`; the right exterior steps from about `Y=-52.739` to
`-42 mm`.  Revision B therefore uses an eight-vertex concave footprint for the
nominal visual B-rep.  Its corner radii remain simplified.  Collision screening
continues to use the larger rectangular `X=[-305,-96]`, `Y=[-57,+60]`,
`Z=[0,54] mm` keep-out; the two visual recesses do not grant usable volume.

All top photographs are also stored in a consistent `front -> right`
orientation for comparison.  They remain perspective images, so no dimension
is upgraded merely because a photograph was rotated.

### Scan-registered sensor review assemblies (2026-07-30)

The source-backed J20A/MID-360/S410 transforms are unchanged in upper-assembly
Rev B.  Only the chassis context changes: the scan-derived two-recess nominal
enclosure is visible for review and the larger rectangular Rev B keep-out is
used for collision screening.  The upper assembly remains `5.0 mm` ahead of
that conservative keep-out, with zero positive-volume intersection among the
three source components or against the keep-out.  This preserves the reusable
upper module without treating the enclosure recesses as mounting pockets.

The D435i support remains a separate camera-first study.  Its rear bridge
preserves two 3.4 mm clearances on the official 45 mm M3 axes; two side posts
and future lower-union pads form one connected solid.  Moving the post front
edge back to `X=11.5 mm` removes the former positive-volume camera penetration.
At the current review pose the nominal camera envelope is 20 degrees
downward, clears the source upper assembly by approximately `7.781 mm`, and
extends approximately `24.198 mm` beyond the measured nose edge.  That
overhang is a visible placement question, not an accepted design result.

The headless Rev B document uses the official D435i datasheet envelope for
collision checks.  The detailed manufacturer B-rep remains preserved in the
Fusion review archive and must be used in the final appearance/animation
track.  The two lower pads have no bores and establish no Lite3 receiver,
thread, usable depth, screw length, or structural load path.

### Receiver measurement gate (2026-07-30)

The lower-adapter gate now uses the same Rev B enclosure contract as the upper
review: the scan-derived eight-vertex footprint is nominal display geometry,
while `X=[-305,-96]`, `Y=[-57,+60]`, `Z=[0,54] mm` remains the collision
authority.  Neither visible recess is treated as an attachment pocket or as
free cable volume.

The physical request is split into four callouts.  A and B are the two front
axes at `Y=+/-32.5 mm` and must be checked independently for thread, usable
depth, counterbore/recess, material, insert, and onward load path.  C is the
centre feature at approximately `X=-75 mm`; its first question is whether it
is structural at all.  D covers enclosure feet, ventilation, inserted plugs,
cable bends, cover service, and tool corridors.  Until A/B/C/D are reviewed,
the ledger records zero accepted receivers and no printable lower-adapter
geometry.

### Rejection propagation

The V1 carrier's upper topology, sensor-axis checks, collision methodology,
and animation implementation are retained as reusable or negative evidence.
Its robot-side attachment is rejected: the animated rows are `65.0 mm` and
`105.004442 mm` wide, separated by `133.998676 mm`, on planes `5.0 mm` apart.
The V1 `robot_rear_pair_pitch` field also contains the `67.882251 mm` web width
rather than the animated rear screw pitch.  These values may not seed the
current-Pro lower adapter.

The design remains a measurement-ready architecture, not a fabrication-ready
part, until the current physical receiver and enclosure ledger is complete.

## Superseded Physical-Lite3 Fusion Adapter V1 Design (2026-07-29)

This design records the archived V1 upper-module work. The current-Pro lower
interface is governed by the revision correction above.

The purchased robot is the design target.  Its existing long white Interface
box remains an external keep-out, while the new carrier occupies only the
front top-deck region shown free in the user photograph.  The robot STEP,
photo, manufacturer bracket STEP files, and sensor CAD remain separate evidence
tracks so a convenient assembly does not become a false factory claim.

### Mechanical architecture

The printable part is
`LITE3_MID360_D435I_MONOLITHIC_CARRIER_V1_NOT_OFFICIAL_CAD`.  It derives from
the exterior and hole geometry of J17A and J20A and joins their load paths with
four internal fusion regions plus a continuous rear web.  The rear web spans
the two former rear layer-connection regions; front fusion regions preserve the
original lower/upper source envelopes.  Manufacturer J17A and J20A occurrences
remain unchanged and hidden in the review assembly.

The carrier intentionally retains these interfaces:

- the original robot-side 65 mm front pair and original rear support features;
- two 3.2 mm J17A camera clearance holes on 45 mm centres;
- four J20A Mid-360 clearances on the 48 x 36 mm source pattern;
- four J20A M5 guard receivers aligned to S410's 5.2 mm clearances.

D435i remains a separate official B-rep and seats directly on J17A.  Mid-360
remains a separate official B-rep and seats on J20A.  S410 remains a separate
manufacturer guard.  The monolithic carrier removes the J17A-to-J20A layer
fasteners only; it does not remove the sensor, guard, or robot fasteners.

### Parameters and evidence boundary

The source generator exposes rear-web thickness/depth, front fusion diameter,
minimum wall, Interface keep-out clearance, robot front/rear pitch, spacer
height, and candidate screw lengths.  Parameters recovered from B-rep geometry
are locked separately from physical-only values.  The default robot-side M3x8
front screws, M3x12 rear screws, and rear spacers are display candidates until
the purchased robot's thread and depth are measured.

The Interface envelope is deliberately translucent in diagnostic renders and
opaque white in the final context render.  It is named
`PHYSICAL_INTERFACE_KEEP_OUT_PENDING_MEASUREMENT`, excluded from exports, and
must never be confused with the earlier rejected 160/233 mm reconstructed box.

### Human-executable assembly

1. Off-robot, seat D435i on bare carrier/J17A and install its two M3 screws from
   the bracket side into the camera threads.
2. Off-robot, seat Mid-360 on the J20A portion and install four underside M3
   screws in a diagonal sequence.
3. Seat S410 on its four J20A axes and install its four screws independently in
   a cross pattern.
4. Place any measured rear locating spacers on Lite3, then bring the complete
   sensor carrier to the robot along the deck normal without passing through
   the Interface envelope.
5. Start the four robot-side screws loosely, verify seating and cable freedom,
   then cross-tighten.  Actual torque is absent until manufacturer or measured
   hardware evidence exists.

The animation uses close-ups at each active axis, ghosting only during hidden
path diagnosis, and finishes with a fully opaque global robot view.

### Preliminary structural intent

The FDM target is carbon-fibre nylon for the moving-robot candidate; PETG may
be used only for a dimensional prototype.  The rear web and front fusion
regions are sized for a conservative analytical check using declared payload,
acceleration, safety factor, and printed-material allowable stress.  This check
is a screening calculation, not a fatigue/impact certification.  The release
gate remains a printed coupon, stationary proof load, fastener-retention test,
and low-speed tethered trial after dimensional fit is confirmed.

## Current J17A Front-Pair Adaptation Design (2026-07-27)

Human review established the two front shallow chassis holes as the intended
screw-axis targets. The current design therefore adapts the bracket-side
front-pair pitch instead of adding an invented chassis receiver pattern.

The manufacturer J17A stays unchanged and hidden. A derived component fills
only the two original front stepped holes and cuts the same
`diameter 4.5 mm` through / `diameter 8.0 mm` counterbore geometry on the
robot's two `64.999999659 mm`-pitch axes. The rear J17A pair is untouched. This
keeps the edit local, reversible, and explicit as nonofficial geometry.

The sensor stack moves as one rigid group by
`[-0.151878610, -3.128370000, +40.923512315] mm` in world `[X, Y, Z]`.
The robot axes themselves define the new cuts; a visual midpoint or global
scale factor does not. The rejected Rev A chassis proxy is hidden but retained
as negative evidence.

After visual authorization, the preservation design uses two complementary
local outputs: an F3D archive for the complete editable assembly and an AP214
STEP for the single adapted J17A component. The active Fusion document need
not be promoted into cloud storage; local project files remain the source of
truth.

Acceptance at this stage means two-axis coaxiality, one valid B-rep, proper
rigid transforms, numerical contact, zero positive collision, and visual
approval of the resulting position. It does not mean a complete fastener
contract. The `diameter 8 mm` J17A recess seats the screw head, the
`diameter 4.5 mm` J17A bore clears the shaft, and the `diameter 2.5 mm`
chassis opening receives the threaded end. Their unequal diameters are an
expected clearance-to-receiver relationship, not incompatibility. Exact
thread identity, engagement, torque, anti-rotation, and load path remain
unresolved; the unchanged rear pair is not claimed as installed.

## Rejected Receiver-Proxy Design (2026-07-27)

Dr Sun authorized a model correction after the interface mismatch was
isolated. Frame-level review of the official installation video confirms the
presenter points to the four large J17A counterbored holes, not the outer tabs
or the two circled Experience-body shell features.

The selected correction keeps the official J17A source body unchanged. The
original Experience top shell is preserved and hidden; a derived B-rep shell
copy adds four hidden `8 mm` outside-diameter, `6 mm`-deep receiver bosses with
`3.3 mm` pilot envelopes on the unchanged J17A `67.88225 mm` square axes.
Those dimensions are an explicit interface proxy, not recovered Venture
manufacturing geometry.

The receiver proxy is integrated into the derived shell rather than exposed as
a new visible base plate. This preserves the requested basic sensor
appearance, avoids scaling the manufacturer carrier, and keeps the original
source body recoverable. The Fusion assembly captures the reviewed
forward/down pose before the proxy component is added; this prevents Fusion
from reverting uncaptured occurrence positions when a new timeline feature is
created.

Acceptance at this stage means exact four-axis registration, one valid B-rep
solid, zero new collision, and a visually coherent basic model. It does not
mean verified thread depth, material, strength, service procedure, or a safe
physical installation. Dr Sun rejected this design because the invented
four-receiver chassis proxy did not make the actual two front screw axes
usable. It is superseded by Rev B.

## Superseded Interface Gate (2026-07-27)

The forward-30-mm Fusion candidate is rejected. The physical-top review exposed
that the J17A robot-side features do not align with the visible front chassis
features. The first audit mistakenly selected J17A's separate `4 x M3`,
`110 x 86 mm` pattern. The official drawing and installation video instead
identify the direct-installation group as four `diameter 4.50 mm` through
holes with `diameter 8 mm` counterbores. Fusion-native B-rep inspection
resolves those centres as a `67.88225 mm` square.

The circled J17A front-row pitch is `67.88225 mm`; the circled Experience-body
row is approximately `65.00172 mm` and lies `40.92332 mm` farther toward
robot `+Z` in the current pose. A midpoint-aligned translation would still
leave each hole approximately `1.440265 mm` off-axis. Among `71` plausible
robot circular-feature centres, the complete fixed-orientation pattern matches
only `1/4` centres at `0.5 mm` tolerance.

This is a source-interface mismatch, not a remaining visual-registration
problem. The J17A source is explicitly declared for Lite3 Venture, while the
supplied robot source is an Exploration top-level assembly with an Experience
robot child. Zero collision and numerical surface contact cannot overcome the
missing mounting correspondence.

The Fusion document remains unsaved and unchanged as rejection evidence.
Installation modeling is frozen until matching Lite3 Venture/LiDAR
chassis/interface CAD or an official manufacturer adapter/base CAD is
available. Another translation and a new custom base are both forbidden under
that historical instruction. The current two-front-hole model correction is
the explicit, narrower override; it still does not authorize a new base.

## Rejected Target Override (2026-07-27, Post-Reboot)

The rejected target was the smallest source-CAD baseline: the full opaque
user-provided Lite3 B-rep plus manufacturer J17A, J20A, S410, and Livox
Mid-360 B-reps. It is a visual/packaging candidate, not factory assembly CAD
and not a fit-validated mount.

The scene contains no adapter, custom base, hidden bridge, D435, BZ20, AGX,
external industrial PC, or factory Interface reconstruction. The separate
Exploration backload branch is hidden. The visible robot child remains
identified as `Lite3体验版总装.STEP`, not Lite3 Pro.

The physical-top view of the real chassis establishes source/world `+Z` as the
robot head/front. J17A maps its source `+X` into robot `+Z`, source `+Y` into
robot `+X`, and source `+Z` into robot `+Y`:

```text
R_j17a = [[0, 1, 0],
          [0, 0, 1],
          [1, 0, 0]]
```

This proper rotation has determinant `+1`. The older mesh-style transform
would have reflected J17A and is rejected. J20A, S410, and Mid-360 inherit
proper rotations; the Mid-360 optical window faces the head while its
connector faces rearward.

Only rigid seating corrections are applied: `11.625 mm` upward to
J20A/S410/Mid-360, `0.106515 mm` outward to S410 along the 15-degree mount
normal, `2.0015 mm` outward to Mid-360 along the same normal, and `0.58375 mm`
upward to the complete sensor stack. These corrections remove positive solid
intersection while preserving source shapes. Zero intersection and
zero-distance contact are appearance evidence only; robot-side holes,
fasteners, receivers, cable clearance, and load path remain unresolved.

Dr Sun rejected the first post-reboot longitudinal registration because the
stack appeared too far rearward compared with the official laser-version
silhouette. The historical replacement candidate therefore translated the
complete rigid
sensor assembly `30.0 mm` toward robot `+Z`, using the sensor centre relative
to the front hip/cover landmark in the official product view and installation
frame as a visual constraint. Because the front cover slopes downward in that
direction, the complete assembly also moves `2.4 mm` down. This restores
numerical contact (`0.006602556 mm`) without solid intersection. The visual
registration remains an `image_estimate`, not a published mounting dimension.
Dr Sun subsequently rejected this replacement because its J17A mounting
features do not align with the visible chassis interface. It is no longer a
current target.

D435 is deferred. Its true SolidWorks CAD must be translated in a separate
clean session before it can enter this baseline; no D435 mesh or hand-authored
proxy may be substituted.

## Evidence And Fidelity Layers

The design separates what is known from what is reconstructed:

1. `official_nominal`: current manual envelope and published interface facts.
2. `source_model`: exterior geometry inherited from the official
   high-resolution Lite3 URDF/DAE and official sensor assets.
3. `image_estimate`: placement and surrounding Lite3 geometry inferred from
   official product and manual views.
4. `print_adaptation`: thickness, clearance, keys, seams, and support changes
   required by the declared print profile.

The fourth layer must never be mistaken for real robot construction.

## Archived Target Override (2026-07-26)

The target identity remains the official Lite3 LiDAR assembly shown in the
V1.0.7 manual, but there is no current geometry candidate. Dr Sun rejected both
the engineered mounting adaptations and the later multiview reconstruction.

The only source-backed geometry that may remain active is:

- the official Lite3 body/leg exterior;
- the manufacturer Livox Mid-360 component geometry;
- the manufacturer RealSense D435 component geometry.

The factory Interface transform, LiDAR/camera bracket, robot-side attachment,
hole layout, fastener receivers, and load path are unresolved. J17A, J20A,
S410, BZ20, and AGX are separate Lite3 Venture FAST-LIVO2 extension evidence,
not factory V1.0.7 assembly parts. No image-estimated plate, post, support,
guard, screw head, Interface position, or collision-driven translation may be
promoted into the current target.

Geometry work is frozen until the project archives either manufacturer factory
assembly CAD/drawings or physical Lite3 LiDAR measurements/scan data.

## Dual-Track Body Fidelity

The official Lite3 visual mesh and the printable body serve different
purposes and must not be conflated:

- the official raw high-resolution URDF/DAE world links are the visual and
  CAD-reference track; they preserve the manufacturer's smooth exterior and
  drive the 1:1 reference GLB plus the primary full-robot renders;
- the resolution-bounded watertight reconstruction is the print track; it
  drives the 1:1 printable 3MF/component masters and the 1:4 sliced parts;
- bounded topology-preserving smoothing may reduce marching-cubes stair
  stepping on the print track only after its displacement, volume, manifold,
  connected-component, round-trip, and slicer effects are recorded;
- because the official visual shells are open and non-manifold, no output that
  contains them may be called a print-ready master.

This separation prevents voxel terraces from being misrepresented as the
original SolidWorks/CAD surface while preserving an honest, independently
validated fabrication path.

## Geometry Pipeline

```text
 official Lite3 URDF/DAE + V1.0.7 manual views
       + Mid-360/D435 source geometry
       + J17A/J20A/S410 related-source candidates
            |
            v
 topology audit and source metrics
            |
            +---------------- official raw visual links
            |                         |
            |                         v
            |              1:1 visual/CAD reference
            |                + primary appearance renders
            |
            +---------------- resolution-bounded watertight reconstruction
                                      |
                                      v
                         bounded print-surface smoothing
                                      |
                                      v
                         1:1 printable master components
                                      |
                                      +---- official sensor geometry
                                      |     + estimated Lite3 interfaces
                                      v
                         scale-aware printable adaptations
                                      |
                                      v
                         1:4 print kit + print assembly
                                      |
                                      v
                         manifold validation + real slicer check
```

## Watertight Reconstruction

Direct hole filling is rejected because tests show that it can discard
high-resolution shells and visibly change volume. The baseline method is
resolution-bounded voxel reconstruction followed by marching-cubes extraction:

- torso master candidate: 1.0 mm voxel pitch;
- leg-component candidates: 0.5-0.75 mm voxel pitch;
- printed 1:4 equivalent: 0.25-0.1875 mm geometric sampling.

Each candidate is compared to the source surface before selection. Detached
decorative fragments below the print profile's minimum feature are either
joined deliberately or omitted and listed.

The official raw exterior remains available in parallel and is not replaced
by the watertight candidate in visual-reference exports. Any print-track
smoothing profile is a parameterized `print_adaptation`, and its maximum and
percentile displacement plus volume change are reported per component.

## Print Architecture

The 1:1 master remains an exterior reference in millimetres. The 1:4 kit is
designed as a static display model:

- one torso/body print module;
- four side-specific three-part legs (`HIP`, `THIGH`, and `SHANK`);
- one upper LiDAR equipment module;
- one separate image-derived Interface enclosure after the V1.0.7
  appearance layout is accepted;
- one separate source-derived D435i print part;
- keyed pins and matching sockets at the torso and leg display interfaces.

Side-specific identifiers prevent mirrored-leg confusion. The assembled
reference preserves the factory standing pose but does not contain working
joints.

Twelve loose 2.4 mm pins connect the three leg joints on each side. The upper
module has two integrated underside pins, a shallow keyed torso pocket, and
0.20 mm nominal radial/planar clearance. The D435i visual and source-derived
print body are retained, but their robot-side support is now unresolved. No
camera bracket, receiver, rail, or fastener bundle is part of the accepted
architecture until the replica-identity gate is passed. The previous
two-piece/yoke architecture remains only as a rejected revision record.

## Print Profile

The initial acceptance profile targets common 0.4 mm-nozzle FDM:

- target layer height: 0.16-0.20 mm;
- minimum free-standing wall/detail: 0.8 mm;
- minimum assembly pin diameter: 2.4 mm;
- nominal radial pin clearance: 0.20 mm;
- maximum single-part build envelope: `220 x 220 x 250 mm`.

The source master is also suitable for later resin-specific adaptation, but a
resin profile is not claimed until separately sliced.

## LiDAR Reconstruction

The sensor cluster now uses public primary CAD instead of a hand-authored
rounded substitute:

- Livox `mid-360-asm.stp` supplies the real optical window, finned square
  housing, mounting pattern, and M12 connector;
- DEEP Robotics' Lite3 Venture `1T21-J20A` STEP/drawing supplies the real
  15-degree adapter;
- DEEP Robotics' Lite3 Venture `1CA5-S410` STEP/drawing supplies the real
  protective steel guard;
- DEEP Robotics' Lite3 Venture `1T21-J17A` STEP/drawing supplies a
  source-backed candidate whose visible silhouette is compared with the
  V1.0.7 manual; it is not relabeled as proven factory-LiDAR CAD or as a
  proven Pro base;
- Intel RealSense's official `realsense-ros` package supplies the detailed
  `d435.dae` visual geometry used by the official D435i URDF, while the
  CAD/datasheet supplies the nominal `90 x 25 x 25 mm` product envelope;
- whole-cluster registration and connector yaw remain `image_estimate`;
- the hidden bridge, narrow upper-module connectivity webs,
  minimum-feature thickening, and assembly pins remain `print_adaptation`;
- the D435 is authorized only in direct contact with the J17A short camera
  faces and their two source-backed M3 axes; no additional visible camera
  bracket geometry is authorized.

The V1.0.7 manual's long `Interface` enclosure is part of the current target.
The perception manual independently confirms Xavier NX as the host but does
not publish its internal location. The visible model therefore contains the
Interface exterior only, never a Jetson developer kit. BZ20 and the rear AGX
support belong to the rejected Venture FAST-LIVO2 detour.

The official Mid-360 STEP is not print-ready as one closed body. The print
master is reconstructed at 0.4 mm voxel pitch and compared back to the source
surface. Reference renders retain the official optical-window, housing-exterior
and connector tessellations as separately colored layers so the blue dome,
silver fins, and black connector remain recognizable.

The J20A drawing and STEP define the 15-degree angle. After mapping the source
frame to the robot frame, the sensor body axis is
`[sin(15 deg), 0, cos(15 deg)]`: positive X is the robot head direction, so the
sensor leans forward and its mounting plane descends toward the front. A
rearward lean is rejected. The connector receives a 180-degree yaw around the
body axis so it faces the rear Interface enclosure without changing the
forward tilt. The D435i uses the camera-axis direction derived from the
  published J17A reference, `[0.939693, 0, -0.342020]`, i.e. 20 degrees downward
  toward robot `+X`; J17A is exported only as a labeled related-source
  candidate.

The J20A and S410 are officially published for the related Lite3 Venture
FAST-LIVO2 extension. They are source-backed geometry for this requested
replica, not proof of a factory V1.0.7 assembly or physical fit.

### Rejected V1.0.7 Interface Visual Track

The material in this subsection is historical rejection evidence. The
Interface dimensions, position, feet, relief, sensor translation, and all
dependent support geometry must not govern a future model.

The rejected designs successively exposed a large solid deck, a dual-rail
industrial-PC base, and a lower carrier plate. None matched the plate-free
silhouette in the official Lite3 LiDAR views.

The rejected visual-reference track:

- exports the top enclosure as `DEEP Robotics Interface`, not as a visible
  Jetson development kit;
- records `NVIDIA Jetson Xavier NX` only as a separately listed configuration
  item whose physical location is `not_published`;
- omits `UPPER_DECK_INTERFACE`, `PAYLOAD_BASE`, and every spanning plate;
- keeps J17A only as a labeled `related_source_candidate`, never as proven
  factory V1.0.7 geometry;
- shows only the Interface's local mounting pads and the source-visible LiDAR
  carrier features;
- keeps the Interface, candidate carrier, radar adapter, guard, sensor, and
  D435 as separate inspectable visual components.

The former `160 x 92 x 46.8 mm` rectangular placeholder remains rejected. Its
rejected replacement is an image-derived approximately `233 x 92 x 46 mm` enclosure
registered to the V1.0.7 orthographic-like views. The rejected registration
placed the J17A rear edge about `34 mm` inside the Interface envelope and then
cut the enclosure around that collision. The later rejected registration preserves
the Interface position and moves the complete source sensor stack rigidly
`35 mm` toward robot `+X`, matching the visible carrier/Interface separation.
The shallow central underside relief remains an image-estimated enclosure
feature rather than a collision patch. The visible side walls, lid, ports,
vents, and four bored local feet remain separate inspectable objects. The feet
span the image-registered `7.899495 mm` distance from the Interface underside
to the `391.967571 mm` source-body deck datum.

The next 1:4 `UPPER_LIDAR_MODULE` may still require narrow hidden webs and the
Mid-360 seating bridge, but those features can never be exported as official
exterior evidence. The Interface and source-derived D435 body must remain
separate print parts. The previously generated
`CAMERA_MOUNT_BRACKET`, `CAMERA_CARRIER_PLATE`,
`CAMERA_FASTENERS`, and `CAMERA_RECEIVER_YOKE` are rejected and prohibited
from the next official-appearance output. There is therefore no accepted
camera-mount print architecture or accepted final part count at this stage.

The visible camera is the pinned official RealSense `d435.dae`, transformed as
one rigid source assembly onto the declared 20-degree downward camera axis.
Because that visual mesh is open, the printable camera body is reconstructed
from the same source at 0.35 mm voxel pitch and compared back to the original.
The printable camera body is cropped at the official rear plane and receives
only two blind print-clearance holes on the official 45 mm rear M3 axes. No
mounting lugs, locating pins, camera sockets, hand-authored bezel, aperture, or
lens-insert geometry remains.

The visual and printable camera tracks use the same source-to-robot transform.
The build report records the source hash and bounds, transform matrix,
watertight reconstruction topology, and bidirectional surface-distance
statistics. The official visual mesh is explicitly `print_ready: false`; the
source-derived print master is never described as the original SolidWorks
surface. The open official mesh uses deterministic sampled surface clearance
for installation-space checks. Exact Boolean collision volumes use the closed
source-derived print proxy and are explicitly labeled as such.

### Rejected D435i Two-Piece Mount And Receiver Revision

Intel's D400-series datasheet defines two rear M3 mounting points on 45 mm
centres, 3 mm maximum thread insertion, and 0.4 Nm combined recommended torque.
The carrier-side axes come from the pinned J17A source model; the complete
factory Lite3 LiDAR camera-bracket drawing is not public.

The rejected revision used:

- two camera-side M3x6 fasteners through a 3.2 mm plate and 0.6 mm mating pads;
- two carrier-side M3x6 fasteners on the source-backed camera axes;
- four lateral M3x8 fasteners joining the camera bracket to a separate carrier
  plate after both axial pairs are installed;
- two 12 mm-outer-diameter receiver bosses with 3.0 mm blind bores, joined by
  4 x 4 mm struts into the S410/upper module;
- 2.2 mm modeled insertion for each M3x6 pair, below the official 3 mm maximum;
- 3.4 mm service space between opposing axial screw heads;
- 0.02 mm face gap between carrier plate and receiver bosses;
- 0.9 mm minimum receiver radial wall at 1:4, above the 0.8 mm print floor;
- separate watertight bracket and carrier-plate components, with eight separate
  fastener components.

Its screw sequence was: pre-install the two axial pairs, mate the bracket
halves, then close the four lateral screws. The complete modeled chain was
D435i body -> camera screws -> camera-side bracket -> lateral screws -> carrier
plate -> carrier screws -> blind receiver bosses -> receiver struts ->
S410/upper module.

This revision is not the design contract. Dr Sun rejected it because the long
rails, deep carrier plate, receiver bosses, and external eight-screw chain were
invented and changed the factory-visible silhouette. Its mechanical
completeness, watertightness, and slicer success do not establish replica
identity. Those features must not be reused merely because they validate
cleanly.

### Replica-First Camera-Support Restart

The restart originally followed
`.trellis/tasks/07-24-lite3-pro-parametric-model/research/official-lidar-camera-mount-evidence.md`.
Before the FAST-LIVO2 target identity was fixed, the visible facts were:

- the D435i sits immediately in front of and below the LiDAR;
- the visible support is compact and local to the camera/radar front;
- no long longitudinal rails, deep carrier plate, rear receiver yoke, or
  eight-screw external assembly appears in the official product/manual views;
- the J17A Venture drawing contains short angled camera faces and a 45 mm
  pattern that may be visually compatible, but its identity with the factory
  Lite3 LiDAR V1.0.7 base is unresolved;
- no public source currently reveals the hidden factory screw stack or load
  path.

The later official FAST-LIVO2 installation video resolved J17A identity only
for that separate extension. It did not prove J17A as factory V1.0.7 geometry,
so the next section remains rejection history. The general rule remains:
hidden geometry stays absent and labeled `unknown`; later 1:4-only support
must be hidden and exported only as an explicitly separate
`print_adaptation`.

### Rejected FAST-LIVO2 Identity Detour

The following paragraph records a rejected identity detour and is not the
current design contract. That detour treated the official Lite3 Venture
FAST-LIVO2 extension as the target and therefore assumed that
J17A, J20A, S410, and the Mid-360 are unchanged source components of that
extension. It did not establish factory V1.0.7 identity or unchanged Lite3
Pro robot-side fit.

Official frames 284 and 292 constrain the D435 relationship. The camera rear
plane seats directly on the two short J17A faces, whose drawing defines two
`Ø3.20` holes at 45 mm centres and a 20-degree downward viewing direction.
Only those two M3 axes are exposed; the rejected 17 mm standoff, rails, carrier
plate, receiver yoke, and eight-screw chain remain prohibited.

The adjacent white enclosure is the official `1T21-BZ20` backload shell. Its
source STEP is one closed solid with a `108 x 96 x 30 mm` envelope. Official
frames 296 and 320 show that it is separate from J17A and from the black rear
AGX compute device. The prior `160 x 92 x 46.8 mm` generic Interface box was a
wrong identity, so its collision, 36 mm forward sensor shift, and large hidden
adapter are not design inputs.

The reviewed candidate keeps the official sensor position unchanged, aligns
the official full-standing Lite3 visual to the same torso-top datum, and places
the BZ20 by an explicitly image-estimated rigid translation. It reports zero
BZ20/J17A Boolean intersection and positive BZ20/D435 torso AABB clearances.
This is an appearance gate only: the official exterior and D435 meshes remain
open visual geometry and are not relabeled printable solids.

The user's industrial PC is a separate rear component whose geometry is not
currently available. The Pro base therefore remains undesigned. Once the real
IPC CAD or measurements arrive, the only permitted new geometry is a hidden
lower `print_adaptation` from J17A to the Pro `74 x 94 mm` four-M3 pattern,
shaped around measured IPC, connector, and cable keep-outs. The visible source
stack must not move to compensate for a guessed box.

### Real Mechanical Assembly Restart

The appearance candidate exposed a mixed-datum error. Its four black J17A
fastener references retained the old crossbar X coordinates
`[72.676, 182.676] mm`, but the current rigid J17A mesh is the official STEP
under the transform
`source +X -> robot +X`, `source +Y -> robot -Y`,
`source +Z -> robot +Z`, with translation approximately
`[134.602, 0, 446] mm`. The source M3 axes
`X=[-51.75, 58.25] mm`, `Y=+/-43 mm`, `Z=0..2.5 mm` therefore map to
`X=[82.851997, 192.851997] mm`, `Y=+/-43 mm`,
`Z=446..448.5 mm`. Ray probes through those transformed axes pass through the
real J17A voids; the stale axes intersect unrelated J17A material.

The replacement lower adapter is a sensor-only mechanical closure, not a
final industrial-PC base. It keeps the visible FAST-LIVO2 stack rigid and uses:

- four official Lite3 Pro axes at `X=[-17, 57] mm`, `Y=+/-47 mm`;
- two fixed side trusses outside the BZ20 side faces, joined only by local
  dogbone webs, with no centre deck or sliding-rail features;
- four lower pads seated on the Lite3 payload plane and counterbored from
  above for candidate ISO 4762 M3x8 screws;
- four raised sensor columns seated at `Z=446 mm`, counterbored deeply from
  below for candidate ISO 4762 M3x20 screws into the J17A source M3 receivers;
- explicit Lite3 threaded-receiver proxies because the official manual proves
  M3 threads but does not publish their depth.

The intended order is to invert J17A and the adapter, install the four recessed
M3x20 screws upward into J17A, place that subassembly on the robot, install the
four M3x8 screws downward into the Pro interface, and install BZ20 or the
measured user IPC last. This order keeps both screw groups tool-accessible.

The candidate may prove a complete Lite3-to-sensor load path without pretending
to fit the unknown user IPC. Final truss outline and the BZ20/user-IPC
relationship remain separate gates: the official BZ20 solid is checked now,
while the user's different IPC still requires its real envelope, holes,
connectors, and cable keep-outs.

### Redesigned Seating Contract

The first forward-tilted assembly aligned nominal pattern centers but let the
voxel-sealed Mid-360 printable master penetrate the J20A solid. That is not a
valid assembly relationship even for a static replica.

The redesign preserves the official component rotations and hole pattern while
moving the printable Mid-360 exterior 3.0 mm outward along the J20A mounting
normal. The offset is a `print_adaptation` compensation for the reconstructed
exterior, not a published Livox spacer dimension. A centered hidden bridge
spans the resulting seating interface, remains inside the 48 x 36 mm hole
rectangle, and overlaps both printable bodies. It therefore provides deliberate
one-piece connectivity without blocking the four source mounting holes or
using accidental Mid-360/J20A interpenetration.

The official S410 geometry and its hole-derived registration remain rigid. The
build must prove zero Mid-360/S410 Boolean overlap and report the closest
sampled clearance rather than silently widening or deforming the guard. The
same audit records connector clearance, connected-component count, and the
approximate front/rear longitudinal field-of-view envelope implied by Livox's
published `-7 to 52 degree` vertical field of view and the 15-degree forward
tilt.

### Current V1.0.7 Baseline Registration

The current evidence-only baseline is generated under
`evidence/official-lidar-v107-baseline-candidate/` and leaves the main
printable generator frozen.

> Rejected on 2026-07-26: this entire baseline is retained only as engineering
> adaptation evidence. The `35 mm` translation, profiled supports, bored feet,
> hidden receiver proxies, and provisional M3 chains below are not part of the
> replacement factory-visible replica contract.

- The high-resolution Lite3 URDF is posed at
  `hip_y=-0.68 rad`, `knee=1.48 rad`, selected from the manual side view.
  Its visual standing envelope becomes
  `604.784973 x 372.657928 x 496.0 mm`, within the declared image-fit
  tolerance of the published `610 x 370 x 496 mm`.
- The related-source sensor stack receives the image-estimated translation
  `[55.0, 0.0, -28.132935] mm`; the S410 guard top is exactly `496.0 mm`.
  The additional `35 mm` robot-X correction separates the J17A carrier from
  the fixed Interface rather than carving one part around the other.
- The real-source D435 direct-mount mesh and its two 45 mm-centre M3 evidence
  axes receive the same rigid transform. The inherited sampled D435/J17A
  surface distance remains `0.0002 mm`; the rejected 17 mm standoff is absent.
- The Interface envelope is `233 x 92 x 46 mm`, with its bottom at
  `399.867065 mm`. Its four `7.899495 mm` bored feet reach the source-body
  deck datum at `391.967571 mm`; the former floating appearance is absent.
  Each foot has an M3 clearance bore, a downward M3 fastener, and a labeled
  hidden receiver proxy. Exact Interface/J17A and Interface/local-support
  intersections are both `0.0 mm3`.
- The J17A source drawing supplies four M3 axes on a `110 x 86 mm` pattern.
  Four independent profiled supports carry upward M3 fasteners into J17A and
  separately accessible downward M3 fasteners into labeled body-side receiver
  proxies. Their sampled minimum body clearance is `0.250008 mm`; unintended
  support/fastener overlap is `0.0 mm3`.
- The black D435 face is a display-only surface derived from front-facing
  triangles of the pinned source mesh. It adds no synthetic camera body,
  bracket, aperture, or manufacturing claim.
- The editable evidence assembly is saved as
  `lite3_lidar_v107_baseline_candidate.FCStd`; four comparison sheets place
  the candidate beside the losslessly extracted manual views.
- `validate_official_lidar_v107_baseline.py` passes all 27 targeted identity,
  envelope, collision, source-hash, model-readability, and render checks.

These numbers are image-fit and evidence-registration results, not factory
nominal bracket dimensions.

## Historical Validation Of Rejected Adaptation

Geometry validation checks, per delivered part:

- positive non-zero volume;
- closed and consistently oriented mesh;
- no boundary or non-manifold edges;
- no degenerate faces;
- finite coordinates and millimetre units;
- declared bounding box and build-volume fit;
- minimum print-adapted feature rules;
- successful re-import;
- successful slicer/toolpath generation.

The rejected 20-part revision passed 125 geometry/contract checks and produced
non-empty PrusaSlicer 2.9.6 toolpaths for 20/20 parts. Those results prove only
that the rejected invented mechanism was mesh-valid and sliceable. They do not
validate the replica and are not acceptance evidence for the replacement.

Replica identity is now the first gate: human review must compare the
camera/radar/Interface silhouette with the four losslessly extracted V1.0.7
manual views before replacement print geometry is built. Geometry, collision,
printability, and slicer validation follow only after that gate.
Dr Sun's visual approval remains the final gate.

## Rejected Multiview Replica Track

The multiview scene under
`evidence/official-lidar-v107-multiview-replica-candidate/` is rejected
negative evidence. It correctly avoided importing J17A/J20A/S410 as factory
parts, but then replaced them with an unsupported lower plate, unequal posts,
tilted plate, D435 rear support, guard straps, fastener heads, and a rearward
image-estimated Interface position.

Its `496.003681 mm` total height and `11 mm` visible separation validate only
the candidate's internal construction. They do not validate factory identity,
placement, contact, fastening, assembly order, or printability. No part of
that reconstructed mounting chain may seed a new model.

## Evidence-Locked Restart

A new CAD assembly may start only after one of these packages is archived:

1. manufacturer factory LiDAR assembly CAD or dimensioned drawings; or
2. physical-robot scan/measurement data covering the Interface datum, bracket
   contact surfaces, hole axes, thread/receiver information, and component
   transforms.

Until then, the project may display the three independent source-backed
components for inventory purposes, but must not position them as a complete
factory assembly.

## Claim Boundary

`printable_static_replica` means a static exterior model suitable for the
validated print profile. It does not mean official CAD, exact hidden geometry,
functional joints, structural suitability, replacement-part fit, or
manufacturer approval.
