"""Probe the separated official visual, proxy, registration, and clip replay."""

import json
from pathlib import Path

from isaacsim import SimulationApp


OUTPUT = Path(
    "/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human/"
    "results/v8_official_police_integration_asset_probe01"
)
OUTPUT.mkdir(parents=True, exist_ok=True)
app = SimulationApp({"headless": True})

from pxr import Usd, UsdGeom, UsdPhysics, UsdSkel  # noqa: E402

from lite3_sim_bridge.isaac_adapter_core import (  # noqa: E402
    DynamicObstacleSpec,
    dynamic_obstacle_state,
    official_human_registered_state,
)
from lite3_sim_bridge.run_isaac_v12_fallback import (  # noqa: E402
    DYNAMIC_HUMAN_VISUAL_RUNTIME_PRIM,
    OFFICIAL_HUMAN_SOURCE_FOOT_Z_M,
    OFFICIAL_HUMAN_SOURCE_FORWARD_YAW_RADIANS,
    OFFICIAL_HUMAN_SOURCE_VISIBLE_TOP_Z_M,
    _OfficialHumanAnimationPlayer,
    _set_official_human_visual_pose,
    _write_official_human_visual_usd,
    _write_official_human_wrapper_usd,
)


spec = DynamicObstacleSpec(
    name="official_police",
    start_xy=(-3.0, 1.2),
    end_xy=(-3.0, 4.8),
    wait_seconds=0.2,
    speed_mps=0.8,
    radius_m=0.30,
    height_m=1.70,
    terrain_clearance_m=0.02,
)
proxy_path = OUTPUT / "official_human_proxy.usda"
visual_path = OUTPUT / "official_human_visual.usda"
proxy_identity = _write_official_human_wrapper_usd(proxy_path, spec)
visual_identity = _write_official_human_visual_usd(visual_path)

stage = Usd.Stage.CreateNew(str(OUTPUT / "composed_probe.usda"))
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())
visual_root = UsdGeom.Xform.Define(stage, DYNAMIC_HUMAN_VISUAL_RUNTIME_PRIM)
visual_root.GetPrim().GetReferences().AddReference(str(visual_path))

player = _OfficialHumanAnimationPlayer(stage)
skel_roots = [prim for prim in stage.Traverse() if prim.GetTypeName() == "SkelRoot"]
skeletons = [prim for prim in stage.Traverse() if prim.GetTypeName() == "Skeleton"]
if len(skel_roots) != 1 or len(skeletons) != 1:
    raise RuntimeError("composed official visual skeleton cardinality mismatch")


def joint_matrices():
    cache = UsdSkel.Cache()
    cache.Populate(UsdSkel.Root(skel_roots[0]), Usd.PrimDefaultPredicate)
    query = cache.GetSkelQuery(UsdSkel.Skeleton(skeletons[0]))
    if not query or not query.GetAnimQuery():
        raise RuntimeError("retargeted animation did not bind to the skeleton")
    return query.ComputeJointLocalTransforms(Usd.TimeCode.Default())


idle = player.update(0.0, "waiting")
idle_matrices = joint_matrices()
walk = player.update(0.5, "crossing")
walk_matrices = joint_matrices()
maximum_joint_delta = max(
    abs(float(walk_matrices[joint][row][column]) - float(idle_matrices[joint][row][column]))
    for joint in range(len(walk_matrices))
    for row in range(4)
    for column in range(4)
)

dynamic_state = dynamic_obstacle_state(1.0, spec, lambda _x, _y: 0.35)
registered = official_human_registered_state(
    dynamic_state,
    spec,
    source_foot_z_m=OFFICIAL_HUMAN_SOURCE_FOOT_Z_M,
    source_visible_top_z_m=OFFICIAL_HUMAN_SOURCE_VISIBLE_TOP_Z_M,
    source_forward_yaw_radians=OFFICIAL_HUMAN_SOURCE_FORWARD_YAW_RADIANS,
)
pose = _set_official_human_visual_pose(stage, registered)
stage.GetRootLayer().Save()

proxy_stage = Usd.Stage.Open(str(proxy_path))
proxy_collision_paths = [
    str(prim.GetPath())
    for prim in proxy_stage.Traverse()
    if prim.HasAPI(UsdPhysics.CollisionAPI)
]
visual_collision_paths = [
    str(prim.GetPath())
    for prim in stage.Traverse()
    if str(prim.GetPath()).startswith(DYNAMIC_HUMAN_VISUAL_RUNTIME_PRIM)
    and prim.HasAPI(UsdPhysics.CollisionAPI)
]
result = {
    "proxy_identity": proxy_identity,
    "visual_identity": visual_identity,
    "runtime_visual_prim": DYNAMIC_HUMAN_VISUAL_RUNTIME_PRIM,
    "proxy_collision_paths": proxy_collision_paths,
    "visual_collision_paths": visual_collision_paths,
    "skeleton_joint_count": len(walk_matrices),
    "idle_evidence": idle,
    "walk_evidence": walk,
    "maximum_idle_to_walk_joint_matrix_delta": maximum_joint_delta,
    "pose_evidence": pose,
    "passed": (
        len(proxy_collision_paths) == 1
        and not visual_collision_paths
        and len(walk_matrices) == 101
        and maximum_joint_delta > 0.05
        and pose["root_pose_error_m"] < 1.0e-6
        and abs(pose["foot_to_capsule_bottom_error_m"]) < 1.0e-6
    ),
}
print("OFFICIAL_INTEGRATION_ASSET_PROBE=" + json.dumps(result, sort_keys=True), flush=True)
app.close()
