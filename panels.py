"""Custom modifier-tab UI for Clone Fields cloners."""

import bpy

from . import effectors, modifier_inputs, object_settings


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
        elif settings.distribution_mode == "BRICK":
            _draw_brick(layout, settings)
        elif settings.distribution_mode == "LINEAR":
            _draw_linear(layout, settings)
        elif settings.distribution_mode == "RADIAL":
            _draw_radial(layout, settings)
        elif settings.distribution_mode == "OBJECT":
            _draw_object(layout, settings)

        _draw_effectors(layout, settings)
        _draw_source_transform(layout, settings)


def _draw_grid(layout, settings) -> None:
    layout.prop(settings, "spacing_mode")
    _draw_xyz_row(layout, settings, "Count", "count_x", "count_y", "count_z")
    label = "Spacing" if settings.spacing_mode == "PER_STEP" else "Endpoint"
    _draw_xyz_row(layout, settings, label, "spacing_x", "spacing_y", "spacing_z")


def _draw_brick(layout, settings) -> None:
    _draw_grid(layout, settings)
    layout.prop(settings, "brick_row_offset")
    layout.prop(settings, "brick_layer_offset")


def _draw_linear(layout, settings) -> None:
    layout.prop(settings, "spacing_mode")
    layout.prop(settings, "linear_count")
    label = "Spacing" if settings.spacing_mode == "PER_STEP" else "Endpoint"
    layout.prop(settings, "linear_spacing", text=label)
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


def _draw_object(layout, settings) -> None:
    layout.prop(settings, "object_distribution_object")
    is_curve_object = object_settings.is_curve_distribution_object(
        settings.object_distribution_object
    )
    if is_curve_object:
        row = layout.row()
        row.label(text="Placement")
        row.label(text="Spline Points")
    else:
        layout.prop(settings, "object_distribution_mode")
    if is_curve_object or settings.object_distribution_mode == "SPLINE":
        layout.prop(settings, "object_spline_distribution", text="Distribution")
        if settings.object_spline_distribution in {"COUNT", "EVEN"}:
            layout.prop(settings, "object_spline_count", text="Count")
        elif settings.object_spline_distribution == "STEP":
            layout.prop(settings, "object_spline_step", text="Step")
        if settings.object_spline_distribution != "EVALUATED":
            layout.prop(settings, "object_spline_per_spline")
        layout.prop(settings, "object_spline_smooth_rotation")
        row = layout.row(align=True)
        row.use_property_split = False
        row.label(text="Alignment")
        row.prop_enum(settings, "object_alignment", "NONE", text="None")
        row.prop_enum(settings, "object_alignment", "TANGENT", text="Tangent")
    else:
        if settings.object_distribution_mode == "SURFACE":
            layout.prop(settings, "object_surface_distribution")
            if settings.object_surface_distribution == "UV_GRID":
                layout.prop(settings, "object_surface_u_count")
                layout.prop(settings, "object_surface_v_count")
                layout.prop(settings, "object_surface_uv_map")
            elif settings.object_surface_distribution in {"COUNT", "EVEN"}:
                layout.prop(settings, "object_surface_count")
            else:
                layout.prop(settings, "object_surface_density")
            if settings.object_surface_distribution == "POISSON":
                layout.prop(settings, "object_surface_distance_min")
            if settings.object_surface_distribution != "UV_GRID":
                layout.prop(settings, "object_surface_seed")
        layout.prop(settings, "object_use_vertex_map")
        if settings.object_use_vertex_map:
            layout.prop(settings, "object_vertex_map")
            layout.prop(settings, "object_vertex_map_threshold")
        row = layout.row(align=True)
        row.use_property_split = False
        row.label(text="Alignment")
        row.prop_enum(settings, "object_alignment", "NONE", text="None")
        row.prop_enum(settings, "object_alignment", "NORMALS", text="Normals")
        row.prop_enum(settings, "object_alignment", "CENTER", text="Center")
        if settings.object_alignment in {"NORMALS", "CENTER"}:
            layout.prop(settings, "object_up_vector")


def _draw_effectors(layout, settings) -> None:
    layout.label(text="Effectors")
    list_box = layout.box()
    has_empty_slot = False
    for index, slot in enumerate(effectors.EFFECTOR_SLOT_PROPERTIES):
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
        select_scene = row.operator(
            "clone_fields.select_effector_object",
            text="",
            icon="RESTRICT_SELECT_OFF",
        )
        select_scene.slot_index = index
        move_up = row.operator("clone_fields.move_plain_effector", text="", icon="TRIA_UP")
        move_up.slot_index = index
        move_up.direction = -1
        move_down = row.operator("clone_fields.move_plain_effector", text="", icon="TRIA_DOWN")
        move_down.slot_index = index
        move_down.direction = 1
        delete = row.operator("clone_fields.delete_effector", text="", icon="X")
        delete.slot_index = index

    if has_empty_slot:
        add_row = list_box.row(align=True)
        add_row.operator("clone_fields.add_plain_effector", text="New Basic")
        add_row.operator("clone_fields.add_random_effector", text="New Random")
        add_row = list_box.row(align=True)
        add_row.operator("clone_fields.add_target_effector", text="New Target")
        add_row.operator("clone_fields.add_shader_effector", text="New Shader")
        add_row = list_box.row(align=True)
        add_row.operator("clone_fields.add_step_effector", text="New Step")
        add_row.operator("clone_fields.link_existing_effector", text="Link Existing")

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
    effector = getattr(settings, slot["object"])
    if effector is None:
        return

    box.label(text=effector.name)
    effector_settings = getattr(effector, "clone_fields_effector", None)
    if effector_settings is None:
        return

    box.separator()
    box.label(text="Effector")
    _draw_effector_settings(box, settings, slot, effector_settings)

    box.separator()
    box.label(text="Field")
    _draw_field_settings(box, effector_settings)


def _draw_effector_settings(box, settings, slot, effector_settings) -> None:
    if effector_settings.type == effectors.EFFECTOR_TYPE_RANDOM:
        box.prop(effector_settings, "seed")
    elif effector_settings.type == effectors.EFFECTOR_TYPE_STEP:
        box.prop(effector_settings, "invert", text="Reverse")
    elif effector_settings.type == effectors.EFFECTOR_TYPE_SHADER:
        image_row = box.row(align=True)
        image_row.prop_search(
            effector_settings,
            "shader_image",
            bpy.data,
            "images",
            text="Image",
        )
        image_row.operator("clone_fields.load_shader_image", text="", icon="FILE_FOLDER")
        clear = image_row.row(align=True)
        clear.enabled = effector_settings.shader_image is not None
        clear.operator("clone_fields.clear_shader_image", text="", icon="X")
        if effector_settings.shader_image is not None:
            box.template_preview(effector_settings.shader_image, show_buttons=False)
        box.prop(effector_settings, "shader_preserve_aspect")
        size_row = box.row(align=True)
        size_row.label(text="Projection Size")
        size_row.prop(effector_settings, "shader_width", text="")
        size_row.prop(effector_settings, "shader_height", text="")
        tiles_row = box.row(align=True)
        tiles_row.label(text="Tiles")
        tiles_row.prop(effector_settings, "shader_tiles_x", text="")
        tiles_row.prop(effector_settings, "shader_tiles_y", text="")
        if settings.distribution_mode == "GRID":
            fit_row = box.row(align=True)
            if effector_settings.shader_preserve_aspect:
                fit_row.prop(effector_settings, "shader_fit_mode", text="")
            fit_row.operator("clone_fields.fit_shader_to_grid", icon="FULLSCREEN_ENTER")
        box.prop(effector_settings, "invert", text="Invert Image")
    box.prop(effector_settings, "strength")

    if effector_settings.type == effectors.EFFECTOR_TYPE_TARGET:
        box.prop(effector_settings, "target_object", text="Target")
        axis_row = box.row(align=True)
        axis_row.prop(effector_settings, "target_axis")
        axis_row.prop(effector_settings, "target_up_axis")
    else:
        box.prop(effector_settings, "use_position")
    if effector_settings.type != effectors.EFFECTOR_TYPE_TARGET and effector_settings.use_position:
        label = "Position Variation" if effector_settings.type == effectors.EFFECTOR_TYPE_RANDOM else ""
        _draw_xyz_row(box, effector_settings, label, "position_x", "position_y", "position_z")

    if effector_settings.type != effectors.EFFECTOR_TYPE_TARGET:
        box.prop(effector_settings, "use_rotation")
    if effector_settings.type != effectors.EFFECTOR_TYPE_TARGET and effector_settings.use_rotation:
        label = "Rotation Variation" if effector_settings.type == effectors.EFFECTOR_TYPE_RANDOM else ""
        _draw_xyz_row(box, effector_settings, label, "rotation_x", "rotation_y", "rotation_z")

    if effector_settings.type != effectors.EFFECTOR_TYPE_TARGET:
        box.prop(effector_settings, "use_scale")
    if effector_settings.type != effectors.EFFECTOR_TYPE_TARGET and effector_settings.use_scale:
        label = "Scale Variation" if effector_settings.type == effectors.EFFECTOR_TYPE_RANDOM else ""
        _draw_xyz_row(box, effector_settings, label, "scale_x", "scale_y", "scale_z")

    box.separator()
    box.prop(settings, slot["strength"], text="Cloner Influence")


def _draw_field_settings(box, effector_settings) -> None:
    box.prop(effector_settings, "shape", text="Shape")
    if effector_settings.shape == effectors.FIELD_SHAPE_NONE:
        return

    if effector_settings.shape == effectors.FIELD_SHAPE_LINEAR:
        box.prop(effector_settings, "length")
    elif effector_settings.shape == effectors.FIELD_SHAPE_CUBE:
        box.prop(effector_settings, "box_uniform")
        _draw_xyz_row(
            box,
            effector_settings,
            "Size",
            "box_x",
            "box_y",
            "box_z",
        )
    else:
        box.prop(effector_settings, "radius")
    if effector_settings.shape == effectors.FIELD_SHAPE_CYLINDER:
        box.prop(effector_settings, "height")
    box.prop(effector_settings, "falloff")
    if effector_settings.type not in {
        effectors.EFFECTOR_TYPE_SHADER,
        effectors.EFFECTOR_TYPE_STEP,
    }:
        box.prop(effector_settings, "invert", text="Invert Field")


def _selected_effector_slot(settings):
    selected_index = min(
        max(settings.selected_effector_slot, 0),
        len(effectors.EFFECTOR_SLOT_PROPERTIES) - 1,
    )
    selected_slot = effectors.EFFECTOR_SLOT_PROPERTIES[selected_index]
    if getattr(settings, selected_slot["object"]) is not None:
        return selected_slot
    for slot in effectors.EFFECTOR_SLOT_PROPERTIES:
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
