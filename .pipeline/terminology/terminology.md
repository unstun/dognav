# Terminology

| Chinese | English | Abbreviation | Notes |
|---|---|---|---|
| 四足机器人 | Quadruped Robot | — | Do not use “quadruped dog” in academic writing. |
| 自主导航 | Autonomous Navigation | — | Goal-directed operation without continuous human commands. |
| 运动控制 | Locomotion Control | — | The lower-level controller that executes motion commands. |
| 几何航点 | Geometric Waypoint | — | A target position or pose expressed in a geometric coordinate frame. |
| 航点跟踪 | Waypoint Tracking | — | Converting waypoint error into commands and reaching the waypoint. |
| 路径规划器 | Path Planner | — | Produces a path or waypoint sequence toward a goal. |
| 局部规划器 | Local Planner | — | Produces near-term collision-aware motion commands or waypoints. |
| 可通行性 | Traversability | — | Robot-dependent ability or cost of crossing terrain. |
| 视觉语言动作模型 | Vision-Language-Action Model | VLA | Maps visual and language context to actions or action abstractions. |
| 仿真到现实 | Sim-to-Real / Sim2Real | — | Transfer from simulation to a physical robot. |
| 修订版 | Revision | — | A named snapshot of source, configuration, component contracts, and evidence references. A working revision is not necessarily clean, accepted, or formal. |
| 运行标识 | Run ID | — | The immutable identifier for one execution and its artifact set. It identifies evidence but does not make that run a candidate. |
| 候选项 | Candidate | — | A run explicitly submitted against a declared acceptance protocol. A smoke, dry run, or preflight is not a candidate unless deliberately promoted. |
| 呈现契约 | Presentation Contract | — | A versioned definition of views, layout, resolution, timing, and synchronization used for review. Conformance validates the presentation package, not the navigation behavior shown inside it. |
| 自动门控 | Automated Gate | — | Machine-checkable conditions for a declared scope and protocol. A pass applies only to that scope and cannot satisfy a human gate or promote another run. |
| 人工门控 | Human Gate | AC55 | A decision reserved for a named human reviewer. Office AC55 is owned exclusively by Dr Sun and cannot be inferred from automated metrics or presentation conformance. |

New project terms require a literature or official-source check before use.

Revision, Run ID, Candidate, Presentation Contract, Automated Gate, and Human
Gate are separate control dimensions. None is evidence that another has passed.
