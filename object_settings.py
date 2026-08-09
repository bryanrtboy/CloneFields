"""Object-level settings shown in the Clone Fields cloner panel."""

import bpy
from bpy.props import FloatProperty, IntProperty, PointerProperty

from . import modifier_inputs, properties, source_management


def _sync_source(self, context) -> None:
    obj = self.id_data
    modifier = modifier_inputs.get_cloner_modifier(obj)
    if modifier is None:
        return

    source = self.source_object
    if source is not None and (
        modifier_inputs.is_cloner_object(source)
        or source_management.would_create_cycle(obj, source)
    ):
        current_source = modifier_inputs.get_modifier_input(
            modifier,
            properties.SOCKET_SOURCE_OBJECT,
        )
        self.source_object = current_source if current_source != source else None
        return

    source_management.assign_source(obj, source)


def _sync_count_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_COUNT_X, self.count_x)


def _sync_count_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_COUNT_Y, self.count_y)


def _sync_count_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_COUNT_Z, self.count_z)


def _sync_spacing_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SPACING_X, self.spacing_x)


def _sync_spacing_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SPACING_Y, self.spacing_y)


def _sync_spacing_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SPACING_Z, self.spacing_z)


def _sync_modifier_value(self, socket_name: str, value) -> None:
    modifier = modifier_inputs.get_cloner_modifier(self.id_data)
    if modifier is not None:
        modifier_inputs.set_modifier_input(modifier, socket_name, value)


class CloneFieldsClonerSettings(bpy.types.PropertyGroup):
    source_object: PointerProperty(
        name=properties.SOCKET_SOURCE_OBJECT,
        description="Object to instance across the grid",
        type=bpy.types.Object,
        update=_sync_source,
    )
    count_x: IntProperty(
        name=properties.SOCKET_COUNT_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_COUNT_X],
        min=1,
        update=_sync_count_x,
    )
    count_y: IntProperty(
        name=properties.SOCKET_COUNT_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_COUNT_Y],
        min=1,
        update=_sync_count_y,
    )
    count_z: IntProperty(
        name=properties.SOCKET_COUNT_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_COUNT_Z],
        min=1,
        update=_sync_count_z,
    )
    spacing_x: FloatProperty(
        name=properties.SOCKET_SPACING_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_X],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_spacing_x,
    )
    spacing_y: FloatProperty(
        name=properties.SOCKET_SPACING_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_Y],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_spacing_y,
    )
    spacing_z: FloatProperty(
        name=properties.SOCKET_SPACING_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_Z],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_spacing_z,
    )


classes = (CloneFieldsClonerSettings,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.clone_fields_cloner = PointerProperty(type=CloneFieldsClonerSettings)


def unregister() -> None:
    del bpy.types.Object.clone_fields_cloner
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
