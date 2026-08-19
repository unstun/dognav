# Verified Current Behavior for Office Review Visualization R2

## Evidence Boundary

- `.pipeline/experiments/2026-08-17_office_l0_scan_crowd/REPORT.md:7` records
  candidate38/39 automated PASS and AC55 pending.
- The report explicitly keeps AC55 human-owned at lines 17--21 and 141--146.
- Candidate38/39 are immutable inputs to this child task; no existing run may
  be edited or renamed.

## Robot Appearance

- Candidate39 and the earlier forest review candidate both record Isaac-safe
  robot asset SHA-256
  `803d552703bcc4f72ce15f38b95bc3f62e3e4ada0b42bf3ecf71b32b6590bb9d`.
  The robot asset itself did not change.
- The exact local sibling asset has 13 visual elements but only 8 explicit
  material/colour elements. The main torso, hip, and thigh visuals do not carry
  explicit colours; one shank visual is explicitly white.
- The Office runtime adds a 900-intensity neutral dome light at
  `integration/lite3_sim_bridge/lite3_sim_bridge/run_isaac_v12_fallback.py:1854`.
- Contact-sheet inspection shows the light robot against a light floor with
  weak silhouette/part contrast. The same asset is easier to see on the green
  forest background. This supports a presentation/contrast diagnosis, not a
  physics or asset-identity change.

## Current Camera Contract

- One writer is initialized at
  `run_isaac_v12_fallback.py:3287` and opened at `:3597`.
- Office capture computes one root-relative chase camera and calls one render at
  `run_isaac_v12_fallback.py:4453--4478`.
- A wall-occlusion fallback is recorded at `:4479--4497`.
- Run identity currently records only one camera eye/look-at pair at
  `run_isaac_v12_fallback.py:2982--2990`.

## Current Trajectory Review Contract

- `trajectory_review.py:46--60` validates and samples true XYZ B-spline points.
- `_plot_bounds`, `_world_to_inset`, and the accumulated actual path discard Z
  at `trajectory_review.py:231--278` and `:407`.
- Candidate39 raw evidence contains B-spline control-point Z in approximately
  `0.295--0.854 m` and physical root Z in approximately `0.282--0.350 m`.
  A non-decorative 3D view is therefore feasible from already recorded data.

## Required Quality Contracts

From `.trellis/spec/backend/quality-guidelines.md`:

- preserve policy/asset/sensor identities and local/remote hashes
  (`:341--479`);
- do not use truth to populate planner input, and retain simulator-time causal
  alignment (`:757--897`, `:1238--1248`);
- same-input runs must compare normalized identities and independently pass
  (`:1249--1255`, `:1293--1300`);
- preserve failed runs and leave human acceptance unchecked until Dr Sun's
  explicit decision.

## Remote Boundary

- `.pipeline/experiments/2026-08-13_scan_foxy_isaac_closed_loop/execution_manifest.yaml`
  records SSH alias `gpu5070ti`, Isaac Sim 5.1, the isolated Foxy boundary, and
  local-to-remote-to-local hash parity requirements.
- The remote workspace is an execution copy. Remote-only edits or success are
  invalid.
