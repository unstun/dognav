# Current Lite3 Professional Physical Scan — Revision A

This package archives and processes the user-provided `7_30_2026.glb` physical
scan. The original archive and GLB are preserved byte-for-byte under
`source/2026-07-30-user-glb-scan/`.

## What was corrected

- The source scene contains the robot, floor, and unrelated room objects.
- The robot is isolated with an explicit raw-scene region of interest.
- Scan yaw is fitted from the flat top of the measured compute enclosure, not
  from whole-scene PCA.
- Corrected photographs establish the rounded empty nose as the front. The
  standard frame is right-handed: `+X` front, `+Y` left, `+Z` up.
- The exported orientation is expressed in millimetres.

The fitted compute-enclosure top spans approximately `199.6 x 108.6 mm` between
the 0.1 and 99.9 percentiles. This is consistent with the physical enclosure
measurements and is strong evidence that the GLB export uses metres. It is not
evidence for screw size, thread form, or small-hole manufacturing tolerance.

## Main outputs

- `inspection/scan-inspection.json`: raw GLB structure and whole-scene bounds.
- `inspection/orientation-contract.json`: crop, yaw, axes, scale, and claim
  boundary.
- `inspection/compute-enclosure-footprint.json`: scan-derived two-recess
  enclosure footprint and X-bin diagnostics.
- `renders/scan-photo-orientation-comparison.png`: photo/scan heading audit.
- `renders/oriented-robot/`: corrected orthographic robot views.
- `renders/mount-area/`: fixed-millimetre-grid upper-body and front-deck views.
- `derived/lite3-pro-oriented-point-reference-mm.ply`: oriented color point
  reference.
- `derived/upper-body-mesh-reference/`: textured OBJ and a lightweight 3 mm
  clustered STL for visual/collision reference.

## Manufacturing boundary

The original scan is a textured mesh, not exact CAD. The derived STL is
deliberately lightweight and must never be printed as a robot part. The scan is
accepted for envelope, orientation, and relative-placement work. Hole centres,
hole diameters, threads, insertion depth, and load-bearing use remain gated on
caliper or manufacturer evidence.

The nominal enclosure footprint is not a rectangle: the scan shows two
front-side recesses beginning near `X=-130 mm`, each running approximately
`30 mm` to the front edge. The left and right inset depths are approximately
`11.9 mm` and `10.7 mm`. The separate rectangular collision keep-out remains
intentionally conservative.
