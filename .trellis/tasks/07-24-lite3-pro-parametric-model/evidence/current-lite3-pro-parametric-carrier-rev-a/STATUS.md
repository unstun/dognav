# Status

`carrier_rev_f_sensor_fit_verified_print_relief_applied_release_still_blocked`

- Stage: experiment + analysis
- Session handoff: continued from Codex session `019fa20a-82f7-7750-95ab-f7293fef79ea`,
  driven from Claude Code through the Fusion MCP server.
- Fusion document `Lite3Pro_SensorCarrier_Lightweight` (hub `sun` / project
  `Default Project` / root folder), saved at checkpoint-17.
- **Printable release remains blocked.** Fastener strength, cable routing, the
  D435i station, and human review of the sensor placement are all still open.
  Nothing here authorises fabrication.

## Exported artifacts

| File | Size | Content |
| --- | --- | --- |
| `cad/carrier-rev-f-print-relief-fillets.step` | 766 KB | rev-f, current carrier |
| `cad/carrier-rev-f-print-relief-fillets.stl` | 428 KB | same, high mesh refinement |
| `cad/carrier-rev-e-rear-tabs-group-b.step` | 621 KB | rev-e, superseded by rev-f |
| `cad/carrier-rev-e-rear-tabs-group-b.stl` | 402 KB | same |
| `cad/lite3pro-carrier-scene-rev-e.step` | 56 MB | rev-e scene: torso, host, carrier |

Renders in `renders/`; `90`-`93` sensor fit, `94`-`95` rev-f, `96`-`97` keep-outs.

## Robot registration (unchanged, load-bearing)

The Experience-branch torso B-rep
(`../factory-step-lite3-lightweight-brep/superseded-torso-only/lite3-real-brep-lightweight.step`,
89 solids, 22 803 faces, legs absent) was registered **from geometry, not by eye**:

- source `+Z` -> robot forward (`+X`), source `+X` -> robot left (`+Y`),
  source `+Y` -> up (`+Z`);
- datum: the 65.00 mm front bore pair at source `X = +/-32.50`, `Z = 219.000`;
- seating plane: hole top at source `Y = 61.387`.

After transform the two front bores land at `X = -0.000`, `Y = +/-32.500`,
`Z(top) = 0.000`, matching
`../current-lite3-pro-lower-adapter-measurement-gate/measurement_results.json`.

## Robot top-side M3 receivers (complete enumeration)

| Group | Y | X | Span | Thread depth | Insert thickness |
| --- | --- | --- | --- | --- | --- |
| A | +/-32.5 | 0 | 2 holes only | **2.40 mm** | 2.40 mm |
| B | +/-52.5 | -134, -304 | 170 mm | **6.00 mm** | 6.00 mm |
| C | +/-72.5 | -116.5, -321.5 | 205 mm | **3.00 mm** | 3.00 mm |

Group B and C centre on `X = -219.0`, `Y = 0`; the `Z = 6.168` deck pocket
(`X -342..-94`, `Y +/-51.08` plus side strips to `+/-60.85`) centres on `X = -218`.
Group C sits on four raised bosses (`26 x 16 x 8 mm`, top at `Z = 11.11`).

## Perception host

Not present in any CAD; Pro-only addition, **measured by Dr Sun**: centre hole
(`X = -88`, dia 6.0) to host front face = **28 mm**, giving host front
`X = -116.0`. Final placement `X -315.59..-116.00`, `Y +/-54.31`,
`Z 6.168..56.168`, footprint `199.585 x 108.618 mm`, with the two scan-recovered
front side recesses that expose the `(-134, +/-52.5)` group B receivers
(`10.07 mm` clearance).

Solid geometry, confirmed this session: a 10-face prism. Long sides are the
planes `Y = +/-54.309` spanning `X -315.585..-146.000`, `Z 6.168..56.168`; the
nose narrows to `Y -43.570..+42.430` over `X -146..-116`.

## Sensor fit re-check after the tail trim (this session, PASS)

MID-360 and the S410 guard were imported from the pinned upstream STEP files and
registered **on the carrier's own mounting-hole axes**, not by eye.

Deck frame: `n = (sin15, 0, cos15)` (deck normal, 15 deg nose-down),
`t = (cos15, 0, -sin15)` (in-deck forward), `b = (0, 1, 0)`.
Deck top plane: axial `a = 10.157296 mm`. Both hole patterns centre on
`u = -47.557901 mm`, `v = 0`.

| Interface | Carrier feature | Sensor feature | Match |
| --- | --- | --- | --- |
| MID-360 | 4 x dia 3.5 clearance, `48.000 x 36.000` | 4 x M3, `48 x 36` | 4/4 axes, `<= 0.0001 mm` |
| S410 | 4 x dia 4.2 (M5 tap), `83.431 x 49.48` | 4 x dia 5.2 through | 4/4 axes, `<= 0.0001 mm` |

The S410 pattern is not symmetric (`+/-24.880` rear, `+/-24.598` front, and the
native origin offset `+0.0835 mm` from the pattern centre). Both asymmetries
reproduce on the carrier, which is what identifies the front/rear sense.

Baked placement matrices (`Occurrences.addNewComponent`, mm):

- `S410_registered`: native X -> `t`, Y -> `n`, Z -> `-b`;
  T = `(-43.308503, 0.000000, 22.120085)`.
- `MID360_registered`: native X -> `-t`, Y -> `n`, Z -> `+b`;
  T = `(-36.600664, 0.000000, 47.154081)`.

Verification:

- both sensors' minimum axial coordinate = `10.157296` exactly = the deck plane;
- interference over 23 sensor bodies + carrier + host: **0 hits, 0.000000 mm3**;
- all 89 robot bodies checked: **none overlaps the sensor bounding box**.

World envelopes:

| Body | X | Y | Z |
| --- | --- | --- | --- |
| S410 guard | `-88.471..21.004` | `+/-34.730` | `10.019..105.690` |
| MID-360 | `-80.618..-2.582` | `+/-32.437` | `13.736..86.768` |

**Clearance to the host front face is `27.529 mm`** (S410 rear-most `X = -88.471`
against host front `X = -116.000`). The tail trim did not cost the sensors
anything: the front zone grew from the 116 mm assumed by
`../current-lite3-pro-compact-sensor-layout-rev-a/` to 136 mm, and the sensors
need only 109.5 mm of it.

### MID-360 connector orientation is a design choice, not a geometric result

The `48 x 36` pattern is symmetric, so the lidar can be bolted either way. Both
were built and tested: connector rearward (current, envelope `X -80.618..-2.582`)
and connector forward (envelope `X -74.598..1.377`). **Both give 0.000000 mm3
against the guard and the carrier.** Rearward was kept because the cable has to
reach the host at `X <= -116`. This needs Dr Sun's confirmation.

## Carrier rev-f (current)

rev-e plus print relief plus rear-tab internal fillets. Robot-interface hole axes
are bit-identical to rev-e (12 of 12).

| Metric | rev-e | rev-f |
| --- | --- | --- |
| Volume | 74319.73 mm3 | **72941.09 mm3** (72.94 cm3, approx 93 g PETG) |
| Lumps / faces | 1 / 183 | **1 / 195** |
| Bounding box | `157.73 x 116.00 x 33.56` | unchanged |
| Min clearance to robot | `0.000000 mm` | **`0.302563 mm`** |
| Interference vs host, S410, MID-360 | 0 mm3 | **0 mm3** |

Fixing unchanged: 2 x M3 front `(0, +/-32.5)` into 2.40 mm thread, M3x8-10;
2 x M3 rear `(-134, +/-52.5)` into 6.00 mm thread, M3x12.

### 1. Print relief, 0.320 mm (replaces the failed six-way dilation)

Six-way `0.3 mm` dilation of the robot bodies fails with
`ASM_BODY_VERTEX_CRUMBLE`. The method that works is a **rigid translation of the
cutting tool**, which needs no offset operator at all:

1. copy the 6 robot bodies that reach the carrier envelope
   (`Body72/73/74/77/78/80`) as temporary B-reps;
2. translate each by `+0.320 mm` in `Z`;
3. boolean-difference them out of a temporary copy of rev-e.

This is valid because the conformal underside is shallow. Sampled over the eight
conformal NURBS faces of rev-e (441.08 mm2 total), `|n_z|` is `0.9751..0.9904`,
i.e. a worst slope of **12.82 deg**, so a vertical lift `t` yields a normal
clearance of `t * n_z`, never less than `0.312 mm` on those faces.

Three local remnants had to be cut separately. All share one cause: **the robot
feature underneath is a hole, so the lifted tool has no material there and cannot
cut the carrier lip hanging over it.**

| Remnant | Fix | Removed |
| --- | --- | --- |
| ring at each rear M3 hole rim, `r 1.70..1.762` | dia 4.5 counterbore, `Z 5.5..6.488` | 0.4573 mm3 |
| conical lip at each front M3 hole rim, `r 1.75..1.775`, `Z 0.812..1.761` | cone `r 2.10 @ Z 0.6` -> `r 1.75 @ Z 1.95` | 1.4609 mm3 |
| tongue over the robot's `X = -88` dia-6 countersink | dia 6.0 cylinder, `Z 4.5..6.488` | 0.9841 mm3 |

Total removed by relief: `1400.8847 mm3`.

Verification: all 126 faces with `z_min < 12 mm` were measured against the robot
shell. **Zero faces below 0.300 mm.** Global minimum `0.302563 mm`, which occurs
on the steeper front outer faces (`n_z ~ 0.9455`, 18.9 deg), not on the conformal
patch. `0.308 mm` was tried first and left those faces at `0.291503 mm`, which is
why the lift is `0.320` and not `0.300`.

**Consequence Dr Sun must decide on.** rev-e touched the robot on the conformal
patch (`0.000000 mm`) and on the `Z = 6.061` flat (`0.00017 mm`). rev-f touches
nothing: the carrier is now located and clamped **only by the four M3 screws**,
which will pull the plate down across a 0.3 mm gap. If a defined seat is wanted,
the fix is small contact pads left proud at the four screw bosses; that is a
design change and was not made.

### 2. Rear tab internal fillets

The tabs are 12 mm wide arms (`Y 46..58` / `-58..-46`) running `X -142..-106`,
`Z 6.488..10.168`, projecting rearward past the main body's rear face at
`X = -116`, and standing 1.607 mm proud of the plate top at `Z = 8.561`.

| Fillet | Edges | Radius | Added |
| --- | --- | --- | --- |
| plan-view root corners | `(-116, +/-46)` and `(-106, +/-49.5)`, `Z 6.488..8.561` | **R3.0** | +15.0322 mm3 |
| step roots on the plate top | `X = -106` (`|Y| 46..52.5`) and `Y = +/-46` (`X -118.91..-106`), `Z = 8.561` | **R1.0** | +7.2095 mm3 |

Both fillets add material, which is the independent confirmation that the
selected edges really are concave; a `pointContainment` concavity test built on
`BRepFace.isParamReversed` misclassified several edges and should not be trusted.

## Host long-side connector keep-outs

Photos show connectors on both long sides
(`HDMI / USB 3.0 / network / power switch / 24V-12V-5V` on one,
`SD card / USB 3.0 / laser port` on the other). **Individual positions along X
and Z have not been measured**, so the keep-out is modelled as a full-length slab
per side, not as per-connector boxes.

Component `Host_connector_keepout`, four bodies, all spanning
`X -315.585..-146.000` and `Z 6.168..56.168`:

| Body | Y | Volume | Meaning |
| --- | --- | --- | --- |
| `keepout_left_hard_connector_0_40mm` | `54.309..94.309` | 339170 mm3 | mated plug body and operator access |
| `keepout_left_soft_cablebend_40_70mm` | `94.309..124.309` | 254378 mm3 | first cable bend |
| `keepout_right_hard_connector_0_40mm` | `-94.309..-54.309` | 339170 mm3 | as above |
| `keepout_right_soft_cablebend_40_70mm` | `-124.309..-94.309` | 254378 mm3 | as above |

The 40 mm hard depth is sized for an RJ45 with a moulded boot; USB 3.0 and HDMI
plugs are shorter. It is an engineering assumption, not a measurement.

Intrusion check:

- carrier rev-f, S410, MID-360: **no body reaches the envelope**, 0 mm3. Every
  added part lies forward of `X = -146`.
- the robot itself intrudes `816.340 mm3`: the two group C bosses `Body25` and
  `Body87` (`X -334.499..-308.499`, `Y +/-64.5..80.5`, `Z 3.113..11.113`,
  408.170 mm3 each) occupy the bottom 4.9 mm of the hard zone over the rear-most
  26 mm of each side. No connector may sit there below `Z = 11.113`.

## Outstanding before any print

1. **Seat definition.** See the consequence note above: four-screw clamping
   across a 0.3 mm gap, or contact pads.
2. **Front receiver strength.** The `2.40 mm` group A threads remain the weakest
   link. Thread locker is advised; no strength calculation has been done.
3. **Connector positions.** The keep-out is a slab because nothing was measured.
   Measure each connector's `X` and `Z` centre and its plug depth, then split the
   slab into per-connector boxes.
4. **MID-360 connector orientation.** Confirm rearward.
5. **Cable routing.** The MID-360 connector lands at world `(-70.0, 0, 38.9)`
   facing rearward. No cable path, bend radius, or strain relief is modelled.
6. **D435i.** The `D435i_official_brep` occurrence still sits at the
   compact-layout station (`X -7.75..17.25`, `Z 84.020..109.070`), which is not
   the carrier's own D435i interface (2 x dia 3.2 at `Y = +/-22.5`, `X ~ 12.4`,
   `Z ~ 20`, normal `(0.94, 0, -0.34)`). One of the two has to go. The occurrence
   is hidden and was excluded from every fit claim in this document.
7. **Slicer and material.** No slice, no coupon, no print.

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
- Occurrence transforms are not driven by user parameters.
- Always check `BRepBody.lumps.count` after a union or a cut.
- Walk occurrences **recursively**. A STEP import nests its geometry one level
  down, so a one-level walk silently dropped 7 of 23 sensor bodies and would have
  made an interference result meaningless.
- **A dilation is not needed for print clearance.** Translating a temporary copy
  of the tool body and subtracting it is robust where `thicken` / six-way offset
  raise `ASM_BODY_VERTEX_CRUMBLE`. The cost is that clearance scales with
  `cos(slope)` and that lips hanging over holes in the tool body survive.
- If a script throws **after** `BaseFeature.finishEdit()`, Fusion rolls the last
  operation back. Re-read the body and re-check its volume; do not trust the
  values printed before the exception.
- A `pointContainment` concavity test using `BRepFace.isParamReversed` to orient
  normals gave wrong answers. Verify concavity by the sign of the volume change
  after the fillet instead.
- `BRepEdge.geometry` can be `None`; guard before touching `objectType`.
- Whole-body `measureMinimumDistance` against the 1714-face torso shell is cheap;
  looping it over every face of the carrier without a bounding-box prefilter
  times out.
