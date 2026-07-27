# Official Lite3 LiDAR V1.0.7 Assembly Evidence

## Current Target

The target is the factory-visible Lite3 LiDAR edition shown in the official
`Jueying-Lite3-LiDAR-User-Manual-CE-V1.0.7` overview and part-identification
views. It is not the separate Lite3 Venture FAST-LIVO2 extension and it is not
the earlier custom Pro-to-J17A adapter candidate.

The public evidence supports an appearance reconstruction only. No public
factory assembly CAD, manufacturing drawing, sensor extrinsic, tolerance
scheme, enclosure wall construction, or hidden fastener stack has been found.

## 2026-07-26 Replica Reset

Dr Sun rejected the prior baseline because it changed the factory-visible
problem into a mounting redesign. Its four profiled local supports, bored
Interface feet, two provisional M3 chains, hidden receiver proxies, and
additional `35 mm` sensor-stack translation are not supported as factory
geometry. Passing the candidate's `27/27` internal geometry checks does not
change that evidence boundary.

The replacement track reproduces only official-visible geometry: the compact
thin local carrier, short blocks/posts, visible fastener heads, Mid-360,
D435, guard, Interface, and their image-registered relationships. Unpublished
underside receivers and load paths remain unresolved and are not invented.

## Primary Evidence Matrix

| Evidence | Directly supported fact | Unsupported inference that is forbidden |
| --- | --- | --- |
| V1.0.7 manual page 6, extracted front render | Mid-360-style blue optical dome; forward/downward radar attitude; front D435-class camera; black guard; long rear Interface enclosure; official standing envelope `610 x 370 x 496 mm` | Exact bracket dimensions, hidden fasteners, enclosure internals |
| V1.0.7 manual page 6, extracted side render | Sensor is at the front; Interface is behind it; the carrier and Interface front face remain visibly separate; Interface is about `209 mm` long when scaled from the published `548 mm` body length; local mounting feet are visible | Treating the image-derived length or the hidden carrier-to-body receiver as nominal factory geometry |
| V1.0.7 manual page 7, extracted front/rear line art | Separate `Laser Radar`, `Depth Camera`, and `Interface`; stepped/relieved Interface front/underside relationship around the sensor carrier; no long external rail or spanning lower deck | Filling hidden underside volume with a guessed adapter or rail |
| Perception Development Manual V2.2.2 pages 6 and 13 | Lite3 Pro/LiDAR uses Xavier NX as perception host and D435i as depth camera | A visible Jetson developer kit or a published Jetson mounting position |
| Perception Development Manual V2.2.2 pages 44 and 56 | The supplied ROS/ROS 2 driver layout includes `mid360_ws` | Factory mechanical geometry or sensor extrinsics |
| Official `Lite3_Navigation` repository at `b091cee...` | Published navigation consumes `rslidar` data | Mechanical CAD, URDF, or static transforms; none are present |

## Source Geometry Policy

- The official Livox Mid-360 STEP and official RealSense D435 visual mesh may
  be used as component geometry because the manuals independently support
  those component identities.
- The DEEP Robotics J17A, J20A, and S410 source models visually match major
  portions of the manual silhouette and may be used as
  `related_source_candidate` geometry.
- J17A, J20A, and S410 were published for the separate Lite3 Venture
  FAST-LIVO2 extension. Their reuse does not prove that they are the exact
  factory V1.0.7 parts or that their hidden robot-side interface is unchanged.
- After Dr Sun's replica/adaptation correction, those three parts remain
  useful only as rejected comparison evidence. They are forbidden imports in
  the current V1.0.7 replica scene.
- The BZ20 shell, rear AGX assembly, custom Pro adapter, long rails, carrier
  plate, receiver yoke, artificial 17 mm D435 standoff, and fake Jetson are not
  part of the current official-LiDAR appearance target.

## Rejected Image-Derived Engineering Baseline

The rejected comparison candidate used an image-derived Interface envelope of
approximately `233 x 92 x 46 mm`. The length and height were re-scaled from
the losslessly extracted orthographic-like manual side view; width remains an
earlier image estimate. None of these values may be reported as official
nominal dimensions.

An earlier registration placed the related-source J17A rear edge about
`34 mm` inside the Interface body envelope, then cut the Interface around that
collision. This contradicted the visible separation in the official side
render. The now-rejected engineering registration kept the Interface fixed and
moved the complete J17A/J20A/S410/Mid-360/D435 source stack rigidly `35 mm`
farther toward robot `+X`. The total source-stack image-fit translation is now
`[55.0, 0.0, -28.132935] mm`. The shallow central Interface underside relief
remains an `image_estimate`, but it is no longer used to conceal a
carrier/Interface collision.

The visible enclosure model may include:

- a separate lid and front cap seam;
- side connector apertures matching the manual grouping;
- rear/end ventilation slots;
- four bored local feet that reach the source-body deck datum;
- a shallow central front/underside relief matching the visible enclosure
  silhouette.

It must omit any hidden full-width plate, long rail, BZ20 shell, AGX support,
or invented internal computer geometry.

The Interface bottom is at `399.867065 mm`; its four bored feet are
`7.899495 mm` high and meet the sampled top-deck datum at
`391.967571 mm`. Each foot includes an image-inferred M3 clearance bore,
downward screw, and replaceable hidden receiver proxy.

The related-source J17A drawing explicitly calls out `4 x M3` on a
`110 x 86 mm` pattern. The corrected image registration places those axes at
robot X=`137.851997/247.851997 mm`, Y=`+/-43 mm`, with the J17A seating plane
at `417.867065 mm`. Four separate profiled supports provide an upward M3 path
into J17A and an independently accessible downward M3 path into a replaceable
body-side receiver proxy. Their sampled minimum body clearance is
`0.250008 mm`.

These two inspectable chains made the guessed assembly mechanically legible,
but did not reproduce proven factory geometry. They are rejected. The hidden
V1.0.7 carrier-to-robot connection remains unresolved until a factory drawing
or physical Lite3 measurement is available.

## Superseded Geometry Gate

The rejected candidate attempted to:

1. use the official Lite3 standing exterior;
2. preserve the source Mid-360/J20A/S410 rotations;
3. re-register the sensor stack to the manual `496 mm` standing height rather
   than the rejected approximately `524 mm` custom position;
4. place the real-source D435 from the manual silhouette, with no synthetic
   camera body or long standoff;
5. use the long notched Interface enclosure, not BZ20;
6. report enclosure/carrier separation, both invented four-fastener mounting
   chains, body clearance, and all image-estimated transforms;
7. provide front, side, rear, and isometric comparisons before modifying the
   accepted printable generator.

Dr Sun's visual acceptance remains mandatory. A watertight or sliceable mesh
does not pass the replica-identity gate by itself.

## Replacement Visible-Replica Gate

The next candidate must first trace the official-visible plate perimeter,
short post/block silhouettes, visible screw heads, and shared component
landmarks across the front, rear, side, and oblique sources. It must omit all
unseen receivers and attachment mechanisms. Printability and the user
industrial-PC base are later, separately labeled adaptation work and cannot be
used to change the accepted replica silhouette.

## 2026-07-26 Rejected Multiview Replica Candidate

The rejected candidate is retained under
`evidence/official-lidar-v107-multiview-replica-candidate/`. It imports no
J17A carrier, J20A adapter, or S410 guard. The only imported sensor exteriors
are the manufacturer Mid-360 CAD and the pinned official RealSense D435 ROS
visual mesh.

The bracket scene is reconstructed from the official V1.0.7 front, side, and
rear assets plus the current official studio photograph:

- a `163 x 112 x 3.5 mm` image-estimated local lower plate;
- four vertical short posts whose image-registered heights are
  `24.712601/5.559992 mm` at the rear/front rows;
- a `96 x 82 x 4 mm` upper plate tilted forward/down by `15 degrees`;
- an image-estimated D435 rear plate with two visible vertical supports;
- two orthogonal guard straps, their visible crossbars, and a top cap;
- surface fastener heads only, without any modeled thread or receiver;
- an independent rear Interface with an `11 mm` visible X separation from the
  local sensor plate.

The guard reaches `496.003681 mm`, matching the published standing height
within `0.004 mm` in this image-registration coordinate system. That numerical
match is not a factory-dimension claim. The bracket dimensions above remain
rejected image estimates. The unknown underside
hole layout, thread specification, tolerance stack, material, and load path
remain deliberately absent, so this candidate is not print-ready.

## 2026-07-26 Second Rejection And Public-CAD Boundary

Dr Sun rejected the multiview candidate after review. The rejection is broader
than a visual mismatch:

- the Interface was moved rearward using an image estimate rather than a
  factory datum or physical measurement;
- the lower plate, unequal posts, tilted plate, camera rear support, guard
  straps, standoffs, and visible fastener heads were invented without verified
  contact surfaces, hole axes, receivers, assembly order, or load path;
- `496.003681 mm` total height and `11 mm` visible separation are candidate
  self-consistency values, not factory-placement or assembly evidence.

The candidate is therefore neither an official replica nor a mechanically
assembled model. Its directory remains available only as negative evidence,
and its acceptance checks have been reset.

A renewed primary-source audit found no publicly downloadable complete factory
Lite3 LiDAR CAD, STEP, URDF, dimensioned upper-assembly drawing, hidden-hole
layout, or assembly transform. The available materials remain separate:

1. official Lite3 body/leg URDF and mesh geometry;
2. official V1.0.7 LiDAR manual imagery and the published
   `610 x 370 x 496 mm` standing envelope;
3. manufacturer Mid-360 and D435 component geometry; and
4. J17A/J20A/S410/BZ20/AGX STEP files for the separate Lite3 Venture
   FAST-LIVO2 extension.

None of those sources supplies the missing factory Interface position or
factory LiDAR mounting chain. Geometry work is frozen until either
manufacturer factory-assembly CAD/drawings or physical Lite3 LiDAR
measurement/scan data supplies the required datums and connections.
