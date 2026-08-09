"""Custom modifier-tab UI for Clone Fields cloners."""

import bpy

from . import modifier_inputs


class CLONE_FIELDS_PT_cloner_modifier(bpy.types.Panel):
    bl_label = "Clone Fields"
    bl_idname = "CLONE_FIELDS_PT_cloner_modifier"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"

    @classmethod
    def poll(cls, context) -> bool:
        return modifier_inputs.get_cloner_modifier(context.object) is not None

    def draw(self, context) -> None:
        obj = context.object
        settings = obj.clone_fields_cloner
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(settings, "source_object")
        layout.prop(settings, "distribution_mode")

        if settings.distribution_mode == "GRID":
            _draw_grid(layout, settings)
        elif settings.distribution_mode == "LINEAR":
            _draw_linear(layout, settings)
        elif settings.distribution_mode == "RADIAL":
            _draw_radial(layout, settings)

        _draw_source_transform(layout, settings)


def _draw_grid(layout, settings) -> None:
    layout.label(text="Count")
    column = layout.column(align=True)
    column.prop(settings, "count_x", text="X")
    column.prop(settings, "count_y", text="Y")
    column.prop(settings, "count_z", text="Z")

    layout.label(text="Spacing")
    column = layout.column(align=True)
    column.prop(settings, "spacing_x", text="X")
    column.prop(settings, "spacing_y", text="Y")
    column.prop(settings, "spacing_z", text="Z")


def _draw_linear(layout, settings) -> None:
    layout.prop(settings, "linear_count")
    layout.prop(settings, "linear_spacing")

    layout.label(text="Direction")
    column = layout.column(align=True)
    column.prop(settings, "linear_direction_x", text="X")
    column.prop(settings, "linear_direction_y", text="Y")
    column.prop(settings, "linear_direction_z", text="Z")


def _draw_radial(layout, settings) -> None:
    layout.prop(settings, "radial_count")
    layout.prop(settings, "radial_radius")
    layout.prop(settings, "radial_arc")
    layout.prop(settings, "radial_axis")
    layout.prop(settings, "radial_align")


def _draw_source_transform(layout, settings) -> None:
    layout.label(text="Source Transform")

    _draw_toggle_header(
        layout,
        settings,
        "show_source_position",
        "Position",
    )
    if settings.show_source_position:
        column = layout.column(align=True)
        column.prop(settings, "source_position_x", text="X")
        column.prop(settings, "source_position_y", text="Y")
        column.prop(settings, "source_position_z", text="Z")

    _draw_toggle_header(
        layout,
        settings,
        "show_source_rotation",
        "Rotation",
    )
    if settings.show_source_rotation:
        column = layout.column(align=True)
        column.prop(settings, "source_rotation_x", text="X")
        column.prop(settings, "source_rotation_y", text="Y")
        column.prop(settings, "source_rotation_z", text="Z")

    _draw_toggle_header(
        layout,
        settings,
        "show_source_scale",
        "Scale",
    )
    if settings.show_source_scale:
        column = layout.column(align=True)
        column.prop(settings, "source_scale_x", text="X")
        column.prop(settings, "source_scale_y", text="Y")
        column.prop(settings, "source_scale_z", text="Z")


def _draw_toggle_header(layout, settings, property_name: str, label: str) -> None:
    icon = "TRIA_DOWN" if getattr(settings, property_name) else "TRIA_RIGHT"
    row = layout.row(align=True)
    row.prop(settings, property_name, text=label, icon=icon, emboss=False)


classes = (CLONE_FIELDS_PT_cloner_modifier,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
