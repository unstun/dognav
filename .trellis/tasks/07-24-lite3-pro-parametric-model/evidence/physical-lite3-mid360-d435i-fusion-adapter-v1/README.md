# Physical Lite3 Mid-360 + D435i Fusion Adapter V1

## Supersession notice

**Rejected for Dr Sun's current Lite3 Pro robot interface.** The purchased
robot is a newer Pro hardware revision than the legacy V1.0.7 manual and is
not the local Experience-style B-rep used by this package. V1's robot-side
holes, screws, spacers, placement, installation video, and fit claim must not
be used for fabrication.

The upper Mid-360/D435i/S410 geometry and internal digital checks are retained
as reusable or historical evidence only. A new, separate current-Pro lower
adapter requires physical receiver and compute-enclosure measurements. See
`STATUS.md` and `validation/current_lite3_pro_interface_rejection.json`.

## Outcome

This package was an engineering-review candidate for the physical white Lite3
shown in `source/physical-lite3-user-photo-2026-07-29.jpg`. It retains the
existing white Interface enclosure and places the fused Mid-360/D435i sensor
module on the vacant forward deck. The printable carrier is one connected
solid derived from the source J17A and J20A exterior/interface geometry, with
two local front fusion regions and a 10 mm continuous rear structural web.
It is explicitly **not official factory CAD**.

The archived digital package passed topology, modeled interference, tool-corridor,
source-axis, conservative Interface-envelope, preliminary load-screen, and
slicer-smoke checks. Physical Lite3 thread positions/depths, the exact
Interface envelope, printed material properties, fatigue, torque, and cable
routing remain measurement/test gates. Subsequent hardware-revision review
rejected its robot-side interface, so it is **not a current-Pro CAD-review
candidate and not released for fabrication or robot motion**.

## Primary deliverables

- `cad/lite3-mid360-d435i-monolithic-carrier-v1.FCStd`: editable parametric
  FreeCAD source.
- `cad/lite3-mid360-d435i-monolithic-carrier-v1.step`: neutral B-rep export.
- `cad/lite3-mid360-d435i-monolithic-carrier-v1.stl`: slicer input.
- `cad/lite3-mid360-d435i-fusion-adapter-v1-review.f3d`: complete Fusion review
  scene with Lite3, sensors, guard, candidate fasteners, and keep-outs.
- `parameters.json`: machine-readable dimensions, assumptions, and evidence
  status.
- `docs/BOM.csv`: candidate hardware bill.
- `docs/ASSEMBLY.md`: human-feasible assembly sequence represented by the
  animation.
- `docs/MEASUREMENT_CARD.md`: minimum physical measurements required before
  manufacturing release.
- `validation/`: direct geometry, assembly, load-screen, slicer, render, and
  video evidence.
- `manifest.sha256`: checksums for every retained deliverable except the 960
  regenerable intermediate PNG frames and FreeCAD/cache backups.
- `renders/07-complete-lite3-global-isometric.png`: final whole-robot view.
- `video/lite3-mid360-d435i-fusion-adapter-v1-installation-no-text.mp4`:
  no-text, step-by-step installation animation.

## Model classification

| Item | Classification | Current claim |
| --- | --- | --- |
| Lite3 robot | user-supplied manufacturer-style B-rep | visual and nominal CAD registration only |
| Mid-360 | official Livox CAD | sensor exterior and mounting-interface evidence |
| D435i | official manufacturer CAD translated by Fusion | sensor exterior and two rear M3 axes |
| J17A/J20A/S410 | official public Lite3 Venture extension files | related-source interface evidence, not proof of this physical chassis |
| V1 monolithic carrier | archived print adaptation | upper geometry evidence only; robot interface rejected |
| White Interface box | photo-derived conservative keep-out | 240 x 100 x 55 mm visualization envelope pending measurement |

## Review order

1. Watch the installation video and inspect the final global render.
2. Review `docs/MEASUREMENT_CARD.md` against the physical Lite3.
3. Enter measured values into `parameters.json` and regenerate all exports.
4. Re-run geometry and slicer checks.
5. Only after coupon and stationary proof-load tests may a tethered, low-speed
   robot trial be considered.
