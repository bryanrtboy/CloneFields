"""Verify the bundled node library inside Blender."""

from __future__ import annotations

from pathlib import Path
import sys
import time

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT.parent))

from CloneFields import properties
from CloneFields.geometry_nodes import create_grid_node_group


def _remove_node_groups() -> None:
    for node_group in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(node_group)


def _assert_master(node_group) -> None:
    assert node_group.name.startswith(properties.GRID_NODE_GROUP_NAME)
    assert (
        node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
        == properties.GRID_NODE_GROUP_BUILD_VERSION
    )
    assert len(node_group.nodes) <= 25, len(node_group.nodes)
    internal_names = {
        node.node_tree.name
        for node in node_group.nodes
        if node.bl_idname == "GeometryNodeGroup" and node.node_tree is not None
    }
    assert properties.GRID_DISTRIBUTION_NODE_GROUP_NAME in internal_names
    assert properties.SOURCE_TRANSFORM_NODE_GROUP_NAME in internal_names
    assert properties.LINEAR_DISTRIBUTION_NODE_GROUP_NAME in internal_names
    assert properties.RADIAL_DISTRIBUTION_NODE_GROUP_NAME in internal_names
    assert properties.OBJECT_DISTRIBUTION_NODE_GROUP_NAME in internal_names


_remove_node_groups()
started = time.perf_counter()
bundled = create_grid_node_group()
bundled_seconds = time.perf_counter() - started
_assert_master(bundled)

_remove_node_groups()
started = time.perf_counter()
generated = create_grid_node_group(use_bundled=False)
generated_seconds = time.perf_counter() - started
_assert_master(generated)

print(
    "CLONE_FIELDS_NODE_LIBRARY_OK "
    f"bundled={bundled_seconds:.4f}s generated={generated_seconds:.4f}s "
    f"master_nodes={len(generated.nodes)}"
)
