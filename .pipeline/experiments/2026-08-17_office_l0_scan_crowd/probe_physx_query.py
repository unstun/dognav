"""Minimal Isaac Sim 5.1 ground-plane raycast API probe."""

from isaaclab.app import AppLauncher

launcher = AppLauncher(headless=True, device="cuda:0")
app = launcher.app
try:
    import carb
    import isaaclab.sim as sim_utils
    from isaaclab.sim import SimulationCfg, SimulationContext
    from omni.physx import get_physx_scene_query_interface
    from omni.physics.core import get_physics_scene_query_interface

    sim = SimulationContext(SimulationCfg(device="cuda:0"))
    cfg = sim_utils.GroundPlaneCfg()
    cfg.func("/World/ProbeGround", cfg)
    sim.reset()
    for _ in range(4):
        sim.step(render=False)
    legacy_hit = get_physx_scene_query_interface().raycast_closest(
        carb.Float3(0.0, 0.0, 1.0),
        carb.Float3(0.0, 0.0, -1.0),
        2.0,
        True,
    )
    print(f"PHYSX_LEGACY_QUERY_TYPE={type(legacy_hit)!r}", flush=True)
    print(f"PHYSX_LEGACY_QUERY_RESULT={legacy_hit!r}", flush=True)
    current_found, current_hit = get_physics_scene_query_interface().raycast_closest(
        carb.Float3(0.0, 0.0, 1.0),
        carb.Float3(0.0, 0.0, -1.0),
        2.0,
        both_sides=True,
    )
    print(f"PHYSICS_UMBRELLA_FOUND={current_found!r}", flush=True)
    print(f"PHYSICS_UMBRELLA_HIT={current_hit!r}", flush=True)
    if not current_found:
        raise RuntimeError("minimal ground-plane umbrella raycast did not hit")
finally:
    app.close()
