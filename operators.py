"""Operators for Clone Fields."""

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty

from . import cloner, effectors, modifier_inputs, properties


EFFECTOR_SLOT_PROPERTIES = effectors.EFFECTOR_SLOT_PROPERTIES


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
    bl_label = "Add Basic Effector"
    bl_description = "Add a spherical Basic Effector to the active Cloner"
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
            self.report({"ERROR"}, "This milestone supports up to three Effectors")
            return {"CANCELLED"}
        slot_properties = EFFECTOR_SLOT_PROPERTIES[slot_index]
        shape = getattr(settings, slot_properties["shape"])
        effector = bpy.data.objects.new(effectors.basic_effector_name(shape), None)
        radius = properties.GRID_INPUT_DEFAULTS[
            properties.EFFECTOR_SOCKET_SETS[slot_index]["radius"]
        ]
        effectors.configure_effector_object(effector, shape, radius)
        context.collection.objects.link(effector)
        effector.location = cloner_object.location

        _assign_effector_to_slot(settings, modifier, slot_index, effector, shape)

        bpy.ops.object.select_all(action="DESELECT")
        cloner_object.select_set(True)
        context.view_layer.objects.active = cloner_object
        return {"FINISHED"}


class CLONE_FIELDS_OT_link_existing_effector(bpy.types.Operator):
    bl_idname = "clone_fields.link_existing_effector"
    bl_label = "Link Existing Effector"
    bl_description = "Link an existing Clone Fields Effector to the active Cloner"
    bl_options = {"REGISTER", "UNDO"}

    effector_object_name: StringProperty(
        name="Effector",
        description="Existing Clone Fields Effector to link",
    )

    def invoke(self, context, event):
        for obj in bpy.data.objects:
            if effectors.is_effector_object(obj):
                self.effector_object_name = obj.name
                break
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop_search(self, "effector_object_name", context.scene, "objects")

    def execute(self, context):
        cloner_object = context.object
        modifier = modifier_inputs.get_cloner_modifier(cloner_object)
        if modifier is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        effector = bpy.data.objects.get(self.effector_object_name)
        if not effectors.is_effector_object(effector):
            self.report({"ERROR"}, "Choose a Clone Fields Effector")
            return {"CANCELLED"}

        settings = cloner_object.clone_fields_cloner
        if _effector_already_linked(settings, effector):
            self.report({"ERROR"}, "That Effector is already linked to this Cloner")
            return {"CANCELLED"}

        slot_index = _first_empty_effector_slot(settings)
        if slot_index is None:
            self.report({"ERROR"}, "This milestone supports up to three Effectors")
            return {"CANCELLED"}

        shape = effector.get(properties.PROP_EFFECTOR_SHAPE, effectors.FIELD_SHAPE_SPHERE)
        _assign_effector_to_slot(settings, modifier, slot_index, effector, shape)

        bpy.ops.object.select_all(action="DESELECT")
        cloner_object.select_set(True)
        context.view_layer.objects.active = cloner_object
        return {"FINISHED"}


class CLONE_FIELDS_OT_move_plain_effector(bpy.types.Operator):
    bl_idname = "clone_fields.move_plain_effector"
    bl_label = "Move Effector"
    bl_description = "Move an Effector up or down in the Cloner stack"
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
    bl_label = "Select Effector"
    bl_description = "Show this Effector's settings"
    bl_options = {"REGISTER", "UNDO"}

    slot_index: IntProperty(min=0, max=2)

    def execute(self, context):
        cloner_object = context.object
        if modifier_inputs.get_cloner_modifier(cloner_object) is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        cloner_object.clone_fields_cloner.selected_effector_slot = self.slot_index
        return {"FINISHED"}


class CLONE_FIELDS_OT_select_effector_object(bpy.types.Operator):
    bl_idname = "clone_fields.select_effector_object"
    bl_label = "Select Effector Object"
    bl_description = "Select this Effector in the scene for moving or animation"
    bl_options = {"REGISTER", "UNDO"}

    slot_index: IntProperty(min=0, max=2)

    def execute(self, context):
        cloner_object = context.object
        if modifier_inputs.get_cloner_modifier(cloner_object) is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        settings = cloner_object.clone_fields_cloner
        settings.selected_effector_slot = self.slot_index
        effector = getattr(settings, EFFECTOR_SLOT_PROPERTIES[self.slot_index]["object"])
        if effector is None:
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        effector.select_set(True)
        context.view_layer.objects.active = effector
        return {"FINISHED"}


class CLONE_FIELDS_OT_delete_effector(bpy.types.Operator):
    bl_idname = "clone_fields.delete_effector"
    bl_label = "Delete Effector"
    bl_description = "Remove this Effector from the stack and delete its scene object"
    bl_options = {"REGISTER", "UNDO"}

    slot_index: IntProperty(min=0, max=2)

    def execute(self, context):
        cloner_object = context.object
        if modifier_inputs.get_cloner_modifier(cloner_object) is None:
            self.report({"ERROR"}, "Select a Clone Fields cloner first")
            return {"CANCELLED"}

        settings = cloner_object.clone_fields_cloner
        slot = EFFECTOR_SLOT_PROPERTIES[self.slot_index]
        effector = getattr(settings, slot["object"])
        if effector is None:
            return {"CANCELLED"}

        for index in range(self.slot_index, len(EFFECTOR_SLOT_PROPERTIES) - 1):
            _copy_effector_slot(settings, index + 1, index)
        _clear_effector_slot(settings, len(EFFECTOR_SLOT_PROPERTIES) - 1)

        if not _is_effector_referenced(effector) and effector.name in bpy.data.objects:
            bpy.data.objects.remove(effector, do_unlink=True)

        settings.selected_effector_slot = _nearest_used_effector_slot(
            settings,
            min(self.slot_index, len(EFFECTOR_SLOT_PROPERTIES) - 1),
        )
        bpy.ops.object.select_all(action="DESELECT")
        cloner_object.select_set(True)
        context.view_layer.objects.active = cloner_object
        return {"FINISHED"}


classes = (
    CLONE_FIELDS_OT_add_cloner,
    CLONE_FIELDS_OT_add_plain_effector,
    CLONE_FIELDS_OT_link_existing_effector,
    CLONE_FIELDS_OT_move_plain_effector,
    CLONE_FIELDS_OT_select_plain_effector,
    CLONE_FIELDS_OT_select_effector_object,
    CLONE_FIELDS_OT_delete_effector,
)


def _first_empty_effector_slot(settings) -> int | None:
    for index, slot_properties in enumerate(EFFECTOR_SLOT_PROPERTIES):
        if getattr(settings, slot_properties["object"]) is None:
            return index
    return None


def _assign_effector_to_slot(
    settings,
    modifier,
    slot_index: int,
    effector: bpy.types.Object,
    shape: str,
) -> None:
    slot_properties = EFFECTOR_SLOT_PROPERTIES[slot_index]
    _reset_effector_slot(settings, slot_index)
    setattr(settings, slot_properties["shape"], shape)
    setattr(settings, slot_properties["object"], effector)
    setattr(settings, slot_properties["enabled"], True)
    settings.selected_effector_slot = slot_index
    modifier_inputs.set_modifier_input(
        modifier,
        properties.EFFECTOR_SOCKET_SETS[slot_index]["object"],
        effector,
    )


def _effector_already_linked(settings, effector: bpy.types.Object) -> bool:
    return any(
        getattr(settings, slot["object"]) == effector
        for slot in EFFECTOR_SLOT_PROPERTIES
    )


def _reset_effector_slot(settings, slot_index: int) -> None:
    slot_properties = EFFECTOR_SLOT_PROPERTIES[slot_index]
    socket_set = properties.EFFECTOR_SOCKET_SETS[slot_index]
    for key, property_name in slot_properties.items():
        if key in {"object", "shape"}:
            continue
        default = (
            properties.EFFECTOR_STRENGTH_PERCENT_DEFAULT
            if key == "strength"
            else properties.GRID_INPUT_DEFAULTS[socket_set[key]]
        )
        setattr(settings, property_name, default)


def _clear_effector_slot(settings, slot_index: int) -> None:
    slot_properties = EFFECTOR_SLOT_PROPERTIES[slot_index]
    setattr(settings, slot_properties["object"], None)
    setattr(settings, slot_properties["shape"], effectors.FIELD_SHAPE_SPHERE)
    _reset_effector_slot(settings, slot_index)


def _copy_effector_slot(settings, source_index: int, target_index: int) -> None:
    source = EFFECTOR_SLOT_PROPERTIES[source_index]
    target = EFFECTOR_SLOT_PROPERTIES[target_index]
    keys = ("shape", "object") + tuple(
        key for key in source if key not in {"shape", "object"}
    )
    for key in keys:
        setattr(settings, target[key], getattr(settings, source[key]))


def _nearest_used_effector_slot(settings, start_index: int) -> int:
    for index in range(start_index, len(EFFECTOR_SLOT_PROPERTIES)):
        if getattr(settings, EFFECTOR_SLOT_PROPERTIES[index]["object"]) is not None:
            return index
    for index in range(start_index - 1, -1, -1):
        if getattr(settings, EFFECTOR_SLOT_PROPERTIES[index]["object"]) is not None:
            return index
    return 0


def _is_effector_referenced(effector: bpy.types.Object) -> bool:
    for obj in bpy.data.objects:
        if modifier_inputs.get_cloner_modifier(obj) is None:
            continue
        settings = obj.clone_fields_cloner
        if _effector_already_linked(settings, effector):
            return True
    return False


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
