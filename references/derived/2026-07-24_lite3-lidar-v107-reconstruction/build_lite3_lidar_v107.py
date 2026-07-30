#!/usr/bin/env python3
"""Build the Lite3 LiDAR V1.0.7 appearance reconstruction in FreeCAD."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

import FreeCAD as App
import Mesh
import Part


ALLOWED_EVIDENCE_CLASSES = {
    "official_nominal",
    "source_model",
    "image_estimate",
}
REQUIRED_COMPONENT_NAMES = (
    "Upper_Mounting_References",
    "Upper_Interface_Enclosure",
    "Laser_Radar_Core",
    "Cooling_Fins",
    "Protective_Hoop",
    "Front_Sensor_Bar",
)


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError(f"Could not find repository root above {start}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    if not isinstance(result, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return result


def parameter(section: dict[str, Any], key: str) -> float | int:
    try:
        node = section["parameters"][key]
    except KeyError as exc:
        raise ValueError(f"Missing parameter {key!r}") from exc
    if not isinstance(node, dict):
        raise ValueError(f"Parameter {key!r} must be an object")
    evidence_class = node.get("evidence_class")
    if evidence_class not in ALLOWED_EVIDENCE_CLASSES:
        raise ValueError(
            f"Parameter {key!r} has invalid evidence class {evidence_class!r}"
        )
    if not node.get("source_note"):
        raise ValueError(f"Parameter {key!r} must include a source note")
    value = node.get("value")
    if not isinstance(value, (int, float)):
        raise ValueError(f"Parameter {key!r} must be numeric")
    return value


def validate_parameter_contract(config: dict[str, Any]) -> None:
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported parameter schema version")
    if config.get("coordinate_system", {}).get("unit") != "millimetre":
        raise ValueError("Mechanical authoring unit must be millimetre")
    for source_name, source in config.get("sources", {}).items():
        if source.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
            raise ValueError(f"Source {source_name!r} has invalid evidence class")
        if not source.get("path") or not source.get("sha256"):
            raise ValueError(f"Source {source_name!r} lacks path or SHA-256")
    sections = (
        "official_envelope",
        "mounting_reference",
        "upper_interface_enclosure",
        "laser_radar_core",
        "cooling_fins",
        "protective_hoop",
        "front_sensor_bar",
        "meshing",
    )
    for section_name in sections:
        section = config.get(section_name)
        if not isinstance(section, dict) or not isinstance(
            section.get("parameters"), dict
        ):
            raise ValueError(f"Missing parameter section {section_name!r}")
        for key in section["parameters"]:
            parameter(section, key)


def rounded_box(
    length: float,
    width: float,
    height: float,
    center_x: float,
    center_y: float,
    base_z: float,
    radius: float,
) -> Part.Shape:
    if min(length, width, height) <= 0:
        raise ValueError("Rounded-box dimensions must be positive")
    if radius <= 0:
        return Part.makeBox(
            length,
            width,
            height,
            App.Vector(
                center_x - length / 2.0,
                center_y - width / 2.0,
                base_z,
            ),
        )
    if radius * 2.0 >= min(length, width):
        raise ValueError("Rounded-box corner radius is too large")

    shapes = [
        Part.makeBox(
            length - 2.0 * radius,
            width,
            height,
            App.Vector(
                center_x - length / 2.0 + radius,
                center_y - width / 2.0,
                base_z,
            ),
        ),
        Part.makeBox(
            length,
            width - 2.0 * radius,
            height,
            App.Vector(
                center_x - length / 2.0,
                center_y - width / 2.0 + radius,
                base_z,
            ),
        ),
    ]
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            shapes.append(
                Part.makeCylinder(
                    radius,
                    height,
                    App.Vector(
                        center_x + x_sign * (length / 2.0 - radius),
                        center_y + y_sign * (width / 2.0 - radius),
                        base_z,
                    ),
                )
            )
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def build_mounting_reference(config: dict[str, Any]) -> Part.Shape:
    section = config["mounting_reference"]
    length = float(parameter(section, "length_mm"))
    width = float(parameter(section, "width_mm"))
    thickness = float(parameter(section, "thickness_mm"))
    radius = float(parameter(section, "corner_radius_mm"))
    center_x = float(parameter(section, "center_x_mm"))
    center_y = float(parameter(section, "center_y_mm"))
    base_z = float(parameter(section, "base_z_mm"))
    pattern_x = float(parameter(section, "pattern_x_mm"))
    pattern_y = float(parameter(section, "pattern_y_mm"))
    hole_radius = float(parameter(section, "reference_hole_radius_mm"))

    shape = rounded_box(
        length,
        width,
        thickness,
        center_x,
        center_y,
        base_z,
        radius,
    )
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            hole = Part.makeCylinder(
                hole_radius,
                thickness + 2.0,
                App.Vector(
                    center_x + x_sign * pattern_x / 2.0,
                    center_y + y_sign * pattern_y / 2.0,
                    base_z - 1.0,
                ),
            )
            shape = shape.cut(hole)
    return shape.removeSplitter()


def build_upper_enclosure(config: dict[str, Any]) -> Part.Shape:
    section = config["upper_interface_enclosure"]
    length = float(parameter(section, "length_mm"))
    width = float(parameter(section, "width_mm"))
    height = float(parameter(section, "height_mm"))
    radius = float(parameter(section, "corner_radius_mm"))
    center_x = float(parameter(section, "center_x_mm"))
    center_y = float(parameter(section, "center_y_mm"))
    base_z = float(parameter(section, "base_z_mm"))
    port_count = int(parameter(section, "port_count"))
    port_width = float(parameter(section, "port_width_mm"))
    port_height = float(parameter(section, "port_height_mm"))
    port_depth = float(parameter(section, "port_depth_mm"))
    port_pitch = float(parameter(section, "port_pitch_mm"))
    port_center_x = float(parameter(section, "port_group_center_x_mm"))
    port_base_z = float(parameter(section, "port_base_z_mm"))

    shape = rounded_box(
        length,
        width,
        height,
        center_x,
        center_y,
        base_z,
        radius,
    )
    side_y = center_y - width / 2.0
    for index in range(port_count):
        x_center = port_center_x + (index - (port_count - 1) / 2.0) * port_pitch
        pocket = Part.makeBox(
            port_width,
            port_depth + 1.0,
            port_height,
            App.Vector(
                x_center - port_width / 2.0,
                side_y - 1.0,
                port_base_z,
            ),
        )
        shape = shape.cut(pocket)
    return shape.removeSplitter()


def upper_hemisphere(radius: float, center: App.Vector) -> Part.Shape:
    sphere = Part.makeSphere(radius, center)
    clip = Part.makeBox(
        radius * 2.4,
        radius * 2.4,
        radius * 1.2,
        App.Vector(
            center.x - radius * 1.2,
            center.y - radius * 1.2,
            center.z,
        ),
    )
    return sphere.common(clip)


def build_radar_core(config: dict[str, Any]) -> Part.Shape:
    section = config["laser_radar_core"]
    center_x = float(parameter(section, "center_x_mm"))
    center_y = float(parameter(section, "center_y_mm"))
    base_z = float(parameter(section, "base_z_mm"))
    radius = float(parameter(section, "radius_mm"))
    cylinder_height = float(parameter(section, "cylinder_height_mm"))
    dome_height = float(parameter(section, "dome_height_mm"))
    if abs(dome_height - radius) > 1.0e-9:
        raise ValueError("The current dome builder requires dome height = radius")

    cylinder = Part.makeCylinder(
        radius,
        cylinder_height,
        App.Vector(center_x, center_y, base_z),
    )
    dome = upper_hemisphere(
        radius,
        App.Vector(center_x, center_y, base_z + cylinder_height),
    )
    return cylinder.fuse(dome).removeSplitter()


def build_cooling_fins(config: dict[str, Any]) -> Part.Shape:
    section = config["cooling_fins"]
    center_x = float(parameter(section, "center_x_mm"))
    center_y = float(parameter(section, "center_y_mm"))
    base_z = float(parameter(section, "base_z_mm"))
    base_length = float(parameter(section, "base_length_mm"))
    base_width = float(parameter(section, "base_width_mm"))
    base_height = float(parameter(section, "base_height_mm"))
    fin_count = int(parameter(section, "fin_count"))
    fin_length = float(parameter(section, "fin_length_mm"))
    fin_thickness = float(parameter(section, "fin_thickness_mm"))
    fin_height = float(parameter(section, "fin_height_mm"))
    fin_pitch = float(parameter(section, "fin_pitch_mm"))
    if fin_count < 2:
        raise ValueError("Cooling-fin group requires at least two fins")

    shapes = [
        Part.makeBox(
            base_length,
            base_width,
            base_height,
            App.Vector(
                center_x - base_length / 2.0,
                center_y - base_width / 2.0,
                base_z,
            ),
        )
    ]
    for index in range(fin_count):
        y_center = center_y + (index - (fin_count - 1) / 2.0) * fin_pitch
        shapes.append(
            Part.makeBox(
                fin_length,
                fin_thickness,
                fin_height,
                App.Vector(
                    center_x - fin_length / 2.0,
                    y_center - fin_thickness / 2.0,
                    base_z + base_height - 0.5,
                ),
            )
        )
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def build_protective_hoop(config: dict[str, Any]) -> Part.Shape:
    section = config["protective_hoop"]
    center_x = float(parameter(section, "center_x_mm"))
    center_y = float(parameter(section, "center_y_mm"))
    center_z = float(parameter(section, "arc_center_z_mm"))
    major_radius = float(parameter(section, "major_radius_mm"))
    tube_radius = float(parameter(section, "tube_radius_mm"))
    support_base_z = float(parameter(section, "support_base_z_mm"))
    segments = int(parameter(section, "arc_segments"))
    if segments < 6:
        raise ValueError("Protective hoop requires at least six arc segments")

    points = [
        App.Vector(
            center_x,
            center_y + major_radius * math.cos(index * math.pi / segments),
            center_z + major_radius * math.sin(index * math.pi / segments),
        )
        for index in range(segments + 1)
    ]
    shapes: list[Part.Shape] = []
    for start, end in zip(points, points[1:]):
        direction = end - start
        shapes.append(
            Part.makeCylinder(
                tube_radius,
                direction.Length,
                start,
                direction,
            )
        )
    shapes.extend(Part.makeSphere(tube_radius, point) for point in points)
    support_height = center_z - support_base_z
    for y_sign in (-1.0, 1.0):
        shapes.append(
            Part.makeCylinder(
                tube_radius,
                support_height,
                App.Vector(
                    center_x,
                    center_y + y_sign * major_radius,
                    support_base_z,
                ),
            )
        )
    return shapes[0].multiFuse(shapes[1:]).removeSplitter()


def build_front_sensor_bar(config: dict[str, Any]) -> Part.Shape:
    section = config["front_sensor_bar"]
    center_x = float(parameter(section, "center_x_mm"))
    center_y = float(parameter(section, "center_y_mm"))
    base_z = float(parameter(section, "base_z_mm"))
    depth_x = float(parameter(section, "depth_x_mm"))
    width_y = float(parameter(section, "width_y_mm"))
    height_z = float(parameter(section, "height_z_mm"))
    corner_radius = float(parameter(section, "corner_radius_mm"))
    aperture_count = int(parameter(section, "aperture_count"))
    aperture_radius = float(parameter(section, "aperture_radius_mm"))
    aperture_pitch = float(parameter(section, "aperture_pitch_mm"))

    shape = rounded_box(
        depth_x,
        width_y,
        height_z,
        center_x,
        center_y,
        base_z,
        corner_radius,
    )
    front_x = center_x + depth_x / 2.0
    aperture_z = base_z + height_z / 2.0
    for index in range(aperture_count):
        y = center_y + (index - (aperture_count - 1) / 2.0) * aperture_pitch
        hole = Part.makeCylinder(
            aperture_radius,
            depth_x + 2.0,
            App.Vector(center_x - depth_x / 2.0 - 1.0, y, aperture_z),
            App.Vector(1.0, 0.0, 0.0),
        )
        shape = shape.cut(hole)
    if shape.BoundBox.XMax > front_x + 1.0e-6:
        raise RuntimeError("Unexpected front sensor-bar extent")
    return shape.removeSplitter()


def add_part_object(
    document: App.Document,
    name: str,
    shape: Part.Shape,
    evidence_class: str,
    source_note: str,
    color: list[float] | None,
) -> App.DocumentObject:
    if not shape.isValid() or not shape.isClosed() or len(shape.Solids) != 1:
        raise RuntimeError(
            f"{name} is not one valid closed solid: "
            f"valid={shape.isValid()} closed={shape.isClosed()} "
            f"solids={len(shape.Solids)}"
        )
    obj = document.addObject("Part::Feature", name)
    obj.Label = name.replace("_", " ")
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "EvidenceClass", "Provenance")
    obj.EvidenceClass = evidence_class
    obj.addProperty("App::PropertyString", "SourceNote", "Provenance")
    obj.SourceNote = source_note
    if App.GuiUp and color is not None:
        obj.ViewObject.ShapeColor = tuple(color)
    return obj


def bbox_dict(bbox: App.BoundBox) -> dict[str, Any]:
    return {
        "min_mm": [bbox.XMin, bbox.YMin, bbox.ZMin],
        "max_mm": [bbox.XMax, bbox.YMax, bbox.ZMax],
        "size_mm": [bbox.XLength, bbox.YLength, bbox.ZLength],
    }


def combined_bbox(boxes: list[App.BoundBox]) -> App.BoundBox:
    if not boxes:
        raise ValueError("Cannot combine an empty bounding-box list")
    result = App.BoundBox()
    for box in boxes:
        result.add(box)
    return result


def output_hashes(paths: list[Path]) -> dict[str, dict[str, Any]]:
    return {
        path.name: {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in paths
    }


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)
    params_path = Path(
        os.environ.get("LITE3_MODEL_PARAMS", script_dir / "model_parameters.json")
    ).resolve()
    build_root = Path(
        os.environ.get("LITE3_MODEL_BUILD_ROOT", script_dir)
    ).resolve()
    models_dir = build_root / "models"
    reports_dir = build_root / "reports"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    config = load_json(params_path)
    validate_parameter_contract(config)

    source_records: dict[str, dict[str, Any]] = {}
    for name, source in config["sources"].items():
        path = (repo_root / source["path"]).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_hash = sha256(path)
        if actual_hash != source["sha256"]:
            raise RuntimeError(
                f"Source hash mismatch for {name}: "
                f"expected {source['sha256']}, got {actual_hash}"
            )
        source_records[name] = {
            "path": str(path),
            "sha256": actual_hash,
            "size_bytes": path.stat().st_size,
            "evidence_class": source["evidence_class"],
        }

    document = App.newDocument("Lite3_LiDAR_V107_Reconstruction")
    source_mesh = Mesh.Mesh(source_records["standing_stl"]["path"])
    source_bbox = source_mesh.BoundBox
    rotation_deg = float(
        parameter(config["coordinate_system"], "source_rotation_x_deg")
        if "parameters" in config["coordinate_system"]
        else config["coordinate_system"]["source_rotation_x_deg"]["value"]
    )
    scale = float(config["coordinate_system"]["source_scale"]["value"])
    if abs(scale - 1.0) > 1.0e-12:
        raise RuntimeError("Official visual mesh scale must remain exactly 1.0")
    transform = App.Matrix()
    transform.rotateX(math.radians(rotation_deg))
    source_mesh.transform(transform)
    source_mesh.translate(0.0, 0.0, -source_mesh.BoundBox.ZMin)
    base_obj = document.addObject("Mesh::Feature", "Official_Lite3_Base_Mesh")
    base_obj.Label = "Official Lite3 Base Mesh"
    base_obj.Mesh = source_mesh
    base_obj.addProperty("App::PropertyString", "EvidenceClass", "Provenance")
    base_obj.EvidenceClass = "source_model"
    base_obj.addProperty("App::PropertyString", "ArtifactLabel", "Provenance")
    base_obj.ArtifactLabel = "visual_only"
    if App.GuiUp:
        base_color = config["visual"]["colors_rgb"]["Official_Lite3_Base_Mesh"]
        base_obj.ViewObject.ShapeColor = tuple(base_color)

    builders = {
        "Upper_Mounting_References": (
            build_mounting_reference,
            "mounting_reference",
        ),
        "Upper_Interface_Enclosure": (
            build_upper_enclosure,
            "upper_interface_enclosure",
        ),
        "Laser_Radar_Core": (build_radar_core, "laser_radar_core"),
        "Cooling_Fins": (build_cooling_fins, "cooling_fins"),
        "Protective_Hoop": (build_protective_hoop, "protective_hoop"),
        "Front_Sensor_Bar": (build_front_sensor_bar, "front_sensor_bar"),
    }
    part_objects: list[App.DocumentObject] = []
    component_metrics: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_COMPONENT_NAMES:
        builder, section_name = builders[name]
        shape = builder(config)
        source_note = config[section_name]["source_note"]
        evidence_classes = {
            node["evidence_class"]
            for node in config[section_name]["parameters"].values()
        }
        evidence_class = (
            "official_nominal"
            if evidence_classes == {"official_nominal"}
            else "image_estimate"
        )
        color = config["visual"]["colors_rgb"].get(name)
        obj = add_part_object(
            document,
            name,
            shape,
            evidence_class,
            source_note,
            color,
        )
        obj.addProperty("App::PropertyString", "ArtifactLabel", "Provenance")
        obj.ArtifactLabel = "appearance_reconstruction"
        part_objects.append(obj)
        component_metrics[name] = {
            "valid": shape.isValid(),
            "closed": shape.isClosed(),
            "solid_count": len(shape.Solids),
            "bbox": bbox_dict(shape.BoundBox),
            "volume_mm3": shape.Volume,
        }

    document.recompute()
    assembly_bbox = combined_bbox(
        [base_obj.Mesh.BoundBox, *(obj.Shape.BoundBox for obj in part_objects)]
    )
    target_height = float(parameter(config["official_envelope"], "height_mm"))
    height_tolerance = float(
        parameter(config["official_envelope"], "height_tolerance_mm")
    )
    height_error = assembly_bbox.ZMax - target_height
    if abs(height_error) > height_tolerance:
        raise RuntimeError(
            f"Assembly height {assembly_bbox.ZMax:.6f} mm misses "
            f"target {target_height:.6f} mm by {height_error:.6f} mm"
        )
    if abs(assembly_bbox.ZMin) > 1.0e-6:
        raise RuntimeError(
            f"Assembly is not ground aligned: minimum Z={assembly_bbox.ZMin}"
        )

    fcstd_path = models_dir / "lite3_lidar_v107_reconstruction.FCStd"
    step_path = models_dir / "lite3_lidar_v107_upper_module.step"
    upper_stl_path = models_dir / "lite3_lidar_v107_upper_module.stl"
    visual_stl_path = models_dir / "lite3_lidar_v107_standing_visual.stl"
    document.recompute()
    document.saveAs(str(fcstd_path))
    Part.export(part_objects, str(step_path))
    Mesh.export(part_objects, str(upper_stl_path))
    Mesh.export([base_obj, *part_objects], str(visual_stl_path))

    reimport_step = Part.read(str(step_path))
    reimport_upper_mesh = Mesh.Mesh(str(upper_stl_path))
    reimport_visual_mesh = Mesh.Mesh(str(visual_stl_path))

    artifact_paths = [
        fcstd_path,
        step_path,
        upper_stl_path,
        visual_stl_path,
    ]
    freecad_version = App.Version()
    report = {
        "schema_version": 1,
        "model_id": config["model_id"],
        "artifact_labels": config["artifact_labels"],
        "freecad_version": ".".join(freecad_version[:3]),
        "parameters_path": str(params_path),
        "sources": source_records,
        "base_mesh": {
            "source_bbox_y_up": bbox_dict(source_bbox),
            "transformed_bbox_z_up": bbox_dict(base_obj.Mesh.BoundBox),
            "scale": scale,
            "rotation_x_deg": rotation_deg,
            "point_count": base_obj.Mesh.CountPoints,
            "facet_count": base_obj.Mesh.CountFacets,
        },
        "components": component_metrics,
        "required_component_names": list(REQUIRED_COMPONENT_NAMES),
        "object_count": 1 + len(part_objects),
        "assembly_bbox": bbox_dict(assembly_bbox),
        "official_target_bbox_mm": {
            "length": parameter(config["official_envelope"], "length_mm"),
            "width": parameter(config["official_envelope"], "width_mm"),
            "height": target_height,
        },
        "height_error_mm": height_error,
        "preserved_width_difference_mm": (
            assembly_bbox.YLength
            - float(parameter(config["official_envelope"], "width_mm"))
        ),
        "reimport": {
            "step": {
                "valid": reimport_step.isValid(),
                "solid_count": len(reimport_step.Solids),
                "bbox": bbox_dict(reimport_step.BoundBox),
            },
            "upper_stl": {
                "facet_count": reimport_upper_mesh.CountFacets,
                "bbox": bbox_dict(reimport_upper_mesh.BoundBox),
            },
            "standing_visual_stl": {
                "facet_count": reimport_visual_mesh.CountFacets,
                "bbox": bbox_dict(reimport_visual_mesh.BoundBox),
            },
        },
        "outputs": output_hashes(artifact_paths),
        "claim_boundary": (
            "Appearance reconstruction only. Exact sensor identity, brackets, "
            "internal details, mounting tolerance, material, strength, and "
            "physical fit are unknown."
        ),
    }
    report_path = reports_dir / "validation.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"fcstd={fcstd_path}")
    print(f"step={step_path}")
    print(f"upper_stl={upper_stl_path}")
    print(f"visual_stl={visual_stl_path}")
    print(f"validation={report_path}")
    print(
        "assembly_bbox_mm="
        + ",".join(f"{value:.6f}" for value in (
            assembly_bbox.XLength,
            assembly_bbox.YLength,
            assembly_bbox.ZLength,
        ))
    )
    print(f"height_error_mm={height_error:.6f}")
    print(f"object_count={1 + len(part_objects)}")
    App.closeDocument(document.Name)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise
