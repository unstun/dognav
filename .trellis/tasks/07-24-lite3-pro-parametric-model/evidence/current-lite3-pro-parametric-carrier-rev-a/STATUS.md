# Status

`carrier_rev_e_geometry_complete_print_release_still_blocked`

- Stage: experiment + analysis
- Session handoff: continued from Codex session `019fa20a-82f7-7750-95ab-f7293fef79ea`,
  driven from Claude Code through the Fusion MCP server.
- Fusion document `Lite3Pro_SensorCarrier_Lightweight` (hub `sun` / project
  `Default Project` / root folder) is **saved and closed** at checkpoint-13.
- **Printable release remains blocked.** Nothing here authorises fabrication:
  print clearance, fillets, and the sensor fit re-check are all outstanding.

## Exported artifacts

| File | Size | Content |
| --- | --- | --- |
| `cad/carrier-rev-e-rear-tabs-group-b.step` | 621 KB | the rev-e carrier alone |
| `cad/carrier-rev-e-rear-tabs-group-b.stl` | 402 KB | same, high mesh refinement |
| `cad/lite3pro-carrier-scene-rev-e.step` | 56 MB | full scene: robot torso, host, carrier |

34 renders in `renders/`.

## Robot registration (the load-bearing result of this session)

The Experience-branch torso B-rep
(`../factory-step-lite3-lightweight-brep/superseded-torso-only/lite3-real-brep-lightweight.step`,
89 solids, 22 803 faces, legs absent) was imported and registered **from geometry,
not by eye**:

- source `+Z` -> robot forward (`+X`), source `+X` -> robot left (`+Y`),
  source `+Y` -> up (`+Z`);
- datum: the 65.00 mm front bore pair at source `X = +/-32.50`, `Z = 219.000`;
- seating plane: hole top at source `Y = 61.387`.

Verification: after transform the two front bores land at `X = -0.000`,
`Y = +/-32.500`, `Z(top) = 0.000`. This matches
`../current-lite3-pro-lower-adapter-measurement-gate/measurement_results.json`
exactly, so the photo-derived 65 mm pitch and the CAD agree.

Dr Sun confirmed the local CAD *is* his robot; the Pro differs only by the added
perception host. The legacy `74 x 94 mm` manual figure is therefore superseded,
not a live candidate.

## Robot top-side M3 receivers (complete enumeration)

All ten top-accessible `dia 2.5` threaded bores on the robot:

| Group | Y | X | Span | Thread depth | Insert thickness |
| --- | --- | --- | --- | --- | --- |
| A | +/-32.5 | 0 | 2 holes only | **2.40 mm** | 2.40 mm |
| B | +/-52.5 | -134, -304 | 170 mm | **6.00 mm** | 6.00 mm |
| C | +/-72.5 | -116.5, -321.5 | 205 mm | **3.00 mm** | 3.00 mm |

Group B and group C both centre on `X = -219.0`, `Y = 0`; the `Z = 6.168` deck
pocket (`X -342..-94`, `Y +/-51.08` plus side strips to `+/-60.85`) centres on
`X = -218`. Group C sits on four raised bosses (`26 x 16 x 8 mm`, top at
`Z = 11.11`) that already carry factory screws.

## Perception host

Not present in any CAD; it is the Pro-only addition. Position could not be
derived and was **measured by Dr Sun**: centre hole (`X = -88`, dia 6.0) to host
front face = **28 mm**, giving host front `X = -116.0`.

Independent confirmation: that lands the host front face `0.50 mm` from the
centreline of the front raised boss pair — a feature never used to place it.

Final placement `X -315.59..-116.00`, `Y +/-54.31`, `Z 6.168..56.168`,
footprint `199.585 x 108.618 mm` with the two scan-recovered front side recesses.

**The recesses exist to expose the group B front receivers.** Between
`X = -116` and `-146` the host narrows to `Y -43.57..+42.43`, leaving the
`(-134, +/-52.5)` receivers exposed with `10.07 mm` of clearance. An earlier
conclusion in this session that group B was buried under the host was wrong;
Dr Sun spotted it.

### Rejected earlier positions

- scan-registered `X -299.59..-100.00`: its X came from the photo-measured
  enclosure front and its Y "assumed centreline" while producing a `+1.57 mm`
  off-centre result — circular and self-contradicting.
- robot-symmetry `X -318.79..-119.21` and boss-flush `X -303.09..-103.50`: both
  superseded by the measurement.

## Carrier rev-e

Derived from the Codex V1 monolithic carrier
(`../physical-lite3-mid360-d435i-fusion-adapter-v1/cad/lite3-mid360-d435i-monolithic-carrier-v1.step`),
registered on its own `65.00 mm`, `dia 3.5` bore pair.

Three changes from V1:

1. tail trimmed at the host front face (`-3453 mm3`);
2. underside boolean-conformed to the robot shell (`-340 mm3`) — V1 had a flat
   underside resting on a curved shell and cut `403 mm3` into it;
3. two rear tabs added (`+3231 mm3`) reaching the group B receivers.

| Metric | Value |
| --- | --- |
| Volume | 74.3 cm3 (approx 92 g in PETG) |
| Bodies | 1 lump, 183 faces |
| Bounding box | 157.73 x 116.00 x 33.56 mm |
| Interference vs host | 0.000 mm3 |
| Interference vs robot | 0.000 mm3 |
| Fixing | 2 x M3 front `(0, +/-32.5)` 2.40 mm thread, screw M3x8-10 |
| | 2 x M3 rear `(-134, +/-52.5)` 6.00 mm thread, screw M3x12 |
| Span | 134.0 mm fore-aft, 105.0 mm lateral |

Two heavier alternatives were built and rejected: rev-c full fork (83.0 cm3) and
rev-d outboard tabs (76.9 cm3), both anchoring on the shallower 3.00 mm group C
threads with a shorter 116.5 mm span.

## Outstanding before any print

1. **Print clearance.** The conformed underside is a zero-clearance boolean
   result. It needs roughly 0.3 mm relief or the part will not seat. A six-way
   `0.3 mm` dilation of the robot bodies was attempted and failed with
   `ASM_BODY_VERTEX_CRUMBLE` from near-coincident faces; another method is needed.
2. **Fillets.** The rear tabs are plain prismatic blocks with sharp internal
   corners.
3. **Sensor fit.** MID-360 and the S410 guard were never re-imported after the
   tail trim. The available front zone grew from the 116 mm assumed by
   `../current-lite3-pro-compact-sensor-layout-rev-a/` to 136 mm, so the fit is
   likely better than that package predicted, but this is unverified.
4. **Front receiver strength.** The `2.40 mm` group A threads remain the weakest
   link. Thread locker is advised; no strength calculation has been done.
5. **Connector keep-outs.** Photos show the host carries connectors on both long
   sides (`HDMI / USB 3.0 / network / power switch / 24V-12V-5V` on one,
   `SD card / USB 3.0 / laser port` on the other). These are not yet modelled.

## Fusion API notes

- `Occurrence.transform2` assignment followed by `Design.snapshots.add()`
  silently reverts to identity. Place components with
  `Occurrences.addNewComponent(matrix)` and import into the already-transformed
  component instead.
- `Occurrence.boundingBox` returned all-zero after programmatic edits. Compute
  world extents from `occurrence.bRepBodies` proxies.
- `BRepBody.copyToComponent` preserves world position and ignores the target
  occurrence transform; rebuild geometry inside the transformed component when a
  move is intended.
- Occurrence transforms are not driven by user parameters; changing a parameter
  does not move a component placed with a baked matrix.
- Always check `BRepBody.lumps.count` after a union — a first attempt at the rear
  tabs produced three disconnected lumps because the arms floated 2.55 mm above
  the carrier plate.
