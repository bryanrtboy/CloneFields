"""Verify that an older Cloner migrates to the current shared node group."""

from __future__ import annotations

from pathlib import Path
import sys

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT.parent))

import CloneFields
from CloneFields import cloner, modifier_inputs, properties, source_management


def _source() -> bpy.types.Object:
    mesh = bpy.data.meshes.new("Upgrade Source Mesh")
    mesh.from_pydata(
        [
            (-0.5, -0.5, -0.5),
            (0.5, -0.5, -0.5),
            (0.5, 0.5, -0.5),
            (-0.5, 0.5, -0.5),
            (-0.5, -0.5, 0.5),
            (0.5, -0.5, 0.5),
            (0.5, 0.5, 0.5),
            (-0.5, 0.5, 0.5),
        ],
        [],
        [
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (4, 0, 3, 7),
        ],
    )
    source = bpy.data.objects.new("Upgrade Source", mesh)
    bpy.context.collection.objects.link(source)
    return source


CloneFields.register()
created = cloner.create_grid_cloner(
    bpy.context,
    source_object=_source(),
    count_x=7,
    count_y=4,
    count_z=2,
    spacing_x=1.25,
    spacing_y=2.5,
    spacing_z=3.75,
)
modifier = modifier_inputs.get_cloner_modifier(created)
assert modifier is not None
created.clone_fields_cloner.distribution_mode = "RADIAL"
created.clone_fields_cloner.radial_count = 13
created.clone_fields_cloner.radial_radius = 8.5

expected = {
    name: modifier_inputs.get_modifier_input(modifier, name)
    for name in (
        properties.SOCKET_COUNT_X,
        properties.SOCKET_COUNT_Y,
        properties.SOCKET_COUNT_Z,
        properties.SOCKET_SPACING_X,
        properties.SOCKET_SPACING_Y,
        properties.SOCKET_SPACING_Z,
        properties.SOCKET_DISTRIBUTION_MODE,
        properties.SOCKET_RADIAL_COUNT,
        properties.SOCKET_RADIAL_RADIUS,
        properties.SOCKET_SOURCE_COLLECTION,
    )
}
old_group = modifier.node_group
old_group[properties.PROP_NODE_GROUP_BUILD_VERSION] = (
    properties.GRID_NODE_GROUP_BUILD_VERSION - 1
)

source_management._upgrade_stale_cloner_node_groups()
modifier = modifier_inputs.get_cloner_modifier(created)
assert modifier is not None
assert modifier.node_group != old_group
assert (
    modifier.node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
    == properties.GRID_NODE_GROUP_BUILD_VERSION
)
for name, value in expected.items():
    assert modifier_inputs.get_modifier_input(modifier, name) == value, name

print("CLONE_FIELDS_UPGRADE_OK")
