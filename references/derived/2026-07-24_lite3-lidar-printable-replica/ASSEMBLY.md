# Lite3 LiDAR 1:4 Static Replica Assembly

This map applies to the 20 STLs in `models/print_1_4/`.

## Part Codes

- `TORSO`: printable main body with leg sockets and a shallow upper-module
  display pocket.
- `FL_*`, `FR_*`, `HL_*`, `HR_*`: front-left, front-right, hind-left, and
  hind-right leg parts.
- `*_HIP`, `*_THIGH`, `*_SHANK`: the three side-specific segments of each
  leg.
- `UPPER_LIDAR_MODULE`: connected print-only sensor module containing the
  Mid-360-derived exterior, adapter, guard, local radar mounts, hidden
  connectivity webs, and the two-arm camera receiver yoke integrated into the
  S410 guard. Each receiver arm ends in a 3.0 mm blind bore on the
  source-derived carrier axis. The official visual-reference model does not
  show a spanning lower plate.
- `FACTORY_INTERFACE`: separate printable approximation of the enclosure
  labeled `Interface` in DEEP Robotics documentation. It is not a visible
  Jetson development kit and does not claim the unpublished Xavier NX location.
- `FRONT_CAMERA_BAR`: watertight reconstruction of the official RealSense
  D435 mesh with two blind print-clearance holes on the official 45 mm M3
  mounting axes. It has no separately invented bezel or lens inserts.
- `CAMERA_MOUNT_BRACKET`: camera-side plate with four longitudinal side rails.
- `CAMERA_CARRIER_PLATE`: separate carrier-side mating plate aligned to the
  two source-backed J17A camera axes and the two receiver bosses in
  `UPPER_LIDAR_MODULE`.
- `CAMERA_FASTENERS`: eight print-adapted screw models: two camera-side M3x6,
  two carrier-side M3x6, and four lateral M3x8 at 1:1 nominal scale.
- `ASSEMBLY_PINS`: twelve 2.4 mm leg pins plus two spares.

## Assembly Order

1. Dry-fit every pin and socket. The nominal radial clearance is 0.20 mm, but
   printer calibration and hole shrinkage may require light reaming or sanding.
2. Join each `HIP` to the matching side of `TORSO` with one loose pin.
3. Join each matching `THIGH` to its `HIP` with one loose pin.
4. Join each matching `SHANK` to its `THIGH` with one loose pin.
5. Seat `UPPER_LIDAR_MODULE` in the shallow torso pocket. Its two integrated
   underside pins enter the matching torso sockets.
6. Position `FACTORY_INTERFACE` according to
   `models/reference/lite3_lidar_1_4_assembled.glb`. The current display part
   does not assert an unpublished factory fastening method; use only minimal
   model-safe adhesive after visual alignment.
7. Identify the three screw groups in `CAMERA_FASTENERS`. The M3 names and
   lengths describe the 1:1 mounting contract; the 1:4 screw shafts and holes
   are enlarged to the declared FDM minimum feature and clearance.
8. Before closing the bracket, attach `CAMERA_MOUNT_BRACKET` to
   `FRONT_CAMERA_BAR` with the two camera-side screw models. The optical face
   points forward and 20 degrees downward. The 1:1 contract uses M3x6 screws
   with 2.2 mm modeled thread insertion, below Intel's 3 mm maximum.
9. Separately attach `CAMERA_CARRIER_PLATE` to the two blind-bore receiver
   bosses integrated into `UPPER_LIDAR_MODULE` with the two carrier-side screw
   models. The screw axes are source-derived; the receiver arms and their
   S410 engagement are print adaptations. The carrier plate has a modeled
   0.02 mm face gap, while each screw enters 2.2 mm into a 3.0 mm blind bore.
10. Slide the four side rails of `CAMERA_MOUNT_BRACKET` over the mating edges
    of `CAMERA_CARRIER_PLATE`. Install the four lateral screw models last.
    This sequence keeps both opposing axial screw pairs accessible before the
    two halves close.

Do not force a binding pin or printed screw. The geometry is software-audited,
but no physical calibration coupon or full test print has yet been completed.

## Visual Reference

Use `models/reference/lite3_lidar_1_4_assembled.glb` for the printable assembly
and `models/reference/lite3_lidar_1_1_reference.glb` for the high-detail visible
reference.

For camera inspection:

- `evidence/d435i-official-visual-front.png`;
- `evidence/d435i-official-visual-isometric.png`;
- `evidence/d435i-official-visual-side.png`;
- `evidence/d435i-bracket-fasteners-isometric.png`;
- `evidence/d435i-bracket-fasteners-end.png`;
- `evidence/d435i-bracket-fasteners-top.png`;
- `evidence/d435i-mount-to-s410-isometric.png`;
- `evidence/d435i-receiver-to-s410-isometric.png`;
- `evidence/d435i-receiver-to-s410-top.png`;
- `evidence/d435i-printable-front.png`;
- `evidence/d435i-printable-isometric.png`.

## Claim Boundary

This is a static display replica. The official D435 visual mesh, official
Lite3 exterior, Mid-360/J20A/S410 source geometry, and published nominal
envelopes are source-backed. The D435 rear M3 count, 45 mm spacing, 3 mm
maximum insertion, and 0.4 Nm combined recommended torque are official. The
carrier-side axes come from the pinned J17A source model. The two mating
plates, side rails, carrier screw choice, receiver yoke and its S410
engagement, print clearances, hidden upper-module connectivity, and Interface
placement are print adaptations or image-scored reconstructions. The receiver
yoke closes the modeled load path and prevents a screw-to-empty-space
condition, but this does not establish real-material strength. The result is
not articulated, load-bearing, a replacement part, or validated for
installation on real hardware.
