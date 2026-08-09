"""Object-level settings shown in the Clone Fields cloner panel."""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty

from . import modifier_inputs, properties, source_management


DISTRIBUTION_MODE_ITEMS = (
    ("GRID", "Grid", "Grid distribution"),
    ("LINEAR", "Linear", "Linear distribution"),
    ("RADIAL", "Radial", "Radial distribution"),
)
DISTRIBUTION_MODE_VALUES = {
    "GRID": 0,
    "LINEAR": 1,
    "RADIAL": 2,
}
RADIAL_AXIS_ITEMS = (
    ("Z", "Z", "Rotate around Z"),
    ("X", "X", "Rotate around X"),
    ("Y", "Y", "Rotate around Y"),
)
RADIAL_AXIS_VALUES = {
    "Z": 0,
    "X": 1,
    "Y": 2,
}


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


def _sync_distribution_mode(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_DISTRIBUTION_MODE,
        DISTRIBUTION_MODE_VALUES[self.distribution_mode],
    )
    self.id_data[properties.PROP_CLONER_MODE] = self.distribution_mode


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


def _sync_linear_count(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_LINEAR_COUNT, self.linear_count)


def _sync_linear_spacing(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_LINEAR_SPACING, self.linear_spacing)


def _sync_linear_direction_x(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_LINEAR_DIRECTION_X,
        self.linear_direction_x,
    )


def _sync_linear_direction_y(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_LINEAR_DIRECTION_Y,
        self.linear_direction_y,
    )


def _sync_linear_direction_z(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_LINEAR_DIRECTION_Z,
        self.linear_direction_z,
    )


def _sync_radial_count(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_RADIAL_COUNT, self.radial_count)


def _sync_radial_radius(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_RADIAL_RADIUS, self.radial_radius)


def _sync_radial_arc(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_RADIAL_ARC, self.radial_arc)


def _sync_radial_axis(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_RADIAL_AXIS,
        RADIAL_AXIS_VALUES[self.radial_axis],
    )


def _sync_radial_align(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_RADIAL_ALIGN,
        self.radial_align,
    )


def _sync_source_position_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_POSITION_X, self.source_position_x)


def _sync_source_position_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_POSITION_Y, self.source_position_y)


def _sync_source_position_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_POSITION_Z, self.source_position_z)


def _sync_source_rotation_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_ROTATION_X, self.source_rotation_x)


def _sync_source_rotation_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_ROTATION_Y, self.source_rotation_y)


def _sync_source_rotation_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_ROTATION_Z, self.source_rotation_z)


def _sync_source_scale_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_SCALE_X, self.source_scale_x)


def _sync_source_scale_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_SCALE_Y, self.source_scale_y)


def _sync_source_scale_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_SOURCE_SCALE_Z, self.source_scale_z)


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
    distribution_mode: EnumProperty(
        name="Mode",
        items=DISTRIBUTION_MODE_ITEMS,
        default="GRID",
        update=_sync_distribution_mode,
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
    linear_count: IntProperty(
        name="Count",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_COUNT],
        min=1,
        update=_sync_linear_count,
    )
    linear_spacing: FloatProperty(
        name="Spacing",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_SPACING],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_linear_spacing,
    )
    linear_direction_x: FloatProperty(
        name=properties.SOCKET_LINEAR_DIRECTION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_DIRECTION_X],
        update=_sync_linear_direction_x,
    )
    linear_direction_y: FloatProperty(
        name=properties.SOCKET_LINEAR_DIRECTION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_DIRECTION_Y],
        update=_sync_linear_direction_y,
    )
    linear_direction_z: FloatProperty(
        name=properties.SOCKET_LINEAR_DIRECTION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_DIRECTION_Z],
        update=_sync_linear_direction_z,
    )
    radial_count: IntProperty(
        name="Count",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_COUNT],
        min=1,
        update=_sync_radial_count,
    )
    radial_radius: FloatProperty(
        name=properties.SOCKET_RADIAL_RADIUS,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_RADIUS],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_radial_radius,
    )
    radial_arc: FloatProperty(
        name=properties.SOCKET_RADIAL_ARC,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_ARC],
        subtype="ANGLE",
        unit="ROTATION",
        update=_sync_radial_arc,
    )
    radial_axis: EnumProperty(
        name="Axis",
        items=RADIAL_AXIS_ITEMS,
        default="Z",
        update=_sync_radial_axis,
    )
    radial_align: BoolProperty(
        name=properties.SOCKET_RADIAL_ALIGN,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_ALIGN],
        update=_sync_radial_align,
    )
    source_position_x: FloatProperty(
        name=properties.SOCKET_SOURCE_POSITION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_POSITION_X],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_source_position_x,
    )
    source_position_y: FloatProperty(
        name=properties.SOCKET_SOURCE_POSITION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_POSITION_Y],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_source_position_y,
    )
    source_position_z: FloatProperty(
        name=properties.SOCKET_SOURCE_POSITION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_POSITION_Z],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_source_position_z,
    )
    source_rotation_x: FloatProperty(
        name=properties.SOCKET_SOURCE_ROTATION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_ROTATION_X],
        subtype="ANGLE",
        unit="ROTATION",
        update=_sync_source_rotation_x,
    )
    source_rotation_y: FloatProperty(
        name=properties.SOCKET_SOURCE_ROTATION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_ROTATION_Y],
        subtype="ANGLE",
        unit="ROTATION",
        update=_sync_source_rotation_y,
    )
    source_rotation_z: FloatProperty(
        name=properties.SOCKET_SOURCE_ROTATION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_ROTATION_Z],
        subtype="ANGLE",
        unit="ROTATION",
        update=_sync_source_rotation_z,
    )
    source_scale_x: FloatProperty(
        name=properties.SOCKET_SOURCE_SCALE_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_SCALE_X],
        min=0.0,
        update=_sync_source_scale_x,
    )
    source_scale_y: FloatProperty(
        name=properties.SOCKET_SOURCE_SCALE_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_SCALE_Y],
        min=0.0,
        update=_sync_source_scale_y,
    )
    source_scale_z: FloatProperty(
        name=properties.SOCKET_SOURCE_SCALE_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_SCALE_Z],
        min=0.0,
        update=_sync_source_scale_z,
    )
    show_source_position: BoolProperty(
        name="Position",
        default=False,
    )
    show_source_rotation: BoolProperty(
        name="Rotation",
        default=True,
    )
    show_source_scale: BoolProperty(
        name="Scale",
        default=True,
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
