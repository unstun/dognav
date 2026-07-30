"""Render close-up review views of the one-piece J17A/J20A candidate."""

import adsk.core
import adsk.fusion
import json
import math
import os


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-print-adaptation-candidate"
)
RENDER_REPORT = os.path.join(EVIDENCE_DIR, "render_report.json")

CANDIDATE_INDEX = 34
ASSEMBLY_INDICES = (3, 4, 11, 12, 13, 14, 15, 16, 17, 28, 29, 30, 31, 34)

FRONT_AXES = (
    (-32.24700964468146, 20.468141858307484, 259.73489005808057),
    (-28.647009644681464, 20.468141858307484, 259.73489005808057),
)
REAR_AXES = (
    (-33.84112221937691, 22.018141858307482, 251.89077750838507),
    (-27.05289706998607, 22.018141858307482, 251.89077750838507),
)


def point(values):
    return adsk.core.Point3D.create(*values)


def vector(values):
    return adsk.core.Vector3D.create(*values)


def normalized(values):
    length = math.sqrt(sum(value * value for value in values))
    return tuple(value / length for value in values)


def shifted(first, second):
    return tuple(first[index] + second[index] for index in range(3))


def scaled(values, amount):
    return tuple(value * amount for value in values)


def camera_state(camera):
    return {
        "eye": (camera.eye.x, camera.eye.y, camera.eye.z),
        "target": (camera.target.x, camera.target.y, camera.target.z),
        "up": (camera.upVector.x, camera.upVector.y, camera.upVector.z),
        "extents": camera.viewExtents,
        "type": camera.cameraType,
    }


def restore_camera(viewport, state):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = state["type"]
    camera.eye = point(state["eye"])
    camera.target = point(state["target"])
    camera.upVector = vector(state["up"])
    camera.viewExtents = state["extents"]
    viewport.camera = camera


def apply_camera(viewport, target, direction, extents, up=(0.0, 0.0, 1.0)):
    direction = normalized(direction)
    eye = shifted(target, scaled(direction, 28.0))
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = point(eye)
    camera.target = point(target)
    camera.upVector = vector(up)
    camera.viewExtents = extents
    viewport.camera = camera


def color_effect(red, green, blue, opacity=1.0):
    diffuse = adsk.core.Color.create(red, green, blue, 255)
    ambient = adsk.core.Color.create(
        min(255, red + 28), min(255, green + 28), min(255, blue + 28), 255
    )
    specular = adsk.core.Color.create(255, 255, 255, 255)
    emissive = adsk.core.Color.create(0, 0, 0, 255)
    return adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
        diffuse, ambient, specular, emissive, 22.0, opacity
    )


def add_fusion_zone_graphics(root):
    parent = root.customGraphicsGroups.add()
    if parent is None:
        raise RuntimeError("Could not create transient fusion-zone graphics")
    parent.id = "MONOLITHIC_FUSION_ZONES_TRANSIENT"
    parent.isSelectable = False
    temporary = adsk.fusion.TemporaryBRepManager.get()
    effect = color_effect(245, 124, 28, 1.0)

    for axis in FRONT_AXES:
        x, start_y, z = axis
        shapes = (
            temporary.createCylinderOrCone(
                point((x, start_y, z)),
                0.25,
                point((x, 21.20163550736137, z)),
                0.25,
            ),
            temporary.createCylinderOrCone(
                point((x, start_y, z)),
                0.35,
                point((x, 20.718141858307484, z)),
                0.35,
            ),
        )
        for shape in shapes:
            graphic = parent.addBRepBody(shape)
            if graphic is None:
                raise RuntimeError("Could not add a front fusion-zone graphic")
            graphic.color = effect
            graphic.isSelectable = False

    for axis in REAR_AXES:
        x, shoulder_y, z = axis
        shapes = (
            temporary.createCylinderOrCone(
                point((x, shoulder_y, z)),
                0.34,
                point((x, 23.218141858307483, z)),
                0.34,
            ),
            temporary.createCylinderOrCone(
                point((x, 20.468141858307484, z)),
                0.40,
                point((x, shoulder_y, z)),
                0.40,
            ),
        )
        for shape in shapes:
            graphic = parent.addBRepBody(shape)
            if graphic is None:
                raise RuntimeError("Could not add a rear fusion-zone graphic")
            graphic.color = effect
            graphic.isSelectable = False

    parent.isVisible = False
    return parent


def set_visible(occurrences, visible_indices):
    visible_indices = set(visible_indices)
    for index in range(occurrences.count):
        occurrences.item(index).isLightBulbOn = index in visible_indices


def render(viewport, path, target, direction, extents):
    apply_camera(viewport, target, direction, extents)
    viewport.refresh()
    adsk.doEvents()
    if not viewport.saveAsImageFile(path, 1600, 1000):
        raise RuntimeError("Could not render " + path)


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    if occurrences.count != 35:
        raise RuntimeError("Expected the reviewed 35-occurrence candidate scene")
    if not occurrences.item(CANDIDATE_INDEX).component.name.startswith(
        "J17A_J20A_MONOLITHIC_PRINT_ADAPTATION_REV_A"
    ):
        raise RuntimeError("Unexpected monolithic candidate occurrence")

    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    original_visibility = [
        bool(occurrences.item(index).isLightBulbOn)
        for index in range(occurrences.count)
    ]
    candidate_body = occurrences.item(CANDIDATE_INDEX).component.bRepBodies.item(0)
    original_opacity = candidate_body.opacity
    viewport = application.activeViewport
    original_camera = camera_state(viewport.camera)
    original_graphics_count = root.customGraphicsGroups.count
    graphics = add_fusion_zone_graphics(root)
    rendered = []
    graphics_removed = False

    try:
        set_visible(occurrences, (CANDIDATE_INDEX,))
        candidate_body.opacity = 1.0
        graphics.isVisible = False
        isolated_path = os.path.join(EVIDENCE_DIR, "monolithic-isolated-oblique.png")
        render(
            viewport,
            isolated_path,
            (-30.447, 21.55, 254.45),
            (0.86, -1.0, 0.54),
            19.5,
        )
        rendered.append(isolated_path)

        set_visible(occurrences, ASSEMBLY_INDICES)
        candidate_body.opacity = 1.0
        graphics.isVisible = False
        assembly_path = os.path.join(EVIDENCE_DIR, "monolithic-with-sensors-oblique.png")
        render(
            viewport,
            assembly_path,
            (-30.447, 23.2, 256.7),
            (0.82, -1.0, 0.48),
            22.0,
        )
        rendered.append(assembly_path)

        set_visible(occurrences, (CANDIDATE_INDEX,))
        candidate_body.opacity = 0.30
        graphics.isVisible = True
        xray_path = os.path.join(EVIDENCE_DIR, "monolithic-four-fusion-zones-xray.png")
        render(
            viewport,
            xray_path,
            (-30.447, 21.65, 254.65),
            (0.82, -1.0, 0.46),
            19.8,
        )
        rendered.append(xray_path)
    finally:
        for index, visible in enumerate(original_visibility):
            occurrences.item(index).isLightBulbOn = visible
        candidate_body.opacity = original_opacity
        if graphics is not None and graphics.isValid:
            graphics_removed = bool(graphics.deleteMe())
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

    visibility_mismatches = [
        index
        for index, expected in enumerate(original_visibility)
        if bool(occurrences.item(index).isLightBulbOn) != expected
    ]
    report = {
        "stage": "experiment_and_analysis",
        "status": "awaiting_visual_review",
        "renders": rendered,
        "contains_text_overlay": False,
        "transient_fusion_zone_color": "orange",
        "candidate_xray_opacity": 0.30,
        "restoration": {
            "visibility_mismatches": visibility_mismatches,
            "candidate_opacity_restored": abs(candidate_body.opacity - original_opacity)
            <= 1.0e-12,
            "custom_graphics_removed": graphics_removed,
            "custom_graphics_count_before": original_graphics_count,
            "custom_graphics_count_after": root.customGraphicsGroups.count,
        },
    }
    report["pass"] = bool(
        not visibility_mismatches
        and report["restoration"]["candidate_opacity_restored"]
        and graphics_removed
        and root.customGraphicsGroups.count == original_graphics_count
        and all(os.path.exists(path) for path in rendered)
    )
    with open(RENDER_REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise RuntimeError("Monolithic candidate rendering/restoration failed")
