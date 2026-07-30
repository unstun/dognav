# Lite3 Mid-360 Camera-Mount Evidence Review

Date: 2026-07-26

## Decision

The previous two-piece rail bracket, carrier plate, receiver yoke, and
eight-fastener arrangement are rejected. They passed mesh and slicer checks,
but they were an original engineering adaptation rather than a replica. None
of those shapes may appear in the next official-appearance model.

The evidence now separates two mechanically different DEEP Robotics
configurations:

1. The regulatory/launch factory LiDAR revision uses a cylindrical scanner in
   a long white upper shell.
2. The official Lite3 Venture FAST-LIVO2 extension uses a true Mid-360,
   published J17A/J20A/S410 parts, and a D435 directly screwed to J17A.

Dr Sun requested the true-Mid-360 arrangement. Therefore the accepted visible
sensor stack is the official FAST-LIVO2 extension. Its white adjacent enclosure
is the official `1T21-BZ20` backload shell (`108 x 96 x 30 mm`), not the
previous generic `160 x 92 x 46.8 mm` Interface placeholder and not the rear
AGX/industrial PC. The old placeholder collision, 36 mm sensor shift, and large
hidden adapter are invalid and rejected.

The robot-side conversion must be treated separately: J17A must remain in the
official visible position, while only its hidden lower interface may eventually
be adapted to Lite3 Pro's `74 x 94 mm` pattern around the user's actual
industrial-PC keep-out volume. That adaptation cannot be designed honestly
until the real industrial-PC dimensions, mounting holes, connectors, and cable
keep-outs are supplied.

## Primary Evidence

| Evidence | Provenance | What it establishes | What it does not establish |
| --- | --- | --- | --- |
| [Official FAST-LIVO2 underside frame, 284 s](../../../../references/upstream/2026-07-26_lite3-official-fast-livo2-install-video/derived/sensor-install/frame-284s.jpg) | DEEP Robotics official installation video | One-piece J17A underside, four robot-side holes, D435 directly attached to two short angled J17A faces, and no separate rails/carrier/yoke | Lite3 Pro fit and the user's Interface clearance |
| [Official FAST-LIVO2 installed frame, 292 s](../../../../references/upstream/2026-07-26_lite3-official-fast-livo2-install-video/derived/sensor-install/frame-292s.jpg) | Same official video | Exact visible relation among Mid-360, S410, J20A, J17A, D435, Lite3 Venture body, and adjacent white BZ20 shell | Exact BZ20 transform and Pro-specific base adaptation |
| [Official FAST-LIVO2 installed frame, 320 s](../../../../references/upstream/2026-07-26_lite3-official-fast-livo2-install-video/derived/sensor-install/frame-320s.jpg) | Same official video | BZ20 is separate from the black rear AGX compute device; no rail runs beneath J17A | Geometry of the user's different industrial PC |
| [J17A laser-base drawing](../../../../references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/derived/j17a-drawing.png) | DEEP Robotics public FAST-LIVO2 hardware | One-piece base; `2 x Ø3.20` camera holes at 45 mm centres; 20-degree angled camera faces; 6061-T6 source part | Direct fit of the original Venture robot-side holes to Lite3 Pro |
| [J20A small-LiDAR plate drawing](../../../../references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/source/original/1T21-J20A-small%20lidar%20base.pdf) | Same official extension | Real 15-degree Mid-360 plate and its hole pattern | Pro/Interface lower adaptation |
| [S410 LiDAR guard drawing](../../../../references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/source/original/1CA5-S410-Lidar%20protector.pdf) | Same official extension | Real guard geometry and mounting holes | Pro/Interface lower adaptation |
| [BZ20 source STEP record](../../../../references/upstream/2026-07-24_lite3-venture-fast-livo2-hardware/source_record.yaml) | Same official extension | One closed BRep solid, `108 x 96 x 30 mm`, with real modeled holes/features | Complete electronics inside it or its exact video-frame transform |
| [RealSense D435i source record](../../../../references/upstream/2026-07-25_realsense-d435i-cad/source_record.yaml) | RealSense official CAD/datasheet | D435i identity, envelope, and two rear M3 points on 45 mm centres | Robot-side base geometry |
| [Lite3 LiDAR product image](../evidence/lite3-official-lidar-product.png) | DEEP Robotics partner product page | A currently marketed Mid-360-like guarded arrangement with D435 immediately below/front and an Interface enclosure behind | Manufacturing revision identity and hidden mounting details |
| [FCC external photos](../../../../references/upstream/2026-07-26_lite3-fcc-photos/source_record.yaml) | FCC regulatory package for `Jueying Lite3 LiDAR` | Tested factory revision uses a cylindrical scanner in a long white shell | The requested Mid-360 extension |
| [Official 2023 launch video](../../../../references/upstream/2026-07-26_lite3-official-launch-video/source_record.yaml) | DEEP Robotics launch video | Historical factory LiDAR appearance agrees with the FCC cylindrical revision | The requested Mid-360 extension |
| [Official manual part-name page](../../../../references/upstream/2026-07-24_lite3-design-drawings/derived/lite3-lidar-manual-07.png) | DEEP Robotics Lite3 LiDAR User Manual V1.0.7-0, page 7 | Labels `Laser Radar`, `Depth Camera`, and `Interface`; camera is close to radar front lower edge | Whether the illustration represents J17A or the cylindrical regulatory revision |
| [Current manufacturer gallery](../../../../references/upstream/2026-07-26_lite3-official-product-gallery/source_record.yaml) | DEEP Robotics China product page, acquired 2026-07-26 | Current page still lists an `激光版`; generic body appearance is current | Gallery does not show the LiDAR upper assembly and contributes no bracket dimensions |

## View-by-View Matrix

| Region or relation | Front/front-left evidence | Rear/rear-left evidence | Top/side evidence | Confidence | Modeling permission |
| --- | --- | --- | --- | --- | --- |
| Camera identity | D435 is visible in official frame 284 | Its rear face is seated against J17A | RealSense source fixes the visual body and rear M3 pattern | High | Use pinned official RealSense visual mesh |
| Camera longitudinal position | Immediately ahead of the Mid-360 lower front | Official underside shows direct contact with J17A faces | J17A source fixes the mounting plane | High for the official Mid-360 extension | Seat the D435 rear mounting plane directly on J17A; no 17 mm artificial standoff |
| Camera vertical position | Below the Mid-360 optical body | Fixed by the J17A angled faces | Source STEP fixes the datum | High | Inherit unchanged J17A source placement |
| Camera pitch | Official installed frame shows downward view | Underside view shows the slanted faces | J17A drawing specifies a 110-degree included bend, i.e. 20-degree camera direction | High | Use the source J17A 20-degree face |
| Camera-to-base connection | Two compact local supports | Two direct fastener locations are visible | J17A View A specifies `2 x Ø3.20` at 45 mm; D435 specifies matching rear M3 points | High | Two direct M3 fastener references only; screw length remains unresolved |
| Long rails | None visible | None visible | No primary drawing supports them | High negative evidence | Forbidden |
| Separate deep carrier plate | None visible | None visible | No primary drawing supports it | High negative evidence | Forbidden |
| Rear receiver yoke/bosses | None visible | None visible | No primary drawing supports them | High negative evidence | Forbidden |
| Eight-screw external assembly | None visible | None visible | No primary drawing supports it | High negative evidence | Forbidden |
| J17A/J20A/S410 identity for the Mid-360 extension | Visible parts match official installation sequence | Official video shows the full assembled unit | Published STEP/drawings use the same part shapes | High | Use unchanged source geometry for the visible stack |
| J17A original robot-side fit to Lite3 Venture | Four holes and placement visible | Installed on Venture in official video | J17A drawing fixes the original pattern | High for Venture only | Preserve as source reference |
| White rear-adjacent enclosure | Rounded white shell immediately behind J17A | Separate black AGX device is farther rearward | Official BZ20 STEP fixes `108 x 96 x 30 mm` source geometry | High identity; image-estimated transform | Use unchanged BZ20 source geometry and disclose the estimated rigid transform |
| J17A fit to Lite3 Pro and the user's industrial PC | No source-backed user's-PC geometry is available | No official Pro conversion drawing found | Pro manual specifies only `74 x 94 mm` four-M3 interface | Unknown | Freeze design until actual IPC CAD/dimensions, holes, connectors, and keep-outs are available; do not move J17A to compensate for a guessed box |

## Secondary Nonofficial Reference

The surveyed
[MakerWorld D435i/Mid-360 bracket](../../../../references/upstream/2026-07-26_makerworld-d435i-mid360-bracket/source_record.yaml)
is not Lite3 factory geometry. Its published metadata states a 30-degree
Mid-360 tilt, `45 x 80 mm` robot pattern, four M3x6 robot screws, and eight
M3x8 sensor screws. Those facts conflict with the official J20A 15-degree plate,
Lite3 Pro `74 x 94 mm` pattern, and direct two-M3 J17A/D435 relationship. Its
SLDPRT metadata was visible, but the raw source download reported
`闭源文件无法下载。`; it remains comparison evidence only.

## Replica Gate

Before changing the main replica:

1. Freeze the official-video frames, source hashes, and J17A/J20A/S410 source
   records.
2. Render the unchanged official sensor stack with D435 directly seated on the
   J17A faces and compare it with frames 284 and 292.
3. Keep the J17A front ring, camera faces, J20A, S410, Mid-360, and their visible
   relations unchanged.
4. Replace the incorrect generic Interface placeholder with the unchanged
   official BZ20 source geometry; keep the rear AGX/user industrial PC as a
   separate identity.
5. Do not design the Pro adapter until the real user's industrial-PC envelope,
   mounting pattern, connector zones, and cable keep-outs are available. When
   supplied, modify only the hidden lower J17A-to-Pro attachment region and name
   it `print_adaptation`.
6. Features hidden in all primary views remain `unknown`; omit them rather than
   inventing a mechanism.
7. Mesh closure and slicer success remain downstream checks and cannot
   compensate for a failed visual correspondence.

## Current Result

- Requested target: official true-Mid-360 FAST-LIVO2 extension, not the
  historical cylindrical factory LiDAR revision.
- Mid-360/J20A/S410/J17A visible stack: source-backed.
- D435 placement and direct two-M3 attachment to J17A: source-backed.
- BZ20 identity and geometry: source-backed; rigid placement is explicitly
  estimated from official frames 292/296/320.
- Corrected full-standing visual candidate: generated from the official Lite3
  exterior plus the source stack; BZ20/J17A intersection is `0.0 mm3`, BZ20
  is `2.5 mm` above the torso top AABB, and D435 is `8.293274 mm` above it.
- Original J17A fit to Lite3 Pro around the user's different industrial PC:
  unresolved. No base geometry is authorized until the real PC data exists.
- Previous two-piece/yoke design: rejected and prohibited.
- Previous generic-Interface collision, 36 mm sensor shift, and large hidden
  orange adapter: rejected because they were consequences of the wrong part.
- Modeling state: source-backed appearance candidate is ready for visual review;
  the main printable model and Pro base remain unchanged.
