# Current Lite3 Professional Scan-Registered Interface — Revision B

This package formalizes the planar registration between the corrected physical
scan and the photo-measured hole scaffold.

- The `65 mm` front pair and `-75 mm` centre candidate visually align to scan
  features after enclosure-edge registration.
- The scan-registered enclosure top is approximately
  `X=[-299.585,-100.0]`, `Y=[-52.739,55.879] mm` in the front-pair frame.
- The true nominal footprint is not rectangular. At its front end it narrows
  through two side recesses beginning near `X=-130 mm`: the left side moves
  inward from about `Y=+55.9` to `+44 mm`, and the right side moves inward from
  about `Y=-52.7` to `-42 mm`. Each recessed run is approximately `30 mm`
  long. Corner radii remain simplified in Revision B.
- The revised conservative collision keep-out is
  `X=[-305,-96]`, `Y=[-57,60]`, `Z=[0,54] mm`.

The nominal visual B-rep uses the two-recess polygon. The collision keep-out
deliberately remains a larger rectangle so the recesses cannot be mistaken for
free sensor volume. The model is a non-printable scaffold. It contains axis
markers and keep-outs, not drilled holes or fastener receivers. Thread, usable
depth, seating Z, the centre feature's load path, cables, vents, feet, corner
radii, and service sweeps remain open.
