"""Render review views for the physical-Lite3 fusion-adapter V1."""

import adsk.core
import adsk.fusion
import json
import math
import os


globals().pop("run", None)


PACKAGE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "physical-lite3-mid360-d435i-fusion-adapter-v1"
)
RENDER_DIR = os.path.join(PACKAGE_DIR, "renders")
REPORT_PATH = os.path.join(PACKAGE_DIR, "validation", "render_validation.json")

COMPONENT_NAME = "LITE3_MID360_D435I_MONOLITHIC_CARRIER_V1_NOT_OFFICIAL_CAD"
INTERFACE_COMPONENT = "PHYSICAL_INTERFACE_KEEP_OUT_PENDING_MEASUREMENT"


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
    camera.eye = point(shifted(target, scaled(direction, 65.0)))
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
        diffuse, ambient, specular, emissive, 24.0, opacity
    )


def find_occurrence(occurrences, component_name):
    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == component_name:
            return index, occurrence
    raise RuntimeError("Missing occurrence " + component_name)


def add_body_graphic(root, temporary_body, group_id, color):
    group = root.customGraphicsGroups.add()
    group.id = group_id
    group.isSelectable = False
    graphic = group.addBRepBody(temporary_body)
    if graphic is None:
        raise RuntimeError("Could not add custom graphic " + group_id)
    graphic.color = color
    graphic.isSelectable = False
    return group


def add_white_interface_graphic(root, temporary, interface_occurrence):
    body = temporary.copy(interface_occurrence.bRepBodies.item(0))
    return add_body_graphic(
        root, body, "PHYSICAL_INTERFACE_WHITE_CONTEXT_GRAPHIC", color_effect(242, 242, 238, 1.0)
    )


def add_rear_web_graphic(root, temporary):
    box = adsk.core.OrientedBoundingBox3D.create(
        point((-30.447009644681465, 21.843141858307483, 251.25)),
        vector((1.0, 0.0, 0.0)),
        vector((0.0, 1.0, 0.0)),
        6.788225149390843,
        2.75,
        1.0,
    )
    body = temporary.createBox(box)
    return add_body_graphic(
        root, body, "CARRIER_V1_10MM_REAR_WEB_GRAPHIC", color_effect(242, 126, 32, 0.96)
    )


def occurrence_center(occurrence):
    bounds = occurrence.boundingBox
    return (
        (bounds.minPoint.x + bounds.maxPoint.x) * 0.5,
        (bounds.minPoint.y + bounds.maxPoint.y) * 0.5,
        (bounds.minPoint.z + bounds.maxPoint.z) * 0.5,
    )


def add_fov_and_cable_graphics(root, temporary, mid360, d435):
    groups = []
    camera_origin = occurrence_center(d435)
    camera_direction = normalized((0.0, -0.34202014332566627, 0.9396926207859093))
    camera_end = tuple(camera_origin[index] + camera_direction[index] * 24.0 for index in range(3))
    frustum = temporary.createCylinderOrCone(
        point(tuple(camera_origin[index] + camera_direction[index] * 2.0 for index in range(3))),
        0.7,
        point(camera_end),
        14.0,
    )
    groups.append(
        add_body_graphic(root, frustum, "D435I_FOV_DIAGNOSTIC", color_effect(38, 169, 224, 0.18))
    )

    lidar_origin = occurrence_center(mid360)
    lidar_axis = normalized((0.0, 0.9659258262890683, 0.25881904510252074))
    lidar_start = tuple(lidar_origin[index] - lidar_axis[index] * 3.0 for index in range(3))
    lidar_end = tuple(lidar_origin[index] + lidar_axis[index] * 3.0 for index in range(3))
    lidar_envelope = temporary.createCylinderOrCone(
        point(lidar_start), 13.0, point(lidar_end), 13.0
    )
    groups.append(
        add_body_graphic(root, lidar_envelope, "MID360_SCAN_KEEP_OUT_DIAGNOSTIC", color_effect(66, 111, 238, 0.12))
    )

    d435_bounds = d435.boundingBox
    d435_cable_start = (
        d435_bounds.maxPoint.x + 0.3,
        (d435_bounds.minPoint.y + d435_bounds.maxPoint.y) * 0.5,
        (d435_bounds.minPoint.z + d435_bounds.maxPoint.z) * 0.5,
    )
    d435_cable_end = (d435_cable_start[0] + 4.0, d435_cable_start[1], d435_cable_start[2] - 3.0)
    d435_cable = temporary.createCylinderOrCone(
        point(d435_cable_start), 2.0, point(d435_cable_end), 2.0
    )
    groups.append(
        add_body_graphic(root, d435_cable, "D435I_USB_BEND_ENVELOPE_PENDING_CABLE", color_effect(35, 196, 145, 0.30))
    )

    lidar_bounds = mid360.boundingBox
    lidar_cable_start = (
        lidar_bounds.maxPoint.x + 0.3,
        (lidar_bounds.minPoint.y + lidar_bounds.maxPoint.y) * 0.5,
        (lidar_bounds.minPoint.z + lidar_bounds.maxPoint.z) * 0.5,
    )
    lidar_cable_end = (lidar_cable_start[0] + 5.0, lidar_cable_start[1], lidar_cable_start[2] - 4.0)
    lidar_cable = temporary.createCylinderOrCone(
        point(lidar_cable_start), 3.0, point(lidar_cable_end), 3.0
    )
    groups.append(
        add_body_graphic(root, lidar_cable, "MID360_CABLE_BEND_ENVELOPE_PENDING_CABLE", color_effect(35, 196, 145, 0.24))
    )
    return groups


def set_visible(occurrences, indices):
    indices = set(indices)
    for index in range(occurrences.count):
        occurrences.item(index).isLightBulbOn = index in indices


def render(viewport, path, target, direction, extents, up=(0.0, 0.0, 1.0)):
    apply_camera(viewport, target, direction, extents, up)
    viewport.refresh()
    adsk.doEvents()
    if not viewport.saveAsImageFile(path, 1800, 1200):
        raise RuntimeError("Could not render " + path)


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    temporary = adsk.fusion.TemporaryBRepManager.get()
    os.makedirs(RENDER_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    carrier_index, carrier = find_occurrence(occurrences, COMPONENT_NAME)
    interface_index, interface = find_occurrence(occurrences, INTERFACE_COMPONENT)
    robot_index = 0
    s410_index = 3
    mid360_index = 4
    d435_index = 15
    actual_fasteners = (11, 12, 13, 14, 16, 17, 24, 25, 26, 28, 29, 30, 31)
    sensor_module = (carrier_index, s410_index, mid360_index, d435_index, 11, 12, 13, 14, 16, 17, 28, 29, 30, 31)
    full_assembly = (robot_index, carrier_index, s410_index, mid360_index, d435_index) + actual_fasteners

    original_visibility = [bool(occurrences.item(index).isLightBulbOn) for index in range(occurrences.count)]
    opacity_state = {}
    for occurrence in (carrier, interface, occurrences.item(s410_index), occurrences.item(mid360_index), occurrences.item(d435_index)):
        for body_index in range(occurrence.component.bRepBodies.count):
            body = occurrence.component.bRepBodies.item(body_index)
            opacity_state[(occurrence.component.name, body_index)] = body.opacity
    viewport = application.activeViewport
    original_camera = camera_state(viewport.camera)
    original_graphics_count = root.customGraphicsGroups.count
    interface_graphic = add_white_interface_graphic(root, temporary, interface)
    web_graphic = add_rear_web_graphic(root, temporary)
    diagnostics = add_fov_and_cable_graphics(
        root, temporary, occurrences.item(mid360_index), occurrences.item(d435_index)
    )
    rendered = []

    try:
        interface.isLightBulbOn = False
        interface_graphic.isVisible = False
        web_graphic.isVisible = False
        for group in diagnostics:
            group.isVisible = False

        set_visible(occurrences, (carrier_index,))
        path = os.path.join(RENDER_DIR, "01-carrier-v1-isolated-oblique.png")
        render(viewport, path, (-30.447, 21.6, 254.4), (0.88, 0.72, -0.62), 19.0)
        rendered.append(path)

        set_visible(occurrences, (carrier_index,))
        carrier.component.bRepBodies.item(0).opacity = 0.30
        web_graphic.isVisible = True
        path = os.path.join(RENDER_DIR, "02-carrier-v1-10mm-rear-web-highlight.png")
        render(viewport, path, (-30.447, 22.0, 251.8), (0.80, 1.0, -0.72), 17.5)
        rendered.append(path)
        carrier.component.bRepBodies.item(0).opacity = 1.0
        web_graphic.isVisible = False

        set_visible(occurrences, sensor_module)
        path = os.path.join(RENDER_DIR, "03-complete-sensor-module-oblique.png")
        render(viewport, path, (-30.447, 22.4, 256.0), (0.78, 0.88, -0.30), 23.0)
        rendered.append(path)

        set_visible(occurrences, full_assembly)
        interface.isLightBulbOn = False
        interface_graphic.isVisible = True
        path = os.path.join(RENDER_DIR, "04-lite3-interface-context-top.png")
        render(viewport, path, (-30.447, 20.0, 244.0), (0.0, 1.0, 0.0), 43.0, up=(0.0, 0.0, 1.0))
        rendered.append(path)

        set_visible(occurrences, (robot_index, carrier_index, 24, 25, 26))
        interface.isLightBulbOn = False
        interface_graphic.isVisible = True
        path = os.path.join(RENDER_DIR, "05-lite3-four-point-base-fasteners-closeup.png")
        render(viewport, path, (-30.447, 20.9, 254.2), (0.66, 1.0, 0.42), 19.5)
        rendered.append(path)

        set_visible(occurrences, sensor_module)
        interface_graphic.isVisible = False
        for group in diagnostics:
            group.isVisible = True
        path = os.path.join(RENDER_DIR, "06-sensor-fov-and-cable-diagnostics.png")
        render(viewport, path, (-30.447, 22.4, 258.5), (0.82, 0.62, 0.34), 34.0)
        rendered.append(path)
        for group in diagnostics:
            group.isVisible = False

        set_visible(occurrences, full_assembly)
        interface.isLightBulbOn = False
        interface_graphic.isVisible = True
        path = os.path.join(RENDER_DIR, "07-complete-lite3-global-isometric.png")
        render(
            viewport,
            path,
            (-30.447, 0.0, 246.0),
            (0.82, 0.72, 0.56),
            74.0,
            up=(0.0, 1.0, 0.0),
        )
        rendered.append(path)
    finally:
        for index, visible in enumerate(original_visibility):
            occurrences.item(index).isLightBulbOn = visible
        for occurrence in (carrier, interface, occurrences.item(s410_index), occurrences.item(mid360_index), occurrences.item(d435_index)):
            for body_index in range(occurrence.component.bRepBodies.count):
                key = (occurrence.component.name, body_index)
                occurrence.component.bRepBodies.item(body_index).opacity = opacity_state[key]
        groups = [interface_graphic, web_graphic] + diagnostics
        deleted = []
        for group in groups:
            deleted.append(bool(group.deleteMe()) if group is not None and group.isValid else False)
        restore_camera(viewport, original_camera)
        viewport.refresh()
        adsk.doEvents()

    report = {
        "stage": "experiment_and_analysis",
        "status": "historical_render_pass_rejected_for_current_pro_scene",
        "renders": rendered,
        "contains_text_overlay": False,
        "diagnostic_only": {
            "white_interface": "visual keep-out overlay; dimensions pending physical measurement",
            "orange_rear_web": "10 mm engineering thickening",
            "cyan_camera_frustum": "D435i view diagnostic",
            "blue_lidar_cylinder": "Mid-360 360-degree scan keep-out diagnostic",
            "green_cable_volumes": "conservative cable assumptions pending actual cables",
        },
        "restoration": {
            "visibility_mismatches": [
                index
                for index, expected in enumerate(original_visibility)
                if bool(occurrences.item(index).isLightBulbOn) != expected
            ],
            "custom_graphics_deleted": all(deleted),
            "custom_graphics_count_before": original_graphics_count,
            "custom_graphics_count_after": root.customGraphicsGroups.count,
        },
    }
    report["pass"] = bool(
        all(os.path.exists(path) and os.path.getsize(path) > 50_000 for path in rendered)
        and not report["restoration"]["visibility_mismatches"]
        and report["restoration"]["custom_graphics_deleted"]
        and root.customGraphicsGroups.count == original_graphics_count
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["pass"]:
        raise RuntimeError("V1 render validation failed")
