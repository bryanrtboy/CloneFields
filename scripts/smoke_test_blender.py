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
        cloner_collection = bpy.data.collections[cloner[props.PROP_CLONER_COLLECTION]]
        output_collection = bpy.data.collections[cloner[props.PROP_OUTPUT_COLLECTION]]
        source_collection = bpy.data.collections[cloner[props.PROP_SOURCE_COLLECTION]]
        assert output_collection.name in cloner_collection.children
        assert source_collection.name in cloner_collection.children
        assert cloner.name in output_collection.objects
        assert source.name in source_collection.objects
        assert source.parent is None
        assert source.hide_get()
        assert source.hide_render
        assert _evaluated_instance_count() > 0

        modifier = cloner.modifiers["Cloner"]
        assert modifier.type == "NODES"
        assert modifier.node_group is not None
        assert not modifier.node_group.name.startswith("Clone Fields Grid Cloner")
        if hasattr(modifier.node_group, "is_modifier"):
            assert not modifier.node_group.is_modifier
        assert len(modifier.node_group.nodes) >= 12

        count_x_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_COUNT_X)
        spacing_z_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_SPACING_Z)
        source_id = inputs.get_modifier_input_identifier(modifier, props.SOCKET_SOURCE_OBJECT)

        assert count_x_id is not None
        assert spacing_z_id is not None
        assert source_id is not None

        assert modifier[count_x_id] == 2
        assert modifier[spacing_z_id] == 2.5
        assert modifier[source_id] == source
        assert _evaluated_vertex_count(cloner) > 0

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
        second_cloner_collection = bpy.data.collections[
            second_cloner[props.PROP_CLONER_COLLECTION]
        ]
        second_output_collection = bpy.data.collections[
            second_cloner[props.PROP_OUTPUT_COLLECTION]
        ]
        second_source_collection = bpy.data.collections[
            second_cloner[props.PROP_SOURCE_COLLECTION]
        ]
        assert second_output_collection.name in second_cloner_collection.children
        assert second_source_collection.name in second_cloner_collection.children
        assert second_cloner.name in second_output_collection.objects
        assert second_source.name in second_source_collection.objects
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

        print("CLONE_FIELDS_SMOKE_OK")
    finally:
        addon.unregister()


if __name__ == "__main__":
    main()
