# Physical Measurement Card

## Current-Pro revision correction

The purchased robot is the current Lite3 Pro revision. Do not assume it has
the legacy V1.0.7 `74 x 94 mm` pattern, the Venture/J17A interface, or V1's
four Experience-style deck locations. Inventory and measure every actually
usable receiver first; the count itself is not yet accepted.

## Release gate

Do not print the final part, buy final-length base screws, or move the robot
with this payload until every applicable blank below is measured on Dr Sun's
physical current Pro. The supplied photograph proves layout and occupied/
vacant regions, not millimetre dimensions or thread specifications.

Use the robot forward centreline as `Y = 0`, the forward edge of the exposed
top deck as `X = 0`, and the local deck seating plane as `Z = 0`. Record at
least two repeated measurements. Photograph each gauge/caliper setup.

## M1 — Usable current-Pro receiver inventory and centres

| Label | Visible/usable? | X from forward deck edge (mm) | Y from centreline (mm) | Repeated value (mm) |
| --- | --- | ---: | ---: | ---: |
| A | ____ | ____ | ____ | ____ |
| B | ____ | ____ | ____ | ____ |
| C | ____ | ____ | ____ | ____ |
| D | ____ | ____ | ____ | ____ |
| E, if present | ____ | ____ | ____ | ____ |
| F, if present | ____ | ____ | ____ | ____ |
| G, if present | ____ | ____ | ____ | ____ |
| H, if present | ____ | ____ | ____ | ____ |

For the selected load-bearing set, record every pairwise pitch and both
diagonals. Do not force the measured points into a rectangle if they are not
one.

## M2 — Thread and usable depth at every selected receiver

| Point | Thread gauge | Go/no-go result | Usable depth (mm) | Existing recess/head clearance (mm) |
| --- | --- | --- | ---: | ---: |
| A | ____ | ____ | ____ | ____ |
| B | ____ | ____ | ____ | ____ |
| C | ____ | ____ | ____ | ____ |
| D | ____ | ____ | ____ | ____ |
| Additional selected points | ____ | ____ | ____ | ____ |

Do not infer `M3` from the CAD alone. Final screw length must be calculated
from measured stack thickness plus desired engagement, while remaining below
the measured blind-hole depth.

## M3 — Seating-plane height at selected receivers

| Measurement | Value (mm) |
| --- | ---: |
| A seating height | ____ |
| B seating height | ____ |
| C seating height | ____ |
| D seating height | ____ |
| Additional selected points | ____ |
| Maximum deck flatness error across selected points | ____ |

The V1 `OD 8 / ID 3.5 / H 4 mm` rear spacers are rejected visualization
candidates. The current-Pro lower adapter must derive its seats from these new
measurements; do not force a printed carrier onto a non-coplanar deck.

## M4 — Current white compute enclosure and cable service envelope

| Measurement | Value (mm) |
| --- | ---: |
| Enclosure maximum length | ____ |
| Enclosure maximum width | ____ |
| Enclosure maximum height above local deck | ____ |
| Enclosure front edge X datum | ____ |
| Nearest connector protrusion beyond enclosure | ____ |
| Removable-cover/tool service clearance required | ____ |
| D435i installed plug protrusion and natural bend radius | ____ / ____ |
| Mid-360 installed plug protrusion and natural bend radius | ____ / ____ |

The V1 white box is only a rejected `240 x 100 x 55 mm` photo-derived proxy.
Replace its front edge, feet, outline, height, ventilation, connectors, and
service clearance with physical values.

## After measurement

Generate a new, separate current-Pro lower adapter and update the review scene,
collision report, tool/cable checks, structural screen, and slicer evidence.
Do not regenerate V1 as though it were the current robot. Any dimensional
prototype, proof load, or moving-robot trial requires a later explicit gate.
