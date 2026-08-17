"""Cloner creation API.

This module is deliberately UI-agnostic so future distribution modes and
effectors can reuse object/modifier setup while swapping only the builder.
"""

from __future__ import annotations

import bpy
import uuid

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

    initial_values = {
        socket_name: value
        for socket_name, value in properties.GRID_INPUT_DEFAULTS.items()
        if socket_name in modifier_inputs.GRID_SOCKET_NAMES
    }
    initial_values.update(
        {
            properties.SOCKET_COUNT_X: count_x,
            properties.SOCKET_COUNT_Y: count_y,
            properties.SOCKET_COUNT_Z: count_z,
            properties.SOCKET_SPACING_X: spacing_x,
            properties.SOCKET_SPACING_Y: spacing_y,
            properties.SOCKET_SPACING_Z: spacing_z,
        }
    )
    modifier_inputs.set_modifier_inputs(modifier, initial_values)

    cloner[properties.PROP_CLONER_TYPE] = "CLONER"
    cloner[properties.PROP_CLONER_MODE] = "GRID"
    cloner[properties.PROP_CLONER_ID] = uuid.uuid4().hex
    source_management.assign_source(cloner, source_object)
    cloner[properties.PROP_INITIALIZING_CLONER] = True
    try:
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
    finally:
        cloner.pop(properties.PROP_INITIALIZING_CLONER, None)

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
    settings.effector_object = None
    settings.effector_enabled = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_ENABLED
    ]
    settings.effector_invert = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_INVERT
    ]
    settings.effector_strength = properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT
    settings.effector_radius = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_RADIUS
    ]
    settings.effector_falloff = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_FALLOFF
    ]
    settings.effector_use_position = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_POSITION
    ]
    settings.effector_position_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_POSITION_X
    ]
    settings.effector_position_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_POSITION_Y
    ]
    settings.effector_position_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_POSITION_Z
    ]
    settings.effector_use_rotation = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_ROTATION
    ]
    settings.effector_rotation_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_ROTATION_X
    ]
    settings.effector_rotation_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_ROTATION_Y
    ]
    settings.effector_rotation_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_ROTATION_Z
    ]
    settings.effector_use_scale = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_SCALE
    ]
    settings.effector_scale_uniform = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SCALE_UNIFORM
    ]
    settings.effector_scale_absolute = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SCALE_ABSOLUTE
    ]
    settings.effector_scale_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SCALE_X
    ]
    settings.effector_scale_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SCALE_Y
    ]
    settings.effector_scale_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SCALE_Z
    ]
    cloner[properties.PROP_SPACING_MODE_PREVIOUS] = "PER_STEP"
    settings.distribution_mode = "GRID"
    settings.spacing_mode = "PER_STEP"
    settings.count_x = count_x
    settings.count_y = count_y
    settings.count_z = count_z
    settings.spacing_x = spacing_x
    settings.spacing_y = spacing_y
    settings.spacing_z = spacing_z
    settings.linear_count = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_LINEAR_COUNT
    ]
    settings.linear_spacing = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_LINEAR_SPACING
    ]
    settings.linear_direction_x = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_LINEAR_DIRECTION_X
    ]
    settings.linear_direction_y = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_LINEAR_DIRECTION_Y
    ]
    settings.linear_direction_z = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_LINEAR_DIRECTION_Z
    ]
    settings.radial_count = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_RADIAL_COUNT
    ]
    settings.radial_radius = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_RADIAL_RADIUS
    ]
    settings.radial_arc = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_RADIAL_ARC
    ]
    settings.radial_axis = "Z"
    settings.radial_align = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_RADIAL_ALIGN
    ]
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
