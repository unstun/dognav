# Lite3 Pro With Venture Sensor Stack: Fusion Review Status

Status: `superseded_and_rejected`

## Historical Result

This historical unsaved Fusion scene combined:

- the local official Lite3 high-resolution visual model as non-manufacturing
  context;
- unchanged official-source J17A, J20A, S410, and Livox Mid-360 geometry;
- the source-derived direct J17A-mounted D435 geometry;
- one yellow, separately identified open-centre Pro-to-J17A adapter.

BZ20, AGX, an industrial PC, and the rejected factory-V1.0.7 Interface
reconstruction are absent.

The primary exterior-review screenshot uses a fully opaque Lite3 body. Earlier
semi-transparent screenshots remain diagnostic views for checking the adapter
and sensor placement through the visual shell.

## Fit Decision

This is not a direct bolt-on installation. The published Lite3 Pro/LiDAR
payload pattern is `74 x 94 mm`, `4 x M3`, while the source J17A robot-side
pattern is `110 x 86 mm`. The patterns do not coincide in either orientation,
so a separate adapter is required.

The auxiliary FreeCAD validation passed for the persisted candidate:

- one connected valid adapter solid;
- all four Pro-side and four J17A-side fastener-axis probes remain open;
- zero positive adapter/J17A intersection;
- zero adapter/J17A seating distance;
- unchanged hashes for the official source assets used in the preview.

## Manufacturing And License Boundary

The public package is declared for `Lite3 Venture only`. Its repository is
GPL-2.0, but the public hardware folder has no separate hardware-file license
statement. The released parts are not all 3D-print parts: the J17A and J20A
drawings specify 6061-T6 aluminum with anodizing, while the S410 drawing
specifies welded 45 steel with powder coating. The current adapter is therefore
a new Pro integration candidate, not an official printable kit.

## Blocking Review And Measurement Gates

This candidate is no longer awaiting review. Dr Sun removed the yellow/custom
adapter and D435 from the later baseline, and the current source-interface
audit does not authorize reviving this design. No printable package or
real-hardware procedure is finalized.

Before fabrication or robot installation, measure and archive:

1. the actual robot variant and top payload-hole center spacing;
2. hole diameter, thread type, usable thread depth, and top-surface datum;
3. available fastener access and screw engagement on both sides;
4. cable exits, bend radius, camera field of view, LiDAR field of view, and
   leg/body motion keep-outs;
5. payload mass, center of mass, adapter material, print orientation, and
   structural safety margin.

This evidence proves nominal CAD assembly only. It does not validate physical
fit, structural strength, cable clearance, locomotion safety, or real-robot
use.
