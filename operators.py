"""Operators for Clone Fields."""

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty

from . import cloner, modifier_inputs, properties


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


classes = (CLONE_FIELDS_OT_add_cloner,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
