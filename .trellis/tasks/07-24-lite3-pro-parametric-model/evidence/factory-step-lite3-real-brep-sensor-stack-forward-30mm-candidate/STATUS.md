# Status

`rejected_interface_mismatch`

Dr Sun rejected this candidate after the physical-top view showed that the
J17A robot-side mounting features do not align with the visible front chassis
features. This is not a remaining fore/aft registration error.

The first interface audit selected the wrong J17A hole group: it compared the
separate `4 x M3`, `110 x 86 mm` feature instead of the four large
installation holes identified in the official installation video. That error
is corrected in `mount_interface_audit.json`.

The correct group is the drawing's `4 x diameter 4.50 mm` through holes with
`diameter 8 mm` counterbores. Their Fusion B-rep centres form a
`67.88225 x 67.88225 mm` square. The circled front J17A row has
`67.88225 mm` pitch, while the circled robot row has approximately
`65.00172 mm` pitch and is currently `40.92332 mm` farther toward robot `+Z`.
Aligning the row midpoints would still leave each hole approximately
`1.440265 mm` off-axis. A full search of `71` plausible robot circular-feature
centres found at most `1/4` matches at `0.5 mm` tolerance.

The J17A source is explicitly declared for `Lite3 Venture only`, while the
supplied robot source is an Exploration top-level assembly with an Experience
robot child.

The earlier `30.0 mm` forward and `2.4 mm` downward transform, zero solid
intersection, and `0.006602556 mm` numerical contact remain immutable evidence
for this rejected visual-placement candidate. They do not prove an attachment.

Do not translate this stack again to make one feature look aligned. Replacement
work requires either matching Lite3 Venture/LiDAR chassis/interface CAD or an
official manufacturer adapter/base CAD. A custom base remains outside the
current instruction.

The Fusion document remains intentionally unsaved and unchanged for visual
inspection.
