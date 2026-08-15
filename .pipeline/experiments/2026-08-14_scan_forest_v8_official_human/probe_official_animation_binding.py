"""Verify direct binding of the pinned official walk clip to the official skeleton."""

import json
from pathlib import Path

from isaacsim import SimulationApp


CHARACTER_URL = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/"
    "Isaac/People/Characters/male_adult_construction_03/"
    "male_adult_construction_03.usd"
)
WALK_URL = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/"
    "Isaac/People/Animations/stand_walk_loop_in_place.skelanim.usd"
)
OUTPUT_PATH = Path(
    "/home/sun/machine-dog-nav-runs/2026-08-14_scan_forest_v8_human/"
    "official_human_direct_animation.usda"
)


app = SimulationApp({"headless": True})

from pxr import Sdf, Usd, UsdGeom, UsdSkel  # noqa: E402


stage = Usd.Stage.CreateNew(str(OUTPUT_PATH))
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
stage.SetTimeCodesPerSecond(30.0)
stage.SetStartTimeCode(0.0)
stage.SetEndTimeCode(80.0)
root = UsdGeom.Xform.Define(stage, "/HumanVisual")
stage.SetDefaultPrim(root.GetPrim())
character = UsdGeom.Xform.Define(stage, "/HumanVisual/OfficialCharacter")
character.GetPrim().GetReferences().AddReference(CHARACTER_URL)
animation = stage.OverridePrim("/HumanVisual/OfficialWalk")
animation.GetReferences().AddReference(WALK_URL)

skeleton_prims = [
    prim for prim in stage.Traverse() if prim.GetTypeName() == "Skeleton"
]
skel_root_prims = [
    prim for prim in stage.Traverse() if prim.GetTypeName() == "SkelRoot"
]
if len(skeleton_prims) != 1:
    raise RuntimeError(f"expected one skeleton, got {len(skeleton_prims)}")
if len(skel_root_prims) != 1:
    raise RuntimeError(f"expected one skeleton root, got {len(skel_root_prims)}")
skeleton_prim = skeleton_prims[0]
skel_root_prim = skel_root_prims[0]
skeleton_schema = UsdSkel.Skeleton(skeleton_prim)
rest_transforms = skeleton_schema.GetRestTransformsAttr().Get()
rest_components = UsdSkel.DecomposeTransforms(rest_transforms)
binding = UsdSkel.BindingAPI.Apply(skeleton_prim)
binding.CreateAnimationSourceRel().SetTargets(
    [Sdf.Path("/HumanVisual/OfficialWalk")]
)
stage.GetRootLayer().Save()

cache = UsdSkel.Cache()
cache.Populate(UsdSkel.Root(skel_root_prim), Usd.PrimDefaultPredicate)
skeleton_query = cache.GetSkelQuery(UsdSkel.Skeleton(skeleton_prim))
if not skeleton_query:
    raise RuntimeError("could not create a skeleton query")
bound_animation_query = skeleton_query.GetAnimQuery()
direct_animation_query = cache.GetAnimQuery(
    UsdSkel.Animation(stage.GetPrimAtPath("/HumanVisual/OfficialWalk"))
)

samples = {}
matrix_samples = {}
for time_code in (0.0, 10.0, 20.0, 40.0, 80.0):
    transforms = skeleton_query.ComputeJointLocalTransforms(Usd.TimeCode(time_code))
    samples[str(time_code)] = [
        [float(value) for value in matrix.ExtractTranslation()]
        for matrix in transforms[:6]
    ]
    matrix_samples[str(time_code)] = [
        [float(matrix[row][column]) for row in range(4) for column in range(4)]
        for matrix in transforms
    ]

baseline = matrix_samples["0.0"]
maximum_matrix_delta = {
    time_code: max(
        abs(value - baseline[joint_index][value_index])
        for joint_index, matrix in enumerate(matrices)
        for value_index, value in enumerate(matrix)
    )
    for time_code, matrices in matrix_samples.items()
}
direct_animation_matrices = {}
for time_code in (0.0, 10.0, 20.0, 40.0, 80.0):
    transforms = direct_animation_query.ComputeJointLocalTransforms(
        Usd.TimeCode(time_code)
    )
    direct_animation_matrices[str(time_code)] = [
        [float(matrix[row][column]) for row in range(4) for column in range(4)]
        for matrix in transforms
    ]
direct_baseline = direct_animation_matrices["0.0"]
direct_maximum_matrix_delta = {
    time_code: max(
        abs(value - direct_baseline[joint_index][value_index])
        for joint_index, matrix in enumerate(matrices)
        for value_index, value in enumerate(matrix)
    )
    for time_code, matrices in direct_animation_matrices.items()
}

result = {
    "output_path": str(OUTPUT_PATH),
    "skeleton_path": str(skeleton_prim.GetPath()),
    "animation_path": "/HumanVisual/OfficialWalk",
    "animation_source_targets": [
        str(target) for target in binding.GetAnimationSourceRel().GetTargets()
    ],
    "joint_count": len(skeleton_query.GetJointOrder()),
    "rest_transform_count": len(rest_transforms),
    "rest_component_lengths": [len(values) for values in rest_components],
    "bound_animation_query_valid": bool(bound_animation_query),
    "direct_animation_query_valid": bool(direct_animation_query),
    "bound_animation_joint_count": (
        len(bound_animation_query.GetJointOrder()) if bound_animation_query else 0
    ),
    "direct_animation_joint_count": (
        len(direct_animation_query.GetJointOrder()) if direct_animation_query else 0
    ),
    "joint_order_prefix": [str(value) for value in skeleton_query.GetJointOrder()[:6]],
    "translation_samples_prefix": samples,
    "maximum_joint_matrix_delta_from_time_zero": maximum_matrix_delta,
    "direct_animation_maximum_joint_matrix_delta_from_time_zero": (
        direct_maximum_matrix_delta
    ),
}
print("HUMAN_ANIMATION_JSON=" + json.dumps(result, sort_keys=True), flush=True)
app.close()
