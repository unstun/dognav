# SCAN Forest V8 Human Dynamic-Obstacle Experiment

Status: frozen automated candidate passed 125/125; Dr Sun review pending.

V8 preserves the V7 forest, schedule, V12 policy, Lite3 Pro sensor-rig URDF,
dual-sensor settings, SCAN configurations, 1.0 m/s limit, and reactive-planning
claim boundary. It replaces only the moving actor representation with a locally
generated yellow seven-part humanoid plus a hidden collidable capsule.

The visible head, torso, pelvis, arms, and legs are separate transform-tracked
targets for both simulated sensors. Limb gait is deterministic and active only
while crossing. SCAN receives rendered geometry only; human identity, part
transforms, schedule, and capsule truth are evidence-only.

V7 evidence remains immutable. V8 stage and sensing preflights passed after one
instrumentation-path fix. The first narrow-body full run preserved a real
collision failure; a wider visible high-visibility torso then passed a no-contact
preflight, two same-input dry runs, and the frozen review candidate. The copied
candidate passed local re-evaluation, but Dr Sun's full-video review remains
mandatory.

Review entry points:

- `results/v8_human_review_candidate01/closed_loop_review_overlay.mp4`
- `results/v8_human_review_candidate01/closed_loop.mp4`
- `HUMAN_REVIEW.md`
- `VERIFICATION.md`
