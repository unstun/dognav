# V8 Human Review Checklist

Status: automated candidate ready for Dr Sun review; not human-accepted.

Review candidate: `v8_human_review_candidate01`

Watch both complete 35.82 s files. The contact sheet is navigation-only and
cannot replace either video:

- `results/v8_human_review_candidate01/closed_loop_review_overlay.mp4`
- `results/v8_human_review_candidate01/closed_loop.mp4`
- `results/v8_human_review_candidate01/review_frames/contact_sheet.jpg`

Dr Sun must explicitly check:

- [ ] The yellow obstacle is recognizably human-shaped, with a visible head,
  torso, pelvis, two arms, and two legs; no cylinder fallback is visible.
- [ ] Arms and legs swing in opposite pairs while the person crosses and return
  to a neutral pose while holding or parked; motion has no visible teleport.
- [ ] The Lite3 stops or replans before the person, avoids visible contact, and
  resumes only when the route is safe; the response is consistent with the
  SCAN path rather than a scripted robot turn.
- [ ] In the inset, green is the active SCAN path, cyan is the Isaac physical
  root path, and yellow is the person's physical path; timing and geometry
  agree with the main view.
- [ ] The robot maintains acceptable visible clearance from the person, tree,
  rock, and terrain; no rock/tree penetration or floating is apparent.
- [ ] Approximately 1 m/s motion, gait, body attitude, foot contacts, final
  approach, stop, and post-stop stance are visually acceptable.
- [ ] The raw video agrees with the derived overlay and contains no hidden cut,
  reset, base teleport, or unexplained scene change.

Decision: pending.

Automated evidence: frozen 125/125 PASS and local 125/125 re-evaluation. Agent
frame inspection confirms the person, robot, forest, and three trajectory
traces are visible, but cannot fill these checkboxes or accept the candidate.
