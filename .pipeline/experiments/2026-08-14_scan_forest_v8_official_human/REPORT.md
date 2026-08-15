# V8 R2 Official Isaac Human — Visual Preflight Record

## Current disposition

- Stage: experiment + analysis.
- Automated composition preflight: `PASS`.
- Human appearance review: pending Dr Sun.
- SCAN forest avoidance with the official human: not run yet.
- Strongest claim: the official animated person, Lite3 Pro sensor-rig asset,
  V12 `model_149999`, PhysX, and both simulated sensors co-executed in one
  bounded Isaac Lab qualification scene.

## Implemented composition

- Visible character: NVIDIA Isaac Sim 5.1 `male_adult_police_04`, referenced by
  versioned URL and not redistributed in this repository.
- Animation: NVIDIA Biped AnimationGraph output after its `ControlRigAPI`
  retargets to the exact 101-joint official character skeleton.
- Runtime boundary: the Biped graph executes in a separate bounded Isaac
  process. Its 30 Hz local joint output is cached and replayed through one
  `UsdSkelAnimation` slot in the Direct-GPU Lite3 process. No local procedural
  gait is used.
- Physics and sensing: a hidden 1.70 m by 0.30 m terrain-seated capsule under a
  separate kinematic root owns collision, clearance, MID-360-like returns, and
  D435i-like depth returns.
- Registration: visual and physical roots share schedule time, XY, and heading.
  The visual root uses the official shoe sole as its vertical datum; the capsule
  uses its centre. The recorded foot-to-capsule-bottom error is approximately
  `1e-16 m` and the visual-root pose readback error is `0 m` in the preflight.

## Direct evidence

- Review video:
  `v8_official_lite3_visual_preflight06/lite3_official_human_preflight.mp4`
  - H.264, 1280 x 720, 25 fps, 153 frames, 6.12 s.
  - SHA-256:
    `ff7f4afd9ac854426a184cc100a7c84b72418b449876642900745b0db8de4fb6`.
- Official cache probes 01 and 02 produced the same file and content hashes:
  - content SHA-256:
    `76c19b57ebd03e01820e6b9db79bde8f2f3e436302744ef457278af8d17ef5b3`;
  - file SHA-256:
    `ac58a683fe9dd85ec3ad0266c7653b289dc1dd9b256d2abac0cc96ac7e45cfcb`;
  - 101 joints, 60 idle frames, 90 walk frames, 30 Hz.
- Cache variability check:
  - idle maximum translation/component-rotation deltas: about `0.000361 m` /
    `0.0432`;
  - walk maximum translation/component-rotation deltas: about `0.0380 m` /
    `0.547`.
  These reject a static T-pose cache.
- Local and 5070 Ti hashes matched for the main runtime, cache baker, and shared
  official-human contract after the final quality fix.
- Local integration suite: 77 tests plus 5 subtests passed. Python compilation,
  shell syntax, ShellCheck, and `git diff --check` passed.

## Negative evidence preserved

- Early visual preflights rendered the official character in T-pose and are not
  review candidates.
- Direct use of the People graph in the pinned Direct-GPU PhysX/Fabric process
  caused reproducible CUDA illegal-access failures. Moving the graph outside the
  rigid root did not solve the conflict.
- The CPU-physics isolation attempt completed but did not satisfy the target
  composition. These failures motivated the separate bake/replay boundary.

## Human gate and next action

Dr Sun must review the visual preflight for character choice, scale, terrain
seating, and gait. Only after explicit approval may the unchanged SCAN/V7
reactive path run the no-contact preflight, two same-input full dry runs, and a
frozen official-human review candidate. Automated `PASS` does not satisfy that
human gate.
