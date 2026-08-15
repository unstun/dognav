"""Render an official Isaac People GoTo walk for human visual calibration.

This script intentionally excludes Lite3, SCAN, the local moving capsule, and
the forest.  It verifies the vendor character, Biped animation graph, and
official People GoTo controller in isolation before integration.
"""

import json
from pathlib import Path

from isaacsim import SimulationApp


OUTPUT_ROOT = Path(
    "/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human/"
    "results/official_people_walk_calibration04_police"
)
CHARACTER_URL = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/"
    "Isaac/People/Characters/male_adult_police_04/"
    "male_adult_police_04.usd"
)
FPS = 30
FRAME_COUNT = 240


OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
app = SimulationApp(
    {
        "headless": True,
        "width": 1280,
        "height": 720,
        "anti_aliasing": 3,
    }
)

import carb  # noqa: E402
import imageio.v2 as imageio  # noqa: E402
import numpy as np  # noqa: E402
import omni.kit.app  # noqa: E402
import omni.replicator.core as rep  # noqa: E402
import omni.timeline  # noqa: E402
import omni.usd  # noqa: E402
from pxr import Gf, Sdf, UsdGeom, UsdLux  # noqa: E402


extension_manager = omni.kit.app.get_app().get_extension_manager()
for extension_id in (
    "omni.anim.people",
    "isaacsim.replicator.agent.core",
):
    extension_manager.set_extension_enabled_immediate(extension_id, True)
for _ in range(8):
    app.update()

import omni.anim.graph.core as animation_graph  # noqa: E402
from isaacsim.replicator.agent.core.settings import AssetPaths  # noqa: E402
from isaacsim.replicator.agent.core.stage_util import CharacterUtil  # noqa: E402
from omni.anim.people.scripts.commands.goto import GoTo  # noqa: E402
from omni.anim.people.scripts.navigation_manager import NavigationManager  # noqa: E402
from omni.anim.people.scripts.utils import Utils  # noqa: E402

context = omni.usd.get_context()
context.new_stage()
for _ in range(8):
    app.update()
stage = context.get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)


def cube(path, position, size, color):
    prim = UsdGeom.Cube.Define(stage, path)
    prim.CreateSizeAttr(1.0)
    prim.AddTranslateOp().Set(Gf.Vec3d(*position))
    prim.AddScaleOp().Set(Gf.Vec3f(*size))
    prim.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    return prim


# A metric floor and markers make foot contact, body scale, and travel distance visible.
cube("/World/Floor", (0.0, 2.5, -0.03), (5.0, 6.5, 0.03), (0.24, 0.27, 0.30))
for x_index, x_value in enumerate((-2.0, -1.0, 0.0, 1.0, 2.0)):
    for y_index, y_value in enumerate((0.0, 1.0, 2.0, 3.0, 4.0, 5.0)):
        color = (0.14, 0.22, 0.16) if (x_index + y_index) % 2 == 0 else (0.38, 0.43, 0.39)
        cube(
            f"/World/Checker/X{x_index}Y{y_index}",
            (x_value, y_value, 0.002),
            (0.49, 0.49, 0.004),
            color,
        )
for metre in range(0, 6):
    cube(
        f"/World/Grid/Y{metre}",
        (0.0, float(metre), 0.003),
        (4.5, 0.012, 0.004),
        (0.78, 0.80, 0.82),
    )
for x_index, x_value in enumerate((-2.0, -1.0, 0.0, 1.0, 2.0)):
    cube(
        f"/World/Grid/X{x_index}",
        (x_value, 2.5, 0.004),
        (0.010, 5.5, 0.005),
        (0.54, 0.57, 0.60),
    )
cube("/World/Scale/OneMetre", (-1.25, 0.2, 0.50), (0.025, 0.025, 0.50), (0.20, 0.72, 1.0))
cube("/World/Scale/AdultHeight", (-1.45, 0.2, 0.865), (0.025, 0.025, 0.865), (1.0, 0.78, 0.16))

key = UsdLux.DistantLight.Define(stage, "/World/KeyLight")
key.CreateIntensityAttr(2600.0)
key.CreateAngleAttr(0.65)
key.AddRotateXYZOp().Set(Gf.Vec3f(35.0, -30.0, -25.0))
fill = UsdLux.DomeLight.Define(stage, "/World/FillLight")
fill.CreateIntensityAttr(550.0)

biped = CharacterUtil.load_default_biped_to_stage()
character_root = CharacterUtil.load_character_usd_to_stage(
    CHARACTER_URL,
    (0.0, 0.0, 0.0),
    180.0,
    "Character",
)
for _ in range(45):
    app.update()
characters = CharacterUtil.get_characters_in_stage()
if len(characters) != 1:
    raise RuntimeError(f"expected one visible character, got {len(characters)}")
skel_root = characters[0]
animation_graph_prim = CharacterUtil.get_anim_graph_from_character(biped)
if animation_graph_prim is None or not animation_graph_prim.IsValid():
    raise RuntimeError("official Biped animation graph is missing")
CharacterUtil.setup_animation_graph_to_character(characters, animation_graph_prim)

timeline = omni.timeline.get_timeline_interface()
timeline.set_target_framerate(FPS)
timeline.play()
for _ in range(12):
    app.update()

character = animation_graph.get_character(str(skel_root.GetPath()))
if character is None:
    raise RuntimeError("official animation graph did not bind to the character")
navigation = NavigationManager(str(skel_root.GetPath()), False, False)
command = GoTo(
    character,
    ["GoTo", "0.0", "5.0", "0.0", "180.0"],
    navigation,
    character_name="Character",
    update_metadata_callback_fn=lambda **_kwargs: None,
)

oblique_camera = rep.create.camera(
    position=(4.8, -6.8, 2.45),
    look_at=(0.0, 2.4, 0.86),
    focal_length=38.0,
)
side_camera = rep.create.camera(
    position=(4.8, 2.5, 1.35),
    look_at=(0.0, 2.5, 0.82),
    focal_length=30.0,
)
oblique_product = rep.create.render_product(oblique_camera, (640, 720))
side_product = rep.create.render_product(side_camera, (640, 720))
oblique_rgb = rep.AnnotatorRegistry.get_annotator("rgb")
side_rgb = rep.AnnotatorRegistry.get_annotator("rgb")
oblique_rgb.attach(oblique_product)
side_rgb.attach(side_product)
for _ in range(8):
    rep.orchestrator.step(rt_subframes=2)

video_path = OUTPUT_ROOT / "official_isaac_people_goto_walk.mp4"
writer = imageio.get_writer(
    video_path,
    fps=FPS,
    codec="libx264",
    quality=8,
    macro_block_size=None,
)
sampled_positions = []
for frame_index in range(FRAME_COUNT):
    command.execute(1.0 / FPS)
    rep.orchestrator.step(rt_subframes=1)
    oblique_rgba = oblique_rgb.get_data()
    side_rgba = side_rgb.get_data()
    if (
        oblique_rgba is None
        or side_rgba is None
        or getattr(oblique_rgba, "size", 0) == 0
        or getattr(side_rgba, "size", 0) == 0
    ):
        raise RuntimeError(f"empty RGB frame at {frame_index}")
    frame = np.concatenate((side_rgba[:, :, :3], oblique_rgba[:, :, :3]), axis=1)
    writer.append_data(frame)
    if frame_index % 30 == 0:
        position, rotation = Utils.get_character_transform(character)
        sampled_positions.append(
            {
                "frame": frame_index,
                "seconds": frame_index / FPS,
                "root_position_m": [float(value) for value in position],
                "root_rotation_xyzw": [float(value) for value in rotation],
            }
        )
writer.close()

bbox_cache = UsdGeom.BBoxCache(
    stage.GetTimeCodesPerSecond(),
    [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
    useExtentsHint=False,
)
world_range = bbox_cache.ComputeWorldBound(character_root).ComputeAlignedRange()
result = {
    "schema_version": 1,
    "claim": (
        "official Isaac Sim 5.1 character driven by the official Biped animation "
        "graph and omni.anim.people GoTo controller; isolated visual calibration, "
        "not Lite3 navigation or collision validation"
    ),
    "runtime": {
        "isaac_sim": "5.1",
        "environment": "isaaclab conda runtime",
        "omni_anim_people": "0.7.9",
        "replicator_agent_core": "0.7.28",
    },
    "character_url": CHARACTER_URL,
    "biped_url": AssetPaths.default_biped_asset_path(),
    "character_root": str(character_root.GetPath()),
    "skel_root": str(skel_root.GetPath()),
    "animation_graph": str(animation_graph_prim.GetPath()),
    "controller": "omni.anim.people GoTo",
    "command": "Character GoTo 0 5 0 180",
    "fps": FPS,
    "frame_count": FRAME_COUNT,
    "video_path": str(video_path),
    "sampled_root_positions": sampled_positions,
    "final_visible_bbox_min_m": [float(value) for value in world_range.GetMin()],
    "final_visible_bbox_max_m": [float(value) for value in world_range.GetMax()],
}
(OUTPUT_ROOT / "identity.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print("OFFICIAL_PEOPLE_CALIBRATION=" + json.dumps(result, sort_keys=True), flush=True)
timeline.stop()
oblique_rgb.detach()
side_rgb.detach()
app.close()
