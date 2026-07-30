"""Measure one S410/J20 mounting axis before changing the fastener logic.

The existing Rev B print candidate and the official S410 guard are inspected
without modification.  Fusion uses centimetres internally; the report converts
dimensions to millimetres.
"""

import adsk.core
import adsk.fusion
import json
import os


globals().pop("run", None)


EVIDENCE_DIR = (
    "/Users/sun/tongbu/study/phdproject/machine-dog-nav/.trellis/tasks/"
    "07-24-lite3-pro-parametric-model/evidence/"
    "factory-step-rev-c-s410-through-bolt-top-nut-print-correction"
)
REPORT_PATH = os.path.join(EVIDENCE_DIR, "single_axis_measurement.json")

REV_B_COMPONENT_NAME = (
    "J17A_J20A_MONOLITHIC_REAR_WEB_PRINT_ADAPTATION_REV_B_NOT_OFFICIAL_CAD"
)
SCREW_COMPONENT_NAME = "S410_TO_J20_M5X8_INDIVIDUAL_SCREW_VISUAL_CANDIDATE"
MOUNT_NORMAL = (0.0, 0.9659258262890683, 0.25881904510252074)
SELECTED_POSITION = "S1_TOP_LEFT"


def point_values(point):
    return [point.x, point.y, point.z]


def vector_values(vector):
    return [vector.x, vector.y, vector.z]


def shifted(point, vector, distance):
    return adsk.core.Point3D.create(
        point.x + vector.x * distance,
        point.y + vector.y * distance,
        point.z + vector.z * distance,
    )


def distance_point_to_axis(point, axis_origin, axis_direction):
    delta = axis_origin.vectorTo(point)
    axial = delta.dotProduct(axis_direction)
    radial = adsk.core.Vector3D.create(
        delta.x - axis_direction.x * axial,
        delta.y - axis_direction.y * axial,
        delta.z - axis_direction.z * axial,
    )
    return radial.length


def cylindrical_face_records(occurrence, nominal_radius_cm, target_point, normal):
    records = []
    transform = occurrence.transform2
    for body_index in range(occurrence.component.bRepBodies.count):
        body = occurrence.component.bRepBodies.item(body_index)
        for face_index in range(body.faces.count):
            face = body.faces.item(face_index)
            cylinder = adsk.core.Cylinder.cast(face.geometry)
            if cylinder is None:
                continue
            if abs(cylinder.radius - nominal_radius_cm) > 1.0e-5:
                continue

            origin = cylinder.origin.copy()
            origin.transformBy(transform)
            axis = cylinder.axis.copy()
            axis.transformBy(transform)
            axis.normalize()
            parallel = abs(axis.dotProduct(normal))
            if parallel < 0.999:
                continue

            projections = []
            vertices = []
            for edge_index in range(face.edges.count):
                edge = face.edges.item(edge_index)
                for vertex in (edge.startVertex, edge.endVertex):
                    if vertex is None:
                        continue
                    value = vertex.geometry.copy()
                    value.transformBy(transform)
                    projection = (
                        value.x * normal.x
                        + value.y * normal.y
                        + value.z * normal.z
                    )
                    projections.append(projection)
                    vertices.append(point_values(value))

            if not projections:
                continue
            records.append(
                {
                    "body_index": body_index,
                    "face_index": face_index,
                    "radius_mm": cylinder.radius * 10.0,
                    "origin_cm": point_values(origin),
                    "axis": vector_values(axis),
                    "parallel_to_mount_normal": parallel,
                    "axis_distance_to_selected_point_mm": distance_point_to_axis(
                        target_point, origin, axis
                    )
                    * 10.0,
                    "projection_interval_cm": [min(projections), max(projections)],
                    "axial_length_mm": (max(projections) - min(projections))
                    * 10.0,
                    "edge_vertices_cm": vertices,
                }
            )
    records.sort(key=lambda item: item["axis_distance_to_selected_point_mm"])
    return records


def run(_context: str):
    application = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(application.activeProduct)
    if design is None:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    occurrences = root.occurrences
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    normal = adsk.core.Vector3D.create(*MOUNT_NORMAL)
    normal.normalize()
    rev_b = None
    guard = None
    selected_screw = None
    selected_screw_index = None
    rev_b_index = None
    guard_index = None

    for index in range(occurrences.count):
        occurrence = occurrences.item(index)
        if occurrence.component.name == REV_B_COMPONENT_NAME:
            rev_b = occurrence
            rev_b_index = index
        if "S410" in occurrence.component.name and occurrence.component.bRepBodies.count:
            if occurrence.component.name != SCREW_COMPONENT_NAME and guard is None:
                for body_index in range(occurrence.component.bRepBodies.count):
                    body = occurrence.component.bRepBodies.item(body_index)
                    if any(
                        adsk.core.Cylinder.cast(body.faces.item(face_index).geometry)
                        is not None
                        and abs(
                            adsk.core.Cylinder.cast(
                                body.faces.item(face_index).geometry
                            ).radius
                            - 0.26
                        )
                        < 1.0e-5
                        for face_index in range(body.faces.count)
                    ):
                        guard = occurrence
                        guard_index = index
                        break
        if occurrence.component.name == SCREW_COMPONENT_NAME:
            position = occurrence.attributes.itemByName(
                "s410_sequential_fastener", "position"
            )
            if position is not None and position.value == SELECTED_POSITION:
                selected_screw = occurrence
                selected_screw_index = index

    if rev_b is None:
        raise RuntimeError("Visible Rev B print candidate was not found")
    if guard is None:
        raise RuntimeError("Official S410 guard occurrence was not found")
    if selected_screw is None:
        raise RuntimeError("Selected S410 screw occurrence was not found")

    translation = selected_screw.transform2.translation
    selected_point = adsk.core.Point3D.create(
        translation.x, translation.y, translation.z
    )
    selected_projection = (
        selected_point.x * normal.x
        + selected_point.y * normal.y
        + selected_point.z * normal.z
    )

    guard_faces = cylindrical_face_records(
        guard, 0.26, selected_point, normal
    )
    rev_b_faces = cylindrical_face_records(
        rev_b, 0.21, selected_point, normal
    )
    if not guard_faces or guard_faces[0]["axis_distance_to_selected_point_mm"] > 0.05:
        raise RuntimeError("Could not resolve the selected S410 clearance face")
    if not rev_b_faces or rev_b_faces[0]["axis_distance_to_selected_point_mm"] > 0.05:
        raise RuntimeError("Could not resolve the selected Rev B hole face")

    selected_guard = guard_faces[0]
    selected_rev_b = rev_b_faces[0]
    lower_surface = min(selected_rev_b["projection_interval_cm"])
    upper_surface = max(selected_guard["projection_interval_cm"])
    total_stack_mm = (upper_surface - lower_surface) * 10.0
    guard_interval = selected_guard["projection_interval_cm"]
    rev_b_interval = selected_rev_b["projection_interval_cm"]
    overlap_mm = max(
        0.0,
        min(guard_interval[1], rev_b_interval[1])
        - max(guard_interval[0], rev_b_interval[0]),
    ) * 10.0
    gap_mm = max(
        0.0,
        guard_interval[0] - rev_b_interval[1],
        rev_b_interval[0] - guard_interval[1],
    ) * 10.0

    report = {
        "stage": "experiment_and_analysis",
        "status": "measured_before_geometry_change",
        "document": application.activeDocument.name,
        "selected_position": SELECTED_POSITION,
        "indices": {
            "rev_b": rev_b_index,
            "s410_guard": guard_index,
            "existing_direct_thread_screw": selected_screw_index,
        },
        "mount_normal": vector_values(normal),
        "selected_axis_outer_point_cm": point_values(selected_point),
        "selected_axis_outer_projection_cm": selected_projection,
        "s410_clearance_face": selected_guard,
        "rev_b_hole_face": selected_rev_b,
        "stack": {
            "underside_projection_cm": lower_surface,
            "topside_projection_cm": upper_surface,
            "total_axial_stack_mm": total_stack_mm,
            "modeled_overlap_mm": overlap_mm,
            "modeled_gap_mm": gap_mm,
        },
        "candidate_contract": {
            "printed_part_receiver": "plain M5 clearance hole, not thread",
            "bolt_direction": "from -mount_normal underside toward +mount_normal top",
            "nut_location": "+mount_normal top side",
            "diameter_and_length_status": "to be selected after this measurement; visual and print candidates only",
        },
        "claim_boundary": (
            "This report measures the current CAD stack only. It does not establish "
            "official supplied hardware, final print tolerance, torque, strength, or "
            "real-robot safety."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
