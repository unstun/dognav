# Office L0 Multi-Pedestrian Lite3 + SCAN Review Visual Round 3 Remediation Return

- **Task**: `.trellis/tasks/08-17-office-crowd-review-visual-r2`
- **Date**: 2026-08-17
- **Author**: Antigravity Assistant
- **Status**: `READY_FOR_CODEX_REVIEW`
- **Stage**: `experiment + analysis`
- **Source of Truth**: `/Users/sun/.codex/worktrees/164f/machine-dog-nav`
- **Immutable Evidence Preserved**: `candidate38`, `candidate39`, `dryrun11`, `dryrun12`, `dryrun24`, `dryrun25`

---

## 1. Executive Summary

In this Round 3 remediation, the Office review presentation pipeline has been completely rewritten and unified into an opt-in, non-destructive, strictly validated multi-view capture and verification architecture.

All defects identified in the Codex Round 2 review and the five fail-open reproduction cases have been resolved and verified with fail-closed regression tests.

---

## 2. Summary of Implementation & Changes

### A. Module `integration/lite3_sim_bridge/lite3_sim_bridge/office_review_presentation.py` (New / Full Rewrite)
1. **Multi-Camera Configuration & Target Calculations**:
   - `validate_side_camera_config` & `side_follow_desired_pose`: Smooth external side-follow observer tracking robot lateral aspect.
   - `validate_overview_camera_config` & `overview_desired_pose`: Elevated wide-angle overview displaying route, Lite3, pedestrians, and office corridors.
   - `smooth_pose_bounded`: Exponential pose filter bounded by strict maximum eye/target speed displacement $\Delta \le v_{\max} \cdot dt$. Any non-positive or non-finite $dt \le 0$ immediately raises `ValueError`.
2. **True Before/After Measured USD Material Audit**:
   - `query_stage_robot_inventory`: Directly queries USD stage body prims, joint prims, collision prims, visual mesh prims, applied material bindings, and mass.
   - `apply_office_review_material_usd`: Creates USD `UsdPreviewSurface` shaders for robot visual meshes only (torso: warm amber `[0.92, 0.42, 0.05]`, limbs: deep graphite `[0.12, 0.12, 0.14]`, `opacity=1.0`, `emission=0.0`). Strictly rejects any non-robot scene prims.
   - `build_material_audit`: Explicitly compares pre-inventory against post-inventory to ensure physics invariant topology, collision shapes, mass, and joint kinematics remain 100% identical.
3. **1920x1080 Multi-View 3D Dashboard**:
   - `render_office_review_dashboard`: Direct single-generation encoding via ffmpeg rawvideo pipe (`libx264`, `yuv420p`, `crf=16`, `preset=medium`).
   - 5-zone layout:
     - Top Row (1920x360): Tile 1 (Primary Chase 640x360) + Tile 2 (Side-Follow 640x360) + Tile 3 (Elevated Overview 640x360).
     - Bottom-Left (960x720): 3D isometric world coordinate XYZ trajectory panel (true isometric math, equal scale across all axes, real Z span sensitivity, drawn SCAN B-splines, physical root path, downsampled inflated occupancy points).
     - Bottom-Right (960x720): Telemetry HUD & causal event timeline. Explicitly shows measured metrics (speed, command, contact force, clearance, watchdog) or `unknown`. No hardcoded fake "PASS" or "0" values.
   - Complete removal of `overwrite` parameter; existing output files raise `FileExistsError`.
4. **Strict Fail-Closed Validator**:
   - `validate_office_review_presentation`: Enforces all 10 inputs (`first_video`, `side_video`, `overview_video`, `camera_trace`, `material_audit`, `dashboard_video`, `dashboard_metadata`, `ros_events`, `metrics`, `run_identity`).
   - Full 4-video frame-by-frame decoding, rational frame rate checking, mutual SHA-256 exclusion preventing cloned camera feeds, frame count consistency, camera trace speed bound validation, physical root and plan Z span sensitivity, and material audit verification.

### B. Module `integration/lite3_sim_bridge/lite3_sim_bridge/run_isaac_v12_fallback.py`
1. **Multi-Camera Capture Loop**:
   - Enforces a single root-state snapshot per step:
     ```text
     completed physics step
       -> snapshot root pos/quat
       -> render primary chase view -> video_writer
       -> render side-follow view -> third_person_video_writer
       -> render overview view -> overview_video_writer
       -> append shared multi-view camera trace row
       -> advance to next physics step
     ```
   - Zero `env.step()` calls between multi-camera renders.
   - Closed-loop policy, physics step, sensor rig, and RL locomotion controller remain strictly untouched.
2. **Opt-in Review Lighting**:
   - Added `--office-review-lighting`, `--office-review-light-intensity`, `--office-review-light-color` flags (default disabled).
3. **Packaging & Report**:
   - Direct integration of 3 raw videos, camera trace, material audit, dashboard video, dashboard metadata into `qualification_report.json` with full SHA-256 and byte counters.
   - Invokes `render_office_review_dashboard` and `validate_office_review_presentation` when review presentation is active.

### C. Launcher & Input Hashing
- Updated `run_remote_closed_loop.sh` to include `office_review_presentation.py` in `input_sha256.txt`.

---

## 3. Five Codex Fail-Open Defects Remediation Matrix

| Defect # | Codex Round 2 Identified Defect | Remediation Implementation | Test Assertion in `test_office_review_presentation.py` |
| :--- | :--- | :--- | :--- |
| **Defect 1** | Validator allowed omitted provenance (`ros_events`, `metrics`, `run_identity`) | All 10 input paths are required parameters; non-existent or empty inputs raise issues and return `passed=False` | `test_reproduction_omitted_provenance_fails` (`passed == False`) |
| **Defect 2** | Trace accepted `NaN` dt and missing/empty `run_identity` | `smooth_pose_bounded` rejects $dt \le 0$ / `NaN`; `camera_trace_row` requires non-empty `run_identity`; validator checks monotonic sim time and valid `run_identity` matching run identity file | `test_reproduction_nan_dt_and_missing_run_identity_fails` (`passed == False`) |
| **Defect 3** | Material audit allowed fabricated/copied audit targeting non-robot geometry | `apply_office_review_material_usd` inspects USD prim hierarchy; `build_material_audit` verifies prims belong to robot root; validator checks pre/post inventory and physics invariance | `test_reproduction_fabricated_material_audit_fails` (`passed == False`) |
| **Defect 4** | Dashboard accepted empty metrics/events with hardcoded fallback values | `render_office_review_dashboard` requires valid B-splines, events, and metrics; raises `ValueError` if empty; renders `unknown` for absent telemetry | `test_reproduction_empty_plan_metrics_fails` (`raises ValueError`) |
| **Defect 5** | Overwrite was enabled by default / allowed | Completely removed `overwrite` argument; presence of destination output files raises `FileExistsError` | `test_reproduction_overwrite_forbidden` (`raises FileExistsError`) |

---

## 4. Test Verification Results

All tests have been executed locally in `/Users/sun/.codex/worktrees/164f/machine-dog-nav` and logged to `.trellis/tasks/08-17-office-crowd-review-visual-r2/logs/antigravity-round3-tests.txt`.

### A. Targeted Suite
```bash
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest \
    integration.lite3_sim_bridge.tests.test_trajectory_review \
    integration.lite3_sim_bridge.tests.test_office_review_presentation
```
**Result**: `Ran 32 tests in 6.774s: OK`

### B. Full Bridge Suite
```bash
PYTHONPATH=integration/lite3_sim_bridge \
  python3 -m unittest discover \
    -s integration/lite3_sim_bridge/tests -p 'test_*.py' -v
```
**Result**: `Ran 111 tests in 7.214s: OK`

---

## 5. Preserved Invariants & Boundaries

1. **Evidence Integrity**: `candidate38`, `candidate39`, `dryrun11`, `dryrun12`, `dryrun24`, and `dryrun25` remain strictly unmodified.
2. **Criteria Gate**: AC54 remains `PASS`. AC55 is preserved for Dr Sun's human review judgment.
3. **Execution Gate**: No remote Isaac Sim run, training, or real-robot actuation was conducted.
4. **Clean Diff**: All edits are confined to the review presentation pipeline, test suites, and launchers.

---
**Status**: Ready for Codex review.
