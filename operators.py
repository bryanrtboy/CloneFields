"""Operators for Clone Fields."""

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty

from . import cloner, modifier_inputs, properties


EFFECTOR_SLOT_PROPERTIES = (
    {
        "object": "effector_object",
        "enabled": "effector_enabled",
        "invert": "effector_invert",
        "strength": "effector_strength",
        "radius": "effector_radius",
        "falloff": "effector_falloff",
        "use_position": "effector_use_position",
        "position_x": "effector_position_x",
        "position_y": "effector_position_y",
        "position_z": "effector_position_z",
        "use_rotation": "effector_use_rotation",
        "rotation_x": "effector_rotation_x",
        "rotation_y": "effector_rotation_y",
        "rotation_z": "effector_rotation_z",
        "use_scale": "effector_use_scale",
        "scale_x": "effector_scale_x",
        "scale_y": "effector_scale_y",
        "scale_z": "effector_scale_z",
    },
    {
        "object": "effector2_object",
        "enabled": "effector2_enabled",
        "invert": "effector2_invert",
        "strength": "effector2_strength",
        "radius": "effector2_radius",
        "falloff": "effector2_falloff",
        "use_position": "effector2_use_position",
        "position_x": "effector2_position_x",
        "position_y": "effector2_position_y",
        "position_z": "effector2_position_z",
        "use_rotation": "effector2_use_rotation",
        "rotation_x": "effector2_rotation_x",
        "rotation_y": "effector2_rotation_y",
        "rotation_z": "effector2_rotation_z",
        "use_scale": "effector2_use_scale",
        "scale_x": "effector2_scale_x",
        "scale_y": "effector2_scale_y",
        "scale_z": "effector2_scale_z",
    },
    {
        "object": "effector3_object",
        "enabled": "effector3_enabled",
        "invert": "effector3_invert",
        "strength": "effector3_strength",
        "radius": "effector3_radius",
        "falloff": "effector3_falloff",
        "use_position": "effector3_use_position",
        "position_x": "effector3_position_x",
        "position_y": "effector3_position_y",
        "position_z": "effector3_position_z",
        "use_rotation": "effector3_use_rotation",
        "rotation_x": "effector3_rotation_x",
        "rotation_y": "effector3_rotation_y",
        "rotation_z": "effector3_rotation_z",
        "use_scale": "effector3_use_scale",
        "scale_x": "effector3_scale_x",
        "scale_y": "effector3_scale_y",
        "scale_z": "effector3_scale_z",
    },
)


class CLONE_FIELDS_OT_add_cloner(bpy.types.Operator):
    bl_idname = "clone_fields.add_cloner"
    bl_label = "Add Cloner"
    bl_description = "Add a Clone Fields grid cloner"
    bl_options = {"REGISTER", "UNDO"}

    source_object_name: StringProperty(
        name=properties.SOCKET_SOURCE_OBJECT,
        description="Object to instance across the grid",
    )
    count_x: IntProperty(
        name=properties.SOCKET_COUNT_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_COUNT_X],
        min=1,
    )
    count_y: IntProperty(
        name=properties.SOCKET_COUNT_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_COUNT_Y],
        min=1,
    )
    count_z: IntProperty(
        name=properties.SOCKET_COUNT_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_COUNT_Z],
        min=1,
    )
    spacing_x: FloatProperty(
        name=properties.SOCKET_SPACING_X,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_X],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
    )
    spacing_y: FloatProperty(
        name=properties.SOCKET_SPACING_Y,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_Y],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
    )
    spacing_z: FloatProperty(
        name=properties.SOCKET_SPACING_Z,
        default=properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_Z],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
    )

    def invoke(self, context, event):
        active = context.view_layer.objects.active
        if active is not None:
            self.source_object_name = active.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, "source_object_name", context.scene, "objects")

        grid = layout.grid_flow(row_major=True, columns=2, align=True)
        grid.prop(self, "count_x")
        grid.prop(self, "spacing_x")
        grid.prop(self, "count_y")
        grid.prop(self, "spacing_y")
        grid.prop(self, "count_z")
        grid.prop(self, "spacing_z")

    def execute(self, context):
        source_object = bpy.data.objects.get(self.source_object_name)
        if source_object is None:
            self.report({"ERROR"}, "Choose a source object to clone")
            return {"CANCELLED"}
        if modifier_inputs.is_cloner_object(source_object):
            self.report({"ERROR"}, "Clone Fields cloners cannot be used as sources yet")
            return {"CANCELLED"}

        cloner.create_grid_cloner(
            context,
            source_object=source_object,
            count_x=self.count_x,
            count_y=self.count_y,
            count_z=self.count_z,
            spacing_x=self.spacing_x,
            spacing_y=self.spacing_y,
            spacing_z=self.spacing_z,
        )

        return {"FINISHED"}


class CLONE_FIELDS_OT_add_plain_effector(bpy.types.Operator):
    bl_idname = "clone_fields.add_plain_effector"
    bl_label = "Add Plain Effector"
    bl_description = "Add a spherical Plain Effector to the active Cloner"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cloner_object = context.object
        modifier = modifier_inputs.get_cloner_modifier(cloner_object)
        if modifier is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        settings = cloner_object.clone_fields_cloner
        slot_index = _first_empty_effector_slot(settings)
        if slot_index is None:
            self.report({"ERROR"}, "This milestone supports up to three Plain Effectors")
            return {"CANCELLED"}
        slot_properties = EFFECTOR_SLOT_PROPERTIES[slot_index]
        effector = bpy.data.objects.new("Plain Effector", None)
        effector.empty_display_type = "SPHERE"
        radius = properties.GRID_INPUT_DEFAULTS[
            properties.EFFECTOR_SOCKET_SETS[slot_index]["radius"]
        ]
        effector.empty_display_size = radius
        effector.show_name = True
        effector.hide_render = True
        effector[properties.PROP_EFFECTOR_TYPE] = "PLAIN"
        context.collection.objects.link(effector)
        effector.location = cloner_object.location

        _reset_effector_slot(settings, slot_index)
        setattr(settings, slot_properties["object"], effector)
        setattr(settings, slot_properties["enabled"], True)
        settings.selected_effector_slot = slot_index
        modifier_inputs.set_modifier_input(
            modifier,
            properties.EFFECTOR_SOCKET_SETS[slot_index]["object"],
            effector,
        )

        bpy.ops.object.select_all(action="DESELECT")
        effector.select_set(True)
        context.view_layer.objects.active = effector
        return {"FINISHED"}


class CLONE_FIELDS_OT_move_plain_effector(bpy.types.Operator):
    bl_idname = "clone_fields.move_plain_effector"
    bl_label = "Move Plain Effector"
    bl_description = "Move a Plain Effector up or down in the Cloner stack"
    bl_options = {"REGISTER", "UNDO"}

    slot_index: IntProperty(min=0, max=2)
    direction: IntProperty(default=0)

    def execute(self, context):
        cloner_object = context.object
        if modifier_inputs.get_cloner_modifier(cloner_object) is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        target_index = self.slot_index + self.direction
        if target_index < 0 or target_index >= len(EFFECTOR_SLOT_PROPERTIES):
            return {"CANCELLED"}

        settings = cloner_object.clone_fields_cloner
        _swap_effector_slots(settings, self.slot_index, target_index)
        settings.selected_effector_slot = target_index
        return {"FINISHED"}


class CLONE_FIELDS_OT_select_plain_effector(bpy.types.Operator):
    bl_idname = "clone_fields.select_plain_effector"
    bl_label = "Select Plain Effector"
    bl_description = "Show this Plain Effector's settings"
    bl_options = {"REGISTER", "UNDO"}

    slot_index: IntProperty(min=0, max=2)

    def execute(self, context):
        cloner_object = context.object
        if modifier_inputs.get_cloner_modifier(cloner_object) is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        cloner_object.clone_fields_cloner.selected_effector_slot = self.slot_index
        return {"FINISHED"}


classes = (
    CLONE_FIELDS_OT_add_cloner,
    CLONE_FIELDS_OT_add_plain_effector,
    CLONE_FIELDS_OT_move_plain_effector,
    CLONE_FIELDS_OT_select_plain_effector,
)


def _first_empty_effector_slot(settings) -> int | None:
    for index, slot_properties in enumerate(EFFECTOR_SLOT_PROPERTIES):
        if getattr(settings, slot_properties["object"]) is None:
            return index
    return None


def _reset_effector_slot(settings, slot_index: int) -> None:
    slot_properties = EFFECTOR_SLOT_PROPERTIES[slot_index]
    socket_set = properties.EFFECTOR_SOCKET_SETS[slot_index]
    for key, property_name in slot_properties.items():
        if key == "object":
            continue
        setattr(settings, property_name, properties.GRID_INPUT_DEFAULTS[socket_set[key]])


def _swap_effector_slots(settings, first_index: int, second_index: int) -> None:
    first = EFFECTOR_SLOT_PROPERTIES[first_index]
    second = EFFECTOR_SLOT_PROPERTIES[second_index]
    values = {key: getattr(settings, first[key]) for key in first}
    for key in first:
        setattr(settings, first[key], getattr(settings, second[key]))
    for key, value in values.items():
        setattr(settings, second[key], value)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
