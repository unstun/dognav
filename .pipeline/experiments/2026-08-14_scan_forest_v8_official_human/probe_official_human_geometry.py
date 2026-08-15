"""Read metric geometry evidence from the pinned Isaac Sim person asset."""

import json

from isaacsim import SimulationApp


CHARACTER_URL = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/"
    "Isaac/People/Characters/male_adult_police_04/"
    "male_adult_police_04.usd"
)
WALK_URL = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/"
    "Isaac/People/Animations/stand_walk_loop_in_place.skelanim.usd"
)


def vector(values):
    return [float(value) for value in values]


app = SimulationApp({"headless": True})

from pxr import Usd, UsdGeom  # noqa: E402


stage = Usd.Stage.Open(CHARACTER_URL)
if stage is None:
    raise RuntimeError(f"could not open official character: {CHARACTER_URL}")

purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render]
bbox_cache = UsdGeom.BBoxCache(
    Usd.TimeCode.Default(), purposes, useExtentsHint=True
)
default_prim = stage.GetDefaultPrim()
aligned_range = bbox_cache.ComputeWorldBound(default_prim).ComputeAlignedRange()
minimum = aligned_range.GetMin()
maximum = aligned_range.GetMax()

transform_rows = []
imageable_rows = []
binding_rows = []
for prim in stage.Traverse():
    if prim.GetTypeName() in {"SkelRoot", "Skeleton", "Mesh"}:
        binding_rows.append(
            {
                "path": str(prim.GetPath()),
                "type": prim.GetTypeName(),
                "applied_schemas": list(prim.GetAppliedSchemas()),
                "relationships": {
                    relationship.GetName(): [str(target) for target in relationship.GetTargets()]
                    for relationship in prim.GetRelationships()
                    if relationship.GetName().startswith("skel:")
                },
            }
        )
    if prim.GetTypeName() not in {"SkelRoot", "Skeleton"}:
        continue
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
        Usd.TimeCode.Default()
    )
    transform_rows.append(
        {
            "path": str(prim.GetPath()),
            "type": prim.GetTypeName(),
            "world_translation": vector(matrix.ExtractTranslation()),
        }
    )
for prim in stage.Traverse():
    if not prim.IsA(UsdGeom.Boundable):
        continue
    imageable = UsdGeom.Imageable(prim)
    if imageable.ComputeVisibility(Usd.TimeCode.Default()) == UsdGeom.Tokens.invisible:
        continue
    bound = bbox_cache.ComputeWorldBound(prim).ComputeAlignedRange()
    bound_minimum = bound.GetMin()
    bound_maximum = bound.GetMax()
    imageable_rows.append(
        {
            "path": str(prim.GetPath()),
            "type": prim.GetTypeName(),
            "world_bbox_min": vector(bound_minimum),
            "world_bbox_max": vector(bound_maximum),
            "world_bbox_size": vector(bound_maximum - bound_minimum),
        }
    )

result = {
    "source_url": CHARACTER_URL,
    "stage_meters_per_unit": float(UsdGeom.GetStageMetersPerUnit(stage)),
    "stage_up_axis": str(UsdGeom.GetStageUpAxis(stage)),
    "default_prim": str(default_prim.GetPath()),
    "world_bbox_min": vector(minimum),
    "world_bbox_max": vector(maximum),
    "world_bbox_size": vector(maximum - minimum),
    "world_bbox_center": vector((maximum + minimum) * 0.5),
    "prim_count": sum(1 for _ in stage.Traverse()),
    "skeleton_transforms": transform_rows,
    "visible_boundables": imageable_rows,
    "skel_binding_rows": binding_rows,
}
walk_stage = Usd.Stage.Open(WALK_URL)
if walk_stage is None:
    raise RuntimeError(f"could not open official walk animation: {WALK_URL}")
result["walk_animation"] = {
    "source_url": WALK_URL,
    "default_prim": str(walk_stage.GetDefaultPrim().GetPath()),
    "start_time_code": float(walk_stage.GetStartTimeCode()),
    "end_time_code": float(walk_stage.GetEndTimeCode()),
    "time_codes_per_second": float(walk_stage.GetTimeCodesPerSecond()),
    "prims": [
        {"path": str(prim.GetPath()), "type": prim.GetTypeName()}
        for prim in walk_stage.Traverse()
    ],
}
print("HUMAN_GEOMETRY_JSON=" + json.dumps(result, sort_keys=True), flush=True)
app.close()
