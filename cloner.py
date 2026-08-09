"""Cloner creation API.

This module is deliberately UI-agnostic so future distribution modes and
effectors can reuse object/modifier setup while swapping only the builder.
"""

from __future__ import annotations

import bpy

from . import modifier_inputs, properties, source_management
from .geometry_nodes import create_grid_node_group


def create_grid_cloner(
    context: bpy.types.Context,
    *,
    source_object: bpy.types.Object | None,
    count_x: int,
    count_y: int,
    count_z: int,
    spacing_x: float,
    spacing_y: float,
    spacing_z: float,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(properties.CLONER_MESH_NAME)
    cloner = bpy.data.objects.new(properties.CLONER_OBJECT_NAME, mesh)

    context.collection.objects.link(cloner)
    cloner.location = context.scene.cursor.location
    cloner.show_name = True

    modifier = cloner.modifiers.new(
        name=properties.CLONER_MODIFIER_NAME,
        type="NODES",
    )
    modifier.node_group = create_grid_node_group()

    modifier_inputs.set_modifier_input(modifier, properties.SOCKET_COUNT_X, count_x)
    modifier_inputs.set_modifier_input(modifier, properties.SOCKET_COUNT_Y, count_y)
    modifier_inputs.set_modifier_input(modifier, properties.SOCKET_COUNT_Z, count_z)
    modifier_inputs.set_modifier_input(modifier, properties.SOCKET_SPACING_X, spacing_x)
    modifier_inputs.set_modifier_input(modifier, properties.SOCKET_SPACING_Y, spacing_y)
    modifier_inputs.set_modifier_input(modifier, properties.SOCKET_SPACING_Z, spacing_z)
    _set_default_source_transform(modifier)

    cloner[properties.PROP_CLONER_TYPE] = "CLONER"
    cloner[properties.PROP_CLONER_MODE] = "GRID"
    source_management.assign_source(cloner, source_object)
    _set_object_settings(
        cloner,
        source_object=source_object,
        count_x=count_x,
        count_y=count_y,
        count_z=count_z,
        spacing_x=spacing_x,
        spacing_y=spacing_y,
        spacing_z=spacing_z,
    )

    bpy.ops.object.select_all(action="DESELECT")
    cloner.select_set(True)
    context.view_layer.objects.active = cloner

    return cloner


def _set_object_settings(
    cloner: bpy.types.Object,
    *,
    source_object: bpy.types.Object | None,
    count_x: int,
    count_y: int,
    count_z: int,
    spacing_x: float,
    spacing_y: float,
    spacing_z: float,
) -> None:
    if not hasattr(cloner, "clone_fields_cloner"):
        return

    settings = cloner.clone_fields_cloner
    settings.source_object = source_object
    settings.count_x = count_x
    settings.count_y = count_y
    settings.count_z = count_z
    settings.spacing_x = spacing_x
    settings.spacing_y = spacing_y
    settings.spacing_z = spacing_z
    settings.source_position_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_POSITION_X
    ]
    settings.source_position_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_POSITION_Y
    ]
    settings.source_position_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_POSITION_Z
    ]
    settings.source_rotation_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_ROTATION_X
    ]
    settings.source_rotation_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_ROTATION_Y
    ]
    settings.source_rotation_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_ROTATION_Z
    ]
    settings.source_scale_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_SCALE_X
    ]
    settings.source_scale_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_SCALE_Y
    ]
    settings.source_scale_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_SOURCE_SCALE_Z
    ]


def _set_default_source_transform(modifier: bpy.types.NodesModifier) -> None:
    for socket_name in (
        properties.SOCKET_SOURCE_POSITION_X,
        properties.SOCKET_SOURCE_POSITION_Y,
        properties.SOCKET_SOURCE_POSITION_Z,
        properties.SOCKET_SOURCE_ROTATION_X,
        properties.SOCKET_SOURCE_ROTATION_Y,
        properties.SOCKET_SOURCE_ROTATION_Z,
        properties.SOCKET_SOURCE_SCALE_X,
        properties.SOCKET_SOURCE_SCALE_Y,
        properties.SOCKET_SOURCE_SCALE_Z,
    ):
        modifier_inputs.set_modifier_input(
            modifier,
            socket_name,
            properties.GRID_INPUT_DEFAULTS[socket_name],
        )
