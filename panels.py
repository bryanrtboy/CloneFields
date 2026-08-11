"""Custom modifier-tab UI for Clone Fields cloners."""

import bpy

from . import modifier_inputs
from .operators import EFFECTOR_SLOT_PROPERTIES


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

        _draw_effectors(layout, settings)
        _draw_source_transform(layout, settings)


def _draw_grid(layout, settings) -> None:
    _draw_xyz_row(layout, settings, "Count", "count_x", "count_y", "count_z")
    _draw_xyz_row(layout, settings, "Spacing", "spacing_x", "spacing_y", "spacing_z")


def _draw_linear(layout, settings) -> None:
    layout.prop(settings, "linear_count")
    layout.prop(settings, "linear_spacing")
    _draw_xyz_row(
        layout,
        settings,
        "Direction",
        "linear_direction_x",
        "linear_direction_y",
        "linear_direction_z",
    )


def _draw_radial(layout, settings) -> None:
    layout.prop(settings, "radial_count")
    layout.prop(settings, "radial_radius")
    layout.prop(settings, "radial_arc")
    layout.prop(settings, "radial_axis")
    layout.prop(settings, "radial_align")


def _draw_effectors(layout, settings) -> None:
    layout.label(text="Effectors")
    list_box = layout.box()
    has_empty_slot = False
    for index, slot in enumerate(EFFECTOR_SLOT_PROPERTIES):
        effector = getattr(settings, slot["object"])
        if effector is None:
            has_empty_slot = True
            continue

        row = list_box.row(align=True)
        row.prop(settings, slot["enabled"], text="")
        select = row.operator(
            "clone_fields.select_plain_effector",
            text=effector.name,
            depress=index == settings.selected_effector_slot,
        )
        select.slot_index = index
        move_up = row.operator("clone_fields.move_plain_effector", text="", icon="TRIA_UP")
        move_up.slot_index = index
        move_up.direction = -1
        move_down = row.operator("clone_fields.move_plain_effector", text="", icon="TRIA_DOWN")
        move_down.slot_index = index
        move_down.direction = 1

    if has_empty_slot:
        list_box.operator("clone_fields.add_plain_effector", text="Add Plain Effector")

    selected_slot = _selected_effector_slot(settings)
    if selected_slot is not None:
        _draw_effector_slot(layout, settings, selected_slot)


def _draw_source_transform(layout, settings) -> None:
    layout.prop(settings, "show_source_offset", text="Offset")
    if not settings.show_source_offset:
        return

    _draw_xyz_row(
        layout,
        settings,
        "Position",
        "source_position_x",
        "source_position_y",
        "source_position_z",
    )
    _draw_xyz_row(
        layout,
        settings,
        "Rotation",
        "source_rotation_x",
        "source_rotation_y",
        "source_rotation_z",
    )
    _draw_xyz_row(
        layout,
        settings,
        "Scale",
        "source_scale_x",
        "source_scale_y",
        "source_scale_z",
    )


def _draw_effector_slot(layout, settings, slot: dict) -> None:
    box = layout.box()
    box.prop(settings, slot["invert"])
    box.prop(settings, slot["strength"])
    box.prop(settings, slot["radius"])
    box.prop(settings, slot["falloff"])

    box.prop(settings, slot["use_position"])
    if getattr(settings, slot["use_position"]):
        _draw_xyz_row(box, settings, "", slot["position_x"], slot["position_y"], slot["position_z"])

    box.prop(settings, slot["use_rotation"])
    if getattr(settings, slot["use_rotation"]):
        _draw_xyz_row(box, settings, "", slot["rotation_x"], slot["rotation_y"], slot["rotation_z"])

    box.prop(settings, slot["use_scale"])
    if getattr(settings, slot["use_scale"]):
        _draw_xyz_row(box, settings, "", slot["scale_x"], slot["scale_y"], slot["scale_z"])


def _selected_effector_slot(settings):
    selected_index = min(max(settings.selected_effector_slot, 0), len(EFFECTOR_SLOT_PROPERTIES) - 1)
    selected_slot = EFFECTOR_SLOT_PROPERTIES[selected_index]
    if getattr(settings, selected_slot["object"]) is not None:
        return selected_slot
    for slot in EFFECTOR_SLOT_PROPERTIES:
        if getattr(settings, slot["object"]) is not None:
            return slot
    return None


def _draw_xyz_row(
    layout,
    settings,
    label: str,
    x_property: str,
    y_property: str,
    z_property: str,
) -> None:
    row = layout.row(align=True)
    if label:
        row.label(text=label)
    else:
        row.label(text="")
    row.prop(settings, x_property, text="")
    row.prop(settings, y_property, text="")
    row.prop(settings, z_property, text="")


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
