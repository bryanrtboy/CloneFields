"""Add menu integration for Clone Fields."""

from __future__ import annotations

import bpy


class VIEW3D_MT_clone_fields_add(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_clone_fields_add"
    bl_label = "Clone Fields"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("clone_fields.add_cloner", text="Cloner", icon="OUTLINER_OB_EMPTY")


def draw_add_menu(self, context):
    self.layout.menu(VIEW3D_MT_clone_fields_add.bl_idname, icon="MOD_ARRAY")


classes = (VIEW3D_MT_clone_fields_add,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_add.append(draw_add_menu)


def unregister() -> None:
    bpy.types.VIEW3D_MT_add.remove(draw_add_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

