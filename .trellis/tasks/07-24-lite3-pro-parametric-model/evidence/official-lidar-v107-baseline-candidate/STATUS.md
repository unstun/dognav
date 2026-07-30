# Lite3 LiDAR V1.0.7 Baseline Candidate

Status: rejected on 2026-07-26 — engineering adaptation, not a factory-visible
replica. Not accepted and not print-ready.

This directory targets the assembly shown in the official Lite3 LiDAR V1.0.7
manual. It excludes BZ20, AGX, a fake Jetson, custom rails, spanning decks, and
the rejected 17 mm D435 standoff.

The Lite3 exterior, Mid-360, and D435 use pinned source geometry. J17A, J20A,
and S410 are labeled related-source candidates. The `233 x 92 x 46 mm`
Interface, its rigid registration, shallow underside relief, ports, seams,
and local mounting feet are image estimates rather than factory dimensions.

The Interface uses four bored feet with downward M3 fastener proxies. J17A
uses its source `110 x 86 mm`, `4 x M3` pattern, four profiled local supports,
upward M3 fastener proxies, and separate downward body-side fastener proxies.
Those profiled supports, receiver proxies, two invented fastener chains, and
the additional `35 mm` sensor-stack translation were engineering decisions
made to clear and support guessed geometry. They are not visible in, or
dimensioned by, the official V1.0.7 evidence. Dr Sun therefore rejected this
whole candidate as an adaptation rather than a replica.

The artifacts are retained only as rejection evidence. They must not be used
as the visual baseline or silently promoted into the printable model.

Reproduction:

```sh
/opt/homebrew/Caskroom/miniforge/base/bin/python3 \
  references/upstream/2026-07-24_deep-robotics-model/assemble_lite3_urdf.py \
  references/upstream/2026-07-24_deep-robotics-model/source/high_res_official/Lite3/urdf/Lite3_high_res.urdf \
  .trellis/tasks/07-24-lite3-pro-parametric-model/evidence/official-lidar-v107-baseline-candidate/models/lite3_official_manual_pose \
  --hip-y -0.68 --knee 1.48 --ground-align --foot-radius-m 0.02 \
  --output-up-axis z

/opt/homebrew/Caskroom/miniforge/base/bin/python3 \
  .trellis/tasks/07-24-lite3-pro-parametric-model/research/prepare_official_lidar_v107_baseline.py

/Applications/FreeCAD.app/Contents/MacOS/FreeCAD \
  .trellis/tasks/07-24-lite3-pro-parametric-model/research/render_official_lidar_v107_baseline.py

/opt/homebrew/Caskroom/miniforge/base/bin/python3 \
  .trellis/tasks/07-24-lite3-pro-parametric-model/research/compose_official_lidar_v107_comparison.py

/opt/homebrew/Caskroom/miniforge/base/bin/python3 \
  .trellis/tasks/07-24-lite3-pro-parametric-model/research/validate_official_lidar_v107_baseline.py
```

Historical targeted geometry validation: `27/27` passed. That result proves
only that the rejected adaptation met its own collision/structure assertions;
it provides no factory-replica evidence.
