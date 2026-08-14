# V7 Human Review Checklist

Status: R2 candidate ready for Dr Sun review; not yet accepted.

Review candidate: `forest_v7_review_candidate03`

Superseded automated candidates: `forest_v7_review_candidate01` and
`forest_v7_review_candidate02`

Required complete videos:

- `results/forest_v7_review_candidate03/closed_loop_review_overlay.mp4`
- `results/forest_v7_review_candidate03/closed_loop.mp4`

The contact sheets are navigation aids only and cannot replace watching both
36.35 s videos:

- `results/forest_v7_review_candidate03/review_contact_sheet.jpg`
- `results/forest_v7_review_candidate03/raw_contact_sheet.jpg`

Dr Sun must explicitly check:

- [ ] The orange cylinder waits, crosses, visibly holds in the route, and
  leaves without teleporting.
- [ ] The Lite3 avoids the cylinder with no visible body contact or hidden
  reset; its turn is consistent with the SCAN path rather than a scripted turn.
- [ ] In the inset, green is the active SCAN path, cyan is the Isaac physical
  root path, and orange is the dynamic-obstacle path; their timing and geometry
  agree with the main view.
- [ ] The robot maintains acceptable clearance from the orange cylinder, tree,
  rock, and terrain; the corrected rock placement does not visibly penetrate
  or float.
- [ ] The approximately 1 m/s motion, gait, body attitude, contacts, final goal
  approach, and stop behavior are visually acceptable.
- [ ] The raw video agrees with the derived overlay and contains no hidden cut,
  base teleport, or unexplained scene change.

Decision: pending.

Automated evidence: R2 frozen 120/120 PASS, locally re-evaluated 120/120. Agent
frame inspection found the obstacle, robot, forest geometry, and overlay
visible, but cannot fill the checkboxes or accept the candidate for Dr Sun.
