# VLA Navigation & Legged Path Planning — Literature Review (2025–2026)

> Compiled: 2026-07-06 · Scope: ~July 2025 – July 2026, with a few seminal 2024 framing papers.
> Purpose: related-work / survey material for the `machine-dog-nav` path-planning layer, whose end goal is a VLA→planner→RL-locomotion stack on a Lite3 quadruped.
> Method: deep-research harness — 6 search angles, 24 sources fetched, 104 claims extracted, top 25 adversarially verified (3-vote, 2/3-to-kill). **All 12 synthesized findings were confirmed 3-0; none refuted.** Every claim rests on a single primary arXiv source and every "SOTA/first/outperforms" is an author self-report — see [Caveats](#caveats).

## TL;DR

Over 2025–2026, VLA/VLN navigation converged on **hierarchical, dual-system, and streaming** designs that split high-level language grounding from low-level action execution. In parallel, legged path-planning research advanced **learning-based, stability-aware traversability** and planners **explicitly engineered to feed an RL locomotion policy** via waypoints. The two works most directly on-target for this project are **NaVILA** (language mid-level actions → visual locomotion RL policy) and **Skill-Nav** (waypoints as the planner↔RL-policy interface). No single 2025–2026 system was found that end-to-end unifies a VLA planner + terrain-aware legged planner + RL locomotion policy on a quadruped — a likely open gap this PhD could fill.

---

## 1. End-to-end VLA / VLN navigation systems

### NaVILA — the closest architectural analog
[arXiv:2412.04453](https://arxiv.org/abs/2412.04453) (RSS 2025). A **two-level VLA framework for legged robots**: the VLM first generates *mid-level actions expressed in language* (e.g. "moving forward 75cm"), which serve as input to a **separate visual locomotion RL policy** for execution. Explicitly targets Vision-and-Language Navigation (VLN) on legged robots in cluttered/challenging terrain; demonstrated on a Unitree Go2 quadruped and humanoids. **This is the reference design for the project's "VLA plans / RL locomotion executes" stack** — the language-action interface is the key contrast point against waypoint interfaces below.

### Uni-NaVid — unified video VLA
[arXiv:2412.06224](https://arxiv.org/abs/2412.06224). The first **video-based VLA** to unify four embodied navigation sub-tasks in one model — instruction following (VLN), object search, embodied QA, and human following/tracking — trained on **3.6M samples**, reporting SOTA on navigation benchmarks with real-world validation and strong generalization. Relevant as evidence that a single VLA backbone can serve multiple navigation task types.

### StreamVLN — streaming, latency-bounded VLN
[arXiv:2507.05240](https://arxiv.org/abs/2507.05240) (ICRA 2026). Built on Video-LLMs (LLaVA-Video) with a **hybrid slow-fast context strategy**: a fast sliding-window dialogue path for responsive actions plus a slow-updating memory that compresses history via **3D-aware token pruning** and KV-cache reuse, bounding context/inference cost over long streams. Reports **RGB-only SOTA on VLN-CE** with stable low latency (R2R Val-Unseen 56.9% SR / 51.9% SPL; RxR Val-Unseen 52.9% SR / 46.0% SPL). Directly relevant to the real-time-deployment problem when a VLA drives a physical robot.

### DualVLN (InternVLA-N1) — "Ground Slow, Move Fast"
[arXiv:2512.08186](https://arxiv.org/abs/2512.08186). A **dual-system VLN foundation model**: a slow VLM global planner (System 2) predicts intermediate/mid-term **waypoint goals** via image-grounded reasoning, and a fast lightweight **Diffusion Transformer** local executor (System 1) generates smooth trajectories from pixel goals + latent features. Designed to fix the latency and fragmented-motion problems of end-to-end VLN; reports outperforming prior methods across all VLN benchmarks with robust long-horizon planning. The System-2/System-1 split is a second candidate architecture for the project.

### UrbanVLA — route-conditioned micromobility
[arXiv:2510.23576](https://arxiv.org/abs/2510.23576). A scalable **route-conditioned VLA** for urban delivery robots: follows long-horizon route instructions by **explicitly aligning noisy route waypoints with visual observations at execution time**, then planning trajectories. Two-stage SFT+RFT pipeline reported to surpass baselines by 55%+ on SocialNav. Relevant for the "noisy global route → grounded local execution" pattern.

---

## 2. Legged / quadruped path planning

### Traversability-Aware Legged Navigation — value-function traversability
[arXiv:2410.10621](https://arxiv.org/abs/2410.10621) (Oct 2024, seminal framing). Builds a **robot-centric traversability estimator grounded in the value function of the robot's RL locomotion controller**, rather than human-labeled terrain features — so the planner's cost map is derived from what the locomotion policy can *actually* traverse. **This is the cleanest conceptual bridge between the planning and RL-locomotion layers** and is worth close study for this project.

### SCAN-Planner — whole-body collision for elongated bodies
[arXiv:2606.19555](https://arxiv.org/pdf/2606.19555) (SJTU, June 2026 — newest, least corroborated). A route-guided local planner for long-range quadruped navigation introducing a **yaw-aware twin-cylinder footprint** to model the elongated robot body for whole-body 3D collision checking in narrow passages (vs. isotropic point/sphere/inflation). In dense random-obstacle MARSIM sim (40×20 m, 100–500 obstacles, 50 trials): **1.00 SR / 0.00 CR / 0.95 SPL**, above EGO-Planner-2D (0.96/0.04/0.88), EGO-Planner-3D (0.76/0.24/0.75), CMU-Planner (0.92/0.08/0.86), ART-Planner (0.44/0.56/0.31). (Perfect scores are best-case self-report.)

### QuadPiPS — perception-informed footstep planning
[arXiv:2501.00112](https://arxiv.org/pdf/2501.00112) (Jan 2025). A footstep planner built on a novel ego-centric **"legged egocan"** representation fusing geometric + semantic data (surface normals, steppability) for foothold selection. Partitions footstep planning into discrete and continuous sub-problems, producing perception-informed, real-time, kinodynamically-feasible reference trajectories via **search + trajectory optimization**. Relevant if the project later needs foothold-level (rather than body-level) planning.

### STATE-NAV — learning-based traversability for legged rough-terrain
[arXiv:2506.01046](https://arxiv.org/pdf/2506.01046). Presents the **first learning-based traversability + risk-sensitive navigation framework for bipedal robots** on rough terrain. TravFormer predicts instability with uncertainty from self-supervised labels; traversability is defined as a **stability-aware command velocity** (fastest velocity keeping predicted instability below a user limit), fed to a hierarchical planner combining a traversability-informed **RRT\*** global planner (TravRRT\*) with an **MPC** local planner. A template for coupling learned traversability to classical planners.

### Hierarchical planner + learned controller for high-speed discrete terrain
[arXiv:2506.02835](https://arxiv.org/pdf/2506.02835). A planner + learned-tracking-controller pipeline for high-speed quadruped locomotion on discrete terrain: Raibo runs over stepping stones at **4 m/s** and jumps **1.3 m** gaps. The planner uses **sampling-based optimization with fast sequential filtering** (heuristics + a neural network), validated by physics-simulation rollouts, feeding a learned tracking controller. Illustrates planner/controller co-design at aggressive dynamics.

---

## 3. The bridge layer — planner ↔ RL locomotion

### Skill-Nav — waypoints as the interface
[arXiv:2506.21853](https://arxiv.org/pdf/2506.21853). Couples high-level planning to a **deep-RL quadrupedal locomotion policy using waypoints as the interface**, training a waypoint-guided policy that autonomously adjusts locomotion skills to reach targets while avoiding obstacles. Argues waypoints are **simpler and more flexible than direct velocity commands** and let general planners — LLMs *or* classical path-planning algorithms — drive the locomotion policy. **This is the single most on-point paper for the project's interface decision**, and the direct counterpoint to NaVILA's language-action interface.

### ODYSSEY — the full stack on a legged mobile manipulator
[arXiv:2508.08240](https://arxiv.org/html/2508.08240v1). A hierarchical framework stacking a **vision-language task planner** (GPT-4.1 for instruction decomposition, Qwen2.5-VL-72B for grounding) atop a **whole-body RL control policy** on a legged mobile manipulator (Unitree Go2 + Arx5 arm). Performs **map-aware navigation** by projecting language-derived targets onto a 2D occupancy map built via **online SLAM from LiDAR scans**, then local-searching for a collision-free goal pose. The closest existing instance of the end-to-end "language intent → spatial path → RL execution" pipeline (minor caveat: the task-planning layer is a VLM pipeline, so "VLA" is a slightly loose label).

---

## 4. Cross-cutting trends

- **Interface convergence on waypoints/goals over raw velocity.** Skill-Nav (geometric waypoints), DualVLN (pixel goals), UrbanVLA (route waypoints), and NaVILA (language mid-level actions) all interpose a mid-level abstraction between reasoning and the low-level controller. The *form* of that abstraction is the live design question.
- **Dual-system / slow-fast decomposition.** DualVLN and StreamVLN both separate slow semantic reasoning from fast reactive execution, chiefly to meet real-time latency budgets on hardware.
- **Traversability is being redefined robot-centrically.** From human-labeled terrain features → value-function grounding (2410.10621) and stability-aware command velocity (STATE-NAV), tying the cost map to the locomotion policy's actual capability.
- **Streaming, long-horizon, low-latency deployment** is now a first-class objective, not an afterthought (StreamVLN, DualVLN).

## 5. Open problems (most relevant to this project)

1. **Which interface couples best to an Isaac Lab RL policy on a Lite3-class quadruped** — NaVILA's language actions vs. Skill-Nav's geometric waypoints vs. DualVLN's pixel goals? None of these are validated on Lite3 specifically.
2. **Do streaming/dual-system latency optimizations survive a real DRL gait policy on rough terrain**, rather than a wheeled or smooth-trajectory execution assumption?
3. **Can value-function / stability-aware traversability (2410.10621, STATE-NAV) be fed directly from VLA-issued high-level goals**, closing the loop from semantic language intent to terrain-aware quadruped planning?
4. **No 2025–2026 system end-to-end combines a VLA planner + terrain-aware legged planner + RL locomotion policy for a quadruped** — this integrated three-layer stack appears to be an open gap.

## Caveats

- All 12 findings rest on **single primary arXiv sources** (the papers themselves). Verification votes were unanimous 3-0, but there is **no independent third-party replication** for any reported result.
- Every "state-of-the-art," "first," and "outperforms" is the **authors' own self-report** — notably SCAN-Planner's perfect 1.00 SR / 0.00 CR and STATE-NAV/DualVLN benchmark superiority. Benchmark numbers were verified *against the papers*, not re-run.
- **Date-window notes:** NaVILA and Uni-NaVid (Dec 2024) and the value-function traversability paper (Oct 2024) are seminal framing that falls just outside the strict July 2025–July 2026 window; QuadPiPS (Jan 2025) is marginally early. SCAN-Planner (June 2026) and DualVLN (Dec 2025) are the newest and least externally corroborated.
- A 2025 survey, *Pure Vision Language Action (VLA) Models: A Comprehensive Survey* ([arXiv:2509.19012](https://arxiv.org/html/2509.19012v1)), surfaced as a taxonomy/trends source but its specific claims were not individually verified in this pass.

## References

| Paper | arXiv | Layer |
|---|---|---|
| NaVILA: Legged Robot VLA for Navigation (RSS 2025) | [2412.04453](https://arxiv.org/abs/2412.04453) | VLA / bridge |
| Uni-NaVid: unified video VLA | [2412.06224](https://arxiv.org/abs/2412.06224) | VLA |
| StreamVLN: streaming VLN (ICRA 2026) | [2507.05240](https://arxiv.org/abs/2507.05240) | VLN |
| DualVLN / InternVLA-N1: dual-system VLN | [2512.08186](https://arxiv.org/abs/2512.08186) | VLN |
| UrbanVLA: route-conditioned VLA | [2510.23576](https://arxiv.org/abs/2510.23576) | VLA |
| Traversability-Aware Legged Navigation | [2410.10621](https://arxiv.org/abs/2410.10621) | planning / bridge |
| SCAN-Planner: yaw-aware twin-cylinder planner | [2606.19555](https://arxiv.org/pdf/2606.19555) | planning |
| QuadPiPS: perception-informed footstep planner | [2501.00112](https://arxiv.org/pdf/2501.00112) | planning |
| STATE-NAV: learned traversability + TravRRT\*/MPC | [2506.01046](https://arxiv.org/pdf/2506.01046) | planning |
| Hierarchical planner + learned controller (Raibo) | [2506.02835](https://arxiv.org/pdf/2506.02835) | planning |
| Skill-Nav: waypoint interface to RL locomotion | [2506.21853](https://arxiv.org/pdf/2506.21853) | bridge |
| ODYSSEY: VLA task planner + whole-body RL + SLAM | [2508.08240](https://arxiv.org/html/2508.08240v1) | bridge |
| Pure VLA Models: A Comprehensive Survey (unverified) | [2509.19012](https://arxiv.org/html/2509.19012v1) | survey |
