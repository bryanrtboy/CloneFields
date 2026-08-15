"""Object-level settings shown in the Clone Fields cloner panel."""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from . import effectors, modifier_inputs, properties, source_management


DISTRIBUTION_MODE_ITEMS = (
    ("GRID", "Grid", "Grid distribution"),
    ("LINEAR", "Linear", "Linear distribution"),
    ("RADIAL", "Radial", "Radial distribution"),
    ("OBJECT", "Object", "Place clones on another object"),
    ("BRICK", "Brick", "Stagger rows in a brick pattern"),
)
DISTRIBUTION_MODE_VALUES = {
    "GRID": 0,
    "LINEAR": 1,
    "RADIAL": 2,
    "OBJECT": 3,
    "BRICK": 4,
}
OBJECT_DISTRIBUTION_MODE_ITEMS = (
    ("VERTICES", "Vertices", "Place clones on mesh vertices"),
    ("POLYGONS", "Polygon Centers", "Place clones on mesh polygon centers"),
    ("SPLINE", "Spline Points", "Place clones along a curve or spline"),
    ("SURFACE", "Surface", "Scatter clones across mesh faces"),
)
OBJECT_DISTRIBUTION_MODE_VALUES = {
    "VERTICES": 0,
    "POLYGONS": 1,
    "SPLINE": 2,
    "SURFACE": 3,
}
OBJECT_ALIGNMENT_ITEMS = (
    ("NONE", "None", "Keep the source object's rotation"),
    ("NORMALS", "Normals", "Point the source object's local Z axis along the surface normal"),
    ("CENTER", "Center", "Point the source object's local Z axis toward the distribution object's center"),
    ("TANGENT", "Tangent", "Point the source object's local X axis along the spline"),
)
OBJECT_ALIGNMENT_VALUES = {
    "NONE": 0,
    "NORMALS": 1,
    "CENTER": 2,
    "TANGENT": 3,
}
OBJECT_UP_VECTOR_ITEMS = (
    ("AUTOMATIC", "None", "Prevent banking using an automatically selected reference axis"),
    ("X", "+X", "Use the Cloner's local X axis as the up reference"),
    ("Y", "+Y", "Use the Cloner's local Y axis as the up reference"),
    ("Z", "+Z", "Use the Cloner's local Z axis as the up reference"),
)
OBJECT_UP_VECTOR_VALUES = {
    "AUTOMATIC": 0,
    "X": 1,
    "Y": 2,
    "Z": 3,
}
SPLINE_DISTRIBUTION_ITEMS = (
    ("EVALUATED", "Points", "Place clones at the curve's evaluated points"),
    ("COUNT", "Count", "Place this many clones on every spline"),
    ("STEP", "Step", "Place clones at a fixed distance along every spline"),
    ("EVEN", "Even", "Distribute a total clone count evenly by curve length"),
)
SPLINE_DISTRIBUTION_VALUES = {
    "EVALUATED": 0,
    "COUNT": 1,
    "STEP": 2,
    "EVEN": 3,
}
SURFACE_DISTRIBUTION_ITEMS = (
    ("RANDOM", "Random", "Scatter surface points by density"),
    ("POISSON", "Poisson", "Scatter surface points with minimum distance spacing"),
    ("COUNT", "Count", "Scatter an approximate target number of surface points"),
    ("EVEN", "Even", "Scatter an approximate target count with more even spacing"),
    ("UV_GRID", "UV Grid", "Place clones in a regular grid across the object's UV map"),
)
SURFACE_DISTRIBUTION_VALUES = {
    "RANDOM": 0,
    "POISSON": 1,
    "COUNT": 2,
    "EVEN": 3,
    "UV_GRID": 4,
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
SPACING_MODE_ITEMS = (
    ("PER_STEP", "Per Step", "Distance between neighboring clones"),
    ("ENDPOINT", "Endpoint", "Total distance from first clone to last clone"),
)
SPACING_MODE_VALUES = {
    "PER_STEP": 0,
    "ENDPOINT": 1,
}
SHADER_FIT_MODE_ITEMS = (
    ("COVER", "Cover", "Fill the grid and crop image content outside its bounds"),
    ("CONTAIN", "Contain", "Show the complete image inside the grid bounds"),
)
_CONVERTING_SPACING_MODE = False
_SYNCING_SHADER_ASPECT = False


def is_curve_distribution_object(obj: bpy.types.Object | None) -> bool:
    return bool(obj and obj.type in {"CURVE", "CURVES", "FONT", "GREASEPENCIL"})


def _sync_source(self, context) -> None:
    obj = self.id_data
    if obj.get(properties.PROP_INITIALIZING_CLONER):
        return
    modifier = modifier_inputs.get_cloner_modifier(obj)
    if modifier is None:
        return

    source = self.source_object
    if source is not None and (
        source_management.would_create_cycle(obj, source)
        or source_management.nested_cloner_depth(source)
        > source_management.MAX_NESTED_CLONER_DEPTH
    ):
        current_source = modifier_inputs.get_modifier_input(
            modifier,
            properties.SOCKET_SOURCE_OBJECT,
        )
        self.source_object = current_source if current_source != source else None
        return

    source_management.assign_source(obj, source)


def _sync_effector_object(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_OBJECT, self.effector_object)
    self.effector_enabled = self.effector_object is not None
    if self.effector_object is not None:
        modifier = modifier_inputs.get_cloner_modifier(self.id_data)
        if modifier is not None:
            effectors.sync_effector_slot(self, modifier, 0)


def _sync_effector_shape(self, context) -> None:
    if self.effector_object is not None:
        effectors.configure_effector_object(
            self.effector_object,
            self.effector_shape,
            self.effector_radius,
            self.effector_type,
        )
        effectors.rename_effector_object(
            self.effector_object,
            self.effector_shape,
            self.effector_type,
        )


def _sync_effector_enabled(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_EFFECTOR_ENABLED,
        self.effector_enabled,
    )


def _sync_effector_invert(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_EFFECTOR_INVERT,
        self.effector_invert,
    )


def _sync_effector_strength(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_EFFECTOR_STRENGTH,
        _combined_effector_strength(self, 0, self.effector_strength),
    )


def _sync_effector_radius(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_RADIUS, self.effector_radius)
    if self.effector_object is not None:
        self.effector_object.empty_display_size = self.effector_radius


def _sync_effector_falloff(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_FALLOFF, self.effector_falloff)


def _sync_effector_use_position(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_EFFECTOR_USE_POSITION,
        self.effector_use_position,
    )


def _sync_effector_position_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_POSITION_X, self.effector_position_x)


def _sync_effector_position_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_POSITION_Y, self.effector_position_y)


def _sync_effector_position_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_POSITION_Z, self.effector_position_z)


def _sync_effector_use_rotation(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_EFFECTOR_USE_ROTATION,
        self.effector_use_rotation,
    )


def _sync_effector_rotation_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_ROTATION_X, self.effector_rotation_x)


def _sync_effector_rotation_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_ROTATION_Y, self.effector_rotation_y)


def _sync_effector_rotation_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_ROTATION_Z, self.effector_rotation_z)


def _sync_effector_use_scale(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_EFFECTOR_USE_SCALE,
        self.effector_use_scale,
    )


def _sync_effector_scale_x(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_SCALE_X, self.effector_scale_x)


def _sync_effector_scale_y(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_SCALE_Y, self.effector_scale_y)


def _sync_effector_scale_z(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_EFFECTOR_SCALE_Z, self.effector_scale_z)


def _sync_effector_slot_value(
    self,
    slot_index: int,
    socket_key: str,
    property_name: str,
) -> None:
    value = getattr(self, property_name)
    modifier_value = (
        _combined_effector_strength(self, slot_index, value)
        if socket_key == "strength"
        else effectors.effector_type_value(value)
        if socket_key == "type"
        else effectors.target_axis_value(value)
        if socket_key in {"target_axis", "target_up_axis"}
        else value
    )
    object_property = _effector_slot_property_name(slot_index, "object")
    shape_property = _effector_slot_property_name(slot_index, "shape")
    radius_property = _effector_slot_property_name(slot_index, "radius")
    type_property = _effector_slot_property_name(slot_index, "type")

    if socket_key == "shape":
        effector = getattr(self, object_property)
        if effector is not None:
            effectors.configure_effector_object(
                effector,
                getattr(self, shape_property),
                getattr(self, radius_property),
                getattr(self, type_property),
            )
            effectors.rename_effector_object(
                effector,
                getattr(self, shape_property),
                getattr(self, type_property),
            )
        return

    _sync_modifier_value(
        self,
        properties.EFFECTOR_SOCKET_SETS[slot_index][socket_key],
        modifier_value,
    )
    if socket_key == "target_object":
        _sync_modifier_value(
            self,
            properties.EFFECTOR_SOCKET_SETS[slot_index]["use_target_object"],
            value is not None,
        )
    if socket_key == "object":
        enabled_property = _effector_slot_property_name(slot_index, "enabled")
        setattr(self, enabled_property, value is not None)
        modifier = modifier_inputs.get_cloner_modifier(self.id_data)
        if value is not None and modifier is not None:
            effectors.sync_effector_slot(self, modifier, slot_index)
    if socket_key == "radius":
        effector = getattr(self, object_property)
        if effector is not None:
            effector.empty_display_size = value


def _sync_distribution_mode(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_DISTRIBUTION_MODE,
        DISTRIBUTION_MODE_VALUES[self.distribution_mode],
    )
    self.id_data[properties.PROP_CLONER_MODE] = self.distribution_mode


def _sync_spacing_mode(self, context) -> None:
    global _CONVERTING_SPACING_MODE
    if not _CONVERTING_SPACING_MODE:
        _CONVERTING_SPACING_MODE = True
        try:
            previous_mode = self.id_data.get(
                properties.PROP_SPACING_MODE_PREVIOUS,
                self.spacing_mode,
            )
            if previous_mode != self.spacing_mode:
                _convert_spacing_mode_values(self, previous_mode, self.spacing_mode)
        finally:
            _CONVERTING_SPACING_MODE = False

    self.id_data[properties.PROP_SPACING_MODE_PREVIOUS] = self.spacing_mode
    _sync_modifier_value(
        self,
        properties.SOCKET_SPACING_MODE,
        SPACING_MODE_VALUES[self.spacing_mode],
    )


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


def _sync_brick_row_offset(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_BRICK_ROW_OFFSET, self.brick_row_offset)


def _sync_brick_layer_offset(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_BRICK_LAYER_OFFSET,
        self.brick_layer_offset,
    )


def _sync_linear_count(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_LINEAR_COUNT, self.linear_count)


def _sync_linear_spacing(self, context) -> None:
    _sync_modifier_value(self, properties.SOCKET_LINEAR_SPACING, self.linear_spacing)


def _convert_spacing_mode_values(self, previous_mode: str, next_mode: str) -> None:
    if previous_mode == next_mode:
        return

    if previous_mode == "PER_STEP" and next_mode == "ENDPOINT":
        factor = "TO_ENDPOINT"
    elif previous_mode == "ENDPOINT" and next_mode == "PER_STEP":
        factor = "TO_PER_STEP"
    else:
        return

    self.spacing_x = _convert_spacing_value(self.spacing_x, self.count_x, factor)
    self.spacing_y = _convert_spacing_value(self.spacing_y, self.count_y, factor)
    self.spacing_z = _convert_spacing_value(self.spacing_z, self.count_z, factor)
    self.linear_spacing = _convert_spacing_value(
        self.linear_spacing,
        self.linear_count,
        factor,
    )


def _convert_spacing_value(value: float, count: int, mode: str) -> float:
    step_count = max(1, count - 1)
    if mode == "TO_ENDPOINT":
        return value * step_count
    return value / step_count


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


def _sync_object_distribution_object(self, context) -> None:
    distribution_object = self.object_distribution_object
    if distribution_object is not None and distribution_object == self.id_data:
        self.object_distribution_object = None
        distribution_object = None
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_DISTRIBUTION_OBJECT,
        distribution_object,
    )
    if is_curve_distribution_object(distribution_object):
        self.object_distribution_mode = "SPLINE"


def _sync_object_distribution_mode(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_DISTRIBUTION_MODE,
        OBJECT_DISTRIBUTION_MODE_VALUES[self.object_distribution_mode],
    )
    if self.object_distribution_mode == "SPLINE":
        if self.object_alignment not in {"NONE", "TANGENT"}:
            self.object_alignment = "TANGENT"
    elif self.object_alignment not in {"NONE", "NORMALS", "CENTER"}:
        self.object_alignment = "NORMALS"


def _sync_object_spline_count(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SPLINE_COUNT,
        self.object_spline_count,
    )


def _sync_object_spline_distribution(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION,
        SPLINE_DISTRIBUTION_VALUES[self.object_spline_distribution],
    )


def _sync_object_spline_step(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SPLINE_STEP,
        self.object_spline_step,
    )


def _sync_object_spline_per_spline(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SPLINE_PER_SPLINE,
        self.object_spline_per_spline,
    )


def _sync_object_spline_smooth_rotation(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SPLINE_SMOOTH_ROTATION,
        self.object_spline_smooth_rotation,
    )


def _sync_object_use_vertex_map(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_USE_VERTEX_MAP,
        self.object_use_vertex_map,
    )


def _sync_object_vertex_map(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_VERTEX_MAP,
        self.object_vertex_map,
    )


def _sync_object_vertex_map_threshold(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_VERTEX_MAP_THRESHOLD,
        self.object_vertex_map_threshold,
    )


def _sync_object_surface_distribution(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_DISTRIBUTION,
        SURFACE_DISTRIBUTION_VALUES[self.object_surface_distribution],
    )


def _sync_object_surface_density(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_DENSITY,
        self.object_surface_density,
    )


def _sync_object_surface_count(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_COUNT,
        self.object_surface_count,
    )


def _sync_object_surface_u_count(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_U_COUNT,
        self.object_surface_u_count,
    )


def _sync_object_surface_v_count(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_V_COUNT,
        self.object_surface_v_count,
    )


def _sync_object_surface_uv_map(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_UV_MAP,
        self.object_surface_uv_map,
    )


def _sync_object_surface_distance_min(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_DISTANCE_MIN,
        self.object_surface_distance_min,
    )


def _sync_object_surface_seed(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_SURFACE_SEED,
        self.object_surface_seed,
    )


def _sync_object_alignment(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_ALIGNMENT,
        OBJECT_ALIGNMENT_VALUES[self.object_alignment],
    )


def _sync_object_up_vector(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_OBJECT_UP_VECTOR,
        OBJECT_UP_VECTOR_VALUES[self.object_up_vector],
    )


def _sync_source_position_x(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_POSITION_X,
        self.source_position_x if self.show_source_offset else 0.0,
    )


def _sync_source_position_y(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_POSITION_Y,
        self.source_position_y if self.show_source_offset else 0.0,
    )


def _sync_source_position_z(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_POSITION_Z,
        self.source_position_z if self.show_source_offset else 0.0,
    )


def _sync_source_rotation_x(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_ROTATION_X,
        self.source_rotation_x if self.show_source_offset else 0.0,
    )


def _sync_source_rotation_y(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_ROTATION_Y,
        self.source_rotation_y if self.show_source_offset else 0.0,
    )


def _sync_source_rotation_z(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_ROTATION_Z,
        self.source_rotation_z if self.show_source_offset else 0.0,
    )


def _sync_source_scale_x(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_SCALE_X,
        self.source_scale_x if self.show_source_offset else 1.0,
    )


def _sync_source_scale_y(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_SCALE_Y,
        self.source_scale_y if self.show_source_offset else 1.0,
    )


def _sync_source_scale_z(self, context) -> None:
    _sync_modifier_value(
        self,
        properties.SOCKET_SOURCE_SCALE_Z,
        self.source_scale_z if self.show_source_offset else 1.0,
    )


def _sync_show_source_offset(self, context) -> None:
    if self.id_data.get(properties.PROP_INITIALIZING_CLONER):
        return
    modifier = modifier_inputs.get_cloner_modifier(self.id_data)
    if modifier is None:
        return
    if self.show_source_offset:
        values = {
            properties.SOCKET_SOURCE_POSITION_X: self.source_position_x,
            properties.SOCKET_SOURCE_POSITION_Y: self.source_position_y,
            properties.SOCKET_SOURCE_POSITION_Z: self.source_position_z,
            properties.SOCKET_SOURCE_ROTATION_X: self.source_rotation_x,
            properties.SOCKET_SOURCE_ROTATION_Y: self.source_rotation_y,
            properties.SOCKET_SOURCE_ROTATION_Z: self.source_rotation_z,
            properties.SOCKET_SOURCE_SCALE_X: self.source_scale_x,
            properties.SOCKET_SOURCE_SCALE_Y: self.source_scale_y,
            properties.SOCKET_SOURCE_SCALE_Z: self.source_scale_z,
        }
    else:
        values = {
            properties.SOCKET_SOURCE_POSITION_X: 0.0,
            properties.SOCKET_SOURCE_POSITION_Y: 0.0,
            properties.SOCKET_SOURCE_POSITION_Z: 0.0,
            properties.SOCKET_SOURCE_ROTATION_X: 0.0,
            properties.SOCKET_SOURCE_ROTATION_Y: 0.0,
            properties.SOCKET_SOURCE_ROTATION_Z: 0.0,
            properties.SOCKET_SOURCE_SCALE_X: 1.0,
            properties.SOCKET_SOURCE_SCALE_Y: 1.0,
            properties.SOCKET_SOURCE_SCALE_Z: 1.0,
        }
    modifier_inputs.set_modifier_inputs(modifier, values)


def _sync_modifier_value(self, socket_name: str, value) -> None:
    if self.id_data.get(properties.PROP_INITIALIZING_CLONER):
        return
    modifier = modifier_inputs.get_cloner_modifier(self.id_data)
    if modifier is not None:
        modifier_inputs.set_modifier_input(modifier, socket_name, value)


def _combined_effector_strength(self, slot_index: int, cloner_strength: int) -> float:
    effector = getattr(self, _effector_slot_property_name(slot_index, "object"))
    global_strength = properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT
    if (
        effectors.is_effector_object(effector)
        and hasattr(effector, "clone_fields_effector")
    ):
        global_strength = effector.clone_fields_effector.strength
    return global_strength * cloner_strength / 10000.0


def _sync_effector_settings(self, context) -> None:
    obj = self.id_data
    if self.type == effectors.EFFECTOR_TYPE_SHADER:
        obj.data = self.shader_image
    effectors.configure_effector_object(obj, self.shape, self.radius, self.type)
    effectors.rename_effector_object(obj, self.shape, self.type)
    effectors.sync_effector_to_referencing_cloners(obj)


def _sync_shader_image(self, context) -> None:
    image = self.shader_image
    if (
        self.shader_preserve_aspect
        and image is not None
        and image.size[0] > 0
        and image.size[1] > 0
    ):
        self.shader_height = self.shader_width * image.size[1] / image.size[0]
    _sync_effector_settings(self, context)


def _shader_image_aspect(self) -> float | None:
    image = self.shader_image
    if image is None or image.size[0] <= 0 or image.size[1] <= 0:
        return None
    return image.size[0] / image.size[1]


def _sync_shader_width(self, context) -> None:
    global _SYNCING_SHADER_ASPECT
    if not _SYNCING_SHADER_ASPECT and self.shader_preserve_aspect:
        aspect = _shader_image_aspect(self)
        if aspect is not None:
            _SYNCING_SHADER_ASPECT = True
            try:
                self.shader_height = self.shader_width / aspect
            finally:
                _SYNCING_SHADER_ASPECT = False
    _sync_effector_settings(self, context)


def _sync_shader_height(self, context) -> None:
    global _SYNCING_SHADER_ASPECT
    if not _SYNCING_SHADER_ASPECT and self.shader_preserve_aspect:
        aspect = _shader_image_aspect(self)
        if aspect is not None:
            _SYNCING_SHADER_ASPECT = True
            try:
                self.shader_width = self.shader_height * aspect
            finally:
                _SYNCING_SHADER_ASPECT = False
    _sync_effector_settings(self, context)


def _sync_shader_preserve_aspect(self, context) -> None:
    if self.shader_preserve_aspect:
        _sync_shader_width(self, context)
    else:
        _sync_effector_settings(self, context)


def _sync_shader_fit_mode(self, context) -> None:
    cloner = getattr(context, "object", None)
    effector = self.id_data
    if (
        modifier_inputs.is_cloner_object(cloner)
        and any(
            getattr(cloner.clone_fields_cloner, slot["object"]) == effector
            for slot in effectors.EFFECTOR_SLOT_PROPERTIES
        )
    ):
        effectors.fit_shader_to_grid(effector, cloner)


def _sync_box_dimension(self, context, property_name: str) -> None:
    if self.box_uniform:
        value = getattr(self, property_name)
        for name in ("box_x", "box_y", "box_z"):
            if name != property_name and getattr(self, name) != value:
                setattr(self, name, value)
    _sync_effector_settings(self, context)


def _sync_box_uniform(self, context) -> None:
    if self.box_uniform:
        self.box_y = self.box_x
        self.box_z = self.box_x
    _sync_effector_settings(self, context)


def _sync_effector_radius_setting(self, context) -> None:
    obj = self.id_data
    effectors.configure_effector_object(obj, self.shape, self.radius, self.type)
    effectors.sync_effector_to_referencing_cloners(obj)


def _effector_slot_property_name(slot_index: int, key: str) -> str:
    return effectors.EFFECTOR_SLOT_PROPERTIES[slot_index][key]


class CloneFieldsEffectorSettings(bpy.types.PropertyGroup):
    type: EnumProperty(
        name="Type",
        items=effectors.EFFECTOR_TYPE_ITEMS,
        default=effectors.EFFECTOR_TYPE_BASIC,
        update=_sync_effector_settings,
    )
    shape: EnumProperty(
        name="Field",
        items=effectors.FIELD_SHAPE_ITEMS,
        default=effectors.FIELD_SHAPE_SPHERE,
        update=_sync_effector_settings,
    )
    seed: IntProperty(
        name="Seed",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SEED],
        min=0,
        update=_sync_effector_settings,
    )
    invert: BoolProperty(
        name="Invert",
        description="Invert image luminance for Shader Effectors or spatial falloff for other Effectors",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_INVERT],
        update=_sync_effector_settings,
    )
    strength: IntProperty(
        name="Global Strength",
        default=properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT,
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=_sync_effector_settings,
    )
    radius: FloatProperty(
        name="Radius",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_RADIUS],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_radius_setting,
    )
    box_x: FloatProperty(
        name="X",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_BOX_X],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_box_dimension(self, context, "box_x"),
    )
    box_y: FloatProperty(
        name="Y",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_BOX_Y],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_box_dimension(self, context, "box_y"),
    )
    box_z: FloatProperty(
        name="Z",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_BOX_Z],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_box_dimension(self, context, "box_z"),
    )
    box_uniform: BoolProperty(
        name="Uniform",
        default=True,
        update=_sync_box_uniform,
    )
    height: FloatProperty(
        name="Height",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_HEIGHT],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_settings,
    )
    length: FloatProperty(
        name="Length",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_LENGTH],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_settings,
    )
    falloff: IntProperty(
        name="Falloff",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_FALLOFF],
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=_sync_effector_settings,
    )
    use_position: BoolProperty(
        name="Position",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_USE_POSITION],
        update=_sync_effector_settings,
    )
    position_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_POSITION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_POSITION_X],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_settings,
    )
    position_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_POSITION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_POSITION_Y],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_settings,
    )
    position_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_POSITION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_POSITION_Z],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_settings,
    )
    use_rotation: BoolProperty(
        name="Rotation",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_USE_ROTATION],
        update=_sync_effector_settings,
    )
    rotation_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_ROTATION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ROTATION_X],
        subtype="ANGLE",
        update=_sync_effector_settings,
    )
    rotation_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_ROTATION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ROTATION_Y],
        subtype="ANGLE",
        update=_sync_effector_settings,
    )
    rotation_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_ROTATION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ROTATION_Z],
        subtype="ANGLE",
        update=_sync_effector_settings,
    )
    target_axis: EnumProperty(
        name="Aim Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Z",
        update=_sync_effector_settings,
    )
    target_up_axis: EnumProperty(
        name="Up Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Y",
        update=_sync_effector_settings,
    )
    target_object: PointerProperty(
        name="Target",
        description="Optional object to aim at; when empty, use the Effector itself",
        type=bpy.types.Object,
        update=_sync_effector_settings,
    )
    shader_image: PointerProperty(
        name="Image",
        description="Image whose luminance controls the Effector",
        type=bpy.types.Image,
        update=_sync_shader_image,
    )
    shader_preserve_aspect: BoolProperty(
        name="Preserve Aspect",
        description="Keep Projection Width and Height matched to the image aspect ratio",
        default=True,
        update=_sync_shader_preserve_aspect,
    )
    shader_fit_mode: EnumProperty(
        name="Fit Mode",
        items=SHADER_FIT_MODE_ITEMS,
        default="COVER",
        update=_sync_shader_fit_mode,
    )
    shader_width: FloatProperty(
        name="Width",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SHADER_WIDTH],
        min=0.001,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_shader_width,
    )
    shader_height: FloatProperty(
        name="Height",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SHADER_HEIGHT],
        min=0.001,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_shader_height,
    )
    shader_tiles_x: IntProperty(
        name="Tiles X",
        description="Number of horizontal image repeats inside the projection",
        default=1,
        min=1,
        update=_sync_effector_settings,
    )
    shader_tiles_y: IntProperty(
        name="Tiles Y",
        description="Number of vertical image repeats inside the projection",
        default=1,
        min=1,
        update=_sync_effector_settings,
    )
    use_scale: BoolProperty(
        name="Scale",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_USE_SCALE],
        update=_sync_effector_settings,
    )
    scale_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_SCALE_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SCALE_X],
        min=0.0,
        update=_sync_effector_settings,
    )
    scale_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_SCALE_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SCALE_Y],
        min=0.0,
        update=_sync_effector_settings,
    )
    scale_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_SCALE_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SCALE_Z],
        min=0.0,
        update=_sync_effector_settings,
    )


class CloneFieldsClonerSettings(bpy.types.PropertyGroup):
    source_object: PointerProperty(
        name=properties.SOCKET_SOURCE_OBJECT,
        description="Object to instance across the grid",
        type=bpy.types.Object,
        update=_sync_source,
    )
    effector_shape: EnumProperty(
        name="Field",
        items=effectors.FIELD_SHAPE_ITEMS,
        default=effectors.FIELD_SHAPE_SPHERE,
        update=_sync_effector_shape,
    )
    effector_type: EnumProperty(
        name="Type",
        items=effectors.EFFECTOR_TYPE_ITEMS,
        default=effectors.EFFECTOR_TYPE_BASIC,
        update=lambda self, context: _sync_effector_slot_value(self, 0, "type", "effector_type"),
    )
    effector_seed: IntProperty(
        name="Seed",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SEED],
        min=0,
        update=lambda self, context: _sync_effector_slot_value(self, 0, "seed", "effector_seed"),
    )
    effector_object: PointerProperty(
        name=properties.SOCKET_EFFECTOR_OBJECT,
        description="Basic Effector controller object",
        type=bpy.types.Object,
        update=_sync_effector_object,
    )
    effector_enabled: BoolProperty(
        name="Enabled",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ENABLED],
        update=_sync_effector_enabled,
    )
    effector_invert: BoolProperty(
        name="Inverse",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_INVERT],
        update=_sync_effector_invert,
    )
    effector_strength: IntProperty(
        name="Strength",
        default=properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT,
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=_sync_effector_strength,
    )
    effector_radius: FloatProperty(
        name="Radius",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_RADIUS],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_radius,
    )
    effector_falloff: IntProperty(
        name="Falloff",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_FALLOFF],
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=_sync_effector_falloff,
    )
    effector_use_position: BoolProperty(
        name="Position",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_USE_POSITION],
        update=_sync_effector_use_position,
    )
    effector_position_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_POSITION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_POSITION_X],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_position_x,
    )
    effector_position_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_POSITION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_POSITION_Y],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_position_y,
    )
    effector_position_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_POSITION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_POSITION_Z],
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_effector_position_z,
    )
    effector_use_rotation: BoolProperty(
        name="Rotation",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_USE_ROTATION],
        update=_sync_effector_use_rotation,
    )
    effector_rotation_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_ROTATION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ROTATION_X],
        subtype="ANGLE",
        update=_sync_effector_rotation_x,
    )
    effector_rotation_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_ROTATION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ROTATION_Y],
        subtype="ANGLE",
        update=_sync_effector_rotation_y,
    )
    effector_rotation_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_ROTATION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_ROTATION_Z],
        subtype="ANGLE",
        update=_sync_effector_rotation_z,
    )
    effector_target_axis: EnumProperty(
        name="Aim Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Z",
        update=lambda self, context: _sync_effector_slot_value(self, 0, "target_axis", "effector_target_axis"),
    )
    effector_target_up_axis: EnumProperty(
        name="Up Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Y",
        update=lambda self, context: _sync_effector_slot_value(self, 0, "target_up_axis", "effector_target_up_axis"),
    )
    effector_target_object: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        update=lambda self, context: _sync_effector_slot_value(self, 0, "target_object", "effector_target_object"),
    )
    effector_use_scale: BoolProperty(
        name="Scale",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_USE_SCALE],
        update=_sync_effector_use_scale,
    )
    effector_scale_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_SCALE_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SCALE_X],
        min=0.0,
        update=_sync_effector_scale_x,
    )
    effector_scale_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_SCALE_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SCALE_Y],
        min=0.0,
        update=_sync_effector_scale_y,
    )
    effector_scale_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_SCALE_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SCALE_Z],
        min=0.0,
        update=_sync_effector_scale_z,
    )
    effector2_shape: EnumProperty(
        name="Field",
        items=effectors.FIELD_SHAPE_ITEMS,
        default=effectors.FIELD_SHAPE_SPHERE,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "shape", "effector2_shape"),
    )
    effector2_type: EnumProperty(
        name="Type",
        items=effectors.EFFECTOR_TYPE_ITEMS,
        default=effectors.EFFECTOR_TYPE_BASIC,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "type", "effector2_type"),
    )
    effector2_seed: IntProperty(
        name="Seed",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_SEED],
        min=0,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "seed", "effector2_seed"),
    )
    effector2_object: PointerProperty(
        name=properties.SOCKET_EFFECTOR_2_OBJECT,
        description="Second Basic Effector controller object",
        type=bpy.types.Object,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "object", "effector2_object"),
    )
    effector2_enabled: BoolProperty(
        name="Enabled",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_ENABLED],
        update=lambda self, context: _sync_effector_slot_value(self, 1, "enabled", "effector2_enabled"),
    )
    effector2_invert: BoolProperty(
        name="Inverse",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_INVERT],
        update=lambda self, context: _sync_effector_slot_value(self, 1, "invert", "effector2_invert"),
    )
    effector2_strength: IntProperty(
        name="Strength",
        default=properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT,
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "strength", "effector2_strength"),
    )
    effector2_radius: FloatProperty(
        name="Radius",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_RADIUS],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "radius", "effector2_radius"),
    )
    effector2_falloff: IntProperty(
        name="Falloff",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_FALLOFF],
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "falloff", "effector2_falloff"),
    )
    effector2_use_position: BoolProperty(
        name="Position",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_USE_POSITION],
        update=lambda self, context: _sync_effector_slot_value(self, 1, "use_position", "effector2_use_position"),
    )
    effector2_position_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_POSITION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_POSITION_X],
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "position_x", "effector2_position_x"),
    )
    effector2_position_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_POSITION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_POSITION_Y],
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "position_y", "effector2_position_y"),
    )
    effector2_position_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_POSITION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_POSITION_Z],
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "position_z", "effector2_position_z"),
    )
    effector2_use_rotation: BoolProperty(
        name="Rotation",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_USE_ROTATION],
        update=lambda self, context: _sync_effector_slot_value(self, 1, "use_rotation", "effector2_use_rotation"),
    )
    effector2_rotation_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_ROTATION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_ROTATION_X],
        subtype="ANGLE",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "rotation_x", "effector2_rotation_x"),
    )
    effector2_rotation_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_ROTATION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_ROTATION_Y],
        subtype="ANGLE",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "rotation_y", "effector2_rotation_y"),
    )
    effector2_rotation_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_ROTATION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_ROTATION_Z],
        subtype="ANGLE",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "rotation_z", "effector2_rotation_z"),
    )
    effector2_target_axis: EnumProperty(
        name="Aim Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Z",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "target_axis", "effector2_target_axis"),
    )
    effector2_target_up_axis: EnumProperty(
        name="Up Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Y",
        update=lambda self, context: _sync_effector_slot_value(self, 1, "target_up_axis", "effector2_target_up_axis"),
    )
    effector2_target_object: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "target_object", "effector2_target_object"),
    )
    effector2_use_scale: BoolProperty(
        name="Scale",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_USE_SCALE],
        update=lambda self, context: _sync_effector_slot_value(self, 1, "use_scale", "effector2_use_scale"),
    )
    effector2_scale_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_SCALE_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_SCALE_X],
        min=0.0,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "scale_x", "effector2_scale_x"),
    )
    effector2_scale_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_SCALE_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_SCALE_Y],
        min=0.0,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "scale_y", "effector2_scale_y"),
    )
    effector2_scale_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_2_SCALE_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_2_SCALE_Z],
        min=0.0,
        update=lambda self, context: _sync_effector_slot_value(self, 1, "scale_z", "effector2_scale_z"),
    )
    effector3_shape: EnumProperty(
        name="Field",
        items=effectors.FIELD_SHAPE_ITEMS,
        default=effectors.FIELD_SHAPE_SPHERE,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "shape", "effector3_shape"),
    )
    effector3_type: EnumProperty(
        name="Type",
        items=effectors.EFFECTOR_TYPE_ITEMS,
        default=effectors.EFFECTOR_TYPE_BASIC,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "type", "effector3_type"),
    )
    effector3_seed: IntProperty(
        name="Seed",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_SEED],
        min=0,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "seed", "effector3_seed"),
    )
    effector3_object: PointerProperty(
        name=properties.SOCKET_EFFECTOR_3_OBJECT,
        description="Third Basic Effector controller object",
        type=bpy.types.Object,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "object", "effector3_object"),
    )
    effector3_enabled: BoolProperty(
        name="Enabled",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_ENABLED],
        update=lambda self, context: _sync_effector_slot_value(self, 2, "enabled", "effector3_enabled"),
    )
    effector3_invert: BoolProperty(
        name="Inverse",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_INVERT],
        update=lambda self, context: _sync_effector_slot_value(self, 2, "invert", "effector3_invert"),
    )
    effector3_strength: IntProperty(
        name="Strength",
        default=properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT,
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "strength", "effector3_strength"),
    )
    effector3_radius: FloatProperty(
        name="Radius",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_RADIUS],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "radius", "effector3_radius"),
    )
    effector3_falloff: IntProperty(
        name="Falloff",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_FALLOFF],
        min=0,
        max=100,
        subtype="PERCENTAGE",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "falloff", "effector3_falloff"),
    )
    effector3_use_position: BoolProperty(
        name="Position",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_USE_POSITION],
        update=lambda self, context: _sync_effector_slot_value(self, 2, "use_position", "effector3_use_position"),
    )
    effector3_position_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_POSITION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_POSITION_X],
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "position_x", "effector3_position_x"),
    )
    effector3_position_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_POSITION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_POSITION_Y],
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "position_y", "effector3_position_y"),
    )
    effector3_position_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_POSITION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_POSITION_Z],
        subtype="DISTANCE",
        unit="LENGTH",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "position_z", "effector3_position_z"),
    )
    effector3_use_rotation: BoolProperty(
        name="Rotation",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_USE_ROTATION],
        update=lambda self, context: _sync_effector_slot_value(self, 2, "use_rotation", "effector3_use_rotation"),
    )
    effector3_rotation_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_ROTATION_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_ROTATION_X],
        subtype="ANGLE",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "rotation_x", "effector3_rotation_x"),
    )
    effector3_rotation_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_ROTATION_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_ROTATION_Y],
        subtype="ANGLE",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "rotation_y", "effector3_rotation_y"),
    )
    effector3_rotation_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_ROTATION_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_ROTATION_Z],
        subtype="ANGLE",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "rotation_z", "effector3_rotation_z"),
    )
    effector3_target_axis: EnumProperty(
        name="Aim Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Z",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "target_axis", "effector3_target_axis"),
    )
    effector3_target_up_axis: EnumProperty(
        name="Up Axis",
        items=effectors.TARGET_AXIS_ITEMS,
        default="Y",
        update=lambda self, context: _sync_effector_slot_value(self, 2, "target_up_axis", "effector3_target_up_axis"),
    )
    effector3_target_object: PointerProperty(
        name="Target",
        type=bpy.types.Object,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "target_object", "effector3_target_object"),
    )
    effector3_use_scale: BoolProperty(
        name="Scale",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_USE_SCALE],
        update=lambda self, context: _sync_effector_slot_value(self, 2, "use_scale", "effector3_use_scale"),
    )
    effector3_scale_x: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_SCALE_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_SCALE_X],
        min=0.0,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "scale_x", "effector3_scale_x"),
    )
    effector3_scale_y: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_SCALE_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_SCALE_Y],
        min=0.0,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "scale_y", "effector3_scale_y"),
    )
    effector3_scale_z: FloatProperty(
        name=properties.SOCKET_EFFECTOR_3_SCALE_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_3_SCALE_Z],
        min=0.0,
        update=lambda self, context: _sync_effector_slot_value(self, 2, "scale_z", "effector3_scale_z"),
    )
    distribution_mode: EnumProperty(
        name="Mode",
        items=DISTRIBUTION_MODE_ITEMS,
        default="GRID",
        update=_sync_distribution_mode,
    )
    spacing_mode: EnumProperty(
        name="Spacing Mode",
        items=SPACING_MODE_ITEMS,
        default="PER_STEP",
        update=_sync_spacing_mode,
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
    brick_row_offset: FloatProperty(
        name="Row Offset",
        description="X spacing fraction added to every other row",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_BRICK_ROW_OFFSET],
        min=-10.0,
        max=10.0,
        update=_sync_brick_row_offset,
    )
    brick_layer_offset: FloatProperty(
        name="Layer Offset",
        description="X spacing fraction added to every other Z layer",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_BRICK_LAYER_OFFSET],
        min=-10.0,
        max=10.0,
        update=_sync_brick_layer_offset,
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
    object_distribution_object: PointerProperty(
        name=properties.SOCKET_OBJECT_DISTRIBUTION_OBJECT,
        description="Mesh or curve object to place clones on",
        type=bpy.types.Object,
        update=_sync_object_distribution_object,
    )
    object_distribution_mode: EnumProperty(
        name="Placement",
        items=OBJECT_DISTRIBUTION_MODE_ITEMS,
        default="VERTICES",
        update=_sync_object_distribution_mode,
    )
    object_spline_count: IntProperty(
        name=properties.SOCKET_OBJECT_SPLINE_COUNT,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SPLINE_COUNT],
        min=1,
        update=_sync_object_spline_count,
    )
    object_spline_distribution: EnumProperty(
        name="Distribution",
        items=SPLINE_DISTRIBUTION_ITEMS,
        default="EVEN",
        update=_sync_object_spline_distribution,
    )
    object_spline_step: FloatProperty(
        name="Step",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SPLINE_STEP],
        min=0.001,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_object_spline_step,
    )
    object_spline_per_spline: BoolProperty(
        name="Per Spline",
        description="Apply Count, Step, or Even separately to each spline or contour",
        default=properties.GRID_INPUT_DEFAULTS[
            properties.SOCKET_OBJECT_SPLINE_PER_SPLINE
        ],
        update=_sync_object_spline_per_spline,
    )
    object_spline_smooth_rotation: BoolProperty(
        name="Smooth Rotation",
        description="Use the curve normal to stabilize rotation around the tangent",
        default=properties.GRID_INPUT_DEFAULTS[
            properties.SOCKET_OBJECT_SPLINE_SMOOTH_ROTATION
        ],
        update=_sync_object_spline_smooth_rotation,
    )
    object_use_vertex_map: BoolProperty(
        name="Use Vertex Map",
        description="Limit mesh Object distribution to a named vertex group",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_USE_VERTEX_MAP],
        update=_sync_object_use_vertex_map,
    )
    object_vertex_map: StringProperty(
        name="Vertex Map",
        description="Vertex group name used to filter Object distribution",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_VERTEX_MAP],
        update=_sync_object_vertex_map,
    )
    object_vertex_map_threshold: FloatProperty(
        name="Threshold",
        description="Minimum vertex group weight included by the Object distribution",
        default=properties.GRID_INPUT_DEFAULTS[
            properties.SOCKET_OBJECT_VERTEX_MAP_THRESHOLD
        ],
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=_sync_object_vertex_map_threshold,
    )
    object_surface_distribution: EnumProperty(
        name="Distribution",
        items=SURFACE_DISTRIBUTION_ITEMS,
        default="RANDOM",
        update=_sync_object_surface_distribution,
    )
    object_surface_density: FloatProperty(
        name="Density",
        description="Approximate number of surface points per square Blender unit",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SURFACE_DENSITY],
        min=0.0,
        update=_sync_object_surface_density,
    )
    object_surface_count: IntProperty(
        name="Count",
        description="Approximate number of surface points",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SURFACE_COUNT],
        min=1,
        update=_sync_object_surface_count,
    )
    object_surface_u_count: IntProperty(
        name="U Count",
        description="Number of surface grid points across the UV map's U direction",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SURFACE_U_COUNT],
        min=1,
        update=_sync_object_surface_u_count,
    )
    object_surface_v_count: IntProperty(
        name="V Count",
        description="Number of surface grid points across the UV map's V direction",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SURFACE_V_COUNT],
        min=1,
        update=_sync_object_surface_v_count,
    )
    object_surface_uv_map: StringProperty(
        name="UV Map",
        description="UV map name used by UV Grid surface distribution",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SURFACE_UV_MAP],
        update=_sync_object_surface_uv_map,
    )
    object_surface_distance_min: FloatProperty(
        name="Minimum Distance",
        description="Minimum spacing between randomly scattered surface points",
        default=properties.GRID_INPUT_DEFAULTS[
            properties.SOCKET_OBJECT_SURFACE_DISTANCE_MIN
        ],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        update=_sync_object_surface_distance_min,
    )
    object_surface_seed: IntProperty(
        name="Seed",
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_OBJECT_SURFACE_SEED],
        min=0,
        update=_sync_object_surface_seed,
    )
    object_alignment: EnumProperty(
        name="Alignment",
        items=OBJECT_ALIGNMENT_ITEMS,
        default="NORMALS",
        update=_sync_object_alignment,
    )
    object_up_vector: EnumProperty(
        name="Up Vector",
        items=OBJECT_UP_VECTOR_ITEMS,
        default="AUTOMATIC",
        update=_sync_object_up_vector,
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
    show_source_offset: BoolProperty(
        name="Offset",
        default=False,
        update=_sync_show_source_offset,
    )
    selected_effector_slot: IntProperty(
        name="Selected Effector",
        default=0,
        min=0,
        max=2,
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
    show_effector_position: BoolProperty(
        name="Position",
        default=False,
    )
    show_effector_rotation: BoolProperty(
        name="Rotation",
        default=False,
    )
    show_effector_scale: BoolProperty(
        name="Scale",
        default=True,
    )


classes = (CloneFieldsEffectorSettings, CloneFieldsClonerSettings)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.clone_fields_effector = PointerProperty(type=CloneFieldsEffectorSettings)
    bpy.types.Object.clone_fields_cloner = PointerProperty(type=CloneFieldsClonerSettings)


def unregister() -> None:
    del bpy.types.Object.clone_fields_cloner
    del bpy.types.Object.clone_fields_effector
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
