"""Smoke-test Clone Fields inside Blender.

Run with:
    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/smoke_test_blender.py
"""

from __future__ import annotations

import importlib
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PARENT = REPO_ROOT.parent


def _evaluated_instance_count() -> int:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return sum(1 for _instance in depsgraph.object_instances)


def _evaluated_vertex_count(obj: bpy.types.Object) -> int:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return len(mesh.vertices)
    finally:
        evaluated.to_mesh_clear()


def _evaluated_bounds_size(obj: bpy.types.Object) -> tuple[float, float, float]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        xs = [vertex.co.x for vertex in mesh.vertices]
        ys = [vertex.co.y for vertex in mesh.vertices]
        zs = [vertex.co.z for vertex in mesh.vertices]
        return (
            max(xs) - min(xs),
            max(ys) - min(ys),
            max(zs) - min(zs),
        )
    finally:
        evaluated.to_mesh_clear()


def _evaluated_bounds_center(obj: bpy.types.Object) -> tuple[float, float, float]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        xs = [vertex.co.x for vertex in mesh.vertices]
        ys = [vertex.co.y for vertex in mesh.vertices]
        zs = [vertex.co.z for vertex in mesh.vertices]
        return (
            (max(xs) + min(xs)) / 2.0,
            (max(ys) + min(ys)) / 2.0,
            (max(zs) + min(zs)) / 2.0,
        )
    finally:
        evaluated.to_mesh_clear()


def _evaluated_vertices(obj: bpy.types.Object) -> list[tuple[float, float, float]]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [(vertex.co.x, vertex.co.y, vertex.co.z) for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def _max_xy_radius(vertices: list[tuple[float, float, float]]) -> float:
    return max((vertex[0] ** 2 + vertex[1] ** 2) ** 0.5 for vertex in vertices)


def _max_z_range_near_xy(
    vertices: list[tuple[float, float, float]],
    *,
    x: float,
    y: float,
    radius: float,
) -> float:
    nearby = [
        vertex[2]
        for vertex in vertices
        if ((vertex[0] - x) ** 2 + (vertex[1] - y) ** 2) ** 0.5 < radius
    ]
    if not nearby:
        return 0.0
    return max(nearby) - min(nearby)


def _has_vertex_near(
    vertices: list[tuple[float, float, float]],
    expected: tuple[float, float, float],
    tolerance: float = 0.0001,
) -> bool:
    return any(
        max(abs(vertex[i] - expected[i]) for i in range(3)) < tolerance
        for vertex in vertices
    )


def _min_vertex_distance(vertices: list[tuple[float, float, float]]) -> float:
    distances = []
    for index, first in enumerate(vertices):
        for second in vertices[index + 1 :]:
            distances.append(
                sum((first[axis] - second[axis]) ** 2 for axis in range(3)) ** 0.5
            )
    return min(distances)


def _max_abs_axis_for_vertices(
    vertices: list[tuple[float, float, float]],
    *,
    axis: int,
    predicate,
) -> float:
    return max(abs(vertex[axis]) for vertex in vertices if predicate(vertex))


def _modifier_input_id(
    inputs_module,
    modifier: bpy.types.NodesModifier,
    socket_name: str,
) -> str:
    identifier = inputs_module.get_modifier_input_identifier(modifier, socket_name)
    assert identifier is not None
    return identifier


def _set_modifier_mode(
    cloner: bpy.types.Object,
    modifier: bpy.types.NodesModifier,
    mode_id: str,
    mode_value: int,
) -> None:
    modifier[mode_id] = mode_value
    cloner.update_tag()
    modifier.node_group.update_tag()
    bpy.context.view_layer.update()


def main() -> None:
    sys.path.insert(0, str(PACKAGE_PARENT))

    addon = importlib.import_module(REPO_ROOT.name)
    addon.register()
    inputs = importlib.import_module(f"{REPO_ROOT.name}.modifier_inputs")
    props = importlib.import_module(f"{REPO_ROOT.name}.properties")
    cloner_module = importlib.import_module(f"{REPO_ROOT.name}.cloner")
    eff = importlib.import_module(f"{REPO_ROOT.name}.effectors")
    sources = importlib.import_module(f"{REPO_ROOT.name}.source_management")
    guides = importlib.import_module(f"{REPO_ROOT.name}.viewport_guides")
    gizmos = importlib.import_module(f"{REPO_ROOT.name}.gizmos")

    try:
        bpy.ops.mesh.primitive_cube_add()
        source = bpy.context.object
        source.name = "Smoke Source"

        result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            count_x=2,
            count_y=3,
            count_z=2,
            spacing_x=1.5,
            spacing_y=2.0,
            spacing_z=2.5,
        )
        assert result == {"FINISHED"}, result

        cloner = bpy.context.object
        assert cloner.name == "Cloner"
        assert cloner.data.name == "Clone Fields Output"
        assert cloner.display_type == "TEXTURED"
        assert cloner.get(props.PROP_CLONER_TYPE) == "CLONER"
        assert cloner.get(props.PROP_CLONER_MODE) == "GRID"
        assert source.parent == cloner
        assert source.hide_get()
        assert source.hide_render
        assert _evaluated_instance_count() > 0

        modifier = cloner.modifiers["Cloner"]
        assert modifier.type == "NODES"
        assert modifier.node_group is not None
        assert not modifier.node_group.name.startswith("Clone Fields Grid Cloner")
        if hasattr(modifier.node_group, "is_modifier"):
            assert not modifier.node_group.is_modifier
        panel_names = {
            item.name
            for item in modifier.node_group.interface.items_tree
            if getattr(item, "item_type", None) == "PANEL"
        }
        assert {
            "Distribution",
            "Grid",
            "Brick",
            "Count",
            "Spacing",
            "Linear",
            "Direction",
            "Radial",
            "Object",
            "Basic Effector",
            "Effector Position",
            "Effector Rotation",
            "Effector Scale",
            "Source Transform",
            "Position",
            "Rotation",
            "Scale",
        } <= panel_names
        for item in modifier.node_group.interface.items_tree:
            if (
                getattr(item, "item_type", None) == "SOCKET"
                and getattr(item, "in_out", None) == "INPUT"
                and item.name != props.SOCKET_GEOMETRY
            ):
                assert item.hide_in_modifier
        internal_group_names = {
            node.node_tree.name
            for node in modifier.node_group.nodes
            if node.bl_idname == "GeometryNodeGroup" and node.node_tree is not None
        }
        assert props.SOURCE_TRANSFORM_NODE_GROUP_NAME in internal_group_names
        assert props.GRID_DISTRIBUTION_NODE_GROUP_NAME in internal_group_names
        assert props.BRICK_DISTRIBUTION_NODE_GROUP_NAME in internal_group_names
        assert props.LINEAR_DISTRIBUTION_NODE_GROUP_NAME in internal_group_names
        assert props.RADIAL_DISTRIBUTION_NODE_GROUP_NAME in internal_group_names
        assert props.OBJECT_DISTRIBUTION_NODE_GROUP_NAME in internal_group_names
        assert cloner.clone_fields_cloner.distribution_mode == "GRID"

        mode_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_DISTRIBUTION_MODE,
        )
        spacing_mode_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_SPACING_MODE,
        )
        count_x_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_COUNT_X)
        spacing_z_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_SPACING_Z)
        source_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_SOURCE_OBJECT)
        linear_count_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_LINEAR_COUNT,
        )
        linear_spacing_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_LINEAR_SPACING,
        )
        linear_direction_x_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_LINEAR_DIRECTION_X,
        )
        linear_direction_y_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_LINEAR_DIRECTION_Y,
        )
        linear_direction_z_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_LINEAR_DIRECTION_Z,
        )
        radial_count_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_RADIAL_COUNT,
        )
        radial_radius_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_RADIAL_RADIUS,
        )
        radial_arc_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_RADIAL_ARC,
        )
        radial_axis_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_RADIAL_AXIS,
        )
        brick_row_offset_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_BRICK_ROW_OFFSET,
        )
        brick_layer_offset_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_BRICK_LAYER_OFFSET,
        )
        object_distribution_object_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_DISTRIBUTION_OBJECT,
        )
        object_distribution_mode_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_DISTRIBUTION_MODE,
        )
        object_spline_distribution_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_SPLINE_DISTRIBUTION,
        )
        object_spline_count_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_SPLINE_COUNT,
        )
        object_surface_density_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_SURFACE_DENSITY,
        )
        object_surface_distribution_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_SURFACE_DISTRIBUTION,
        )
        object_surface_distance_min_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_SURFACE_DISTANCE_MIN,
        )
        object_surface_seed_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_SURFACE_SEED,
        )
        object_alignment_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_ALIGNMENT,
        )
        object_up_vector_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_OBJECT_UP_VECTOR,
        )
        rotation_z_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_SOURCE_ROTATION_Z,
        )
        scale_x_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_SOURCE_SCALE_X,
        )
        position_y_id = inputs.get_modifier_input_identifier(
            modifier,
            props.SOCKET_SOURCE_POSITION_Y,
        )

        assert mode_id is not None
        assert spacing_mode_id is not None
        assert count_x_id is not None
        assert spacing_z_id is not None
        assert source_id is not None
        assert linear_count_id is not None
        assert linear_spacing_id is not None
        assert linear_direction_x_id is not None
        assert linear_direction_y_id is not None
        assert linear_direction_z_id is not None
        assert radial_count_id is not None
        assert radial_radius_id is not None
        assert radial_arc_id is not None
        assert radial_axis_id is not None
        assert brick_row_offset_id is not None
        assert brick_layer_offset_id is not None
        assert object_distribution_object_id is not None
        assert object_distribution_mode_id is not None
        assert object_spline_distribution_id is not None
        assert object_spline_count_id is not None
        assert object_surface_distribution_id is not None
        assert object_surface_density_id is not None
        assert object_surface_distance_min_id is not None
        assert object_surface_seed_id is not None
        assert object_alignment_id is not None
        assert object_up_vector_id is not None
        assert rotation_z_id is not None
        assert scale_x_id is not None
        assert position_y_id is not None

        assert modifier[mode_id] == 0
        assert modifier[spacing_mode_id] == 0
        assert modifier[count_x_id] == 2
        assert modifier[spacing_z_id] == 2.5
        assert modifier[source_id] == source
        assert _evaluated_vertex_count(cloner) > 0
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 12
        assert max(abs(value) for value in _evaluated_bounds_center(cloner)) < 0.0001

        cloner.clone_fields_cloner.count_x = 4
        cloner.clone_fields_cloner.count_y = 1
        cloner.clone_fields_cloner.count_z = 1
        cloner.clone_fields_cloner.spacing_x = 6.0
        cloner.clone_fields_cloner.spacing_mode = "PER_STEP"
        bpy.context.view_layer.update()
        per_step_bounds = _evaluated_bounds_size(cloner)
        cloner.clone_fields_cloner.spacing_mode = "ENDPOINT"
        bpy.context.view_layer.update()
        endpoint_bounds = _evaluated_bounds_size(cloner)
        assert modifier[spacing_mode_id] == 1
        assert abs(cloner.clone_fields_cloner.spacing_x - 18.0) < 0.0001
        assert max(abs(endpoint_bounds[i] - per_step_bounds[i]) for i in range(3)) < 0.0001
        cloner.clone_fields_cloner.spacing_mode = "PER_STEP"
        bpy.context.view_layer.update()
        assert abs(cloner.clone_fields_cloner.spacing_x - 6.0) < 0.0001

        cloner.clone_fields_cloner.distribution_mode = "LINEAR"
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[mode_id] == 1

        modifier[linear_count_id] = 4
        modifier[linear_spacing_id] = 1.25
        modifier[linear_direction_x_id] = 0.0
        modifier[linear_direction_y_id] = 1.0
        modifier[linear_direction_z_id] = 0.0
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 4
        linear_bounds = _evaluated_bounds_size(cloner)
        assert linear_bounds[1] > linear_bounds[0]

        cloner.clone_fields_cloner.linear_count = 4
        cloner.clone_fields_cloner.linear_spacing = 1.25
        cloner.clone_fields_cloner.spacing_mode = "ENDPOINT"
        bpy.context.view_layer.update()
        assert abs(cloner.clone_fields_cloner.linear_spacing - 3.75) < 0.0001
        converted_linear_bounds = _evaluated_bounds_size(cloner)
        assert max(abs(converted_linear_bounds[i] - linear_bounds[i]) for i in range(3)) < 0.0001
        cloner.clone_fields_cloner.spacing_mode = "PER_STEP"
        bpy.context.view_layer.update()
        assert abs(cloner.clone_fields_cloner.linear_spacing - 1.25) < 0.0001

        cloner.clone_fields_cloner.spacing_mode = "ENDPOINT"
        modifier[linear_spacing_id] = 1.25
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        endpoint_linear_bounds = _evaluated_bounds_size(cloner)
        assert endpoint_linear_bounds[1] < linear_bounds[1]
        cloner.clone_fields_cloner.spacing_mode = "PER_STEP"

        modifier[radial_count_id] = 6
        modifier[radial_radius_id] = 3.0
        modifier[radial_arc_id] = 6.283185307179586
        modifier[radial_axis_id] = 0
        modifier[mode_id] = 2
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 6
        radial_bounds = _evaluated_bounds_size(cloner)
        assert radial_bounds[0] > linear_bounds[0]
        assert radial_bounds[1] > linear_bounds[0]

        cloner.clone_fields_cloner.distribution_mode = "BRICK"
        cloner.clone_fields_cloner.count_x = 3
        cloner.clone_fields_cloner.count_y = 2
        cloner.clone_fields_cloner.count_z = 1
        cloner.clone_fields_cloner.spacing_x = 2.0
        cloner.clone_fields_cloner.spacing_y = 2.0
        cloner.clone_fields_cloner.spacing_z = 2.0
        cloner.clone_fields_cloner.brick_row_offset = 0.5
        cloner.clone_fields_cloner.brick_layer_offset = 0.0
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[mode_id] == 4
        assert abs(modifier[brick_row_offset_id] - 0.5) < 0.0001
        assert abs(modifier[brick_layer_offset_id]) < 0.0001
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 6
        brick_vertices = _evaluated_vertices(cloner)
        lower_y = min(vertex[1] for vertex in brick_vertices)
        upper_y = max(vertex[1] for vertex in brick_vertices)
        lower_row_x = [
            vertex[0] for vertex in brick_vertices if vertex[1] < lower_y + 1.1
        ]
        upper_row_x = [
            vertex[0] for vertex in brick_vertices if vertex[1] > upper_y - 1.1
        ]
        lower_center_x = (min(lower_row_x) + max(lower_row_x)) / 2.0
        upper_center_x = (min(upper_row_x) + max(upper_row_x)) / 2.0
        assert abs((upper_center_x - lower_center_x) - 1.0) < 0.0001
        cloner.clone_fields_cloner.count_x = 4
        cloner.clone_fields_cloner.count_y = 1
        cloner.clone_fields_cloner.count_z = 1
        cloner.clone_fields_cloner.spacing_x = 6.0
        cloner.clone_fields_cloner.spacing_y = 2.0
        cloner.clone_fields_cloner.spacing_z = 2.5

        distribution_mesh = bpy.data.meshes.new("Distribution Mesh")
        distribution_mesh.from_pydata(
            [
                (-1.0, -1.0, 0.0),
                (1.0, -1.0, 0.0),
                (1.0, 1.0, 0.0),
                (-1.0, 1.0, 0.0),
            ],
            [],
            [(0, 1, 2, 3)],
        )
        distribution_mesh.update()
        distribution_object = bpy.data.objects.new("Distribution Object", distribution_mesh)
        bpy.context.collection.objects.link(distribution_object)
        cloner.clone_fields_cloner.distribution_mode = "OBJECT"
        cloner.clone_fields_cloner.object_distribution_object = distribution_object
        cloner.clone_fields_cloner.object_distribution_mode = "VERTICES"
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[mode_id] == 3
        assert modifier[object_distribution_object_id] == distribution_object
        assert modifier[object_distribution_mode_id] == 0
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 4

        cloner.clone_fields_cloner.object_distribution_mode = "POLYGONS"
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[object_distribution_mode_id] == 1
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices)

        cloner.clone_fields_cloner.object_distribution_mode = "SURFACE"
        cloner.clone_fields_cloner.object_surface_distribution = "RANDOM"
        cloner.clone_fields_cloner.object_surface_density = 8.0
        cloner.clone_fields_cloner.object_surface_distance_min = 0.0
        cloner.clone_fields_cloner.object_surface_seed = 7
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[object_distribution_mode_id] == 3
        assert modifier[object_surface_distribution_id] == 0
        assert abs(modifier[object_surface_density_id] - 8.0) < 0.0001
        assert abs(modifier[object_surface_distance_min_id]) < 0.0001
        assert modifier[object_surface_seed_id] == 7
        dense_surface_count = _evaluated_vertex_count(cloner)
        assert dense_surface_count > len(source.data.vertices) * 4
        cloner.clone_fields_cloner.object_surface_distribution = "POISSON"
        cloner.clone_fields_cloner.object_surface_distance_min = 1.5
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[object_surface_distribution_id] == 1
        assert abs(modifier[object_surface_distance_min_id] - 1.5) < 0.0001
        spaced_surface_count = _evaluated_vertex_count(cloner)
        assert 0 < spaced_surface_count < dense_surface_count, (
            dense_surface_count,
            spaced_surface_count,
        )

        tilted_mesh = bpy.data.meshes.new("Tilted Distribution Mesh")
        tilted_mesh.from_pydata(
            [
                (-1.0, 1.0, 0.0),
                (1.0, 1.0, 0.0),
                (1.0, 3.0, 1.25),
                (-1.0, 3.0, 1.25),
            ],
            [],
            [(0, 1, 2, 3)],
        )
        tilted_mesh.update()
        tilted_object = bpy.data.objects.new("Tilted Distribution Object", tilted_mesh)
        bpy.context.collection.objects.link(tilted_object)
        cloner.clone_fields_cloner.object_distribution_object = tilted_object
        cloner.clone_fields_cloner.object_distribution_mode = "POLYGONS"
        cloner.clone_fields_cloner.source_position_z = 0.0
        cloner.clone_fields_cloner.object_alignment = "NONE"
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        unaligned_tilt_size = _evaluated_bounds_size(cloner)
        cloner.clone_fields_cloner.object_alignment = "NORMALS"
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        aligned_tilt_size = _evaluated_bounds_size(cloner)
        assert max(
            abs(aligned_tilt_size[axis] - unaligned_tilt_size[axis])
            for axis in range(3)
        ) > 0.1

        align_source_mesh = bpy.data.meshes.new("Object Align Source Mesh")
        align_source_mesh.from_pydata(
            [
                (-0.1, -0.1, 0.0),
                (0.1, -0.1, 0.0),
                (0.1, 0.1, 0.0),
                (-0.1, 0.1, 0.0),
                (-0.1, -0.1, 2.0),
                (0.1, -0.1, 2.0),
                (0.1, 0.1, 2.0),
                (-0.1, 0.1, 2.0),
            ],
            [],
            [
                (0, 1, 2, 3),
                (4, 7, 6, 5),
                (0, 4, 5, 1),
                (1, 5, 6, 2),
                (2, 6, 7, 3),
                (3, 7, 4, 0),
            ],
        )
        align_source_mesh.update()
        align_source = bpy.data.objects.new("Object Align Source", align_source_mesh)
        bpy.context.collection.objects.link(align_source)

        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16,
            ring_count=8,
            radius=3.0,
            location=(2.0, -1.0, 0.5),
        )
        sphere_object = bpy.context.object
        sphere_object.scale = (1.2, 0.8, 1.1)
        align_cloner = cloner_module.create_grid_cloner(
            bpy.context,
            source_object=align_source,
            count_x=1,
            count_y=1,
            count_z=1,
            spacing_x=1.0,
            spacing_y=1.0,
            spacing_z=1.0,
        )
        align_modifier = align_cloner.modifiers["Cloner"]
        align_cloner.clone_fields_cloner.distribution_mode = "OBJECT"
        align_cloner.clone_fields_cloner.object_distribution_object = sphere_object
        align_cloner.clone_fields_cloner.object_distribution_mode = "POLYGONS"
        align_cloner.clone_fields_cloner.object_alignment = "NONE"
        align_cloner.update_tag()
        align_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        unaligned_vertices = _evaluated_vertices(align_cloner)
        expected_vertex_count = len(sphere_object.data.polygons) * len(align_source.data.vertices)
        assert len(unaligned_vertices) == expected_vertex_count

        align_cloner.clone_fields_cloner.object_alignment = "NORMALS"
        align_cloner.update_tag()
        align_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        normal_vertices = _evaluated_vertices(align_cloner)
        assert len(normal_vertices) == expected_vertex_count
        normal_radius = _max_xy_radius(normal_vertices)
        for up_vector, expected_value in (("AUTOMATIC", 0), ("X", 1), ("Y", 2), ("Z", 3)):
            align_cloner.clone_fields_cloner.object_up_vector = up_vector
            align_cloner.update_tag()
            align_modifier.node_group.update_tag()
            bpy.context.view_layer.update()
            assert align_modifier[object_up_vector_id] == expected_value
            assert _evaluated_vertex_count(align_cloner) == expected_vertex_count
        align_cloner.clone_fields_cloner.object_up_vector = "AUTOMATIC"

        align_cloner.clone_fields_cloner.object_alignment = "CENTER"
        align_cloner.update_tag()
        align_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        center_vertices = _evaluated_vertices(align_cloner)
        assert len(center_vertices) == expected_vertex_count
        center_radius = _max_xy_radius(center_vertices)
        assert normal_radius > center_radius + 1.0

        align_cloner.clone_fields_cloner.object_distribution_mode = "VERTICES"
        align_cloner.clone_fields_cloner.object_alignment = "NORMALS"
        align_cloner.update_tag()
        align_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        vertex_normal_vertices = _evaluated_vertices(align_cloner)
        expected_vertex_count = len(sphere_object.data.vertices) * len(align_source.data.vertices)
        assert len(vertex_normal_vertices) == expected_vertex_count

        align_cloner.clone_fields_cloner.object_alignment = "CENTER"
        align_cloner.update_tag()
        align_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        vertex_center_vertices = _evaluated_vertices(align_cloner)
        assert len(vertex_center_vertices) == expected_vertex_count
        assert _max_xy_radius(vertex_normal_vertices) > _max_xy_radius(vertex_center_vertices) + 1.0

        distribution_curve = bpy.data.curves.new("Distribution Curve", "CURVE")
        distribution_curve.dimensions = "3D"
        spline = distribution_curve.splines.new("POLY")
        spline.points.add(1)
        spline.points[0].co = (-2.0, 0.0, 0.0, 1.0)
        spline.points[1].co = (2.0, 0.0, 0.0, 1.0)
        curve_object = bpy.data.objects.new("Distribution Spline", distribution_curve)
        bpy.context.collection.objects.link(curve_object)
        cloner.clone_fields_cloner.object_distribution_object = curve_object
        cloner.clone_fields_cloner.object_distribution_mode = "SPLINE"
        cloner.clone_fields_cloner.object_alignment = "TANGENT"
        cloner.clone_fields_cloner.object_spline_distribution = "COUNT"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        cloner.clone_fields_cloner.object_spline_count = 5
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[object_distribution_mode_id] == 2
        assert modifier[object_spline_count_id] == 5
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 5

        bezier_data = bpy.data.curves.new("Bezier Distribution", "CURVE")
        bezier_data.dimensions = "3D"
        bezier_spline = bezier_data.splines.new("BEZIER")
        bezier_spline.bezier_points.add(3)
        for point, coordinate in zip(
            bezier_spline.bezier_points,
            ((-2.0, 0.0, 0.0), (-1.0, 1.0, 0.0), (1.0, 1.0, 0.0), (2.0, 0.0, 0.0)),
        ):
            point.co = coordinate
            point.handle_left_type = "AUTO"
            point.handle_right_type = "AUTO"
        bezier_object = bpy.data.objects.new("Bezier Distribution", bezier_data)
        bpy.context.collection.objects.link(bezier_object)
        cloner.clone_fields_cloner.object_distribution_mode = "VERTICES"
        cloner.clone_fields_cloner.object_alignment = "NORMALS"
        cloner.clone_fields_cloner.object_distribution_object = bezier_object
        cloner.clone_fields_cloner.object_spline_distribution = "COUNT"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        cloner.clone_fields_cloner.object_spline_count = 7
        bpy.context.view_layer.update()
        assert cloner.clone_fields_cloner.object_distribution_mode == "SPLINE"
        assert cloner.clone_fields_cloner.object_alignment == "TANGENT"
        assert modifier[object_distribution_mode_id] == 2
        assert modifier[object_alignment_id] == 3
        bezier_clone_count = _evaluated_vertex_count(cloner)
        assert bezier_clone_count == len(source.data.vertices) * 7, bezier_clone_count

        nurbs_data = bpy.data.curves.new("NURBS Circle Distribution", "CURVE")
        nurbs_data.dimensions = "3D"
        nurbs_spline = nurbs_data.splines.new("NURBS")
        nurbs_spline.points.add(7)
        for index, point in enumerate(nurbs_spline.points):
            angle = (index / 8.0) * 6.283185307179586
            point.co = (2.0 * math.cos(angle), 2.0 * math.sin(angle), 0.0, 1.0)
        nurbs_spline.use_cyclic_u = True
        nurbs_spline.order_u = 3
        nurbs_spline.use_endpoint_u = False
        nurbs_object = bpy.data.objects.new("NURBS Circle Distribution", nurbs_data)
        bpy.context.collection.objects.link(nurbs_object)
        cloner.clone_fields_cloner.object_distribution_mode = "POLYGONS"
        cloner.clone_fields_cloner.object_alignment = "CENTER"
        cloner.clone_fields_cloner.object_distribution_object = nurbs_object
        cloner.clone_fields_cloner.object_spline_distribution = "COUNT"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        cloner.clone_fields_cloner.object_spline_count = 9
        bpy.context.view_layer.update()
        assert cloner.clone_fields_cloner.object_distribution_mode == "SPLINE"
        assert cloner.clone_fields_cloner.object_alignment == "TANGENT"
        assert modifier[object_distribution_mode_id] == 2
        assert modifier[object_alignment_id] == 3
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 9

        generated_curve_mesh = bpy.data.meshes.new("Generated Curve Host Mesh")
        generated_curve_object = bpy.data.objects.new(
            "Generated Curve Host",
            generated_curve_mesh,
        )
        bpy.context.collection.objects.link(generated_curve_object)
        generated_curve_group = bpy.data.node_groups.new(
            "Generated Curve Geometry",
            "GeometryNodeTree",
        )
        generated_curve_group.interface.new_socket(
            name="Geometry",
            in_out="OUTPUT",
            socket_type="NodeSocketGeometry",
        )
        generated_curve_output = generated_curve_group.nodes.new("NodeGroupOutput")
        generated_curve_circle = generated_curve_group.nodes.new(
            "GeometryNodeCurvePrimitiveCircle"
        )
        generated_curve_circle.inputs["Resolution"].default_value = 12
        generated_curve_circle.inputs["Radius"].default_value = 2.0
        generated_curve_group.links.new(
            generated_curve_circle.outputs["Curve"],
            generated_curve_output.inputs["Geometry"],
        )
        generated_curve_modifier = generated_curve_object.modifiers.new(
            name="Generated Curve",
            type="NODES",
        )
        generated_curve_modifier.node_group = generated_curve_group
        cloner.clone_fields_cloner.object_distribution_mode = "VERTICES"
        cloner.clone_fields_cloner.object_alignment = "NORMALS"
        cloner.clone_fields_cloner.object_distribution_object = generated_curve_object
        cloner.clone_fields_cloner.object_spline_distribution = "COUNT"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        cloner.clone_fields_cloner.object_spline_count = 11
        bpy.context.view_layer.update()
        assert generated_curve_object.type == "MESH"
        assert cloner.clone_fields_cloner.object_distribution_mode == "VERTICES"
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 11

        multi_curve_data = bpy.data.curves.new("Multi Spline Distribution", "CURVE")
        multi_curve_data.dimensions = "3D"
        for y_offset in (-1.0, 1.0):
            multi_spline = multi_curve_data.splines.new("POLY")
            multi_spline.points.add(1)
            multi_spline.points[0].co = (-2.0, y_offset, 0.0, 1.0)
            multi_spline.points[1].co = (2.0, y_offset, 0.0, 1.0)
        multi_curve_object = bpy.data.objects.new(
            "Multi Spline Distribution",
            multi_curve_data,
        )
        bpy.context.collection.objects.link(multi_curve_object)
        cloner.clone_fields_cloner.object_distribution_object = multi_curve_object
        cloner.clone_fields_cloner.object_spline_count = 5
        cloner.clone_fields_cloner.object_spline_distribution = "COUNT"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 10
        cloner.clone_fields_cloner.object_spline_per_spline = False
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 5

        cloner.clone_fields_cloner.object_spline_distribution = "EVEN"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        bpy.context.view_layer.update()
        assert modifier[object_spline_distribution_id] == 3
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 10
        cloner.clone_fields_cloner.object_spline_per_spline = False
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == len(source.data.vertices) * 5

        cloner.clone_fields_cloner.object_spline_distribution = "STEP"
        cloner.clone_fields_cloner.object_spline_step = 1.0
        cloner.clone_fields_cloner.object_spline_per_spline = True
        bpy.context.view_layer.update()
        per_spline_step_count = _evaluated_vertex_count(cloner)
        cloner.clone_fields_cloner.object_spline_per_spline = False
        bpy.context.view_layer.update()
        global_step_count = _evaluated_vertex_count(cloner)
        assert per_spline_step_count == len(source.data.vertices) * 10
        assert global_step_count == len(source.data.vertices) * 9

        cloner.clone_fields_cloner.object_spline_distribution = "EVALUATED"
        cloner.clone_fields_cloner.object_spline_per_spline = True
        bpy.context.view_layer.update()
        evaluated_per_spline_count = _evaluated_vertex_count(cloner)
        cloner.clone_fields_cloner.object_spline_per_spline = False
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == evaluated_per_spline_count

        generated_grease_mesh = bpy.data.meshes.new("Generated Grease Pencil Host Mesh")
        generated_grease_object = bpy.data.objects.new(
            "Generated Grease Pencil Host",
            generated_grease_mesh,
        )
        bpy.context.collection.objects.link(generated_grease_object)
        generated_grease_group = bpy.data.node_groups.new(
            "Generated Grease Pencil Geometry",
            "GeometryNodeTree",
        )
        generated_grease_group.interface.new_socket(
            name="Geometry",
            in_out="OUTPUT",
            socket_type="NodeSocketGeometry",
        )
        generated_grease_output = generated_grease_group.nodes.new("NodeGroupOutput")
        generated_grease_circle = generated_grease_group.nodes.new(
            "GeometryNodeCurvePrimitiveCircle"
        )
        generated_grease_circle.inputs["Resolution"].default_value = 12
        generated_grease_circle.inputs["Radius"].default_value = 2.0
        curves_to_grease = generated_grease_group.nodes.new(
            "GeometryNodeCurvesToGreasePencil"
        )
        curves_to_grease.inputs["Instances as Layers"].default_value = False
        generated_grease_group.links.new(
            generated_grease_circle.outputs["Curve"],
            curves_to_grease.inputs["Curves"],
        )
        generated_grease_group.links.new(
            curves_to_grease.outputs["Grease Pencil"],
            generated_grease_output.inputs["Geometry"],
        )
        generated_grease_modifier = generated_grease_object.modifiers.new(
            name="Generated Grease Pencil",
            type="NODES",
        )
        generated_grease_modifier.node_group = generated_grease_group
        cloner.clone_fields_cloner.object_distribution_object = generated_grease_object
        cloner.clone_fields_cloner.object_spline_distribution = "COUNT"
        cloner.clone_fields_cloner.object_spline_count = 7
        cloner.clone_fields_cloner.object_spline_per_spline = True
        bpy.context.view_layer.update()
        generated_grease_count = _evaluated_vertex_count(cloner)
        assert generated_grease_count == len(source.data.vertices) * 7, generated_grease_count

        cloner.clone_fields_cloner.distribution_mode = "GRID"
        cloner.update_tag()
        modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        assert modifier[mode_id] == 0
        source_matrix = source.matrix_world.copy()
        original_bounds = _evaluated_bounds_size(cloner)
        original_center = _evaluated_bounds_center(cloner)

        cloner.clone_fields_cloner.source_scale_x = 2.0
        cloner.clone_fields_cloner.source_rotation_z = 1.5707963267948966
        assert abs(modifier[scale_x_id] - 2.0) < 0.0001
        assert abs(modifier[rotation_z_id] - 1.5707963267948966) < 0.0001
        assert source.matrix_world == source_matrix
        transformed_bounds = _evaluated_bounds_size(cloner)
        assert transformed_bounds != original_bounds
        rotated_center = _evaluated_bounds_center(cloner)
        assert max(abs(original_center[i] - rotated_center[i]) for i in range(3)) < 0.0001

        cloner.clone_fields_cloner.source_position_y = 1.25
        assert abs(modifier[position_y_id] - 1.25) < 0.0001

        modifier[count_x_id] = 4
        assert modifier[count_x_id] == 4
        assert _evaluated_vertex_count(cloner) > 0

        modifier.show_viewport = False
        sources.sync_all_source_visibility()
        assert not source.hide_get()
        assert not source.hide_render

        modifier.show_viewport = True
        sources.sync_all_source_visibility()
        assert source.hide_get()
        assert source.hide_render

        original_vertex_count = _evaluated_vertex_count(cloner)
        bpy.ops.object.select_all(action="DESELECT")
        cloner.select_set(True)
        bpy.context.view_layer.objects.active = cloner
        bpy.ops.object.duplicate()
        duplicated_cloner = bpy.context.object
        assert duplicated_cloner != cloner
        assert inputs.is_cloner_object(duplicated_cloner)
        sources.sync_all_source_visibility()
        bpy.context.view_layer.update()
        assert _evaluated_vertex_count(cloner) == original_vertex_count
        assert _evaluated_vertex_count(duplicated_cloner) > 0
        duplicate_sources = [
            child
            for child in duplicated_cloner.children
            if not inputs.is_cloner_object(child)
        ]
        assert duplicate_sources
        assert all(child.hide_get() for child in duplicate_sources)
        duplicate_modifier = duplicated_cloner.modifiers["Cloner"]
        original_collection = inputs.get_modifier_input(
            modifier,
            props.SOCKET_SOURCE_COLLECTION,
        )
        duplicate_collection = inputs.get_modifier_input(
            duplicate_modifier,
            props.SOCKET_SOURCE_COLLECTION,
        )
        assert original_collection is not None
        assert duplicate_collection is not None
        assert original_collection != duplicate_collection

        bpy.ops.mesh.primitive_cube_add(location=(10.0, 0.0, 0.0))
        effector_source = bpy.context.object
        effector_source.name = "Effector Source"
        effector_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=effector_source.name,
            count_x=3,
            count_y=1,
            count_z=1,
            spacing_x=2.5,
            spacing_y=2.0,
            spacing_z=2.0,
        )
        assert effector_result == {"FINISHED"}, effector_result
        effector_cloner = bpy.context.object
        base_effector_bounds = _evaluated_bounds_size(effector_cloner)
        base_effector_center = _evaluated_bounds_center(effector_cloner)
        add_effector_result = bpy.ops.clone_fields.add_plain_effector("EXEC_DEFAULT")
        assert add_effector_result == {"FINISHED"}, add_effector_result
        plain_effector = effector_cloner.clone_fields_cloner.effector_object
        assert plain_effector.type == "EMPTY"
        assert plain_effector.empty_display_type == "SPHERE"
        assert plain_effector.hide_render
        assert plain_effector.name.startswith("Basic Effector [Spherical]")
        assert plain_effector.get(props.PROP_EFFECTOR_TYPE) == "BASIC"
        assert plain_effector.get(props.PROP_EFFECTOR_SHAPE) == "SPHERE"
        assert plain_effector.lock_scale[:] == (True, True, True)
        plain_effector.scale = (2.0, 0.5, 3.0)
        plain_effector.update_tag()
        eff.enforce_all_effector_transform_constraints()
        assert tuple(round(value, 4) for value in plain_effector.scale[:]) == (
            1.0,
            1.0,
            1.0,
        )
        assert effector_cloner == bpy.context.view_layer.objects.active
        assert effector_cloner.select_get()
        assert not plain_effector.select_get()
        assert effector_cloner.clone_fields_cloner.effector_object == plain_effector
        assert effector_cloner.clone_fields_cloner.effector_enabled
        plain_effector_settings = plain_effector.clone_fields_effector
        assert plain_effector_settings.falloff == 50
        assert plain_effector_settings.strength == 100
        assert plain_effector_settings.use_position
        assert not plain_effector_settings.use_rotation
        assert not plain_effector_settings.use_scale
        assert abs(plain_effector_settings.position_z - 1.0) < 0.0001
        assert effector_cloner.clone_fields_cloner.effector_strength == 100
        positioned_effector_center = _evaluated_bounds_center(effector_cloner)
        assert positioned_effector_center[2] > base_effector_center[2]
        effector_modifier = effector_cloner.modifiers["Cloner"]
        effector_object_id = _modifier_input_id(
            inputs,
            effector_modifier,
            props.SOCKET_EFFECTOR_OBJECT,
        )
        effector_radius_id = _modifier_input_id(
            inputs,
            effector_modifier,
            props.SOCKET_EFFECTOR_RADIUS,
        )
        effector_field_id = _modifier_input_id(
            inputs,
            effector_modifier,
            props.SOCKET_EFFECTOR_FIELD,
        )
        effector_strength_id = _modifier_input_id(
            inputs,
            effector_modifier,
            props.SOCKET_EFFECTOR_STRENGTH,
        )
        assert effector_modifier[effector_object_id] == plain_effector
        assert abs(effector_modifier[effector_strength_id] - 1.0) < 0.0001
        effector_cloner.clone_fields_cloner.effector_strength = 50
        assert abs(effector_modifier[effector_strength_id] - 0.5) < 0.0001
        plain_effector_settings.strength = 50
        assert abs(effector_modifier[effector_strength_id] - 0.25) < 0.0001
        plain_effector_settings.strength = 100
        effector_cloner.clone_fields_cloner.effector_strength = 100
        assert abs(effector_modifier[effector_strength_id] - 1.0) < 0.0001

        bpy.ops.mesh.primitive_cube_add(location=(14.0, 0.0, 0.0))
        random_source = bpy.context.object
        random_source.name = "Random Effector Source"
        random_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=random_source.name,
            count_x=5,
            count_y=1,
            count_z=1,
            spacing_x=1.25,
            spacing_y=2.0,
            spacing_z=2.0,
        )
        assert random_result == {"FINISHED"}, random_result
        random_cloner = bpy.context.object
        random_add_result = bpy.ops.clone_fields.add_random_effector("EXEC_DEFAULT")
        assert random_add_result == {"FINISHED"}, random_add_result
        random_effector = random_cloner.clone_fields_cloner.effector_object
        assert random_effector.name.startswith("Random Effector [None]")
        assert random_effector.get(props.PROP_EFFECTOR_TYPE) == "RANDOM"
        random_effector_settings = random_effector.clone_fields_effector
        assert random_effector_settings.type == "RANDOM"
        assert random_effector_settings.shape == eff.FIELD_SHAPE_NONE
        assert random_effector_settings.use_position
        random_modifier = random_cloner.modifiers["Cloner"]
        random_type_id = _modifier_input_id(
            inputs,
            random_modifier,
            props.SOCKET_EFFECTOR_TYPE,
        )
        random_field_id = _modifier_input_id(
            inputs,
            random_modifier,
            props.SOCKET_EFFECTOR_FIELD,
        )
        assert random_modifier[random_type_id] == 1
        assert random_modifier[random_field_id] == eff.field_shape_value(eff.FIELD_SHAPE_NONE)
        random_effector_settings.radius = 10.0
        random_effector_settings.position_x = 1.0
        random_effector_settings.position_y = 0.0
        random_effector_settings.position_z = 0.0
        random_effector_settings.seed = 7
        random_cloner.update_tag()
        random_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        seed_7_vertices = _evaluated_vertices(random_cloner)
        random_effector_settings.seed = 19
        random_cloner.update_tag()
        random_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        seed_19_vertices = _evaluated_vertices(random_cloner)
        assert any(
            abs(before[0] - after[0]) > 0.001
            for before, after in zip(seed_7_vertices, seed_19_vertices)
        )

        bpy.ops.mesh.primitive_cube_add(location=(26.0, 0.0, 0.0))
        step_source = bpy.context.object
        step_source.name = "Step Effector Source"
        step_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=step_source.name,
            count_x=3,
            count_y=3,
            count_z=1,
            spacing_x=2.0,
            spacing_y=2.0,
            spacing_z=2.0,
        )
        assert step_result == {"FINISHED"}, step_result
        step_cloner = bpy.context.object
        step_add_result = bpy.ops.clone_fields.add_step_effector("EXEC_DEFAULT")
        assert step_add_result == {"FINISHED"}, step_add_result
        step_effector = step_cloner.clone_fields_cloner.effector_object
        assert step_effector.name.startswith("Step Effector [None]")
        assert step_effector.get(props.PROP_EFFECTOR_TYPE) == "STEP"
        step_settings = step_effector.clone_fields_effector
        assert step_settings.type == eff.EFFECTOR_TYPE_STEP
        assert step_settings.shape == eff.FIELD_SHAPE_NONE
        step_settings.position_z = 8.0
        step_cloner.update_tag()
        step_cloner.modifiers["Cloner"].node_group.update_tag()
        bpy.context.view_layer.update()
        step_vertices = _evaluated_vertices(step_cloner)
        min_step_x = min(x for x, _y, _z in step_vertices)
        max_step_x = max(x for x, _y, _z in step_vertices)
        min_step_y = min(y for _x, y, _z in step_vertices)
        max_step_y = max(y for _x, y, _z in step_vertices)
        first_step_z = [
            z
            for x, y, z in step_vertices
            if x < min_step_x + 1.1 and y < min_step_y + 1.1
        ]
        last_step_z = [
            z
            for x, y, z in step_vertices
            if x > max_step_x - 1.1 and y > max_step_y - 1.1
        ]
        assert first_step_z and last_step_z
        step_z_values = {round(z, 3) for _x, _y, z in step_vertices}
        assert {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0} <= step_z_values, step_z_values
        assert abs(max(last_step_z) - max(first_step_z) - 8.0) < 0.001
        step_settings.invert = True
        step_cloner.update_tag()
        step_cloner.modifiers["Cloner"].node_group.update_tag()
        bpy.context.view_layer.update()
        reversed_step_vertices = _evaluated_vertices(step_cloner)
        min_reversed_x = min(x for x, _y, _z in reversed_step_vertices)
        max_reversed_x = max(x for x, _y, _z in reversed_step_vertices)
        min_reversed_y = min(y for _x, y, _z in reversed_step_vertices)
        max_reversed_y = max(y for _x, y, _z in reversed_step_vertices)
        reversed_first_z = [
            z
            for x, y, z in reversed_step_vertices
            if x < min_reversed_x + 1.1 and y < min_reversed_y + 1.1
        ]
        reversed_last_z = [
            z
            for x, y, z in reversed_step_vertices
            if x > max_reversed_x - 1.1 and y > max_reversed_y - 1.1
        ]
        assert max(reversed_first_z) - max(reversed_last_z) > 7.9

        target_mesh = bpy.data.meshes.new("Target Effector Source Mesh")
        target_mesh.from_pydata([(0.0, 0.0, 1.0)], [], [])
        target_mesh.update()
        target_source = bpy.data.objects.new("Target Effector Source", target_mesh)
        bpy.context.collection.objects.link(target_source)
        bpy.context.view_layer.objects.active = target_source
        target_source.select_set(True)
        target_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=target_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        assert target_result == {"FINISHED"}, target_result
        target_cloner = bpy.context.object
        target_add_result = bpy.ops.clone_fields.add_target_effector("EXEC_DEFAULT")
        assert target_add_result == {"FINISHED"}, target_add_result
        target_effector = target_cloner.clone_fields_cloner.effector_object
        assert target_effector.name.startswith("Target Effector [None]")
        assert target_effector.get(props.PROP_EFFECTOR_TYPE) == "TARGET"
        target_settings = target_effector.clone_fields_effector
        assert target_settings.type == eff.EFFECTOR_TYPE_TARGET
        assert target_settings.shape == eff.FIELD_SHAPE_NONE
        assert target_settings.target_axis == "Z"
        assert target_settings.target_up_axis == "Y"
        target_effector.location = (3.0, 0.0, 0.0)
        target_modifier = target_cloner.modifiers["Cloner"]
        target_cloner.update_tag()
        target_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        target_vertices = _evaluated_vertices(target_cloner)
        assert _has_vertex_near(target_vertices, (1.0, 0.0, 0.0), tolerance=0.001)
        target_settings.strength = 50
        target_cloner.update_tag()
        bpy.context.view_layer.update()
        partial_target_vertices = _evaluated_vertices(target_cloner)
        expected_partial = Vector((1.0, 0.0, 1.0)).normalized()
        assert _has_vertex_near(
            partial_target_vertices,
            tuple(expected_partial),
            tolerance=0.001,
        )
        target_settings.strength = 100
        target_effector.location = (0.0, 3.0, 0.0)
        target_cloner.update_tag()
        bpy.context.view_layer.update()
        moved_target_vertices = _evaluated_vertices(target_cloner)
        assert _has_vertex_near(moved_target_vertices, (0.0, 1.0, 0.0), tolerance=0.001)
        target_settings.shape = eff.FIELD_SHAPE_SPHERE
        target_settings.radius = 0.25
        target_cloner.update_tag()
        bpy.context.view_layer.update()
        bounded_target_vertices = _evaluated_vertices(target_cloner)
        assert _has_vertex_near(bounded_target_vertices, (0.0, 0.0, 1.0), tolerance=0.001)

        target_camera_data = bpy.data.cameras.new("Target Effector Camera Data")
        target_camera = bpy.data.objects.new("Target Effector Camera", target_camera_data)
        bpy.context.collection.objects.link(target_camera)
        target_camera.location = (3.0, 0.0, 0.0)
        target_effector.location = (0.0, 0.0, 0.0)
        target_settings.target_object = target_camera
        target_cloner.update_tag()
        bpy.context.view_layer.update()
        camera_target_vertices = _evaluated_vertices(target_cloner)
        assert _has_vertex_near(camera_target_vertices, (1.0, 0.0, 0.0), tolerance=0.001)

        target_camera.location = (0.0, 3.0, 0.0)
        bpy.context.view_layer.update()
        moved_camera_target_vertices = _evaluated_vertices(target_cloner)
        assert _has_vertex_near(
            moved_camera_target_vertices,
            (0.0, 1.0, 0.0),
            tolerance=0.001,
        )

        target_settings.target_object = None
        target_effector.location = (0.0, 3.0, 0.0)
        target_settings.shape = eff.FIELD_SHAPE_NONE
        target_settings.target_axis = "X"
        target_cloner.update_tag()
        bpy.context.view_layer.update()
        target_axis_vertices = _evaluated_vertices(target_cloner)
        assert _has_vertex_near(
            target_axis_vertices,
            (1.0, 0.0, 0.0),
            tolerance=0.001,
        ), target_axis_vertices

        radial_target_mesh = bpy.data.meshes.new("Radial Target Source Mesh")
        radial_target_mesh.from_pydata([(0.0, 0.0, 1.0)], [], [])
        radial_target_mesh.update()
        radial_target_source = bpy.data.objects.new("Radial Target Source", radial_target_mesh)
        bpy.context.collection.objects.link(radial_target_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=radial_target_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        radial_target_cloner = bpy.context.object
        radial_target_cloner.clone_fields_cloner.distribution_mode = "RADIAL"
        radial_target_cloner.clone_fields_cloner.radial_count = 1
        radial_target_cloner.clone_fields_cloner.radial_radius = 2.0
        bpy.ops.clone_fields.add_target_effector("EXEC_DEFAULT")
        radial_target_effector = radial_target_cloner.clone_fields_cloner.effector_object
        radial_target_effector.location = (0.0, 0.0, 3.0)
        radial_target_cloner.update_tag()
        radial_target_cloner.modifiers["Cloner"].node_group.update_tag()
        bpy.context.view_layer.update()
        radial_target_vertices = _evaluated_vertices(radial_target_cloner)
        expected_radial_target = Vector((-2.0, 0.0, 3.0)).normalized() + Vector((2.0, 0.0, 0.0))
        assert _has_vertex_near(
            radial_target_vertices,
            tuple(expected_radial_target),
            tolerance=0.001,
        )

        bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
        shader_source = bpy.context.object
        shader_source.name = "Shader Effector Source"
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=shader_source.name,
            count_x=3,
            count_y=1,
            count_z=1,
            spacing_x=2.0,
        )
        shader_cloner = bpy.context.object
        shader_add_result = bpy.ops.clone_fields.add_shader_effector("EXEC_DEFAULT")
        assert shader_add_result == {"FINISHED"}, shader_add_result
        shader_effector = shader_cloner.clone_fields_cloner.effector_object
        shader_settings = shader_effector.clone_fields_effector
        assert shader_settings.type == eff.EFFECTOR_TYPE_SHADER
        assert shader_settings.shape == eff.FIELD_SHAPE_NONE
        assert shader_effector.empty_display_type == "PLAIN_AXES"

        shader_image = bpy.data.images.new("Shader Test", width=2, height=1)
        shader_image.pixels = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        shader_image.update()
        shader_settings.shader_width = 6.0
        shader_settings.shader_image = shader_image
        assert abs(shader_settings.shader_height - 3.0) < 0.001
        assert shader_effector.data == shader_image
        assert shader_effector.empty_display_type == "PLAIN_AXES"
        shader_settings.position_x = 0.0
        shader_settings.position_y = 0.0
        shader_settings.position_z = 2.0
        shader_cloner.update_tag()
        bpy.context.view_layer.update()
        shader_modifier = shader_cloner.modifiers["Cloner"]
        shader_image_id = inputs.get_modifier_input_identifier(
            shader_modifier,
            props.SOCKET_EFFECTOR_SHADER_IMAGE,
        )
        assert shader_image_id is not None
        assert shader_modifier[shader_image_id] == shader_image
        shader_vertices = _evaluated_vertices(shader_cloner)
        left_z = [z for x, _y, z in shader_vertices if x < -1.0]
        right_z = [z for x, _y, z in shader_vertices if x > 1.0]
        assert left_z and right_z
        assert max(right_z) - max(left_z) > 1.0, (left_z, right_z)
        shader_bounds = _evaluated_bounds_size(shader_cloner)
        assert shader_bounds[2] > 2.5, shader_bounds

        shader_settings.invert = True
        shader_cloner.update_tag()
        bpy.context.view_layer.update()
        inverted_shader_vertices = _evaluated_vertices(shader_cloner)
        inverted_left_z = [z for x, _y, z in inverted_shader_vertices if x < -1.0]
        inverted_right_z = [z for x, _y, z in inverted_shader_vertices if x > 1.0]
        assert inverted_left_z and inverted_right_z
        assert max(inverted_left_z) - max(inverted_right_z) > 1.0, (
            inverted_left_z,
            inverted_right_z,
        )
        shader_settings.invert = False

        shader_settings.shader_preserve_aspect = True
        shader_settings.shader_height = 4.0
        assert abs(shader_settings.shader_width - 8.0) < 0.001
        shader_settings.shader_fit_mode = "COVER"
        fit_result = bpy.ops.clone_fields.fit_shader_to_grid("EXEC_DEFAULT")
        assert fit_result == {"FINISHED"}, fit_result
        assert abs(shader_settings.shader_width - 6.0) < 0.001
        assert abs(shader_settings.shader_height - 3.0) < 0.001

        shader_settings.shader_fit_mode = "CONTAIN"
        assert abs(shader_settings.shader_width - 4.0) < 0.001
        assert abs(shader_settings.shader_height - 2.0) < 0.001

        shader_settings.shader_preserve_aspect = False
        shader_settings.shader_height = 3.0
        assert tuple(shader_effector.scale) == (1.0, 1.0, 1.0)
        fit_result = bpy.ops.clone_fields.fit_shader_to_grid("EXEC_DEFAULT")
        assert fit_result == {"FINISHED"}, fit_result
        assert abs(shader_settings.shader_width - 6.0) < 0.001
        assert abs(shader_settings.shader_height - 2.0) < 0.001
        assert tuple(shader_effector.scale) == (1.0, 1.0, 1.0)

        shader_settings.shader_tiles_x = 2
        shader_settings.shader_tiles_y = 1
        shader_cloner.update_tag()
        bpy.context.view_layer.update()
        tiled_shader_vertices = _evaluated_vertices(shader_cloner)
        assert tiled_shader_vertices

        shader_settings.type = eff.EFFECTOR_TYPE_BASIC
        shader_settings.shape = eff.FIELD_SHAPE_CUBE
        shader_settings.box_uniform = False
        shader_settings.box_x = 8.0
        shader_settings.box_y = 2.0
        shader_settings.box_z = 4.0
        shader_settings.falloff = 0
        shader_settings.use_position = True
        shader_settings.position_z = 1.0
        shader_cloner.update_tag()
        bpy.context.view_layer.update()
        rectangular_box_bounds = _evaluated_bounds_size(shader_cloner)
        assert rectangular_box_bounds[2] > 1.5, rectangular_box_bounds
        shader_settings.box_uniform = True
        shader_settings.box_y = 5.0
        assert shader_settings.box_x == 5.0
        assert shader_settings.box_y == 5.0
        assert shader_settings.box_z == 5.0

        bpy.ops.object.select_all(action="DESELECT")
        effector_cloner.select_set(True)
        bpy.context.view_layer.objects.active = effector_cloner

        bpy.ops.mesh.primitive_cube_add(location=(14.0, 0.0, 0.0))
        shared_source = bpy.context.object
        shared_source.name = "Shared Effector Source"
        shared_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=shared_source.name,
            count_x=2,
            count_y=1,
            count_z=1,
        )
        assert shared_result == {"FINISHED"}, shared_result
        shared_cloner = bpy.context.object
        link_result = bpy.ops.clone_fields.link_existing_effector(
            "EXEC_DEFAULT",
            effector_object_name=plain_effector.name,
        )
        assert link_result == {"FINISHED"}, link_result
        assert shared_cloner.clone_fields_cloner.effector_object == plain_effector
        shared_modifier = shared_cloner.modifiers["Cloner"]
        shared_effector_radius_id = _modifier_input_id(
            inputs,
            shared_modifier,
            props.SOCKET_EFFECTOR_RADIUS,
        )
        plain_effector_settings.radius = 2.25
        assert abs(effector_modifier[effector_radius_id] - 2.25) < 0.0001
        assert abs(shared_modifier[shared_effector_radius_id] - 2.25) < 0.0001
        unlink_shared_result = bpy.ops.clone_fields.delete_effector("EXEC_DEFAULT", slot_index=0)
        assert unlink_shared_result == {"FINISHED"}, unlink_shared_result
        assert plain_effector.name in bpy.data.objects
        assert effector_cloner.clone_fields_cloner.effector_object == plain_effector
        bpy.ops.object.select_all(action="DESELECT")
        effector_cloner.select_set(True)
        bpy.context.view_layer.objects.active = effector_cloner

        plain_effector_settings.radius = 1.0
        plain_effector_settings.use_position = False
        plain_effector_settings.use_scale = True
        plain_effector_settings.scale_y = 2.0
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        scaled_effector_bounds = _evaluated_bounds_size(effector_cloner)
        assert scaled_effector_bounds[1] > base_effector_bounds[1]
        scaled_vertices = _evaluated_vertices(effector_cloner)
        center_y = _max_abs_axis_for_vertices(
            scaled_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[0]) < 1.25,
        )
        outside_y = _max_abs_axis_for_vertices(
            scaled_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[0]) > 1.25,
        )
        assert center_y > outside_y

        plain_effector_settings.invert = True
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        inverted_vertices = _evaluated_vertices(effector_cloner)
        inverted_center_y = _max_abs_axis_for_vertices(
            inverted_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[0]) < 1.25,
        )
        inverted_outside_y = _max_abs_axis_for_vertices(
            inverted_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[0]) > 1.25,
        )
        assert inverted_outside_y > inverted_center_y
        plain_effector_settings.invert = False

        effector_cloner.clone_fields_cloner.count_x = 2
        effector_cloner.clone_fields_cloner.count_y = 2
        effector_cloner.clone_fields_cloner.count_z = 1
        effector_cloner.clone_fields_cloner.spacing_x = 2.8
        effector_cloner.clone_fields_cloner.spacing_y = 2.8
        plain_effector_settings.radius = 1.5
        plain_effector_settings.falloff = 100
        plain_effector_settings.use_scale = True
        plain_effector_settings.scale_y = 2.0
        plain_effector_settings.shape = eff.FIELD_SHAPE_SPHERE
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        spherical_field_bounds = _evaluated_bounds_size(effector_cloner)

        plain_effector_settings.shape = eff.FIELD_SHAPE_CUBE
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        cubic_field_bounds = _evaluated_bounds_size(effector_cloner)
        assert plain_effector.name.startswith("Basic Effector [Cubic]")
        assert plain_effector.empty_display_type == "CUBE"
        assert plain_effector.get(props.PROP_EFFECTOR_SHAPE) == "CUBE"
        assert effector_modifier[effector_field_id] == 1
        assert cubic_field_bounds[1] > spherical_field_bounds[1] + 1.0
        plain_effector_settings.shape = eff.FIELD_SHAPE_SPHERE

        effector_cloner.clone_fields_cloner.count_x = 1
        effector_cloner.clone_fields_cloner.count_y = 1
        effector_cloner.clone_fields_cloner.count_z = 3
        effector_cloner.clone_fields_cloner.spacing_z = 2.0
        plain_effector_settings.radius = 0.75
        plain_effector_settings.height = 5.0
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        small_sphere_vertices = _evaluated_vertices(effector_cloner)
        small_sphere_outer_y = _max_abs_axis_for_vertices(
            small_sphere_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[2]) > 1.5,
        )

        plain_effector_settings.shape = eff.FIELD_SHAPE_CYLINDER
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        cylinder_vertices = _evaluated_vertices(effector_cloner)
        cylinder_outer_y = _max_abs_axis_for_vertices(
            cylinder_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[2]) > 1.5,
        )
        assert plain_effector.name.startswith("Basic Effector [Cylindrical]")
        assert plain_effector.empty_display_type == "CIRCLE"
        assert plain_effector.get(props.PROP_EFFECTOR_SHAPE) == "CYLINDER"
        assert effector_modifier[effector_field_id] == 2
        assert cylinder_outer_y > small_sphere_outer_y + 0.2
        plain_effector_settings.shape = eff.FIELD_SHAPE_SPHERE

        effector_cloner.clone_fields_cloner.count_x = 3
        effector_cloner.clone_fields_cloner.count_y = 1
        effector_cloner.clone_fields_cloner.count_z = 1
        effector_cloner.clone_fields_cloner.spacing_x = 2.0
        plain_effector_settings.length = 5.0
        plain_effector_settings.radius = 0.75
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        small_sphere_vertices = _evaluated_vertices(effector_cloner)
        small_sphere_outer_y = _max_abs_axis_for_vertices(
            small_sphere_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[0]) > 1.5,
        )

        plain_effector_settings.shape = eff.FIELD_SHAPE_LINEAR
        effector_cloner.update_tag()
        effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        linear_vertices = _evaluated_vertices(effector_cloner)
        linear_outer_y = _max_abs_axis_for_vertices(
            linear_vertices,
            axis=1,
            predicate=lambda vertex: abs(vertex[0]) > 1.5,
        )
        assert plain_effector.name.startswith("Basic Effector [Linear]")
        assert plain_effector.empty_display_type == "ARROWS"
        assert plain_effector.get(props.PROP_EFFECTOR_SHAPE) == "LINEAR"
        assert effector_modifier[effector_field_id] == 3
        assert linear_outer_y > small_sphere_outer_y + 0.2
        plain_effector_settings.shape = eff.FIELD_SHAPE_SPHERE

        bpy.ops.object.select_all(action="DESELECT")
        effector_cloner.select_set(True)
        bpy.context.view_layer.objects.active = effector_cloner
        second_effector_result = bpy.ops.clone_fields.add_plain_effector("EXEC_DEFAULT")
        assert second_effector_result == {"FINISHED"}, second_effector_result
        second_plain_effector = effector_cloner.clone_fields_cloner.effector2_object
        assert effector_cloner.clone_fields_cloner.effector2_object == second_plain_effector
        assert effector_cloner.clone_fields_cloner.effector_object == plain_effector
        select_result = bpy.ops.clone_fields.select_plain_effector(
            "EXEC_DEFAULT",
            slot_index=1,
        )
        assert select_result == {"FINISHED"}, select_result
        assert effector_cloner.clone_fields_cloner.selected_effector_slot == 1
        assert effector_cloner == bpy.context.view_layer.objects.active
        assert effector_cloner.select_get()
        assert not second_plain_effector.select_get()
        select_object_result = bpy.ops.clone_fields.select_effector_object(
            "EXEC_DEFAULT",
            slot_index=1,
        )
        assert select_object_result == {"FINISHED"}, select_object_result
        assert second_plain_effector == bpy.context.view_layer.objects.active
        assert second_plain_effector.select_get()
        assert not effector_cloner.select_get()
        bpy.ops.object.select_all(action="DESELECT")
        effector_cloner.select_set(True)
        bpy.context.view_layer.objects.active = effector_cloner
        select_result = bpy.ops.clone_fields.select_plain_effector(
            "EXEC_DEFAULT",
            slot_index=1,
        )
        assert select_result == {"FINISHED"}, select_result
        assert effector_cloner == bpy.context.view_layer.objects.active
        assert effector_cloner.select_get()
        assert not second_plain_effector.select_get()
        bpy.context.view_layer.objects.active = effector_cloner
        move_result = bpy.ops.clone_fields.move_plain_effector(
            "EXEC_DEFAULT",
            slot_index=1,
            direction=-1,
        )
        assert move_result == {"FINISHED"}, move_result
        assert effector_cloner.clone_fields_cloner.effector_object == second_plain_effector
        assert effector_cloner.clone_fields_cloner.effector2_object == plain_effector
        assert effector_cloner.clone_fields_cloner.selected_effector_slot == 0
        deleted_effector_name = second_plain_effector.name
        delete_result = bpy.ops.clone_fields.delete_effector("EXEC_DEFAULT", slot_index=0)
        assert delete_result == {"FINISHED"}, delete_result
        assert deleted_effector_name not in bpy.data.objects
        assert effector_cloner.clone_fields_cloner.effector_object == plain_effector
        assert effector_cloner.clone_fields_cloner.effector2_object is None
        assert effector_cloner.clone_fields_cloner.selected_effector_slot == 0
        assert effector_cloner == bpy.context.view_layer.objects.active

        rotation_stack_mesh = bpy.data.meshes.new("Effector Rotation Stack Mesh")
        rotation_stack_mesh.from_pydata(
            [(1.0, 0.0, 0.0), (0.0, 0.25, 0.0), (0.0, 0.0, 0.25)],
            [],
            [(0, 1, 2)],
        )
        rotation_stack_mesh.update()
        rotation_stack_source = bpy.data.objects.new(
            "Effector Rotation Stack Source",
            rotation_stack_mesh,
        )
        bpy.context.collection.objects.link(rotation_stack_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=rotation_stack_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        rotation_stack_cloner = bpy.context.object
        bpy.ops.clone_fields.add_plain_effector("EXEC_DEFAULT")
        bpy.context.view_layer.objects.active = rotation_stack_cloner
        bpy.ops.clone_fields.add_plain_effector("EXEC_DEFAULT")
        rotation_stack_settings = rotation_stack_cloner.clone_fields_cloner
        rotation_stack_settings.effector_enabled = False
        rotation_stack_effector_settings = (
            rotation_stack_settings.effector2_object.clone_fields_effector
        )
        rotation_stack_effector_settings.use_position = False
        rotation_stack_effector_settings.use_rotation = True
        rotation_stack_effector_settings.rotation_y = math.radians(360.0)
        rotation_stack_effector_settings.rotation_z = math.radians(7200.0)
        assert math.isclose(
            rotation_stack_effector_settings.rotation_z,
            math.radians(7200.0),
            abs_tol=0.0001,
        )
        rotation_stack_effector_settings.radius = 10.0
        rotation_stack_effector_settings.falloff = 100
        rotation_stack_modifier = rotation_stack_cloner.modifiers["Cloner"]
        for strength in (0, 1, 37, 73, 100):
            rotation_stack_effector_settings.strength = strength
            rotation_stack_cloner.update_tag()
            bpy.context.view_layer.update()
            rotation_stack_vertices = _evaluated_vertices(rotation_stack_cloner)
            weight = strength / 100.0
            expected_rotation = Euler(
                (
                    rotation_stack_effector_settings.rotation_x * weight,
                    rotation_stack_effector_settings.rotation_y * weight,
                    rotation_stack_effector_settings.rotation_z * weight,
                ),
                "XYZ",
            ).to_quaternion()
            expected_vertex = expected_rotation @ Vector((1.0, 0.0, 0.0))
            assert _has_vertex_near(
                rotation_stack_vertices,
                tuple(expected_vertex),
                tolerance=0.001,
            ), (strength, expected_vertex, rotation_stack_vertices)

        bpy.ops.mesh.primitive_cube_add(location=(6.0, 0.0, 0.0))
        second_source = bpy.context.object
        second_source.name = "Convert Source"

        second_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=second_source.name,
        )
        assert second_result == {"FINISHED"}, second_result
        second_cloner = bpy.context.object
        assert second_cloner.name.startswith("Cloner")
        assert second_cloner.data.name.startswith("Clone Fields Output")
        assert second_cloner.display_type == "TEXTURED"
        assert second_source.parent == second_cloner
        assert _evaluated_instance_count() > 0

        bpy.ops.mesh.primitive_cube_add(location=(10.0, 0.0, 0.0))
        nested_base_source = bpy.context.object
        nested_base_source.name = "Nested Base Source"
        nested_base_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=nested_base_source.name,
        )
        assert nested_base_result == {"FINISHED"}, nested_base_result
        nested_source_cloner = bpy.context.object

        nested_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=nested_source_cloner.name,
            count_x=3,
            count_y=1,
            count_z=1,
            spacing_x=2.0,
        )
        assert nested_result == {"FINISHED"}, nested_result
        nested_cloner = bpy.context.object
        assert nested_source_cloner.parent == nested_cloner
        assert nested_cloner.clone_fields_cloner.source_object == nested_source_cloner
        nested_modifier = nested_cloner.modifiers["Cloner"]
        nested_source_id = inputs.get_modifier_input_identifier(
            nested_modifier,
            props.SOCKET_SOURCE_OBJECT,
        )
        assert nested_source_id is not None
        assert nested_modifier[nested_source_id] == nested_source_cloner
        nested_count_x_id = inputs.get_modifier_input_identifier(
            nested_modifier,
            props.SOCKET_COUNT_X,
        )
        assert nested_count_x_id is not None
        assert nested_modifier[nested_count_x_id] == 3
        nested_vertex_count = _evaluated_vertex_count(nested_cloner)
        assert nested_vertex_count == len(nested_base_source.data.vertices) * 27, nested_vertex_count
        nested_cloner.clone_fields_cloner.source_object = nested_cloner
        assert nested_cloner.clone_fields_cloner.source_object == nested_source_cloner
        assert sources.nested_cloner_depth(nested_cloner) == 2

        bpy.context.view_layer.objects.active = cloner
        cloner.clone_fields_cloner.count_x = 5
        assert modifier[count_x_id] == 5

        cloner.clone_fields_cloner.source_object = cloner
        assert cloner.clone_fields_cloner.source_object == source
        assert modifier[source_id] == source

        bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0.0, 4.0, 0.0))
        boolean_target = bpy.context.object
        boolean_modifier = boolean_target.modifiers.new("Boolean Clone Cut", "BOOLEAN")
        boolean_modifier.operation = "DIFFERENCE"
        boolean_modifier.object = cloner
        assert _evaluated_vertex_count(boolean_target) > 8

        bpy.context.view_layer.objects.active = second_cloner
        second_cloner.select_set(True)
        bpy.ops.object.convert(target="MESH")
        converted = bpy.context.object
        assert converted.type == "MESH"
        assert len(converted.data.vertices) > 0
        assert len(converted.modifiers) == 0

        mesh = bpy.data.meshes.new("Local Rotation Probe Mesh")
        mesh.from_pydata(
            [(1.0, 0.0, 0.0), (0.0, 0.25, 0.0), (0.0, 0.0, 0.25)],
            [],
            [(0, 1, 2)],
        )
        mesh.update()
        rotation_probe = bpy.data.objects.new("Local Rotation Probe", mesh)
        bpy.context.collection.objects.link(rotation_probe)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=rotation_probe.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        rotation_probe_cloner = bpy.context.object
        rotation_probe_cloner.clone_fields_cloner.source_rotation_y = 1.5707963267948966
        rotation_probe_cloner.clone_fields_cloner.source_rotation_z = 1.5707963267948966
        rotation_probe_vertices = _evaluated_vertices(rotation_probe_cloner)
        assert _has_vertex_near(rotation_probe_vertices, (0.0, 1.0, 0.0))

        radial_point_mesh = bpy.data.meshes.new("Radial Point Mesh")
        radial_point_mesh.from_pydata([(0.0, 0.0, 0.0)], [], [])
        radial_point_mesh.update()
        radial_point_source = bpy.data.objects.new("Radial Point Source", radial_point_mesh)
        bpy.context.collection.objects.link(radial_point_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=radial_point_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        radial_point_cloner = bpy.context.object
        radial_point_modifier = radial_point_cloner.modifiers["Cloner"]
        radial_point_mode_id = _modifier_input_id(
            inputs,
            radial_point_modifier,
            props.SOCKET_DISTRIBUTION_MODE,
        )
        radial_point_count_id = _modifier_input_id(
            inputs,
            radial_point_modifier,
            props.SOCKET_RADIAL_COUNT,
        )
        radial_point_radius_id = _modifier_input_id(
            inputs,
            radial_point_modifier,
            props.SOCKET_RADIAL_RADIUS,
        )
        radial_point_arc_id = _modifier_input_id(
            inputs,
            radial_point_modifier,
            props.SOCKET_RADIAL_ARC,
        )
        radial_point_modifier[radial_point_count_id] = 8
        radial_point_modifier[radial_point_radius_id] = 2.0
        radial_point_modifier[radial_point_arc_id] = 6.283185307179586
        _set_modifier_mode(radial_point_cloner, radial_point_modifier, radial_point_mode_id, 2)
        radial_point_vertices = _evaluated_vertices(radial_point_cloner)
        assert len(radial_point_vertices) == 8
        assert _min_vertex_distance(radial_point_vertices) > 0.25
        assert _has_vertex_near(radial_point_vertices, (2.0, 0.0, 0.0))
        assert _has_vertex_near(radial_point_vertices, (1.41421356, 1.41421356, 0.0))

        radial_point_modifier[radial_point_arc_id] = 5.235987755982989
        radial_point_cloner.update_tag()
        radial_point_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        radial_point_vertices = _evaluated_vertices(radial_point_cloner)
        assert len(radial_point_vertices) == 8
        assert _min_vertex_distance(radial_point_vertices) > 0.25
        assert _has_vertex_near(radial_point_vertices, (-0.261052, -1.98289, 0.0), 0.0001)

        radial_rotation_mesh = bpy.data.meshes.new("Radial Rotation Mesh")
        radial_rotation_mesh.from_pydata([(0.0, 0.5, 0.0)], [], [])
        radial_rotation_mesh.update()
        radial_rotation_source = bpy.data.objects.new(
            "Radial Rotation Source",
            radial_rotation_mesh,
        )
        bpy.context.collection.objects.link(radial_rotation_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=radial_rotation_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        radial_rotation_cloner = bpy.context.object
        radial_rotation_modifier = radial_rotation_cloner.modifiers["Cloner"]
        radial_rotation_mode_id = _modifier_input_id(
            inputs,
            radial_rotation_modifier,
            props.SOCKET_DISTRIBUTION_MODE,
        )
        radial_rotation_count_id = _modifier_input_id(
            inputs,
            radial_rotation_modifier,
            props.SOCKET_RADIAL_COUNT,
        )
        radial_rotation_radius_id = _modifier_input_id(
            inputs,
            radial_rotation_modifier,
            props.SOCKET_RADIAL_RADIUS,
        )
        radial_rotation_arc_id = _modifier_input_id(
            inputs,
            radial_rotation_modifier,
            props.SOCKET_RADIAL_ARC,
        )
        radial_rotation_align_id = _modifier_input_id(
            inputs,
            radial_rotation_modifier,
            props.SOCKET_RADIAL_ALIGN,
        )
        radial_rotation_modifier[radial_rotation_count_id] = 4
        radial_rotation_modifier[radial_rotation_radius_id] = 2.0
        radial_rotation_modifier[radial_rotation_arc_id] = 6.283185307179586
        radial_rotation_modifier[radial_rotation_align_id] = True
        _set_modifier_mode(
            radial_rotation_cloner,
            radial_rotation_modifier,
            radial_rotation_mode_id,
            2,
        )
        radial_rotation_vertices = _evaluated_vertices(radial_rotation_cloner)
        assert _has_vertex_near(radial_rotation_vertices, (-0.5, 2.0, 0.0))

        radial_effector_mesh = bpy.data.meshes.new("Radial Effector Rotation Mesh")
        radial_effector_mesh.from_pydata(
            [(1.0, 0.0, 0.0), (0.0, 0.25, 0.0), (0.0, 0.0, 0.25)],
            [],
            [(0, 1, 2)],
        )
        radial_effector_mesh.update()
        radial_effector_source = bpy.data.objects.new(
            "Radial Effector Rotation Source",
            radial_effector_mesh,
        )
        bpy.context.collection.objects.link(radial_effector_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=radial_effector_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        radial_effector_cloner = bpy.context.object
        radial_effector_modifier = radial_effector_cloner.modifiers["Cloner"]
        radial_effector_mode_id = _modifier_input_id(
            inputs,
            radial_effector_modifier,
            props.SOCKET_DISTRIBUTION_MODE,
        )
        radial_effector_count_id = _modifier_input_id(
            inputs,
            radial_effector_modifier,
            props.SOCKET_RADIAL_COUNT,
        )
        radial_effector_radius_id = _modifier_input_id(
            inputs,
            radial_effector_modifier,
            props.SOCKET_RADIAL_RADIUS,
        )
        radial_effector_modifier[radial_effector_count_id] = 1
        radial_effector_modifier[radial_effector_radius_id] = 0.0
        _set_modifier_mode(
            radial_effector_cloner,
            radial_effector_modifier,
            radial_effector_mode_id,
            2,
        )
        bpy.ops.clone_fields.add_plain_effector("EXEC_DEFAULT")
        radial_effector_settings = radial_effector_cloner.clone_fields_cloner
        radial_basic_effector_settings = (
            radial_effector_settings.effector_object.clone_fields_effector
        )
        radial_basic_effector_settings.use_position = False
        radial_basic_effector_settings.use_rotation = True
        radial_basic_effector_settings.rotation_z = 1.5707963267948966
        radial_basic_effector_settings.radius = 10.0
        radial_basic_effector_settings.falloff = 100
        radial_effector_cloner.update_tag()
        radial_effector_modifier.node_group.update_tag()
        bpy.context.view_layer.update()
        radial_effector_vertices = _evaluated_vertices(radial_effector_cloner)
        assert _has_vertex_near(radial_effector_vertices, (0.0, 1.0, 0.0))

        first_mesh = bpy.data.meshes.new("Alternating First Mesh")
        first_mesh.from_pydata([(0.0, 0.0, 0.0)], [], [])
        first_mesh.update()
        first_source = bpy.data.objects.new("Alternating First", first_mesh)
        bpy.context.collection.objects.link(first_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=first_source.name,
            count_x=1,
            count_y=1,
            count_z=1,
        )
        alternating_cloner = bpy.context.object
        alternating_modifier = alternating_cloner.modifiers["Cloner"]
        alternating_mode_id = _modifier_input_id(
            inputs,
            alternating_modifier,
            props.SOCKET_DISTRIBUTION_MODE,
        )
        alternating_linear_count_id = _modifier_input_id(
            inputs,
            alternating_modifier,
            props.SOCKET_LINEAR_COUNT,
        )
        alternating_source_count_id = _modifier_input_id(
            inputs,
            alternating_modifier,
            props.SOCKET_SOURCE_COUNT,
        )
        alternating_modifier[alternating_linear_count_id] = 4
        _set_modifier_mode(
            alternating_cloner,
            alternating_modifier,
            alternating_mode_id,
            1,
        )
        assert alternating_modifier[alternating_source_count_id] == 1
        assert _evaluated_vertex_count(alternating_cloner) == 4

        second_mesh = bpy.data.meshes.new("Alternating Second Mesh")
        second_mesh.from_pydata(
            [(0.0, 0.0, 0.0), (0.25, 0.0, 0.0), (0.0, 0.25, 0.0)],
            [],
            [(0, 1, 2)],
        )
        second_mesh.update()
        second_source = bpy.data.objects.new("Alternating Second", second_mesh)
        bpy.context.collection.objects.link(second_source)
        second_source.parent = alternating_cloner
        sources.sync_all_source_visibility()
        bpy.context.view_layer.update()

        assert alternating_modifier[alternating_source_count_id] == 2
        assert first_source.hide_get()
        assert second_source.hide_get()
        assert _evaluated_vertex_count(alternating_cloner) == 8

        grid_first_mesh = bpy.data.meshes.new("Grid Alternating First Mesh")
        grid_first_mesh.from_pydata([(0.0, 0.0, 0.0)], [], [])
        grid_first_mesh.update()
        grid_first_source = bpy.data.objects.new("Grid Alternating First", grid_first_mesh)
        bpy.context.collection.objects.link(grid_first_source)
        bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=grid_first_source.name,
            count_x=2,
            count_y=2,
            count_z=1,
            spacing_x=2.0,
            spacing_y=2.0,
            spacing_z=2.0,
        )
        grid_alternating_cloner = bpy.context.object
        grid_alternating_modifier = grid_alternating_cloner.modifiers["Cloner"]

        grid_second_mesh = bpy.data.meshes.new("Grid Alternating Second Mesh")
        grid_second_mesh.from_pydata(
            [(0.0, 0.0, 0.0), (0.25, 0.0, 0.0), (0.0, 0.25, 0.0)],
            [],
            [(0, 1, 2)],
        )
        grid_second_mesh.update()
        grid_second_source = bpy.data.objects.new("Grid Alternating Second", grid_second_mesh)
        bpy.context.collection.objects.link(grid_second_source)
        grid_second_source.parent = grid_alternating_cloner
        sources.sync_all_source_visibility()
        bpy.context.view_layer.update()

        grid_vertices = _evaluated_vertices(grid_alternating_cloner)
        assert _has_vertex_near(grid_vertices, (-0.75, -1.0, 0.0))
        assert _has_vertex_near(grid_vertices, (1.25, 1.0, 0.0))
        source_half = guides.source_bounds_half_extents(grid_alternating_cloner)
        assert source_half.x >= 0.25
        assert source_half.y >= 0.25
        bpy.context.view_layer.objects.active = grid_alternating_cloner
        gizmos.apply_handle_offset(grid_alternating_cloner, "X", source_half.x + 3.0)
        assert abs(grid_alternating_cloner.clone_fields_cloner.spacing_x - 6.0) < 0.0001
        grid_alternating_cloner.clone_fields_cloner.distribution_mode = "BRICK"
        grid_alternating_cloner.clone_fields_cloner.count_x = 3
        grid_alternating_cloner.clone_fields_cloner.count_y = 2
        grid_alternating_cloner.clone_fields_cloner.count_z = 1
        grid_alternating_cloner.clone_fields_cloner.spacing_x = 2.0
        grid_alternating_cloner.clone_fields_cloner.brick_row_offset = 0.5
        grid_alternating_cloner.clone_fields_cloner.brick_layer_offset = 0.0
        gizmos.apply_handle_offset(grid_alternating_cloner, "X", source_half.x + 4.5)
        assert abs(grid_alternating_cloner.clone_fields_cloner.spacing_x - 3.0) < 0.0001
        brick_guide_lines = guides._grid_guide_lines(
            grid_alternating_cloner,
            grid_alternating_cloner.clone_fields_cloner,
        )
        assert max(point[0] for point in brick_guide_lines) > 4.7
        x_direction = gizmos._axis_matrix(grid_alternating_cloner, "X").to_3x3() @ Vector((0.0, 0.0, 1.0))
        y_direction = gizmos._axis_matrix(grid_alternating_cloner, "Y").to_3x3() @ Vector((0.0, 0.0, 1.0))
        z_direction = gizmos._axis_matrix(grid_alternating_cloner, "Z").to_3x3() @ Vector((0.0, 0.0, 1.0))
        assert max(abs(x_direction[i] - Vector((1.0, 0.0, 0.0))[i]) for i in range(3)) < 0.0001
        assert max(abs(y_direction[i] - Vector((0.0, 1.0, 0.0))[i]) for i in range(3)) < 0.0001
        assert max(abs(z_direction[i] - Vector((0.0, 0.0, 1.0))[i]) for i in range(3)) < 0.0001

        grid_alternating_cloner.clone_fields_cloner.distribution_mode = "RADIAL"
        radial_radius_before = grid_alternating_cloner.clone_fields_cloner.radial_radius
        gizmos.apply_handle_offset(
            grid_alternating_cloner,
            "R",
            guides.source_bounds_half_extents(grid_alternating_cloner).x + 5.0,
        )
        assert grid_alternating_cloner.clone_fields_cloner.radial_radius != radial_radius_before
        assert abs(grid_alternating_cloner.clone_fields_cloner.radial_radius - 5.0) < 0.0001

        print("CLONE_FIELDS_SMOKE_OK")
    finally:
        addon.unregister()


if __name__ == "__main__":
    main()
