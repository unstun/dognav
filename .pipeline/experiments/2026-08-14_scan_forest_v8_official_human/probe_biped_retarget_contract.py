"""Inspect NVIDIA Biped Setup for the official animation retarget contract."""

import json

from isaacsim import SimulationApp


ROOT = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac"
BIPED_URL = f"{ROOT}/People/Characters/Biped_Setup.usd"
CHARACTER_URL = f"{ROOT}/People/Characters/male_adult_police_04/male_adult_police_04.usd"
WALK_URL = f"{ROOT}/People/Animations/stand_walk_loop_in_place.skelanim.usd"

app = SimulationApp({"headless": True})

from pxr import Usd, UsdSkel  # noqa: E402


def relevant_properties(prim):
    rows = {}
    for attr in prim.GetAttributes():
        name = attr.GetName()
        lowered = name.lower()
        if not any(token in lowered for token in ("joint", "retarget", "mapping", "animation")):
            continue
        value = attr.Get()
        if value is not None:
            text = str(value)
            rows[name] = text if len(text) <= 12000 else text[:12000] + "..."
    for relationship in prim.GetRelationships():
        name = relationship.GetName()
        lowered = name.lower()
        if any(token in lowered for token in ("joint", "retarget", "mapping", "animation")):
            rows[name] = [str(target) for target in relationship.GetTargets()]
    return rows


biped_stage = Usd.Stage.Open(BIPED_URL)
character_stage = Usd.Stage.Open(CHARACTER_URL)
walk_stage = Usd.Stage.Open(WALK_URL)
if not biped_stage or not character_stage or not walk_stage:
    raise RuntimeError("one or more official stages failed to open")

biped_rows = []
for prim in biped_stage.Traverse():
    properties = relevant_properties(prim)
    if properties or any(
        token in prim.GetTypeName().lower()
        for token in ("skeleton", "animation", "retarget", "mapper")
    ):
        biped_rows.append(
            {
                "path": str(prim.GetPath()),
                "type": prim.GetTypeName(),
                "applied_schemas": list(prim.GetAppliedSchemas()),
                "properties": properties,
            }
        )

character_skeletons = [
    UsdSkel.Skeleton(prim)
    for prim in character_stage.Traverse()
    if prim.GetTypeName() == "Skeleton"
]
if len(character_skeletons) != 1:
    raise RuntimeError("official character skeleton cardinality mismatch")
character_skeleton_prim = character_skeletons[0].GetPrim()
walk_animation = UsdSkel.Animation(walk_stage.GetDefaultPrim())
result = {
    "biped_url": BIPED_URL,
    "character_url": CHARACTER_URL,
    "walk_url": WALK_URL,
    "biped_retarget_rows": biped_rows,
    "character_joints": [
        str(value) for value in character_skeletons[0].GetJointsAttr().Get()
    ],
    "character_skeleton": {
        "path": str(character_skeleton_prim.GetPath()),
        "applied_schemas": list(character_skeleton_prim.GetAppliedSchemas()),
        "properties": relevant_properties(character_skeleton_prim),
    },
    "walk_joints": [str(value) for value in walk_animation.GetJointsAttr().Get()],
}
print("BIPED_RETARGET_JSON=" + json.dumps(result, sort_keys=True), flush=True)
app.close()
