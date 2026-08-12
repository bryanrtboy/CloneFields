"""Load generated Geometry Nodes assets bundled with the extension."""

from __future__ import annotations

from pathlib import Path

import bpy

from .. import properties


LIBRARY_PATH = Path(__file__).with_name("assets") / "clone_fields_nodes.blend"


def load_grid_node_group() -> bpy.types.GeometryNodeTree | None:
    """Append the current master Cloner group, returning None on incompatibility."""

    if not LIBRARY_PATH.is_file():
        return None

    try:
        with bpy.data.libraries.load(str(LIBRARY_PATH), link=False) as (source, target):
            if properties.GRID_NODE_GROUP_NAME not in source.node_groups:
                return None
            target.node_groups = [properties.GRID_NODE_GROUP_NAME]
    except (OSError, RuntimeError):
        return None

    node_group = target.node_groups[0] if target.node_groups else None
    if node_group is None:
        return None
    if (
        node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
        != properties.GRID_NODE_GROUP_BUILD_VERSION
    ):
        if node_group.users == 0:
            bpy.data.node_groups.remove(node_group)
        return None
    return node_group
