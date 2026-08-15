"""Probe official AnimationGraph joint-query output after vendor retargeting."""

import json

from isaacsim import SimulationApp


ROOT = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac"
CHARACTER_URL = f"{ROOT}/People/Characters/male_adult_police_04/male_adult_police_04.usd"

app = SimulationApp({"headless": True})

import omni.graph.core as og  # noqa: E402
import omni.kit.app  # noqa: E402
import omni.timeline  # noqa: E402
import omni.usd  # noqa: E402
import numpy as np  # noqa: E402
from pxr import UsdGeom, UsdSkel  # noqa: E402


extension_manager = omni.kit.app.get_app().get_extension_manager()
for extension_id in ("omni.anim.people", "isaacsim.replicator.agent.core"):
    extension_manager.set_extension_enabled_immediate(extension_id, True)
for _ in range(8):
    app.update()

import omni.anim.graph.core as animation_graph  # noqa: E402
from isaacsim.replicator.agent.core.stage_util import CharacterUtil  # noqa: E402
from omni.anim.people.scripts.commands.goto import GoTo  # noqa: E402
from omni.anim.people.scripts.navigation_manager import NavigationManager  # noqa: E402

context = omni.usd.get_context()
context.new_stage()
for _ in range(8):
    app.update()
stage = context.get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)

biped = CharacterUtil.load_default_biped_to_stage()
CharacterUtil.load_character_usd_to_stage(CHARACTER_URL, (0.0, 0.0, 0.0), 180.0, "Character")
for _ in range(45):
    app.update()
characters = CharacterUtil.get_characters_in_stage()
animation_graph_prim = CharacterUtil.get_anim_graph_from_character(biped)
CharacterUtil.setup_animation_graph_to_character(characters, animation_graph_prim)

timeline = omni.timeline.get_timeline_interface()
timeline.set_target_framerate(30)
timeline.play()
for _ in range(12):
    app.update()

skel_root = characters[0]
character = animation_graph.get_character(str(skel_root.GetPath()))
if character is None:
    raise RuntimeError("official animation graph did not bind")

skeleton_prims = [
    prim
    for prim in stage.Traverse()
    if prim.GetTypeName() == "Skeleton" and str(prim.GetPath()).startswith(str(skel_root.GetPath()))
]
if len(skeleton_prims) != 1:
    raise RuntimeError(f"expected one character skeleton, got {len(skeleton_prims)}")
joints = [str(value) for value in UsdSkel.Skeleton(skeleton_prims[0]).GetJointsAttr().Get()]

keys = og.Controller.Keys
query_names = ("Pelvis", "L_Foot", "full_pelvis")
og.Controller.edit(
    {"graph_path": "/World/JointProbe", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            (name, "omni.anim.graph.GetCharacterJointTransform") for name in query_names
        ],
        keys.SET_VALUES: [
            ("Pelvis.inputs:skelRootPath", str(skel_root.GetPath())),
            ("Pelvis.inputs:joint", "Pelvis"),
            ("L_Foot.inputs:skelRootPath", str(skel_root.GetPath())),
            ("L_Foot.inputs:joint", "L_Foot"),
            ("full_pelvis.inputs:skelRootPath", str(skel_root.GetPath())),
            ("full_pelvis.inputs:joint", joints[2]),
        ],
    },
)
query_graph = og.Controller.graph("/World/JointProbe")

navigation = NavigationManager(str(skel_root.GetPath()), False, False)
command = GoTo(
    character,
    ["GoTo", "0.0", "5.0", "0.0", "180.0"],
    navigation,
    character_name="Character",
    update_metadata_callback_fn=lambda **_kwargs: None,
)

samples = []
for frame_index in range(90):
    command.execute(1.0 / 30.0)
    app.update()
    og.Controller.evaluate_sync(query_graph)
    if frame_index in (0, 30, 60, 89):
        sample = {"frame": frame_index}
        local_transforms = character.get_joint_local_transforms()
        local_translations = np.asarray(local_transforms[0], dtype=np.float64)
        local_rotations = np.asarray(local_transforms[1], dtype=np.float64)
        sample["direct_translation_shape"] = list(local_translations.shape)
        sample["direct_rotation_shape"] = list(local_rotations.shape)
        sample["direct_first_three_translations"] = local_translations[:3].tolist()
        sample["direct_first_three_rotations"] = local_rotations[:3].tolist()
        for name in query_names:
            value = og.Controller.get(
                og.Controller.attribute(f"/World/JointProbe/{name}.outputs:transform")
            )
            flat_value = [float(cell) for cell in value]
            if len(flat_value) != 16:
                raise RuntimeError(f"unexpected {name} matrix length: {len(flat_value)}")
            sample[name] = [flat_value[offset : offset + 4] for offset in range(0, 16, 4)]
        samples.append(sample)

print(
    "JOINT_QUERY_JSON="
    + json.dumps(
        {
            "skel_root": str(skel_root.GetPath()),
            "skeleton": str(skeleton_prims[0].GetPath()),
            "skel_root_applied_schemas": list(skel_root.GetAppliedSchemas()),
            "skel_root_animation_graph_targets": [
                str(target)
                for target in skel_root.GetRelationship("animationGraph").GetTargets()
            ],
            "character_public_members": [
                name for name in dir(character) if not name.startswith("_")
            ],
            "get_joint_local_transforms_doc": str(
                character.get_joint_local_transforms.__doc__
            ),
            "joint_count": len(joints),
            "samples": samples,
        },
        sort_keys=True,
    ),
    flush=True,
)
timeline.stop()
app.close()
