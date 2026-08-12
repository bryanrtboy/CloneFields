"""Shared effector metadata and object helpers."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from . import properties


EFFECTOR_TYPE_BASIC = "BASIC"
EFFECTOR_TYPE_RANDOM = "RANDOM"
LEGACY_EFFECTOR_TYPE_PLAIN = "PLAIN"
EFFECTOR_TYPE_VALUES = {
    EFFECTOR_TYPE_BASIC: 0,
    EFFECTOR_TYPE_RANDOM: 1,
    LEGACY_EFFECTOR_TYPE_PLAIN: 0,
}
EFFECTOR_TYPE_ITEMS = (
    (EFFECTOR_TYPE_BASIC, "Basic", "Basic transform effector"),
    (EFFECTOR_TYPE_RANDOM, "Random", "Random transform effector"),
)
EFFECTOR_TYPE_LABELS = {
    EFFECTOR_TYPE_BASIC: "Basic",
    EFFECTOR_TYPE_RANDOM: "Random",
    LEGACY_EFFECTOR_TYPE_PLAIN: "Basic",
}
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
        "use_scale": "effector_use_scale",
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
        "use_scale": "effector2_use_scale",
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
        "use_scale": "effector3_use_scale",
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
    "use_scale",
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
        LEGACY_EFFECTOR_TYPE_PLAIN,
    }


def configure_effector_object(
    obj: bpy.types.Object,
    shape: str,
    radius: float,
    effector_type: str | None = None,
) -> None:
    if shape == FIELD_SHAPE_NONE:
        obj.empty_display_type = "PLAIN_AXES"
    elif shape == FIELD_SHAPE_CUBE:
        obj.empty_display_type = "CUBE"
    elif shape == FIELD_SHAPE_CYLINDER:
        obj.empty_display_type = "CIRCLE"
    elif shape == FIELD_SHAPE_LINEAR:
        obj.empty_display_type = "ARROWS"
    else:
        obj.empty_display_type = "SPHERE"
    obj.empty_display_size = radius
    obj.show_name = True
    obj.hide_render = True
    obj.scale = (1.0, 1.0, 1.0)
    obj.lock_scale = (True, True, True)
    obj[properties.PROP_EFFECTOR_TYPE] = effector_type or obj.get(
        properties.PROP_EFFECTOR_TYPE,
        EFFECTOR_TYPE_BASIC,
    )
    obj[properties.PROP_EFFECTOR_SHAPE] = shape


def enforce_effector_transform_constraints(obj: bpy.types.Object) -> bool:
    changed = False
    if obj.lock_scale[:] != (True, True, True):
        obj.lock_scale = (True, True, True)
        changed = True
    if any(abs(value - 1.0) > 0.0001 for value in obj.scale):
        obj.scale = (1.0, 1.0, 1.0)
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
    )
    rename_effector_object(effector, effector_settings.shape, effector_settings.type)

    modifier_inputs.set_modifier_input(modifier, sockets["object"], effector)
    modifier_inputs.set_modifier_input(
        modifier,
        sockets["field"],
        field_shape_value(effector_settings.shape),
    )
    for key in EFFECTOR_GLOBAL_KEYS:
        if key == "shape":
            continue
        value = (
            effector_type_value(effector_settings.type)
            if key == "type"
            else getattr(effector_settings, key)
        )
        modifier_inputs.set_modifier_input(modifier, sockets[key], value)

    combined_strength = (
        effector_settings.strength
        * getattr(settings, slot["strength"])
        / 10000.0
    )
    modifier_inputs.set_modifier_input(modifier, sockets["strength"], combined_strength)


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
