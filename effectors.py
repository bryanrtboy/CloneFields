"""Shared effector metadata and object helpers."""

from __future__ import annotations

import bpy

from . import properties


EFFECTOR_TYPE_BASIC = "BASIC"
LEGACY_EFFECTOR_TYPE_PLAIN = "PLAIN"
FIELD_SHAPE_SPHERE = "SPHERE"

FIELD_SHAPE_ITEMS = (
    (FIELD_SHAPE_SPHERE, "Spherical", "Spherical field"),
)

FIELD_SHAPE_LABELS = {
    FIELD_SHAPE_SPHERE: "Spherical",
}

EFFECTOR_SLOT_PROPERTIES = (
    {
        "object": "effector_object",
        "shape": "effector_shape",
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
        "shape": "effector2_shape",
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
        "shape": "effector3_shape",
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


def field_shape_label(shape: str) -> str:
    return FIELD_SHAPE_LABELS.get(shape, "Spherical")


def basic_effector_name(shape: str) -> str:
    return f"Basic Effector [{field_shape_label(shape)}]"


def is_effector_object(obj: bpy.types.Object | None) -> bool:
    if obj is None:
        return False
    return obj.get(properties.PROP_EFFECTOR_TYPE) in {
        EFFECTOR_TYPE_BASIC,
        LEGACY_EFFECTOR_TYPE_PLAIN,
    }


def configure_effector_object(obj: bpy.types.Object, shape: str, radius: float) -> None:
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = radius
    obj.show_name = True
    obj.hide_render = True
    obj.scale = (1.0, 1.0, 1.0)
    obj.lock_scale = (True, True, True)
    obj[properties.PROP_EFFECTOR_TYPE] = EFFECTOR_TYPE_BASIC
    obj[properties.PROP_EFFECTOR_SHAPE] = shape


def rename_effector_object(obj: bpy.types.Object | None, shape: str) -> None:
    if obj is None:
        return
    obj.name = basic_effector_name(shape)
    obj[properties.PROP_EFFECTOR_SHAPE] = shape
