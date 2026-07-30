# Current Lite3 Pro Hardware-Revision Audit

## Bottom line

The purchased robot must be treated as the current Lite3 Pro hardware
revision, not the Pro represented by the 2024 V1.0.7 manual and not the local
Exploration/Experience assembly STEP.  The existing fusion-adapter V1 cannot
be promoted to current-Pro fit evidence.

The current upper sensor relationships may still be reused as a separable
Mid-360/D435i/S410 module.  Its robot-side lower carrier must be redesigned
after the purchased Pro's exposed receivers and compute-enclosure keep-out are
measured.

## Verified revision evidence

| Evidence | Direct finding | Design use | Not proved |
| --- | --- | --- | --- |
| DEEP Robotics Pro Manual V1.0.7-0, 2024-03-26 | `610 x 370 x 445 mm`, `12.7 kg`; payload page shows `4 x M3`, `74 x 94 mm` | Legacy-version comparison only | Current delivered hole pattern |
| DEEP Robotics 2025 brochure | Pro is `610 x 370 x 450 mm`, `12.9 kg`, `4 kg`; LiDAR is `610 x 370 x 496 mm`, `13.5 kg`, `2.5 kg` | Confirms a changed marketed revision/spec set | Mounting axes, thread depth, enclosure dimensions |
| Official current Pro and LiDAR product images | Same long rear/centre compute enclosure; LiDAR/depth-camera module is forward of it | Current visual layout and conflict envelope | Hidden lower carrier and fasteners |
| Dr Sun's physical photograph | Long white compute enclosure and forward free-deck layout match the current marketed Pro family | Physical target identity and available-region evidence | Metric geometry from one oblique blurred image |
| Official FAST-LIVO2 repository, commit `624b45c` | Printable hardware is explicitly `Lite3 Venture (ONLY THIS VERSION!)`; Pro/LiDAR already has onboard compute | Keeps J17A/J20A files as related-source upper-module evidence only | Current-Pro robot-side bracket fit |

The older-to-current official spec change is `+5 mm` standing height and
`+0.2 kg` mass.  This is enough to invalidate silent revision equivalence even
though it does not reveal which mechanical parts changed.

## V1 rejection

The V1 animation used two non-coplanar candidate robot rows recovered from the
local Experience-style assembly context:

- front lateral pitch: `65.0 mm`;
- rear lateral pitch: `105.004442 mm`;
- row-centre longitudinal separation: `133.998676 mm`;
- seating-plane difference: `5.0 mm`.

Those axes are not a rigid `74 x 94 mm` rectangle and are not evidence for the
current delivered Pro.  The V1 parameter named `robot_rear_pair_pitch` also
stored the `67.882251 mm` rear-web width rather than the actual animated rear
screw pitch.  V1 remains useful only for upper-module topology, internal
sensor interfaces, collision-method evidence, and negative interface history.

## Current-Pro lower-adapter contract

The next robot-side part must remain separate from the validated upper sensor
module until the fit review closes.  It must:

1. place the sensor module ahead of the compute enclosure, consistent with the
   current official LiDAR image;
2. use only measured receivers on the purchased Pro;
3. keep the centre and rear region open around the compute enclosure, feet,
   cable, ventilation, and driver corridors;
4. expose each robot-side screw to a human tool in a non-colliding assembly
   order;
5. parameterize the sensor-module forward offset instead of deriving it from
   an image;
6. retain no Experience/Venture hole as a current-Pro claim.

## Physical gate before new printable CAD

Record a true top view or caliper measurements for:

- every usable top-deck hole centre, labelled from robot front and centreline;
- left-right and front-back pitch between those centres;
- thread designation and usable depth;
- deck seating-plane height and any local recess/counterbore;
- compute-enclosure front edge, width, height, feet, and cable/vent keep-outs.

Until these values exist, a lower adapter can be a parameter template or visual
envelope only.  It is not a fabrication-ready part.
