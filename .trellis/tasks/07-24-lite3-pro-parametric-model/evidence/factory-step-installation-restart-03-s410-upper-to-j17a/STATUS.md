# Restart step 03: S410 guard and upper-subassembly to J17A

- Status: `rejected_wrong_j17a_j20a_through_bolt_nut_logic`
- Starting state: the visually accepted J17A/D435i first layer and the
  visually accepted J20A/MID360 upper subassembly remain separate.
- Guard interface: official S410 `4 x diameter 5.2 mm` clearance holes to
  official J20A `4 x M5` threaded axes. Four independent M5x8 socket-head
  screws remain visual candidates; no S410 nut is shown.
- Rejected layer interface: the video incorrectly represents the two front M3
  and two rear M4 axes as pre-inserted long through-bolts closed by top-side
  nuts and washers.
- Corrected interpretation to review next: J17A supplies the head seat and
  clearance path; J20A supplies the modeled threaded receiver. Mate J20A to
  J17A first, then insert the two M3 and two M4 screws from the accessible
  J17A side directly into J20A. Do not add far-side nuts or washers without
  separate physical or manufacturer evidence.
- Excluded: Lite3 robot, robot-side screws/spacers, hidden receiver proxies,
  grouped four-screw draft, and long T-driver.
- Claim boundary: hole axes and gross access are geometry-checked. Exact
  supplied screw lengths, thread engagement, torque, wrench access, strength,
  vibration, and real-hardware safety remain unvalidated.
- Validation result: the sampled paths were collision-free for the rendered
  hypothesis, but that does not validate the rejected fastener contract.
  Preserve this folder only as negative evidence. The S410 `diameter 5.2 mm`
  clearance-to-J20A `M5` threaded interface remains a separate source-backed
  observation and is not the reason for rejection.
- Next gate: Dr Sun review of the corrected direct-thread assembly logic before
  any replacement animation is generated.
