# J17A/J20A Monolithic Print Adaptation Rev A

Stage: experiment + analysis  
Status: retained as the reversible Rev B parent; not the current review candidate  
Classification: `print_adaptation`  
Official CAD: no

Dr Sun requested a continuous rear FDM web on 2026-07-29. Rev A remains
unchanged as the frozen parent and rollback artifact; current visual review is
the separately named Rev B rear-web candidate.

## Candidate

- Preserves the current reviewed J17A and J20A exterior pose and sensor interfaces.
- Keeps both manufacturer source occurrences unchanged and hidden.
- Replaces the former 2 x M3 and 2 x M4 inter-layer fasteners with four internal fusion zones.
- Resolves to one closed B-rep solid with one lump, one shell, 192 faces, and no mesh body.
- Retains the 2 x D435i M3 clearance cylinders, 4 x MID360 M3 clearance cylinders, and 4 x S410 M5 receiver cylinders.

## Validation

- Fusion topology and interface validation: pass.
- Clean FreeCAD STEP import: one valid closed solid, pass.
- Added volumetric interference with D435i, MID360, and S410 guard: `0.0 mm3` for each.
- Conservative 6 mm diameter x 30 mm tool corridors for all D435i, MID360, and S410 fasteners: clear in the modeled assembly order.
- Review F3D central directory: 260 entries; full size and CRC validation passed for all 248 files, including 245 Zstandard-compressed entries.
- Fusion visibility, opacity, camera, and transient graphics state after rendering: restored.

## Review Artifacts

- `monolithic-isolated-oblique.png`: isolated real B-rep candidate.
- `monolithic-with-sensors-oblique.png`: candidate with D435i, MID360, S410 guard, and retained sensor fasteners.
- `monolithic-four-fusion-zones-xray.png`: transient orange overlays identify the four internal fusion zones.
- `j17a-j20a-monolithic-print-adaptation-rev-a.step`: candidate-only STEP; SHA-256 `30e5be6d3a001901e4a4583012c32ebb1bda71924fc86fbeef332557cc73c105`.
- `lite3-j17a-j20a-monolithic-print-adaptation-rev-a-review.f3d`: 35-occurrence review scene; SHA-256 `03a60ce1d11b4d707ae0f21c86171baffdd637aed3a1d2d2f9558c72231eb1e5`.
- `pre-monolithic-34-occurrence-scene-backup.f3d`: reversible pre-change scene backup.

## Claim Boundary

This proves only one-piece geometry, preserved modeled interfaces, zero modeled sensor collision, and the tested tool corridors. Material choice, print orientation, local fillet/rib sizing, layer adhesion, strength, fatigue, torque, vibration, fabrication tolerance, and real-hardware safety remain unvalidated. Do not fabricate or mount on a moving robot from this revision without those checks.
