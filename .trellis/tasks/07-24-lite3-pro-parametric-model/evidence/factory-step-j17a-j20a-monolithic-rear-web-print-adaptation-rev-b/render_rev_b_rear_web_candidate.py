"""Render Rev A/Rev B rear-connection comparison views in Fusion."""

import adsk.core
import adsk.fusion
import json
import math
import os


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-j17a-j20a-monolithic-rear-web-print-adaptation-rev-b"
)
RENDER_REPORT = os.path.join(EVIDENCE_DIR, "render_report.json")

REV_A_INDEX = 34
REV_B_INDEX = 35
ASSEMBLY_INDICES = (3, 4, 11, 12, 13, 14, 15, 16, 17, 28, 29, 30, 31, 35)

REAR_LEFT_X_CM = -33.84112221937691
REAR_RIGHT_X_CM = -27.05289706998607
WEB_FRONT_Y_CM = 20.468141858307484
WEB_REAR_Y_CM = 23.218141858307483
WEB_TOP_Z_CM = 251.75
WEB_THICKNESS_CM = 0.60


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
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.eye = point(shifted(target, scaled(direction, 28.0)))
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


def add_rear_web_graphic(root):
    parent = root.customGraphicsGroups.add()
    if parent is None:
        raise RuntimeError("Could not create transient rear-web graphics")
    parent.id = "REV_B_CONTINUOUS_REAR_WEB_TRANSIENT"
    parent.isSelectable = False
    temporary = adsk.fusion.TemporaryBRepManager.get()
    box = adsk.core.OrientedBoundingBox3D.create(
        point(
            (
                (REAR_LEFT_X_CM + REAR_RIGHT_X_CM) * 0.5,
                (WEB_FRONT_Y_CM + WEB_REAR_Y_CM) * 0.5,
                WEB_TOP_Z_CM - WEB_THICKNESS_CM * 0.5,
            )
        ),
        vector((1.0, 0.0, 0.0)),
        vector((0.0, 1.0, 0.0)),
        REAR_RIGHT_X_CM - REAR_LEFT_X_CM,
        WEB_REAR_Y_CM - WEB_FRONT_Y_CM,
        WEB_THICKNESS_CM,
    )
    web = temporary.createBox(box)
    graphic = parent.addBRepBody(web)
    if graphic is None:
        raise RuntimeError("Could not add transient rear-web graphic")
    graphic.color = color_effect(245, 124, 28, 1.0)
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
    if occurrences.count != 36:
        raise RuntimeError("Expected the reviewed 36-occurrence Rev B scene")
    if not occurrences.item(REV_B_INDEX).component.name.startswith(
        "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B"
    ):
        raise RuntimeError("Unexpected Rev B occurrence")

    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    original_visibility = [
        bool(occurrences.item(index).isLightBulbOn)
        for index in range(occurrences.count)
    ]
    rev_a_body = occurrences.item(REV_A_INDEX).component.bRepBodies.item(0)
    rev_b_body = occurrences.item(REV_B_INDEX).component.bRepBodies.item(0)
    original_opacity = {REV_A_INDEX: rev_a_body.opacity, REV_B_INDEX: rev_b_body.opacity}
    viewport = application.activeViewport
    original_camera = camera_state(viewport.camera)
    original_graphics_count = root.customGraphicsGroups.count
    graphics = add_rear_web_graphic(root)
    rendered = []
    graphics_removed = False

    target = (-30.447, 22.0, 253.1)
    direction = (0.82, 1.0, -0.62)
    try:
        set_visible(occurrences, (REV_A_INDEX,))
        rev_a_body.opacity = 1.0
        graphics.isVisible = False
        rev_a_path = os.path.join(EVIDENCE_DIR, "rev-a-rear-two-posts-bottom-oblique.png")
        render(viewport, rev_a_path, target, direction, 19.5)
        rendered.append(rev_a_path)

        set_visible(occurrences, (REV_B_INDEX,))
        rev_b_body.opacity = 1.0
        graphics.isVisible = False
        rev_b_path = os.path.join(
            EVIDENCE_DIR, "rev-b-rear-continuous-web-bottom-oblique.png"
        )
        render(viewport, rev_b_path, target, direction, 19.5)
        rendered.append(rev_b_path)

        set_visible(occurrences, (REV_B_INDEX,))
        rev_b_body.opacity = 0.28
        graphics.isVisible = True
        xray_path = os.path.join(EVIDENCE_DIR, "rev-b-rear-web-highlight-xray.png")
        render(viewport, xray_path, target, direction, 19.5)
        rendered.append(xray_path)

        set_visible(occurrences, ASSEMBLY_INDICES)
        rev_b_body.opacity = 1.0
        graphics.isVisible = False
        assembly_path = os.path.join(
            EVIDENCE_DIR, "rev-b-with-sensors-rear-bottom-oblique.png"
        )
        render(
            viewport,
            assembly_path,
            (-30.447, 23.2, 256.0),
            (0.78, 1.0, -0.32),
            22.5,
        )
        rendered.append(assembly_path)
    finally:
        for index, visible in enumerate(original_visibility):
            occurrences.item(index).isLightBulbOn = visible
        rev_a_body.opacity = original_opacity[REV_A_INDEX]
        rev_b_body.opacity = original_opacity[REV_B_INDEX]
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
        "transient_rear_web_color": "orange",
        "rear_web_xray_opacity": 0.28,
        "restoration": {
            "visibility_mismatches": visibility_mismatches,
            "rev_a_opacity_restored": abs(
                rev_a_body.opacity - original_opacity[REV_A_INDEX]
            )
            <= 1.0e-12,
            "rev_b_opacity_restored": abs(
                rev_b_body.opacity - original_opacity[REV_B_INDEX]
            )
            <= 1.0e-12,
            "custom_graphics_removed": graphics_removed,
            "custom_graphics_count_before": original_graphics_count,
            "custom_graphics_count_after": root.customGraphicsGroups.count,
        },
    }
    report["pass"] = bool(
        not visibility_mismatches
        and report["restoration"]["rev_a_opacity_restored"]
        and report["restoration"]["rev_b_opacity_restored"]
        and graphics_removed
        and root.customGraphicsGroups.count == original_graphics_count
        and all(os.path.exists(path) for path in rendered)
    )
    with open(RENDER_REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise RuntimeError("Rev B rendering or Fusion-state restoration failed")
