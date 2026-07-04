---
origin: ai+web
reviewed: false
---

# Quadruped Navigation Seed Survey

> Date: 2026-07-04
> Scope: first seed list for quadruped navigation / legged robot navigation.
> Evidence: `smart-search doctor` passed; searches and fetched sources are saved under `1_survey/2026-07-04_quadruped_navigation_seed/evidence/`.
> Status: seed list only, not a reviewed literature survey and not a Research Contract.

## Search Scope

This first pass searched for:

- quadruped navigation / legged robot navigation
- point-goal navigation and waypoint following
- local obstacle avoidance
- mapless and map-based local navigation
- visual / depth / RGB-D navigation for legged robots
- sim-to-real navigation for quadruped robots

Pure locomotion, gait, and parkour papers are excluded unless they directly connect locomotion to navigation.

## Seed Papers

| CitationKey | Why it matters for this repo | Local PDF | Evidence |
|---|---|---|---|
| `Cai2025_NavDP` | End-to-end RGB-D navigation diffusion policy; useful as recent point-goal / open-world navigation reference. Treat as high-level nav method, not locomotion training evidence. | `1_survey/papers/Cai2025_NavDP.pdf` | arXiv `2505.08712`; fetched PDF text in `fetch_navdp_2505_08712_pdf.json` |
| `Wang2025_SkillNav` | Directly relevant to waypoint interface between high-level planner and quadruped locomotion policy. This is close to a possible nav Contract design axis. | `1_survey/papers/Wang2025_SkillNav.pdf` | arXiv `2506.21853`; fetched PDF text in `fetch_skillnav_2506_21853_pdf.json` |
| `Zhu2026_TRANS` | Terrain-aware DRL navigation under social interaction; relevant if the nav task includes dynamic humans or socially interactive avoidance. | `1_survey/papers/Zhu2026_TRANS.pdf` | arXiv `2602.12724`; fetched PDF text in `fetch_trans_2602_12724_pdf.json` |
| `Ren2025_TOPNav` | CoRL paper that explicitly integrates terrain, obstacle, and proprioception estimation. Strong seed for terrain-aware local navigation. | `1_survey/papers/Ren2025_TOPNav.pdf` | PMLR page `v270/ren25a.html`; fetched in `fetch_topnav_ren25a.json` |
| `Fu2022_VPNav` | CVPR paper on coupling vision and proprioception for point-goal navigation on legged robots. Important bridge between planner and locomotion feedback. | `1_survey/papers/Fu2022_VPNav.pdf` | CVF PDF; fetched in `fetch_fu22_vp_nav_pdf.json` |
| `Hoeller2021_StateRepresentationNavigation` | Mapless / local navigation in cluttered and dynamic environments on ANYmal; important baseline for depth-based obstacle avoidance. | `1_survey/papers/Hoeller2021_StateRepresentationNavigation.pdf` | arXiv `2103.04351`; fetched in `fetch_hoeller_2103_04351.json` |
| `Kim2022_FDMITS` | RSS paper on learned forward dynamics model and informed trajectory sampler for safe quadruped navigation. Useful for local planner design. | `1_survey/papers/Kim2022_FDMITS.pdf` | RSS PDF; fetched in `fetch_rss18_fdm_its.json` |
| `Wellhausen2021_RoughTerrainNavigation` | Reachability planning and template learning for rough-terrain legged navigation; important non-DRL planning baseline. | `1_survey/papers/Wellhausen2021_RoughTerrainNavigation.pdf` | ETH Research Collection PDF; fetched in `fetch_wellhausen21_rough_terrain_navigation.json` |
| `Truong2023_IndoorSimOutdoorReal` | PointGoal / Context-Guided PointNav from indoor simulation to real outdoor quadruped deployment. Useful for sim-to-real nav framing. | `1_survey/papers/Truong2023_IndoorSimOutdoorReal.pdf` | arXiv `2305.01098`; Google Research page fetched in `fetch_google_indoorsim_outdoorreal.json` |
| `Yu2022_VisualLocomotion` | Visual locomotion with high-level vision policy and low-level motion controller. It is supporting context, not standalone nav evidence. | `1_survey/papers/Yu2022_VisualLocomotion.pdf` | PMLR page `v164/yu22a.html`; fetched in `fetch_yu22_visual_locomotion.json` |
| `Agarwal2023_EgocentricVision` | End-to-end quadruped locomotion over stairs, curbs, stepping stones, and gaps with a single egocentric depth camera. Supporting context for perception-to-locomotion. | `1_survey/papers/Agarwal2023_EgocentricVision.pdf` | PMLR page `v205/agarwal23a.html`; fetched in `fetch_agarwal23_egocentric_vision.json` |
| `Cheng2024_NaVILA` | Vision-language-action navigation for legged robots. Relevant for long-horizon language-conditioned nav, but probably too broad for the first Contract. | `1_survey/papers/Cheng2024_NaVILA.pdf` | Project PDF; fetched in `fetch_navila_pdf.json` |
| `Ren2023_HierarchicalVisionNavigation` | Hierarchical vision navigation plus foothold adaptation. PDF download was blocked/failed; PMC full text is available and fetched. | PDF pending | PMC full text fetched in `fetch_hierarchical_vision_nav_pmc.json`; MDPI PDF fetch attempt failed |

## Initial Reading Order

1. `Fu2022_VPNav` and `Ren2025_TOPNav`: best first pair for the core question "how should navigation talk to locomotion?"
2. `Wang2025_SkillNav`: read next if we want waypoint interface as the first nav task definition.
3. `Hoeller2021_StateRepresentationNavigation` and `Kim2022_FDMITS`: read for local avoidance and local planner baselines.
4. `Truong2023_IndoorSimOutdoorReal` and `Cai2025_NavDP`: read for PointGoal / sim-to-real / end-to-end policy framing.
5. `Yu2022_VisualLocomotion`, `Agarwal2023_EgocentricVision`, and `Ren2023_HierarchicalVisionNavigation`: read as perception-locomotion support, not as primary nav claims.
6. `Zhu2026_TRANS` and `Cheng2024_NaVILA`: keep as emerging directions; useful later if the Contract includes social navigation or language-conditioned nav.

## Early Boundary Notes

- The project is still in planning / survey stage. No paper here defines a validated `machine-dog-nav` result.
- The most immediate design fork is task form: point-goal, waypoint following, mapless local avoidance, map-based local navigation, or a hybrid.
- Several papers solve navigation by using a hierarchical stack: high-level planner or policy outputs waypoints / velocity / local trajectory, while low-level locomotion executes. This makes the interface between nav and locomotion the first thing to define in a Research Contract.
- Visual locomotion papers are useful because they explain perception and terrain traversal, but they should not be cited as evidence for full navigation unless they include goal reaching / planning / obstacle avoidance.
- Old walking checkpoints from `machine-dog` remain source references only. They are not nav evidence unless a future Contract defines reuse boundaries.

## Commands Used

- `smart-search doctor --format json`
- `smart-search search "quadruped navigation legged robot navigation point-goal waypoint obstacle avoidance sim-to-real papers" --validation balanced --extra-sources 5 --timeout 90 --format json`
- `smart-search search "visual locomotion for legged robots depth camera navigation quadruped robot paper" --validation balanced --extra-sources 5 --timeout 90 --format json`
- `smart-search search "mapless navigation quadruped robot local obstacle avoidance reinforcement learning paper" --validation balanced --extra-sources 5 --timeout 90 --format json`
- `smart-search fetch <source-url> --format json --output <evidence-file>`

## Open Items

- Read `Fu2022_VPNav`, `Ren2025_TOPNav`, and `Wang2025_SkillNav` in detail before choosing the first Contract topic.
- Recover or re-download the PDF for `Ren2023_HierarchicalVisionNavigation` if needed; current evidence is PMC full text, not a local PDF.
- Expand references around `VinL`, `Advanced skills by learning locomotion and local navigation end-to-end`, and `Learning robust autonomous navigation and locomotion for wheeled-legged robots` if Dr Sun chooses a waypoint/local-navigation Contract.
