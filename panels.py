"""Properties editor panels for Clone Fields objects."""

from __future__ import annotations

import bpy

from . import modifier_inputs, properties


class CLONE_FIELDS_PT_cloner(bpy.types.Panel):
    bl_label = "Clone Fields"
    bl_idname = "CLONE_FIELDS_PT_cloner"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return modifier_inputs.get_cloner_modifier(context.object) is not None

    def draw(self, context):
        layout = self.layout
        obj = context.object
        modifier = modifier_inputs.get_cloner_modifier(obj)

        if modifier is None:
            layout.label(text="No Clone Fields cloner selected")
            return

        layout.use_property_split = True
        layout.use_property_decorate = False
        settings = obj.clone_fields_cloner

        layout.prop(settings, "source_object")

        layout.separator()

        count_column = layout.column(align=True)
        count_column.label(text="Count")
        count_column.prop(settings, "count_x", text="X")
        count_column.prop(settings, "count_y", text="Y")
        count_column.prop(settings, "count_z", text="Z")

        layout.separator()

        spacing_column = layout.column(align=True)
        spacing_column.label(text="Spacing")
        spacing_column.prop(settings, "spacing_x", text="X")
        spacing_column.prop(settings, "spacing_y", text="Y")
        spacing_column.prop(settings, "spacing_z", text="Z")


classes = (CLONE_FIELDS_PT_cloner,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
