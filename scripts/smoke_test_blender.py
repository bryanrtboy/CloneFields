"""Smoke-test Clone Fields inside Blender.

Run with:
    /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/smoke_test_blender.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy


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


def _has_vertex_near(
    vertices: list[tuple[float, float, float]],
    expected: tuple[float, float, float],
    tolerance: float = 0.0001,
) -> bool:
    return any(
        max(abs(vertex[i] - expected[i]) for i in range(3)) < tolerance
        for vertex in vertices
    )


def main() -> None:
    sys.path.insert(0, str(PACKAGE_PARENT))

    addon = importlib.import_module(REPO_ROOT.name)
    addon.register()
    inputs = importlib.import_module(f"{REPO_ROOT.name}.modifier_inputs")
    props = importlib.import_module(f"{REPO_ROOT.name}.properties")
    sources = importlib.import_module(f"{REPO_ROOT.name}.source_management")

    try:
        bpy.ops.mesh.primitive_cube_add()
        source = bpy.context.object
        source.name = "Smoke Source"

        result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=source.name,
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
        assert {"Count", "Spacing", "Source Transform", "Position", "Rotation", "Scale"} <= panel_names
        for item in modifier.node_group.interface.items_tree:
            if (
                getattr(item, "item_type", None) == "SOCKET"
                and getattr(item, "in_out", None) == "INPUT"
                and item.name != props.SOCKET_GEOMETRY
            ):
                assert not item.hide_in_modifier
        assert len(modifier.node_group.nodes) >= 12

        count_x_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_COUNT_X)
        spacing_z_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_SPACING_Z)
        source_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_SOURCE_OBJECT)
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

        assert count_x_id is not None
        assert spacing_z_id is not None
        assert source_id is not None
        assert rotation_z_id is not None
        assert scale_x_id is not None
        assert position_y_id is not None

        assert modifier[count_x_id] == 2
        assert modifier[spacing_z_id] == 2.5
        assert modifier[source_id] == source
        assert _evaluated_vertex_count(cloner) > 0
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

        bpy.ops.mesh.primitive_cube_add(location=(6.0, 0.0, 0.0))
        second_source = bpy.context.object
        second_source.name = "Convert Source"

        second_result = bpy.ops.clone_fields.add_cloner(
            "EXEC_DEFAULT",
            source_object_name=second_source.name,
        )
        assert second_result == {"FINISHED"}, second_result
        second_cloner = bpy.context.object
        assert second_cloner.name == "Cloner.001"
        assert second_cloner.data.name == "Clone Fields Output.001"
        assert second_cloner.display_type == "TEXTURED"
        assert second_source.parent == second_cloner
        assert _evaluated_instance_count() > 0

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

        print("CLONE_FIELDS_SMOKE_OK")
    finally:
        addon.unregister()


if __name__ == "__main__":
    main()
