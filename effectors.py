"""Shared effector metadata and object helpers."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent
from mathutils import Vector

from . import properties


EFFECTOR_TYPE_BASIC = "BASIC"
EFFECTOR_TYPE_RANDOM = "RANDOM"
EFFECTOR_TYPE_TARGET = "TARGET"
EFFECTOR_TYPE_SHADER = "SHADER"
EFFECTOR_TYPE_STEP = "STEP"
LEGACY_EFFECTOR_TYPE_PLAIN = "PLAIN"
EFFECTOR_TYPE_VALUES = {
    EFFECTOR_TYPE_BASIC: 0,
    EFFECTOR_TYPE_RANDOM: 1,
    EFFECTOR_TYPE_TARGET: 2,
    EFFECTOR_TYPE_SHADER: 3,
    EFFECTOR_TYPE_STEP: 4,
    LEGACY_EFFECTOR_TYPE_PLAIN: 0,
}
EFFECTOR_TYPE_ITEMS = (
    (EFFECTOR_TYPE_BASIC, "Basic", "Basic transform effector"),
    (EFFECTOR_TYPE_RANDOM, "Random", "Random transform effector"),
    (EFFECTOR_TYPE_TARGET, "Target", "Orient clones toward the Effector"),
    (EFFECTOR_TYPE_SHADER, "Shader", "Use image luminance to vary clone transforms"),
    (EFFECTOR_TYPE_STEP, "Step", "Apply transforms progressively by clone order"),
)
EFFECTOR_TYPE_LABELS = {
    EFFECTOR_TYPE_BASIC: "Basic",
    EFFECTOR_TYPE_RANDOM: "Random",
    EFFECTOR_TYPE_TARGET: "Target",
    EFFECTOR_TYPE_SHADER: "Shader",
    EFFECTOR_TYPE_STEP: "Step",
    LEGACY_EFFECTOR_TYPE_PLAIN: "Basic",
}
TARGET_AXIS_ITEMS = (
    ("X", "X", "Aim the source object's local X axis at the target"),
    ("Y", "Y", "Aim the source object's local Y axis at the target"),
    ("Z", "Z", "Aim the source object's local Z axis at the target"),
)
TARGET_AXIS_VALUES = {"X": 0, "Y": 1, "Z": 2}
FIELD_SHAPE_SPHERE = "SPHERE"
FIELD_SHAPE_CUBE = "CUBE"
FIELD_SHAPE_CYLINDER = "CYLINDER"
FIELD_SHAPE_LINEAR = "LINEAR"
FIELD_SHAPE_NONE = "NONE"
FIELD_SHAPE_VALUES = {
    FIELD_SHAPE_SPHERE: 0,
    FIELD_SHAPE_CUBE: 1,
    FIELD_SHAPE_CYLINDER: 2,
    FIELD_SHAPE_LINEAR: 3,
    FIELD_SHAPE_NONE: 4,
}

FIELD_SHAPE_ITEMS = (
    (FIELD_SHAPE_NONE, "None", "Affect all clones without a field shape"),
    (FIELD_SHAPE_SPHERE, "Spherical", "Spherical field"),
    (FIELD_SHAPE_CUBE, "Cubic", "Cubic field"),
    (FIELD_SHAPE_CYLINDER, "Cylindrical", "Cylindrical field"),
    (FIELD_SHAPE_LINEAR, "Linear", "Linear field"),
)

FIELD_SHAPE_LABELS = {
    FIELD_SHAPE_NONE: "None",
    FIELD_SHAPE_SPHERE: "Spherical",
    FIELD_SHAPE_CUBE: "Cubic",
    FIELD_SHAPE_CYLINDER: "Cylindrical",
    FIELD_SHAPE_LINEAR: "Linear",
}

EFFECTOR_SLOT_PROPERTIES = (
    {
        "object": "effector_object",
        "type": "effector_type",
        "shape": "effector_shape",
        "seed": "effector_seed",
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
        "target_axis": "effector_target_axis",
        "target_up_axis": "effector_target_up_axis",
        "target_object": "effector_target_object",
        "use_scale": "effector_use_scale",
        "scale_uniform": "effector_scale_uniform",
        "scale_absolute": "effector_scale_absolute",
        "scale_x": "effector_scale_x",
        "scale_y": "effector_scale_y",
        "scale_z": "effector_scale_z",
    },
    {
        "object": "effector2_object",
        "type": "effector2_type",
        "shape": "effector2_shape",
        "seed": "effector2_seed",
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
        "target_axis": "effector2_target_axis",
        "target_up_axis": "effector2_target_up_axis",
        "target_object": "effector2_target_object",
        "use_scale": "effector2_use_scale",
        "scale_uniform": "effector2_scale_uniform",
        "scale_absolute": "effector2_scale_absolute",
        "scale_x": "effector2_scale_x",
        "scale_y": "effector2_scale_y",
        "scale_z": "effector2_scale_z",
    },
    {
        "object": "effector3_object",
        "type": "effector3_type",
        "shape": "effector3_shape",
        "seed": "effector3_seed",
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
        "target_axis": "effector3_target_axis",
        "target_up_axis": "effector3_target_up_axis",
        "target_object": "effector3_target_object",
        "use_scale": "effector3_use_scale",
        "scale_uniform": "effector3_scale_uniform",
        "scale_absolute": "effector3_scale_absolute",
        "scale_x": "effector3_scale_x",
        "scale_y": "effector3_scale_y",
        "scale_z": "effector3_scale_z",
    },
)

EFFECTOR_GLOBAL_KEYS = (
    "type",
    "shape",
    "seed",
    "invert",
    "radius",
    "box_x",
    "box_y",
    "box_z",
    "height",
    "length",
    "falloff",
    "use_position",
    "position_x",
    "position_y",
    "position_z",
    "use_rotation",
    "rotation_x",
    "rotation_y",
    "rotation_z",
    "target_axis",
    "target_up_axis",
    "target_object",
    "shader_image",
    "shader_width",
    "shader_height",
    "shader_tiles_x",
    "shader_tiles_y",
    "use_scale",
    "scale_uniform",
    "scale_absolute",
    "scale_x",
    "scale_y",
    "scale_z",
)

_CONSTRAINT_TIMER_REGISTERED = False


def field_shape_label(shape: str) -> str:
    return FIELD_SHAPE_LABELS.get(shape, "Spherical")


def effector_type_label(effector_type: str) -> str:
    return EFFECTOR_TYPE_LABELS.get(effector_type, "Basic")


def effector_type_value(effector_type: str) -> int:
    return EFFECTOR_TYPE_VALUES.get(effector_type, EFFECTOR_TYPE_VALUES[EFFECTOR_TYPE_BASIC])


def target_axis_value(axis: str) -> int:
    return TARGET_AXIS_VALUES.get(axis, TARGET_AXIS_VALUES["Z"])


def effector_name(effector_type: str, shape: str) -> str:
    return f"{effector_type_label(effector_type)} Effector [{field_shape_label(shape)}]"


def basic_effector_name(shape: str) -> str:
    return effector_name(EFFECTOR_TYPE_BASIC, shape)


def random_effector_name(shape: str) -> str:
    return effector_name(EFFECTOR_TYPE_RANDOM, shape)


def is_effector_object(obj: bpy.types.Object | None) -> bool:
    if obj is None:
        return False
    return obj.get(properties.PROP_EFFECTOR_TYPE) in {
        EFFECTOR_TYPE_BASIC,
        EFFECTOR_TYPE_RANDOM,
        EFFECTOR_TYPE_TARGET,
        EFFECTOR_TYPE_SHADER,
        EFFECTOR_TYPE_STEP,
        LEGACY_EFFECTOR_TYPE_PLAIN,
    }


def configure_effector_object(
    obj: bpy.types.Object,
    shape: str,
    radius: float,
    effector_type: str | None = None,
    *,
    box_size: tuple[float, float, float] | None = None,
) -> None:
    display_size = radius
    if effector_type == EFFECTOR_TYPE_SHADER:
        obj.empty_display_type = "PLAIN_AXES"
    elif shape == FIELD_SHAPE_NONE:
        obj.empty_display_type = "PLAIN_AXES"
    elif shape == FIELD_SHAPE_CUBE:
        obj.empty_display_type = "PLAIN_AXES"
        display_size = min(0.5, max(0.05, radius * 0.025))
    elif shape == FIELD_SHAPE_CYLINDER:
        obj.empty_display_type = "CIRCLE"
    elif shape == FIELD_SHAPE_LINEAR:
        obj.empty_display_type = "ARROWS"
    else:
        obj.empty_display_type = "SPHERE"
    obj.empty_display_size = display_size
    obj.show_name = True
    obj.hide_render = True
    obj.scale = (1.0, 1.0, 1.0)
    obj.lock_scale = (True, True, True)
    obj[properties.PROP_EFFECTOR_TYPE] = effector_type or obj.get(
        properties.PROP_EFFECTOR_TYPE,
        EFFECTOR_TYPE_BASIC,
    )
    obj[properties.PROP_EFFECTOR_SHAPE] = shape


def configure_shader_display(obj: bpy.types.Object, settings) -> None:
    """Keep the selectable controller separate from the custom image preview."""
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = max(settings.shader_width, settings.shader_height) * 0.025
    obj.scale = (1.0, 1.0, 1.0)


def fit_shader_to_grid(effector: bpy.types.Object, cloner: bpy.types.Object) -> bool:
    if (
        not is_effector_object(effector)
        or not hasattr(effector, "clone_fields_effector")
        or not hasattr(cloner, "clone_fields_cloner")
    ):
        return False
    effector_settings = effector.clone_fields_effector
    cloner_settings = cloner.clone_fields_cloner
    if (
        effector_settings.type != EFFECTOR_TYPE_SHADER
        or cloner_settings.distribution_mode != "GRID"
    ):
        return False

    width = _grid_cell_footprint(
        cloner_settings.spacing_x,
        cloner_settings.count_x,
        cloner_settings.spacing_mode,
    )
    height = _grid_cell_footprint(
        cloner_settings.spacing_y,
        cloner_settings.count_y,
        cloner_settings.spacing_mode,
    )
    bounds = _evaluated_local_bounds(cloner)
    if bounds is not None:
        bounds_center, bounds_size = bounds
        width = max(0.001, bounds_size.x)
        height = max(0.001, bounds_size.y)
    else:
        bounds_center = Vector((0.0, 0.0, 0.0))

    image = effector_settings.shader_image
    if (
        effector_settings.shader_preserve_aspect
        and image is not None
        and image.size[0] > 0
        and image.size[1] > 0
    ):
        aspect = image.size[0] / image.size[1]
        if effector_settings.shader_fit_mode == "CONTAIN":
            width = min(width, height * aspect)
        else:
            width = max(width, height * aspect)
        height = width / aspect

    effector.location = cloner.matrix_world @ bounds_center
    rotation_order = (
        effector.rotation_mode
        if effector.rotation_mode in {"XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"}
        else "XYZ"
    )
    effector.rotation_euler = cloner.matrix_world.to_quaternion().to_euler(rotation_order)
    effector_settings.shader_width = max(0.001, width)
    if not effector_settings.shader_preserve_aspect:
        effector_settings.shader_height = max(0.001, height)
    configure_shader_display(effector, effector_settings)
    return True


def _grid_cell_footprint(spacing: float, count: int, spacing_mode: str) -> float:
    if spacing_mode == "PER_STEP":
        return max(0.001, spacing * max(1, count))
    if count <= 1:
        return max(0.001, spacing)
    return max(0.001, spacing * count / (count - 1))


def _evaluated_local_bounds(
    obj: bpy.types.Object,
) -> tuple[Vector, Vector] | None:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        if not mesh.vertices:
            return None
        xs = [vertex.co.x for vertex in mesh.vertices]
        ys = [vertex.co.y for vertex in mesh.vertices]
        zs = [vertex.co.z for vertex in mesh.vertices]
        minimum = Vector((min(xs), min(ys), min(zs)))
        maximum = Vector((max(xs), max(ys), max(zs)))
        return (minimum + maximum) * 0.5, maximum - minimum
    finally:
        evaluated.to_mesh_clear()


def enforce_effector_transform_constraints(obj: bpy.types.Object) -> bool:
    changed = False
    if obj.lock_scale[:] != (True, True, True):
        obj.lock_scale = (True, True, True)
        changed = True
    expected_scale = (1.0, 1.0, 1.0)
    if any(abs(value - expected) > 0.0001 for value, expected in zip(obj.scale, expected_scale)):
        obj.scale = expected_scale
        changed = True
    return changed


def enforce_all_effector_transform_constraints() -> None:
    for obj in bpy.data.objects:
        if is_effector_object(obj) and enforce_effector_transform_constraints(obj):
            tag_referencing_cloners(obj)


def field_shape_value(shape: str) -> int:
    return FIELD_SHAPE_VALUES.get(shape, FIELD_SHAPE_VALUES[FIELD_SHAPE_SPHERE])


def rename_effector_object(
    obj: bpy.types.Object | None,
    shape: str,
    effector_type: str | None = None,
) -> None:
    if obj is None:
        return
    obj_type = effector_type or obj.get(properties.PROP_EFFECTOR_TYPE, EFFECTOR_TYPE_BASIC)
    obj.name = effector_name(obj_type, shape)
    obj[properties.PROP_EFFECTOR_TYPE] = obj_type
    obj[properties.PROP_EFFECTOR_SHAPE] = shape


def sync_effector_to_referencing_cloners(effector: bpy.types.Object) -> None:
    if not is_effector_object(effector):
        return

    from . import modifier_inputs

    for cloner in bpy.data.objects:
        modifier = modifier_inputs.get_cloner_modifier(cloner)
        if modifier is None:
            continue
        settings = cloner.clone_fields_cloner
        for slot_index, slot in enumerate(EFFECTOR_SLOT_PROPERTIES):
            if getattr(settings, slot["object"]) == effector:
                sync_effector_slot(settings, modifier, slot_index)
                modifier_inputs.tag_modifier_owner(modifier)


def sync_effector_slot(settings, modifier, slot_index: int) -> None:
    effector = getattr(settings, EFFECTOR_SLOT_PROPERTIES[slot_index]["object"])
    if not is_effector_object(effector) or not hasattr(effector, "clone_fields_effector"):
        return

    from . import modifier_inputs

    slot = EFFECTOR_SLOT_PROPERTIES[slot_index]
    sockets = properties.EFFECTOR_SOCKET_SETS[slot_index]
    effector_settings = effector.clone_fields_effector
    configure_effector_object(
        effector,
        effector_settings.shape,
        effector_settings.radius,
        effector_settings.type,
        box_size=(
            effector_settings.box_x,
            effector_settings.box_y,
            effector_settings.box_z,
        ),
    )
    rename_effector_object(effector, effector_settings.shape, effector_settings.type)
    if effector_settings.type == EFFECTOR_TYPE_SHADER:
        configure_shader_display(effector, effector_settings)

    modifier_inputs.set_modifier_input(modifier, sockets["object"], effector)
    modifier_inputs.set_modifier_input(
        modifier,
        sockets["field"],
        field_shape_value(effector_settings.shape),
    )
    for key in EFFECTOR_GLOBAL_KEYS:
        if key == "shape":
            continue
        if key == "type":
            value = effector_type_value(effector_settings.type)
        elif key in {"target_axis", "target_up_axis"}:
            value = target_axis_value(getattr(effector_settings, key))
        else:
            value = getattr(effector_settings, key)
        modifier_inputs.set_modifier_input(modifier, sockets[key], value)

    modifier_inputs.set_modifier_input(
        modifier,
        sockets["use_target_object"],
        effector_settings.target_object is not None,
    )

    combined_strength = (
        effector_settings.strength
        * getattr(settings, slot["strength"])
        / 10000.0
    )
    modifier_inputs.set_modifier_input(modifier, sockets["strength"], combined_strength)


def clear_missing_effector_slots() -> None:
    from . import modifier_inputs

    for cloner in bpy.data.objects:
        modifier = modifier_inputs.get_cloner_modifier(cloner)
        if modifier is None or not hasattr(cloner, "clone_fields_cloner"):
            continue
        settings = cloner.clone_fields_cloner
        changed = False
        for slot_index, slot in enumerate(EFFECTOR_SLOT_PROPERTIES):
            effector = getattr(settings, slot["object"])
            socket_set = properties.EFFECTOR_SOCKET_SETS[slot_index]
            modifier_effector = modifier_inputs.get_modifier_input(
                modifier,
                socket_set["object"],
            )
            if (
                effector is not None
                or (
                    modifier_effector is None
                    and not getattr(settings, slot["enabled"])
                )
            ):
                continue
            setattr(settings, slot["enabled"], False)
            modifier_inputs.set_modifier_input(modifier, socket_set["enabled"], False)
            modifier_inputs.set_modifier_input(modifier, socket_set["object"], None)
            changed = True
        if changed:
            modifier_inputs.tag_modifier_owner(modifier)


def tag_referencing_cloners(effector: bpy.types.Object) -> None:
    if not is_effector_object(effector):
        return

    from . import modifier_inputs

    for cloner in bpy.data.objects:
        modifier = modifier_inputs.get_cloner_modifier(cloner)
        if modifier is None:
            continue
        settings = cloner.clone_fields_cloner
        if any(
            getattr(settings, slot["object"]) == effector
            for slot in EFFECTOR_SLOT_PROPERTIES
        ):
            modifier_inputs.tag_modifier_owner(modifier)


@persistent
def _depsgraph_update_post(scene, depsgraph) -> None:
    for update in depsgraph.updates:
        datablock = update.id
        if isinstance(datablock, bpy.types.Object) and is_effector_object(datablock):
            enforce_effector_transform_constraints(datablock)
            tag_referencing_cloners(datablock)
    clear_missing_effector_slots()


def _effector_constraint_timer() -> float | None:
    if not _CONSTRAINT_TIMER_REGISTERED:
        return None
    enforce_all_effector_transform_constraints()
    return 0.25


def register() -> None:
    global _CONSTRAINT_TIMER_REGISTERED
    if _depsgraph_update_post not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_depsgraph_update_post)
    if not _CONSTRAINT_TIMER_REGISTERED:
        _CONSTRAINT_TIMER_REGISTERED = True
        bpy.app.timers.register(_effector_constraint_timer, first_interval=0.25, persistent=True)


def unregister() -> None:
    global _CONSTRAINT_TIMER_REGISTERED
    _CONSTRAINT_TIMER_REGISTERED = False
    if _depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_depsgraph_update_post)
