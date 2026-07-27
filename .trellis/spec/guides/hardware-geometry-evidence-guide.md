# Hardware Geometry Evidence Guide

Use this guide when importing robot, sensor, bracket, CAD, URDF, DAE, STL, or
similar geometry for visualization, collision review, or printing.

## Source And Identity

- [ ] Preserve the original source file unchanged under `references/upstream/`.
- [ ] Record the primary URL, repository commit or document version, license,
  byte size, and SHA-256.
- [ ] Verify that the referenced URDF/xacro actually uses the selected mesh.
- [ ] Record source axes, units, bounds, topology, and the rigid transform into
  the robot frame.
- [ ] Do not promote a related accessory or variant into factory-assembly
  identity without direct assembly evidence.
- [ ] Do not infer the robot variant from the download filename or top-level
  product name alone. Record the relevant assembly hierarchy and reconcile
  conflicting parent/child names before assigning Pro, Venture, Exploration,
  or Experience identity.
- [ ] If a CAD source is user-provided without a public URL or license, record
  that provenance explicitly, preserve the original hash locally, and prohibit
  redistribution until permission is established.
- [ ] Resolve part role as well as part identity. A backload shell, compute
  device, robot interface, and user-supplied industrial PC may be adjacent in
  one image without being the same component.
- [ ] Before moving an official source part to resolve a collision, verify that
  the other body is measured or source-backed. A collision against a guessed
  enclosure is evidence that the enclosure/identity may be wrong, not
  permission to shift the official sensor stack.
- [ ] A rigid source assembly may be re-registered when primary assembly views
  independently constrain the corrected placement. Record the transform as an
  image estimate and cite the view; do not choose the transform from clearance
  alone or relabel it as a factory dimension.

### Identity-First Collision Gate

- Freeze source-backed transforms before testing image-estimated or user-device
  keep-out volumes.
- Distinguish a source part's internal rigid transform from its
  image-estimated whole-assembly registration into the robot frame.
- If the collision involves an unverified placeholder, replace or remove the
  placeholder and re-run the audit before designing an adapter.
- If the real user device controls the adapter shape, require its CAD or
  measured envelope, mounting holes, connector faces, and cable bend zones.
  Leave the adapter `not_designed` until those inputs exist.
- Mark every placement, collision result, and adapter derived from a wrong
  identity as superseded so it cannot be reused as design evidence.

## Keep Geometry Tracks Separate

Use explicit labels:

- `official_visual`: manufacturer geometry used directly for appearance;
- `source_derived_collision_proxy`: closed geometry used when the official
  visual source cannot support solid Boolean operations;
- `source_derived_print`: watertight geometry reconstructed from the source;
- `print_adaptation`: lugs, pins, clearances, hidden bridges, and thickening
  added for fabrication.

The visible reference should use `official_visual` when available. A printable
or collision-proxy mesh must not silently replace it.

## Open-Mesh Boundary

- [ ] Audit watertightness, winding, connected components, boundary edges, and
  non-manifold edges before choosing an operation.
- [ ] Never call an open visual shell print-ready.
- [ ] Never force an open visual shell through a solid Boolean and treat the
  result as authoritative CAD.
- [ ] For an open official mesh, use an explicitly named surface-clearance
  method for visual-space checks.
- [ ] Use a separately declared watertight proxy for exact intersection volume.
- [ ] Report the source-to-proxy reconstruction resolution and bidirectional
  surface deviation.

## Transform And Assembly Checks

- [ ] Apply the same source-to-robot rigid transform to official visual and
  source-derived tracks.
- [ ] Assert a `4 x 4` transform with rotation determinant `+1`.
- [ ] Keep visual node names distinct from print-proxy node names.
- [ ] Validate visual source presence, print-proxy absence from the visual
  scene, and absence of superseded synthetic detail.
- [ ] Record both surface clearance for the official open mesh and Boolean
  intersection for the closed proxy when both are used.

### Fusion-Native B-Rep Assembly Gate

- [ ] For a source-CAD baseline, record Fusion B-rep and mesh-body counts for
  the robot and every imported accessory. If the declared target is real CAD,
  require zero mesh bodies instead of silently substituting a tessellated
  visual model.
- [ ] Use occurrence `transform2` with a proper rotation whose determinant is
  `+1`. Reject reflected or mirrored transforms inherited from a mesh pipeline,
  even when the rendered placement looks plausible.
- [ ] Verify the robot front against a visible chassis landmark in a physical
  top or side view before placing sensors. Record the chosen robot-frame front
  axis; do not infer it from the current camera direction.
- [ ] A collision-driven seating translation is permitted only along a
  source-backed datum or mount normal. Record the pre/post intersection volume,
  preserve the source shape, and keep the result labeled contact/packaging
  evidence rather than verified physical fit.
- [ ] When correcting a sensor's fore/aft registration, constrain the complete
  rigid assembly against a visible robot landmark such as the nose, front hip
  axis, or cover seam in a cited primary view. Reject the previous whole-stack
  transform, preserve every internal source-part transform, and re-run seating
  checks because the robot support surface may change height along its length.
- [ ] Before adding a component, base feature, or other timeline geometry
  after positioning external occurrences, check
  `design.snapshots.hasPendingSnapshot`. Capture and name the reviewed pose,
  then verify all occurrence transforms again after the new feature is added.
  Fusion can otherwise revert uncaptured occurrence positions to their source
  origins when the timeline changes.
- [ ] Before extracting a bracket pattern, identify the functional hole group
  from a dimensioned drawing, assembly instruction, or direct physical
  evidence. Record whether each candidate group is threaded, through,
  counterbored, countersunk, or accessory-facing. Do not infer "robot-side
  mounting holes" merely because four circular features form a rectangle.
- [ ] When a shallow counterbore surrounds a smaller central opening, register
  the fastener/receiver centre axis, not the outer counterbore diameter. The
  larger circle normally describes screw-head or tool clearance; it does not
  justify matching a different large-hole pattern.
- [ ] If human or physical review identifies a two-hole row as the intended
  interface, do not replace it with a visually convenient rear row or a
  synthetic four-hole receiver pattern. Measure both centre axes in a common
  frame and state which additional bracket holes remain unused.
- [ ] Distinguish an annular insert or sleeve from a threaded receiver. A
  separate ring body around a smaller through-hole proves only the modeled
  sleeve and opening. Use a section, axial ray, or explicit receiver body to
  trace material below the hole before assigning a thread, fastener size, or
  load path.
- [ ] Before calling a source bracket installed, extract its robot-side
  hole/axis pattern from the B-rep and match the full pattern against the
  receiving chassis in a common frame with a declared centre tolerance. A
  single aligned hole, surface contact, or collision-free pose is insufficient.
- [ ] If the full patterns do not match, classify the result as a
  source-interface or robot-variant mismatch. Stop visual translation and
  require matching chassis/interface CAD or an official adapter; do not move
  the bracket until one feature looks aligned.
- [ ] When the user explicitly authorizes adapting a source bracket's hole
  pitch, preserve the source body and create a separately named derived
  component. Fill and relocate only the authorized holes, preserve their bore
  and counterbore diameters unless separately authorized, and record every
  untouched hole group.
- [ ] After human acceptance of a heavy Fusion scene, freeze two local
  artifacts before further editing: a complete editable F3D archive and a
  lightweight STEP of each modified component. Hash both, archive-test the
  F3D, and clean-import the STEP in an isolated CAD process so validation does
  not risk reopening the full scene. Fusion API note:
  `createSTEPExportOptions(filename, geometry)` requires a `Component`;
  pass `occurrence.component`, not the `Occurrence`.

### Seating And Contact Gate

- [ ] For every claimed foot, pad, spacer, or standoff, record the supporting
  datum, support top, part underside, and resulting seating gap. A rendered
  support that stops short of the supporting surface is floating geometry.
- [ ] Use a surface/datum check for an open official visual and an exact
  Boolean or signed-clearance check only with a declared closed proxy. Do not
  infer contact from one camera view.
- [ ] Treat zero-gap seating as appearance/contact evidence only. Without an
  explicit fastener axis, receiver material, engagement, and onward load path,
  do not call the contact a mechanically complete or load-bearing assembly.
- [ ] If the hidden receiver is unpublished, preserve the visible contact but
  label thread, receiver, material, and load path as unresolved.

### Replica Identity Gate

- [ ] Complete and review the official-visible geometry track before adding a
  printable or load-bearing adaptation.
- [ ] Map every replica-visible plate, post, block, foot, screw head, gap, and
  placement to a cited official view or pinned manufacturer component.
- [ ] Treat agreement with an overall envelope, top height, silhouette, or
  inter-part gap as candidate self-consistency only. Those values cannot
  validate an internal part transform, bracket identity, mounting datum, or
  mechanical connection.
- [ ] A rendered screw head is a visible feature, not fastening evidence.
  Do not imply a connection until its axis, clearance/engagement, receiver,
  tool access, and onward load path are source-backed or physically measured.
- [ ] Do not invent hidden receivers, fastener chains, or profiled supports to
  make an appearance replica mechanically complete.
- [ ] Keep any later `print_adaptation` geometry in a separate named track and
  exclude it from official appearance renders.

### Rejection Propagation Gate

- [ ] When human review, a factory source, or a physical measurement rejects a
  candidate, update its status file, manifest, generator metadata, task
  requirements, and acceptance checks in the same change.
- [ ] Reset every checked criterion that only proved the rejected candidate's
  internal geometry, renders, collision result, envelope match, or slicer
  output.
- [ ] Retain rejected artifacts as immutable negative evidence, but remove
  `current`, `awaiting review`, `replica`, `assembled`, and `print-ready`
  labels unless independently supported.
- [ ] Freeze dependent adapters and printable generators until the replacement
  evidence gate is explicit. Do not use rejected transforms or geometry as the
  starting point for the next candidate.

## Fastener And Assembly Contract

- [ ] Record each fastener's count, nominal thread or shaft, length, axis,
  receiver, and evidence class.
- [ ] Distinguish clearance holes, blind/threaded receivers, mating pads, and
  fastener solids instead of calling every cylindrical feature a mounting hole.
- [ ] Do not require the bracket clearance bore and receiving pilot/thread
  opening to have equal diameters. Trace the actual path in order:
  counterbore/head seat -> shaft clearance -> receiving pilot/thread. Compare
  the screw shaft to the receiver contract, not the two surrounding hole
  diameters to each other.
- [ ] Trace every fastener axis into actual receiver material and onward into
  the supported structure. A rendered screw that terminates in open space is
  not an assembly path.
- [ ] When official evidence provides maximum insertion or torque, calculate
  modeled insertion and preserve the published limit in the validation report.
- [ ] Prove an executable assembly order. Opposing or hidden axial screws may
  require separate bracket halves and a later lateral joint so tool access is
  not blocked by the already assembled geometry.
- [ ] Keep intended fastener engagement separate from the structural collision
  matrix. Audit insertion/clearance as a fit contract; require numerical-zero
  undeclared overlap between surrounding solid parts.
- [ ] Validate every separately delivered bracket and carrier part as closed,
  consistently wound geometry, and record the component count of any fastener
  bundle.
- [ ] Label scaled printed screws as display-model adaptations. Do not infer
  real-hardware strength, thread performance, torque capacity, or vibration
  resistance from successful slicing.
- [ ] Treat a two-hole or single-row match as partial interface registration.
  It does not prove anti-rotation, load capacity, rear-hole engagement, or a
  complete installation. Record unused holes and require a separate physical
  screw/receiver contract before fabrication.

## Good, Base, And Bad Evidence

- Good: pinned official visual mesh + separately validated watertight print
  body + recorded transform, topology, deviation, clearance, and collision
  proxy identity; measured user-device keep-outs are separate inputs.
- Base: official nominal envelope only, clearly labeled as an envelope model
  with no claim of detailed source geometry.
- Bad: a hand-authored box or estimated apertures presented as the official
  sensor, a source sensor shifted to clear a guessed box, adjacent enclosure
  and compute devices merged into one identity, or a closed proxy labeled as
  the original CAD.

## Required Assertion Points

- source hashes match the recorded values;
- official visual node is present in the visual reference;
- print proxy and superseded synthetic nodes are absent from that reference;
- print master is closed, consistently wound, and one connected component;
- reconstruction pitch and surface-deviation limits pass;
- source-to-robot transform is rigid;
- no source-backed transform changed solely to clear an unverified placeholder;
- every claimed local support has a recorded seating datum and no undeclared
  positive gap;
- contact-only supports remain labeled as appearance evidence when their
  fastener receiver or load path is unresolved;
- overall-envelope or gap agreement is never used as proof of internal
  placement or assembly;
- a rejected candidate has consistent rejected status across its manifest,
  generator metadata, task state, and acceptance checks;
- the matched hole group has a source-backed assembly role; a separate
  threaded or accessory-facing pattern is not substituted because it is easier
  to detect geometrically;
- a claimed installed source bracket has a full-pattern centre match against
  the receiving chassis, not merely one aligned feature or zero collision;
- a shallow counterbore is interpreted through its central fastener axis, and
  its outer head-clearance circle is not substituted for a receiver axis;
- an authorized hole-pitch adaptation preserves the source body, changes only
  the named derived holes, and lists every unused or unchanged hole;
- a two-hole match remains partial registration until anti-rotation, load
  path, and the physical screw/receiver contract are proven;
- an accepted heavy Fusion scene has a hashed local F3D archive plus a
  clean-imported component STEP before additional timeline edits;
- a reviewed Fusion occurrence pose is captured before adding later timeline
  geometry, and the post-feature transforms still match the accepted pose;
- an annular insert, sleeve, or clearance opening is not promoted into a
  threaded receiver without traced receiver material;
- official-source clearance and proxy collision checks are separately named;
- unresolved user-device keep-outs leave the dependent adapter explicitly
  `not_designed`;
- current print parts produce non-empty slicer toolpaths without repair errors;
- fastener count, insertion, service access, assembly order, and nearby-solid
  clearance are explicit when a mount is part of the deliverable.
