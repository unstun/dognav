# J17A/J20A Monolithic Rear-Web Print Adaptation Rev B

Stage: experiment + analysis  
Status: awaiting Dr Sun visual review  
Classification: `print_adaptation`  
Official CAD: no

## User-Requested Change

The two former rear M4 connection regions are joined by one continuous FDM
web instead of remaining as two independent internal posts. The front two
former M3 fusion regions and all sensor interfaces remain unchanged.

The rear web is `67.882251 mm` wide, `27.5 mm` deep, and `6.0 mm` thick. It is
shifted downward from the original rear M4 axes to avoid the S410 guard while
remaining positively engaged with both manufacturer-source bracket regions.

## Validation

- Rev B is one valid closed B-rep solid: one body, one lump, one shell, 201 faces, zero mesh bodies.
- Clean FreeCAD STEP import resolves to one valid closed solid.
- Rear-web engagement: `1308.278 mm3` with the J17A source region and `1377.971 mm3` with the J20A source region.
- Minimum modeled S410-to-new-web clearance: `1.098944 mm`.
- Added interference with D435i, MID360, S410, 291 robot bodies, and 13 retained fastener occurrences: `0.0 mm3`.
- All twelve reviewed 6 mm diameter x 30 mm tool corridors remain unobstructed by the new web.
- D435i, MID360, and S410 interface-cylinder counts remain `2`, `4`, and `4` respectively.
- Fusion visibility, opacity, camera, and transient graphics state after rendering: restored.

## Review Artifacts

- `rev-a-rear-two-posts-bottom-oblique.png`: frozen Rev A from the same camera.
- `rev-b-rear-continuous-web-bottom-oblique.png`: opaque Rev B from the same camera.
- `rev-b-rear-web-highlight-xray.png`: orange transient overlay identifies only the added continuous web.
- `rev-b-with-sensors-rear-bottom-oblique.png`: Rev B with D435i, MID360, S410, and retained sensor fasteners.
- `j17a-j20a-monolithic-rear-web-print-adaptation-rev-b.step`: candidate-only STEP; SHA-256 `ee74424eab271aa382cc81822c58d14ccf72913dd71d3ef2db5bf8f970876042`.
- `lite3-j17a-j20a-monolithic-rear-web-print-adaptation-rev-b-review.f3d`: 36-occurrence review scene; SHA-256 `1ceb6ed0f3f9d8cb694a5f5267aa08b166bc848e29692ba3e42201e7d2b2ca5c`.

## Claim Boundary

The continuous web improves geometric load distribution compared with Rev A,
but this is not a load-rated or print-ready structural release. FDM material,
print orientation, perimeter count, infill, layer adhesion, local fillets,
strength, fatigue, vibration, cable routing, dimensional tolerance, and
real-hardware safety remain unvalidated. Do not mount this revision on a moving
robot without those checks and a physical proof test.
