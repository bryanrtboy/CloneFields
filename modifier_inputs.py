"""Helpers for Clone Fields Geometry Nodes modifier inputs."""

from __future__ import annotations

import bpy

from . import properties


GRID_SOCKET_NAMES = (
    properties.SOCKET_SOURCE_OBJECT,
    properties.SOCKET_COUNT_X,
    properties.SOCKET_COUNT_Y,
    properties.SOCKET_COUNT_Z,
    properties.SOCKET_SPACING_X,
    properties.SOCKET_SPACING_Y,
    properties.SOCKET_SPACING_Z,
)


def is_cloner_object(obj: bpy.types.Object | None) -> bool:
    return bool(obj and obj.get(properties.PROP_CLONER_TYPE) == "CLONER")


def get_cloner_modifier(obj: bpy.types.Object | None) -> bpy.types.NodesModifier | None:
    if not is_cloner_object(obj):
        return None

    modifier = obj.modifiers.get(properties.CLONER_MODIFIER_NAME)
    if modifier is None or modifier.type != "NODES" or modifier.node_group is None:
        return None

    return modifier


def get_socket_identifier(
    node_group: bpy.types.GeometryNodeTree,
    socket_name: str,
) -> str | None:
    for item in node_group.interface.items_tree:
        if (
            getattr(item, "item_type", None) == "SOCKET"
            and getattr(item, "in_out", None) == "INPUT"
            and item.name == socket_name
        ):
            return item.identifier
    return None


def get_modifier_input_identifier(
    modifier: bpy.types.NodesModifier,
    socket_name: str,
) -> str | None:
    if modifier.node_group is None:
        return None
    return get_socket_identifier(modifier.node_group, socket_name)


def set_modifier_input(
    modifier: bpy.types.NodesModifier,
    socket_name: str,
    value,
) -> None:
    identifier = get_modifier_input_identifier(modifier, socket_name)
    if identifier is not None:
        modifier[identifier] = value


def get_modifier_input(
    modifier: bpy.types.NodesModifier,
    socket_name: str,
):
    identifier = get_modifier_input_identifier(modifier, socket_name)
    if identifier is None:
        return None
    return modifier.get(identifier)
