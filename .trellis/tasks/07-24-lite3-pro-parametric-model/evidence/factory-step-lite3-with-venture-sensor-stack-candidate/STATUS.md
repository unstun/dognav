# Factory STEP Lite3 With Venture Sensor Stack: Fusion Review Status

Status: `superseded_and_rejected`

## Historical Result

This historical unsaved Fusion scene used the downloaded real Lite3 B-rep
assembly instead of the earlier transparent official mesh context. The
separate exploration backload module is hidden. The existing open-truss
adapter, J17A/J20A/S410/Mid-360 stack, and direct J17A-mounted D435 are visible.

No external industrial computer, BZ20 backload shell, AGX carrier, or rejected
factory Interface reconstruction is installed. Native internal robot
electronics from the source assembly were not modified.

## Geometry Result

The downloaded file is a real editable AP214 assembly, not a mesh-only visual:

- 137 products and 319 assembly-use records;
- 77 advanced B-rep shape representations;
- 99 manifold-solid B-rep records and 99 corresponding closed shells;
- zero triangulated-face-set records;
- 1,427 solids and 440,637 faces in the FreeCAD source inspection.

The imported robot base is opaque and preserves detailed body panels, joint
parts, feet, fasteners, and the DEEP Robotics branding.

## Placement And Clearance Result

The source assembly was rigidly reoriented and centre-aligned to the previous
official Lite3 standing reference without scaling. The sensor stack and
adapter were then moved upward together by `0.2 mm` as a preview-only source
alignment correction.

The adapter-to-factory-body intersection changed from `103.920445 mm3` at the
initial aligned pose to `0.0 mm3` after the correction. The remaining minimum
CAD distance to the previously colliding body is `0.020620120 mm`.

This very small nominal clearance is not a manufacturing tolerance or proof of
physical fit.

## Variant And Mounting-Hole Boundary

The top-level STEP product is named `Lite3探索版总装`, while its robot-base
child is named `Lite3体验版总装.STEP`. It must not yet be relabelled Lite3 Pro.

A targeted scan of the visible robot-base B-rep inspected 70,842 faces and 604
unique top vertical-cylinder axes. It found no `74 x 94 mm` four-corner
pattern. Consequently:

- the sensor stack can be placed on this real chassis for appearance and
  packaging review;
- the yellow adapter is still the nominal Lite3 Pro adapter candidate;
- a direct bolt-on installation to this downloaded chassis is not established;
- a chassis-specific adapter or measured robot interface may be required.

## Review Gate

This candidate is no longer awaiting review. Its open-truss adapter and D435
were removed by Dr Sun's later baseline instruction. A corrected native B-rep
audit identifies the direct-installation group as the four counterbored holes
on a `67.88225 mm` square and finds no full-pattern match on this supplied
Exploration/Experience robot body. Retain this directory as negative evidence
only.

Before any future fabrication, verify the physical
robot variant, top-hole pattern, threads, usable depth, datum, fastener access,
cable routing, sensor fields of view, payload mass/centre of mass, structural
margin, and locomotion keep-outs.
