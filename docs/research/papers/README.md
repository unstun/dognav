# Downloaded papers

Source PDFs for the [2026-07-06 VLA & legged-navigation survey](../2026-07-06-vla-and-legged-navigation-survey.md). Filenames are `<arxiv-id>-<slug>.pdf`.

Suggested reading order for the planner-on-RL-locomotion interface decision (★ = start here):

| # | Paper | arXiv | Layer | Why read |
|---|---|---|---|---|
| ★1 | Skill-Nav | [2506.21853](https://arxiv.org/abs/2506.21853) | bridge | Waypoint interface to a deep-RL quadruped policy — the core interface question |
| ★2 | NaVILA | [2412.04453](https://arxiv.org/abs/2412.04453) | VLA/bridge | Language mid-level actions → visual locomotion RL policy (your exact stack) |
| ★3 | Traversability-Aware Legged Navigation | [2410.10621](https://arxiv.org/abs/2410.10621) | planning/bridge | Cost map from the locomotion policy's own value function |
| 4 | ODYSSEY | [2508.08240](https://arxiv.org/abs/2508.08240) | bridge | Closest full stack: VLM planner + SLAM map + whole-body RL |
| 5 | STATE-NAV | [2506.01046](https://arxiv.org/abs/2506.01046) | planning | Learned traversability → TravRRT* + MPC |
| 6 | DualVLN / InternVLA-N1 | [2512.08186](https://arxiv.org/abs/2512.08186) | VLN | Dual-system (slow VLM planner + fast diffusion executor) |
| 7 | StreamVLN | [2507.05240](https://arxiv.org/abs/2507.05240) | VLN | Streaming, latency-bounded VLN (ICRA 2026) |
| 8 | Uni-NaVid | [2412.06224](https://arxiv.org/abs/2412.06224) | VLA | Unified video VLA across 4 navigation sub-tasks |
| 9 | UrbanVLA | [2510.23576](https://arxiv.org/abs/2510.23576) | VLA | Route-conditioned; noisy waypoints ↔ visual alignment |
| 10 | QuadPiPS | [2501.00112](https://arxiv.org/abs/2501.00112) | planning | Perception-informed footstep planning ("legged egocan") |
| 11 | Hierarchical planner + learned controller (Raibo) | [2506.02835](https://arxiv.org/abs/2506.02835) | planning | Planner/controller co-design at high dynamics |
| 12 | SCAN-Planner | [2606.19555](https://arxiv.org/abs/2606.19555) | planning | Yaw-aware twin-cylinder footprint for narrow passages |
| 13 | Pure VLA Models: A Comprehensive Survey | [2509.19012](https://arxiv.org/abs/2509.19012) | survey | Taxonomy/trends background (claims not verified in survey pass) |

Re-download any file: `curl -L -o <name>.pdf https://arxiv.org/pdf/<arxiv-id>`
