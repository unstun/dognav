# Native Isaac Lab Forest Scene Upstream Survey

Date: 2026-08-14

Status: candidate set `surveyed`; the bounded `forest_gen` visual-rendering
claim was subsequently `reproduced` on the RTX 5070 Ti. Collision, sensors,
Lite3, planning integration, and clean simulator teardown were not established.

## Question And Acceptance Criteria

This survey asks whether a ready forest scene exists that is implemented
directly against Isaac Lab, rather than requiring an external scene such as
MAVS, OBJ, or FBX to be converted to USD first.

A strong candidate should provide:

1. a native Isaac Lab launch or scene configuration;
2. forest assets or a forest generator, not only generic rough terrain;
3. collision-ready obstacles suitable for quadruped navigation;
4. a reproducible seed and a documented simulator version;
5. a usable license and a pin-able revision;
6. a plausible path to the project's frozen Isaac Sim 5.1 / Isaac Lab 2.3.2
   environment.

## Bottom Line

[`GrafCzterech/forest_gen`](https://github.com/GrafCzterech/forest_gen) is the
only inspected candidate that combines a native Isaac Lab entry point, a
procedural forest generator, and bundled visual vegetation assets. It ships
USDZ models for pine and birch trees, bushes, ferns, grass, rocks, a stump, and
a fallen trunk; `sim.py` launches the result through Isaac Lab's
`AppLauncher`, `InteractiveScene`, and `SimulationContext`. Its example task
uses the Isaac Lab Spot asset directly. It therefore avoids the external
OBJ/FBX-to-USD conversion pipeline rejected for this task.

It is not yet an unmodified drop-in for this project's frozen runtime:

- release `v0.3.8` declares `numpy>=2.0.0`, while the pinned Isaac Lab 2.3.2
  packages declare `numpy<2`;
- forest terrain has collision, but the vegetation assets are spawned without
  collision properties, and inspection of a bundled pine USDZ did not reveal
  authored physics/collision APIs;
- the full scene is not controlled by one exposed random seed;
- upstream CI tests utilities, but does not launch the Isaac Lab scene.

The initial source-only label was **native Isaac Lab candidate, surveyed**. A
later fixed-seed run produced three raw Isaac Lab viewport captures, supporting
`reproduced` only for native visual scene generation. The package is still not
`integrated`, `validated`, or "ready without modification."

## Candidate Comparison

| Candidate | Native Isaac Lab | Forest representation | Collision state | Version/license evidence | Decision |
|---|---|---|---|---|---|
| [`forest_gen`](https://github.com/GrafCzterech/forest_gen) | Yes: `AppLauncher`, `InteractiveScene`, Spot example | Bundled USDZ trees, understory, rocks, stump, fallen trunk; procedural height/moisture/slope distribution | Terrain collision; vegetation collision absent in inspected source/assets | `v0.3.8` / `a75fb28c7b896e2a67e2d889b804732d33c56e0c`; GPL-3.0-only | Visual generation `reproduced` on Isaac Lab 2.3.2; collision, lifecycle, and integration remain open |
| [`outdoor-nav`](https://github.com/sdfbiasdf/outdoor-nav) | Yes: `InteractiveSceneCfg`; explicitly targets Isaac Sim 5.1 + Isaac Lab 2.3 | Procedural cylinders/cones/spheres/cuboids; USD prop table is empty | Primitive trees, rocks, and houses are collidable | `574bcc21f9414c4c809849c2b651d35c2bb6a8c1`; README says MIT, but no root license file was found | Best exact-version physics scaffold, but not a visually realistic ready forest and licensing is unresolved |
| [`YOPO_isaac_lab`](https://github.com/zwhhhhh9/YOPO_isaac_lab) | Yes | Deterministic tiled cylinder/cone forest for a drone | Primitive trunks are collidable | `423c87049f9d1b6527b9f74f1ecc48982b9b4356`; no detected license | Useful generator reference, not a quadruped-ready realistic forest |
| [`TerrainPilot`](https://github.com/rzrnagi/TerrainPilot) | Yes | Small Go2 bamboo scene using cylinder stems | Primitive stems are collidable | `db93b95eb763e608b28066e68470a06c556e881a`; no README/license found | Too small and primitive for the requested scene |
| [`OmniDrones`](https://github.com/btx0424/OmniDrones) | Legacy `omni.isaac.lab` API | Its Forest task uses box-like discrete obstacles, not tree assets | Generic terrain obstacles | `9ce7c2028b71be64d7e748c31f685cd3b54afe27`; MIT; documents Isaac Sim 4.1 | Not compatible with the current native API/version target |
| [Official Isaac Lab](https://github.com/isaac-sim/IsaacLab) | Yes | Rough/parkour terrain primitives; repeated cylinders can approximate trunks | Supported terrain collision | Official upstream | No ready forest/vegetation scene was found |

All alternatives remain `surveyed`. `forest_gen` alone now has bounded visual
runtime evidence in this repository.

## Recommended Candidate: `forest_gen`

### Pinned upstream

- Repository: <https://github.com/GrafCzterech/forest_gen>
- Stable release: <https://github.com/GrafCzterech/forest_gen/releases/tag/v0.3.8>
- Release commit: `a75fb28c7b896e2a67e2d889b804732d33c56e0c`
- Observed main commit: `01392c1d59e3de7a08064fd6f8b9d08b97146a34`
- Declared license: GPL-3.0-only
- Required scene toolkit: [`GrafCzterech/STRIPE-kit`](https://github.com/GrafCzterech/STRIPE-kit), observed commit `ce97eed40d9fc4927c4856eda6a17204d01087db`, GPL-3.0

The release commit is preferred over main for the first reproduction because it
provides a stable version boundary.

### What is already native

The upstream code directly imports Isaac Lab and provides a runnable simulator
entry point. The documented scene command is:

```bash
python sim.py
```

The README also gives a Spot task example:

```bash
python3 train.py --task=task --video --headless --num_envs=500
```

The repository contains actual USDZ assets rather than download placeholders,
including multiple pine and birch variants, bushes, ferns, grass, seven rocks,
a stump, and a fallen trunk. The generator combines those assets with terrain
height, slope, moisture, and biologically motivated placement layers.

### Verified gaps for the frozen project environment

1. **Dependency conflict.** `forest_gen` 0.3.8 declares `numpy>=2.0.0`; the
   local Isaac Lab 2.3.2 source snapshot declares `numpy<2`. A normal dependency
   resolver cannot satisfy both constraints unchanged. A reproduction should
   preserve the simulator's NumPy version and install the forest package from a
   pinned source with its metadata constrained or dependencies installed
   separately.
2. **Vegetation is visually present but not physics-ready.** The inspected
   asset construction supplies no collision properties. The bundled
   `Pine_1.usdz` has a valid default prim, metre units, and Z-up metadata, but no
   inspected physics, rigid-body, or collision API. A robot or ray-caster must
   not be assumed to collide with or perceive every tree merely because it is
   visible.
3. **Scene determinism is incomplete.** Placement paths still use Python's
   global `random` state without one explicit scene seed covering every asset
   choice and transform.
4. **Upstream CI proof is absent.** Upstream CI does not launch `sim.py`. The
   local visual preview supplies target-GPU runtime evidence but also exposed a
   slow asset-instantiation path and incomplete graceful shutdown.
5. **Asset provenance needs a separate audit.** The repository license is
   explicit, but per-model origin/attribution was not located during this
   source inspection.

### Executed visual preview on the RTX 5070 Ti

The pinned sources were copied from the local repository into a dated remote
execution directory. The run preserved Isaac Sim 5.1, Isaac Lab 2.3.2, and
NumPy 1.26.0, exposed the source trees through `PYTHONPATH`, and installed only
the missing `opensimplex==0.4.5.1` dependency. A project-side wrapper launched
the upstream `ForestGenSpec` with its Spot example at `32 m x 32 m`, seed 14,
and captured overview, robot-context, and canopy views at `1280 x 720`.

The scene instantiated 41 birches, 46 pines, 50 bushes, 4,484 grass assets,
five rocks, and two terrain meshes. Image capture completed after approximately
nine minutes. The high startup cost is attributable largely to first-use USDZ
conversion and thousands of individually registered grass assets. The renderer
also reported corrupt face-varying UV primvar sizes on several meshes.

All three raw images, metrics, and the runtime log were copied back with
remote/local SHA-256 parity under
`.pipeline/experiments/2026-08-14_forest_gen_visual_preview/`. Application
teardown retained about 2.7 GiB of GPU memory and did not finish within six
minutes after output sync, so the task-owned process was interrupted. This
supports `reproduced` for visual scene generation but not a clean full-lifecycle
reproduction and not `integrated`.

The next integration change, only after reproduction, would add explicit
collision proxies for vegetation, freeze scene randomness, and register the
forest mesh prims with the project's camera/LiDAR ray-casting configuration.

## Exact-Version Alternative: `outdoor-nav`

`outdoor-nav` is noteworthy because its README explicitly names Isaac Sim 5.1
and Isaac Lab 2.3, and its source builds collidable procedural trees, rocks,
houses, paths, and grass through native scene configuration. It also exposes a
seed and includes Go2 and Spot configurations plus RGB, depth, and semantic
sensors.

However, its default scene is made from primitive shapes, its table of realistic
USD props is empty, it has only one observed commit, and the README's MIT claim
is not backed by a detected repository license file. It is better used as a
physics/configuration reference than as the requested ready realistic forest.

## Exclusions And Negative Findings

- The inspected official Isaac Lab tree contains no ready forest, vegetation,
  woodland, or grassland task. Existing rough and parkour terrain generators
  are useful building blocks, not a finished forest scene.
- `KinoVLA` has a substantial native forest compiler and explicit collision
  proxies, but its forest assets and outputs are not self-contained in the
  repository; it requires external asset acquisition and compilation. That is
  the conversion/acquisition path excluded by the question.
- `IsaacLab-Arena` has no inspected forest environment; current main also
  targets a newer Isaac Lab/Isaac Sim pair than this project's frozen runtime.
- MAVS and OrchardBench may provide strong outdoor assets or dynamics, but are
  not direct Isaac Lab forest scenes and would require a bridge or conversion.
- Several search hits used "forest" for an isolation-forest algorithm or used
  a forest of box/cylinder obstacles for drones; these are not realistic
  quadruped forest terrain packages.

## Selection Recommendation

Retain `forest_gen` `v0.3.8` as the visual forest base because native rendering
is now directly demonstrated. Before using it for navigation, address four
explicit gaps rather than calling it plug-and-play: instance/teardown scaling,
UV/material warnings, vegetation collision, and deterministic sensor-visible
geometry. Keep `outdoor-nav` as a source reference for seeded placement,
collision primitives, and sensor configuration, not as the visual scene base.
