# Restart step 02: J20A + MID360 direct-thread animation

- Status: `accepted_for_sequence_continuation`
- Scope: bare J20A second-layer bracket, official Livox MID360 BRep, and four
  independent visual M3x8 screw candidates only.
- Excluded: J17A, D435i, S410, Lite3 robot, nuts, and all unrelated hardware.
- Sequence: MID360 reaches its modeled J20A mount position first; screws then enter from the J20A
  underside in diagonal cross order `11 -> 13 -> 12 -> 14`.
- Geometry check: the original J20A and official MID360 models retain a
  `0.2000166 mm` minimum clearance with zero cross-interference. Closing that
  gap by translating the whole MID360 produces `784.0477 mm^3` interference,
  so the animation preserves the source-model position instead of forcing
  face contact.
- Claim boundary: the 48 x 36 mm four-hole pattern and axes are geometrically
  validated. `M3x8` remains a visual fastener candidate until physical
  engagement and torque are checked on hardware.
- Visual acceptance: Dr Sun accepted the step-02 video on 2026-07-29.
- Next authorized step: add the official S410 guard, then connect the completed
  upper subassembly to the first-layer J17A with the existing front and rear
  through-fastener groups.
