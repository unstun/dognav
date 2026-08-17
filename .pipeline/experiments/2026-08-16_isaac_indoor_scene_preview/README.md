# Isaac Indoor Scene Preview

Status: Warehouse visual composition reproduced; Office source-material
reception subset reproduced; Hospital remains a partial clay subset; human
review pending.

This experiment loads the NVIDIA Warehouse, Office, and Hospital source USD
scenes on the existing RTX 5070 Ti Isaac Sim 5.1 / Isaac Lab 2.3.2 runtime.
It captures raw headless viewport images and a stage inventory. A second pass
may insert the pinned Lite3 sensor-rig URDF as a fixed-base visual scale
reference.

## Claim Boundary

The preview can establish that a recorded USD URI resolves, loads, and renders
on the declared runtime. Robot insertion can establish visual composition and
scale only. It does not establish complete collision geometry, physics
materials, articulated locomotion, MID-360 or D435i sensing, route length,
SCAN integration, or navigation success.

The local repository is the source of truth. Remote outputs are copied back
from:

```text
/home/sun/machine-dog-nav-runs/2026-08-16_isaac_indoor_scene_preview
```

No NVIDIA scene asset is copied into this repository.

## Runtime Result

All selected artifacts were produced on the RTX 5070 Ti with Isaac Sim 5.1,
Isaac Lab 2.3.2 (`37ddf626871758333d6ed89cf64ad702aef127d0`), and driver
580.126.09. They are raw camera outputs rather than generated illustrations.

### Warehouse — selected visual candidate

- Source URI:
  `.../Assets/Isaac/5.1/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd`
- Complete source scene, source materials, 3,601 traversed prims, 792 meshes,
  and 792 directly observed CollisionAPI prims.
- The pinned Lite3 sensor-rig URDF was inserted at `[4, 2, 0.35]` as a
  fixed-base scale reference.
- Selected images:
  `results/warehouse_lite3_10/warehouse_manual_1.png` and
  `results/warehouse_lite3_10/warehouse_manual_2.png`.
- This is the only candidate in this pass that is visually ready for human
  scene selection. Fixed-base insertion is not locomotion evidence.

### Office — source-material reception subset candidate

- Source URI: `.../Assets/Isaac/5.1/Isaac/Environments/Office/office.usd`.
- The source packages the office together with 158 distant city-building
  prims. Earlier complete-source textured attempts did not produce a first
  frame within their bounds, but a 4 m source-prim reception subset rendered
  with the original source materials on the same 5070 Ti runtime. The earlier
  clay result is retained as diagnostic evidence and is no longer the selected
  Office appearance.
- A run-owned wrapper references 88 official direct-child prims around the
  reception area and hides 2,805 distant source children. It keeps the official
  city context and source materials; no source geometry is copied or converted.
- The pinned Lite3 sensor-rig URDF was inserted at `[-2, 3, 0.35]` as a
  fixed-base scale reference.
- Selected images:
  `results/office_micro_color13/office_manual_1.png`,
  `results/office_color_interior15/office_manual_1.png`, and the scale-context
  views under `results/office_lite3_color16/`.
- The first two runs show the source reception materials with and without the
  city context. The Lite3 views show only fixed-base visual scale and expose
  unresolved URDF visual-reference warnings in the importer log. None of these
  runs is a full-office, collision, locomotion, sensor, or navigation result.
- `results/office_reception_tour20/office_reception_tour.mp4` is the selected
  reception-only diagnostic. It is superseded by the global tour below because
  it covers only the earlier 4 m crop.
- `results/office_global_tour23/office_global_three_floor_tour.mp4` is the
  selected global visual candidate: 18 seconds, 960x540, 12 FPS, and 216 actual
  moving-camera Isaac RGB frames. It composes all 2,892 Office direct children
  except the separately recorded distant `SM_Buildings` city context. The tour
  shows the three authored floor surfaces at `z=-3.3, 0.0, 3.3 m`; inactive
  levels and ceilings are hidden only while their floor is presented.
- The global floor inventory is source-derived rather than inferred from stair
  height: B1 has 34 floor meshes, L0 has 99, and L1 has one landing mesh. The
  higher stair extension is not mislabeled as a fourth complete floor.

### Hospital — partial local geometry candidate

- Source URI: `.../Assets/Isaac/5.1/Isaac/Environments/Hospital/hospital.usd`.
- A run-owned wrapper references 30 official direct-child prims in a 4 m
  local region and applies one clay material.
- Selected images:
  `results/hospital_micro_clay03/hospital_manual_1.png` and
  `results/hospital_micro_clay03/hospital_manual_2.png`.
- The 8 m Hospital subset with Lite3 did not produce a first frame within the
  frozen 10-minute bound. Hospital therefore remains a geometry-only partial
  result in this pass.

## Preserved Negative Evidence

The following bounded attempts are preserved in `logs/` and must not be
reported as successful previews:

- Warehouse viewport capture without the supported offscreen path;
- Office complete source material attempts, including performance mode;
- Office larger visibility crops and direct authored-camera render products;
- Office 8 m source-material subset attempt `office_color_interior14`, which
  was interrupted after first-frame progress stalled and produced no selected
  image;
- Office complete-source probe `office_full_color_probe17`, which remained at
  the first-frame step with idle GPU utilization and produced no image;
- Office tour 18, whose raw frame zero was black before the camera settled, and
  tour 19, whose video passed visual triage but whose requested run-log path was
  misspelled. Both are superseded by logged rerun 20;
- Office global tour 22, which required a nonexistent fourth floor and exited
  before capture. Its clean shutdown and empty result are preserved; corrected
  three-floor tour 23 supersedes it;
- Hospital 8 m clay subset with fixed-base Lite3.

The failures established three reusable constraints: use a newly created
offscreen camera rather than binding the source Camera prim directly; separate
the Office city-building context from indoor collision/route qualification;
and do not assume a visually plausible source scene is lightweight enough for
the 5070 Ti. The successful colored subset also shows that a failed complete
render must not be generalized into a claim that source materials are unusable.
