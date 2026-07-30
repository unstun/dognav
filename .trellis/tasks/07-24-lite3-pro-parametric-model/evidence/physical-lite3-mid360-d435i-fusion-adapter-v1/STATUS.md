# Status

`superseded_rejected_for_current_lite3_pro_robot_interface`

Dr Sun confirmed that the purchased robot is the current Lite3 Pro hardware
revision and differs from the earlier Pro. V1 is therefore rejected as a
robot-side fit or installation package. It used an Experience-style robot
context and Venture/J17A-derived attachment assumptions rather than measured
current-Pro receivers and the current compute-enclosure geometry.

The one-solid carrier, official Mid-360/D435i geometry, related-source S410
guard, internal sensor interfaces, topology checks, and validation methods are
retained as reusable or historical evidence. They do not validate the V1
lower attachment to Dr Sun's current Pro.

The actual V1 animated robot-side rows are `65.0 mm` and `105.004442 mm` wide,
separated by `133.998676 mm`, with a `5.0 mm` seating-plane difference. The
parameter called `robot_rear_pair_pitch` stored the `67.882251 mm` rear-web
width rather than the animated rear screw pitch. See
`validation/current_lite3_pro_interface_rejection.json`.

## Retained internal digital checks

- clean STEP import: one valid closed solid, one shell, 195 faces, and
  `74958.516410 mm3` volume;
- STL: one solid component, 26428 facets, and `0.0331%` volume deviation;
- sensor/guard interface-axis counts: `2 / 4 / 4`;
- positive-volume carrier collision: `0 mm3` with D435i, Mid-360, S410, and
  all 291 checked Lite3 bodies;
- nominal photo-derived Interface keep-out: `0 mm3` collision and `10 mm`
  minimum distance;
- every modeled D435i, Mid-360, and S410 external driver corridor is clear;
- preliminary 5g x 2 load-factor screen: `6.954 MPa` nominal rear-web bending
  stress and `2.588` nominal margin against the declared `18 MPa` allowable;
- slicer smoke: 0.6 mm nozzle, 0.25 mm layers, six perimeters, 45% gyroid,
  supports and brim, with a `6h31m32s` estimate;
- installation media: 960 sequential 1280 x 720 frames, 40 seconds at 24 fps,
  H.264/yuv420p, no audio, no text overlay, and zero full-decode errors;
- all four Fusion animation chunks restored transforms, visibility, graphics,
  and position-snapshot state.

These checks remain true only inside the archived V1 digital scene. They do
not overcome the rejected robot identity and interface.

## Required before a current-Pro replacement

Measure every usable current-Pro top-deck receiver, thread and usable depth,
seating height/recess, and the complete white compute-enclosure feet/front-edge/
cable/vent/tool envelope. Design a separate current-Pro lower adapter after
those values exist; do not regenerate V1 by substituting another guessed hole
pattern.

No print, physical fastener operation, drilling, or robot actuation was
performed. V1 must not be fabricated for the purchased current Pro.
