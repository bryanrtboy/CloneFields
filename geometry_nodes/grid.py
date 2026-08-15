"""Build the Geometry Nodes graph for the first Clone Fields grid cloner."""

from __future__ import annotations

import bpy

from .. import properties
from . import library


def create_grid_node_group(
    nested_grid: dict | None = None,
    *,
    use_bundled: bool = True,
) -> bpy.types.GeometryNodeTree:
    """Create a fresh grid cloner node group.

    The group intentionally exposes only milestone parameters. Additional
    distribution modes should be implemented as separate builders rather than
    branching this graph into a general-purpose system too early.
    """
    if nested_grid is None:
        reusable = _reusable_grid_node_group()
        if reusable is not None:
            return reusable
        if use_bundled:
            bundled = library.load_grid_node_group()
            if bundled is not None:
                return bundled

    node_group = bpy.data.node_groups.new(
        properties.GRID_NODE_GROUP_NAME,
        "GeometryNodeTree",
    )
    if nested_grid is None:
        node_group[properties.PROP_NODE_GROUP_BUILD_VERSION] = (
            properties.GRID_NODE_GROUP_BUILD_VERSION
        )
    _create_interface(node_group)
    _create_nodes(node_group, nested_grid)

    return node_group


def _reusable_grid_node_group() -> bpy.types.GeometryNodeTree | None:
    for node_group in bpy.data.node_groups:
        if (
            node_group.bl_idname == "GeometryNodeTree"
            and node_group.name.startswith(properties.GRID_NODE_GROUP_NAME)
            and node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
            == properties.GRID_NODE_GROUP_BUILD_VERSION
        ):
            return node_group
    return None


def _create_interface(node_group: bpy.types.GeometryNodeTree) -> None:
    interface = node_group.interface

    _new_socket(interface, properties.SOCKET_GEOMETRY, "INPUT", "NodeSocketGeometry")
    _new_socket(interface, properties.SOCKET_GEOMETRY, "OUTPUT", "NodeSocketGeometry")

    distribution_panel = _new_panel(interface, "Distribution")
    grid_panel = _new_panel(interface, "Grid")
    count_panel = _new_panel(interface, "Count")
    interface.move_to_parent(count_panel, grid_panel, len(grid_panel.interface_items))
    spacing_panel = _new_panel(interface, "Spacing")
    interface.move_to_parent(spacing_panel, grid_panel, len(grid_panel.interface_items))
    brick_panel = _new_panel(interface, "Brick", default_closed=True)
    linear_panel = _new_panel(interface, "Linear", default_closed=True)
    linear_direction_panel = _new_panel(
        interface,
        "Direction",
        parent=linear_panel,
    )
    radial_panel = _new_panel(interface, "Radial", default_closed=True)
    object_panel = _new_panel(interface, "Object", default_closed=True)
    effector_panel = _new_panel(interface, "Basic Effector", default_closed=True)
    effector_position_panel = _new_panel(
        interface,
        "Effector Position",
        parent=effector_panel,
        default_closed=True,
    )
    effector_rotation_panel = _new_panel(
        interface,
        "Effector Rotation",
        parent=effector_panel,
        default_closed=True,
    )
    effector_scale_panel = _new_panel(
        interface,
        "Effector Scale",
        parent=effector_panel,
    )
    source_transform_panel = _new_panel(interface, "Source Transform")
    position_panel = _new_panel(
        interface,
        "Position",
        parent=source_transform_panel,
        default_closed=True,
    )
    rotation_panel = _new_panel(
        interface,
        "Rotation",
        parent=source_transform_panel,
    )
    scale_panel = _new_panel(
        interface,
        "Scale",
        parent=source_transform_panel,
    )

    _new_socket(
        interface,
        properties.SOCKET_SOURCE_OBJECT,
        "INPUT",
        "NodeSocketObject",
    )
    _new_socket(
        interface,
        properties.SOCKET_SOURCE_COLLECTION,
        "INPUT",
        "NodeSocketCollection",
    )
    socket = _new_socket(
        interface,
        properties.SOCKET_SOURCE_COUNT,
        "INPUT",
        "NodeSocketInt",
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SOURCE_COUNT]
    socket.min_value = 1
    _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_OBJECT,
        "INPUT",
        "NodeSocketObject",
    )
    _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_TARGET_OBJECT,
        "INPUT",
        "NodeSocketObject",
    )
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_USE_TARGET_OBJECT,
        "INPUT",
        "NodeSocketBool",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_TARGET_OBJECT
    ]
    _new_socket(interface, properties.SOCKET_EFFECTOR_SHADER_IMAGE, "INPUT", "NodeSocketImage")
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_SHADER_TILES_X,
        "INPUT",
        "NodeSocketInt",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SHADER_TILES_X
    ]
    socket.min_value = 1
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_SHADER_TILES_Y,
        "INPUT",
        "NodeSocketInt",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_SHADER_TILES_Y
    ]
    socket.min_value = 1
    for name in (
        properties.SOCKET_EFFECTOR_SHADER_WIDTH,
        properties.SOCKET_EFFECTOR_SHADER_HEIGHT,
    ):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=effector_panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.001
        socket.subtype = "DISTANCE"
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_TYPE,
        "INPUT",
        "NodeSocketInt",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_TYPE]
    socket.min_value = 0
    socket.max_value = 4
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_FIELD,
        "INPUT",
        "NodeSocketInt",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_FIELD]
    socket.min_value = 0
    socket.max_value = 4
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_SEED,
        "INPUT",
        "NodeSocketInt",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_SEED]
    socket.min_value = 0
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_ENABLED,
        "INPUT",
        "NodeSocketBool",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_ENABLED
    ]
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_INVERT,
        "INPUT",
        "NodeSocketBool",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_INVERT
    ]
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_STRENGTH,
        "INPUT",
        "NodeSocketFloat",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_STRENGTH
    ]
    socket.min_value = 0.0
    socket.max_value = 1.0
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_RADIUS,
        "INPUT",
        "NodeSocketFloat",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_RADIUS]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_HEIGHT,
        "INPUT",
        "NodeSocketFloat",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_HEIGHT]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_LENGTH,
        "INPUT",
        "NodeSocketFloat",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_LENGTH]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    for name in (
        properties.SOCKET_EFFECTOR_BOX_X,
        properties.SOCKET_EFFECTOR_BOX_Y,
        properties.SOCKET_EFFECTOR_BOX_Z,
    ):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=effector_panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.0
        socket.subtype = "DISTANCE"
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_FALLOFF,
        "INPUT",
        "NodeSocketFloat",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_FALLOFF
    ]
    socket.min_value = 0.0
    socket.max_value = 100.0
    socket.subtype = "PERCENTAGE"

    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_USE_POSITION,
        "INPUT",
        "NodeSocketBool",
        parent=effector_position_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_POSITION
    ]

    for name in (
        properties.SOCKET_EFFECTOR_POSITION_X,
        properties.SOCKET_EFFECTOR_POSITION_Y,
        properties.SOCKET_EFFECTOR_POSITION_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=effector_position_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.subtype = "DISTANCE"

    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_USE_ROTATION,
        "INPUT",
        "NodeSocketBool",
        parent=effector_rotation_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_ROTATION
    ]

    for name in (
        properties.SOCKET_EFFECTOR_ROTATION_X,
        properties.SOCKET_EFFECTOR_ROTATION_Y,
        properties.SOCKET_EFFECTOR_ROTATION_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=effector_rotation_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.subtype = "ANGLE"

    for name in (
        properties.SOCKET_EFFECTOR_TARGET_AXIS,
        properties.SOCKET_EFFECTOR_TARGET_UP_AXIS,
    ):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketInt", parent=effector_panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0
        socket.max_value = 2

    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_USE_SCALE,
        "INPUT",
        "NodeSocketBool",
        parent=effector_scale_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_EFFECTOR_USE_SCALE
    ]

    for name in (
        properties.SOCKET_EFFECTOR_SCALE_X,
        properties.SOCKET_EFFECTOR_SCALE_Y,
        properties.SOCKET_EFFECTOR_SCALE_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=effector_scale_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.0

    for slot_index, socket_set in enumerate(properties.EFFECTOR_SOCKET_SETS[1:], start=2):
        _create_effector_interface(interface, socket_set, slot_index)

    socket = _new_socket(
        interface,
        properties.SOCKET_DISTRIBUTION_MODE,
        "INPUT",
        "NodeSocketInt",
        parent=distribution_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_DISTRIBUTION_MODE
    ]
    socket.min_value = 0
    socket.max_value = 4
    socket = _new_socket(
        interface,
        properties.SOCKET_SPACING_MODE,
        "INPUT",
        "NodeSocketInt",
        parent=distribution_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_SPACING_MODE]
    socket.min_value = 0
    socket.max_value = 1

    for name in (
        properties.SOCKET_COUNT_X,
        properties.SOCKET_COUNT_Y,
        properties.SOCKET_COUNT_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketInt",
            parent=count_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 1

    for name in (
        properties.SOCKET_SPACING_X,
        properties.SOCKET_SPACING_Y,
        properties.SOCKET_SPACING_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=spacing_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.0
        socket.subtype = "DISTANCE"

    for name in (
        properties.SOCKET_BRICK_ROW_OFFSET,
        properties.SOCKET_BRICK_LAYER_OFFSET,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=brick_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = -10.0
        socket.max_value = 10.0

    socket = _new_socket(
        interface,
        properties.SOCKET_LINEAR_COUNT,
        "INPUT",
        "NodeSocketInt",
        parent=linear_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_COUNT]
    socket.min_value = 1

    socket = _new_socket(
        interface,
        properties.SOCKET_LINEAR_SPACING,
        "INPUT",
        "NodeSocketFloat",
        parent=linear_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_LINEAR_SPACING]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"

    for name in (
        properties.SOCKET_LINEAR_DIRECTION_X,
        properties.SOCKET_LINEAR_DIRECTION_Y,
        properties.SOCKET_LINEAR_DIRECTION_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=linear_direction_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]

    socket = _new_socket(
        interface,
        properties.SOCKET_RADIAL_COUNT,
        "INPUT",
        "NodeSocketInt",
        parent=radial_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_COUNT]
    socket.min_value = 1

    socket = _new_socket(
        interface,
        properties.SOCKET_RADIAL_RADIUS,
        "INPUT",
        "NodeSocketFloat",
        parent=radial_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_RADIUS]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"

    socket = _new_socket(
        interface,
        properties.SOCKET_RADIAL_ARC,
        "INPUT",
        "NodeSocketFloat",
        parent=radial_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_ARC]
    socket.subtype = "ANGLE"

    socket = _new_socket(
        interface,
        properties.SOCKET_RADIAL_AXIS,
        "INPUT",
        "NodeSocketInt",
        parent=radial_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_RADIAL_AXIS]
    socket.min_value = 0
    socket.max_value = 3

    socket = _new_socket(
        interface,
        properties.SOCKET_RADIAL_ALIGN,
        "INPUT",
        "NodeSocketBool",
        parent=radial_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_RADIAL_ALIGN
    ]

    _new_socket(
        interface,
        properties.SOCKET_OBJECT_DISTRIBUTION_OBJECT,
        "INPUT",
        "NodeSocketObject",
        parent=object_panel,
    )
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_DISTRIBUTION_MODE,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_DISTRIBUTION_MODE
    ]
    socket.min_value = 0
    socket.max_value = 3
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION
    ]
    socket.min_value = 0
    socket.max_value = 3
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SPLINE_COUNT,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SPLINE_COUNT
    ]
    socket.min_value = 1
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SPLINE_STEP,
        "INPUT",
        "NodeSocketFloat",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SPLINE_STEP
    ]
    socket.min_value = 0.001
    socket.subtype = "DISTANCE"
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SPLINE_PER_SPLINE,
        "INPUT",
        "NodeSocketBool",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SPLINE_PER_SPLINE
    ]
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SPLINE_SMOOTH_ROTATION,
        "INPUT",
        "NodeSocketBool",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SPLINE_SMOOTH_ROTATION
    ]
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SURFACE_DISTRIBUTION,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SURFACE_DISTRIBUTION
    ]
    socket.min_value = 0
    socket.max_value = 1
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SURFACE_DENSITY,
        "INPUT",
        "NodeSocketFloat",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SURFACE_DENSITY
    ]
    socket.min_value = 0.0
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SURFACE_DISTANCE_MIN,
        "INPUT",
        "NodeSocketFloat",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SURFACE_DISTANCE_MIN
    ]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_SURFACE_SEED,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_SURFACE_SEED
    ]
    socket.min_value = 0
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_ALIGNMENT,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_ALIGNMENT
    ]
    socket.min_value = 0
    socket.max_value = 3
    socket = _new_socket(
        interface,
        properties.SOCKET_OBJECT_UP_VECTOR,
        "INPUT",
        "NodeSocketInt",
        parent=object_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        properties.SOCKET_OBJECT_UP_VECTOR
    ]
    socket.min_value = 0
    socket.max_value = 3

    for name in (
        properties.SOCKET_SOURCE_POSITION_X,
        properties.SOCKET_SOURCE_POSITION_Y,
        properties.SOCKET_SOURCE_POSITION_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=position_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.subtype = "DISTANCE"

    for name in (
        properties.SOCKET_SOURCE_ROTATION_X,
        properties.SOCKET_SOURCE_ROTATION_Y,
        properties.SOCKET_SOURCE_ROTATION_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=rotation_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.subtype = "ANGLE"

    for name in (
        properties.SOCKET_SOURCE_SCALE_X,
        properties.SOCKET_SOURCE_SCALE_Y,
        properties.SOCKET_SOURCE_SCALE_Z,
    ):
        socket = _new_socket(
            interface,
            name,
            "INPUT",
            "NodeSocketFloat",
            parent=scale_panel,
        )
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.0

    _hide_modifier_inputs(interface)


def _create_nodes(
    node_group: bpy.types.GeometryNodeTree,
    nested_grid: dict | None = None,
) -> None:
    nodes = node_group.nodes
    links = node_group.links
    nodes.clear()

    group_input = _new_node(nodes, "NodeGroupInput", (-900, 100))
    collection_info = _new_node(nodes, "GeometryNodeCollectionInfo", (-680, -180))
    node_group.interface_update(bpy.context)
    collection_info.inputs["Separate Children"].default_value = True
    collection_info.inputs["Reset Children"].default_value = True

    if nested_grid is None:
        _link(
            links,
            group_input,
            properties.SOCKET_SOURCE_COLLECTION,
            collection_info,
            "Collection",
        )
        source_node = _new_source_transform_group_node(
            node_group,
            nodes,
            links,
            group_input,
            collection_info,
            "Instances",
            (-420, -180),
        )
        source_socket = properties.SOCKET_GEOMETRY
        x_offset = -680
    else:
        collection_info.inputs["Collection"].default_value = nested_grid["source_collection"]
        source_node, source_socket = _build_grid_distribution(
            nodes,
            links,
            source_node=collection_info,
            source_socket="Instances",
            counts=(
                nested_grid[properties.SOCKET_COUNT_X],
                nested_grid[properties.SOCKET_COUNT_Y],
                nested_grid[properties.SOCKET_COUNT_Z],
            ),
            spacings=(
                nested_grid[properties.SOCKET_SPACING_X],
                nested_grid[properties.SOCKET_SPACING_Y],
                nested_grid[properties.SOCKET_SPACING_Z],
            ),
            origin=(-680, -180),
            group_input=None,
            source_count=1,
        )
        realize_nested = _new_node(nodes, "GeometryNodeRealizeInstances", (780, -260))
        _link(links, source_node, source_socket, realize_nested, "Geometry")
        source_node = realize_nested
        source_socket = "Geometry"
        x_offset = 180

    grid_node = _new_distribution_group_node(
        node_group,
        nodes,
        links,
        group_input,
        source_node,
        source_socket,
        properties.GRID_DISTRIBUTION_NODE_GROUP_NAME,
        _GRID_DISTRIBUTION_INPUTS,
        _build_internal_grid_distribution,
        (x_offset, 250),
    )
    brick_node = _new_distribution_group_node(
        node_group,
        nodes,
        links,
        group_input,
        source_node,
        source_socket,
        properties.BRICK_DISTRIBUTION_NODE_GROUP_NAME,
        _BRICK_DISTRIBUTION_INPUTS,
        _build_internal_brick_distribution,
        (x_offset, 450),
    )
    linear_node = _new_distribution_group_node(
        node_group,
        nodes,
        links,
        group_input,
        source_node,
        source_socket,
        properties.LINEAR_DISTRIBUTION_NODE_GROUP_NAME,
        _LINEAR_DISTRIBUTION_INPUTS,
        _build_internal_linear_distribution,
        (x_offset, 50),
    )
    radial_node = _new_distribution_group_node(
        node_group,
        nodes,
        links,
        group_input,
        source_node,
        source_socket,
        properties.RADIAL_DISTRIBUTION_NODE_GROUP_NAME,
        _RADIAL_DISTRIBUTION_INPUTS,
        _build_internal_radial_distribution,
        (x_offset, -150),
    )
    object_node = _new_distribution_group_node(
        node_group,
        nodes,
        links,
        group_input,
        source_node,
        source_socket,
        properties.OBJECT_DISTRIBUTION_NODE_GROUP_NAME,
        _OBJECT_DISTRIBUTION_INPUTS,
        _build_internal_object_distribution,
        (x_offset, -350),
    )
    output_node, output_socket = _build_distribution_switch(
        nodes,
        links,
        group_input,
        grid=(grid_node, properties.SOCKET_GEOMETRY),
        brick=(brick_node, properties.SOCKET_GEOMETRY),
        linear=(linear_node, properties.SOCKET_GEOMETRY),
        radial=(radial_node, properties.SOCKET_GEOMETRY),
        object_distribution=(object_node, properties.SOCKET_GEOMETRY),
        location=(x_offset + 1560, -320),
    )
    realize_output = _new_node(
        nodes,
        "GeometryNodeRealizeInstances",
        (x_offset + 1840, -60),
    )
    group_output = _new_node(nodes, "NodeGroupOutput", (x_offset + 1840, 90))
    _link(links, output_node, output_socket, realize_output, "Geometry")
    _link(links, realize_output, "Geometry", group_output, properties.SOCKET_GEOMETRY)


_EFFECTOR_INPUTS = (
    *properties.EFFECTOR_OBJECT_SOCKET_NAMES,
    *properties.EFFECTOR_VALUE_SOCKET_NAMES,
)
_SOURCE_TRANSFORM_INPUTS = (
    properties.SOCKET_SOURCE_POSITION_X,
    properties.SOCKET_SOURCE_POSITION_Y,
    properties.SOCKET_SOURCE_POSITION_Z,
    properties.SOCKET_SOURCE_ROTATION_X,
    properties.SOCKET_SOURCE_ROTATION_Y,
    properties.SOCKET_SOURCE_ROTATION_Z,
    properties.SOCKET_SOURCE_SCALE_X,
    properties.SOCKET_SOURCE_SCALE_Y,
    properties.SOCKET_SOURCE_SCALE_Z,
)
_GRID_DISTRIBUTION_INPUTS = (
    properties.SOCKET_SOURCE_COUNT,
    properties.SOCKET_SPACING_MODE,
    properties.SOCKET_COUNT_X,
    properties.SOCKET_COUNT_Y,
    properties.SOCKET_COUNT_Z,
    properties.SOCKET_SPACING_X,
    properties.SOCKET_SPACING_Y,
    properties.SOCKET_SPACING_Z,
    *_EFFECTOR_INPUTS,
)
_BRICK_DISTRIBUTION_INPUTS = (
    properties.SOCKET_SOURCE_COUNT,
    properties.SOCKET_SPACING_MODE,
    properties.SOCKET_COUNT_X,
    properties.SOCKET_COUNT_Y,
    properties.SOCKET_COUNT_Z,
    properties.SOCKET_SPACING_X,
    properties.SOCKET_SPACING_Y,
    properties.SOCKET_SPACING_Z,
    properties.SOCKET_BRICK_ROW_OFFSET,
    properties.SOCKET_BRICK_LAYER_OFFSET,
    *_EFFECTOR_INPUTS,
)
_LINEAR_DISTRIBUTION_INPUTS = (
    properties.SOCKET_SOURCE_COUNT,
    properties.SOCKET_SPACING_MODE,
    properties.SOCKET_LINEAR_COUNT,
    properties.SOCKET_LINEAR_SPACING,
    properties.SOCKET_LINEAR_DIRECTION_X,
    properties.SOCKET_LINEAR_DIRECTION_Y,
    properties.SOCKET_LINEAR_DIRECTION_Z,
    *_EFFECTOR_INPUTS,
)
_RADIAL_DISTRIBUTION_INPUTS = (
    properties.SOCKET_SOURCE_COUNT,
    properties.SOCKET_RADIAL_COUNT,
    properties.SOCKET_RADIAL_RADIUS,
    properties.SOCKET_RADIAL_ARC,
    properties.SOCKET_RADIAL_AXIS,
    properties.SOCKET_RADIAL_ALIGN,
    *_EFFECTOR_INPUTS,
)
_OBJECT_DISTRIBUTION_INPUTS = (
    properties.SOCKET_SOURCE_COUNT,
    properties.SOCKET_OBJECT_DISTRIBUTION_OBJECT,
    properties.SOCKET_OBJECT_DISTRIBUTION_MODE,
    properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION,
    properties.SOCKET_OBJECT_SPLINE_COUNT,
    properties.SOCKET_OBJECT_SPLINE_STEP,
    properties.SOCKET_OBJECT_SPLINE_PER_SPLINE,
    properties.SOCKET_OBJECT_SPLINE_SMOOTH_ROTATION,
    properties.SOCKET_OBJECT_SURFACE_DISTRIBUTION,
    properties.SOCKET_OBJECT_SURFACE_DENSITY,
    properties.SOCKET_OBJECT_SURFACE_DISTANCE_MIN,
    properties.SOCKET_OBJECT_SURFACE_SEED,
    properties.SOCKET_OBJECT_ALIGNMENT,
    properties.SOCKET_OBJECT_UP_VECTOR,
    *_EFFECTOR_INPUTS,
)


def _new_distribution_group_node(
    master_group,
    nodes,
    links,
    group_input,
    source_node,
    source_socket: str,
    group_name: str,
    input_names: tuple[str, ...],
    builder,
    location: tuple[int, int],
):
    distribution_group = _get_or_create_distribution_group(
        master_group,
        group_name,
        input_names,
        builder,
    )
    group_node = _new_node(nodes, "GeometryNodeGroup", location)
    group_node.node_tree = distribution_group
    _link(links, source_node, source_socket, group_node, properties.SOCKET_GEOMETRY)
    for socket_name in input_names:
        _link(links, group_input, socket_name, group_node, socket_name)
    return group_node


def _new_source_transform_group_node(
    master_group,
    nodes,
    links,
    group_input,
    source_node,
    source_socket: str,
    location: tuple[int, int],
):
    source_group = _get_or_create_source_transform_group(master_group)
    group_node = _new_node(nodes, "GeometryNodeGroup", location)
    group_node.node_tree = source_group
    _link(links, source_node, source_socket, group_node, properties.SOCKET_GEOMETRY)
    for socket_name in _SOURCE_TRANSFORM_INPUTS:
        _link(links, group_input, socket_name, group_node, socket_name)
    return group_node


def _get_or_create_source_transform_group(master_group) -> bpy.types.GeometryNodeTree:
    for node_group in bpy.data.node_groups:
        if (
            node_group.bl_idname == "GeometryNodeTree"
            and node_group.name == properties.SOURCE_TRANSFORM_NODE_GROUP_NAME
            and node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
            == properties.GRID_NODE_GROUP_BUILD_VERSION
        ):
            return node_group

    node_group = bpy.data.node_groups.new(
        properties.SOURCE_TRANSFORM_NODE_GROUP_NAME,
        "GeometryNodeTree",
    )
    node_group[properties.PROP_NODE_GROUP_BUILD_VERSION] = (
        properties.GRID_NODE_GROUP_BUILD_VERSION
    )
    interface = node_group.interface
    _new_socket(interface, properties.SOCKET_GEOMETRY, "INPUT", "NodeSocketGeometry")
    _new_socket(interface, properties.SOCKET_GEOMETRY, "OUTPUT", "NodeSocketGeometry")
    master_inputs = {
        item.name: item
        for item in master_group.interface.items_tree
        if getattr(item, "item_type", None) == "SOCKET"
        and getattr(item, "in_out", None) == "INPUT"
    }
    for socket_name in _SOURCE_TRANSFORM_INPUTS:
        _copy_interface_socket(interface, master_inputs[socket_name])
    _hide_modifier_inputs(interface)

    group_input = _new_node(node_group.nodes, "NodeGroupInput", (-1600, 0))
    group_output = _new_node(node_group.nodes, "NodeGroupOutput", (1600, 0))
    transformed, transformed_socket = _build_source_transform(
        node_group.nodes,
        node_group.links,
        group_input,
        group_input,
        properties.SOCKET_GEOMETRY,
        (-1300, 0),
    )
    _link(
        node_group.links,
        transformed,
        transformed_socket,
        group_output,
        properties.SOCKET_GEOMETRY,
    )
    return node_group


def _get_or_create_distribution_group(
    master_group,
    group_name: str,
    input_names: tuple[str, ...],
    builder,
) -> bpy.types.GeometryNodeTree:
    for node_group in bpy.data.node_groups:
        if (
            node_group.bl_idname == "GeometryNodeTree"
            and node_group.name == group_name
            and node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
            == properties.GRID_NODE_GROUP_BUILD_VERSION
        ):
            return node_group

    node_group = bpy.data.node_groups.new(group_name, "GeometryNodeTree")
    node_group[properties.PROP_NODE_GROUP_BUILD_VERSION] = (
        properties.GRID_NODE_GROUP_BUILD_VERSION
    )
    interface = node_group.interface
    _new_socket(interface, properties.SOCKET_GEOMETRY, "INPUT", "NodeSocketGeometry")
    _new_socket(interface, properties.SOCKET_GEOMETRY, "OUTPUT", "NodeSocketGeometry")
    master_inputs = {
        item.name: item
        for item in master_group.interface.items_tree
        if getattr(item, "item_type", None) == "SOCKET"
        and getattr(item, "in_out", None) == "INPUT"
    }
    for socket_name in input_names:
        _copy_interface_socket(interface, master_inputs[socket_name])
    _hide_modifier_inputs(interface)

    group_input = _new_node(node_group.nodes, "NodeGroupInput", (-2200, 0))
    group_output = _new_node(node_group.nodes, "NodeGroupOutput", (2400, 0))
    output_node, output_socket = builder(node_group.nodes, node_group.links, group_input)
    _link(
        node_group.links,
        output_node,
        output_socket,
        group_output,
        properties.SOCKET_GEOMETRY,
    )
    return node_group


def _copy_interface_socket(interface, source_socket):
    socket = _new_socket(
        interface,
        source_socket.name,
        "INPUT",
        source_socket.socket_type,
    )
    for attribute in ("default_value", "min_value", "max_value", "subtype"):
        if not hasattr(source_socket, attribute) or not hasattr(socket, attribute):
            continue
        try:
            setattr(socket, attribute, getattr(source_socket, attribute))
        except (AttributeError, TypeError, ValueError):
            pass
    return socket


def _build_internal_grid_distribution(nodes, links, group_input) -> tuple:
    return _build_grid_distribution(
        nodes,
        links,
        source_node=group_input,
        source_socket=properties.SOCKET_GEOMETRY,
        counts=(
            properties.SOCKET_COUNT_X,
            properties.SOCKET_COUNT_Y,
            properties.SOCKET_COUNT_Z,
        ),
        spacings=(
            properties.SOCKET_SPACING_X,
            properties.SOCKET_SPACING_Y,
            properties.SOCKET_SPACING_Z,
        ),
        origin=(-1800, 0),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )


def _build_internal_brick_distribution(nodes, links, group_input) -> tuple:
    return _build_brick_distribution(
        nodes,
        links,
        source_node=group_input,
        source_socket=properties.SOCKET_GEOMETRY,
        counts=(
            properties.SOCKET_COUNT_X,
            properties.SOCKET_COUNT_Y,
            properties.SOCKET_COUNT_Z,
        ),
        spacings=(
            properties.SOCKET_SPACING_X,
            properties.SOCKET_SPACING_Y,
            properties.SOCKET_SPACING_Z,
        ),
        origin=(-1800, 0),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )


def _build_internal_linear_distribution(nodes, links, group_input) -> tuple:
    return _build_linear_distribution(
        nodes,
        links,
        source_node=group_input,
        source_socket=properties.SOCKET_GEOMETRY,
        origin=(-1800, 0),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )


def _build_internal_radial_distribution(nodes, links, group_input) -> tuple:
    return _build_radial_distribution(
        nodes,
        links,
        source_node=group_input,
        source_socket=properties.SOCKET_GEOMETRY,
        origin=(-1800, 0),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )


def _build_internal_object_distribution(nodes, links, group_input) -> tuple:
    return _build_object_distribution(
        nodes,
        links,
        source_node=group_input,
        source_socket=properties.SOCKET_GEOMETRY,
        origin=(-1800, 0),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )


def _create_effector_interface(interface, socket_set: dict, slot_index: int) -> None:
    panel = _new_panel(interface, f"Basic Effector {slot_index}", default_closed=True)
    position_panel = _new_panel(
        interface,
        f"Effector {slot_index} Position",
        parent=panel,
        default_closed=True,
    )
    rotation_panel = _new_panel(
        interface,
        f"Effector {slot_index} Rotation",
        parent=panel,
        default_closed=True,
    )
    scale_panel = _new_panel(
        interface,
        f"Effector {slot_index} Scale",
        parent=panel,
    )

    _new_socket(interface, socket_set["object"], "INPUT", "NodeSocketObject")
    _new_socket(interface, socket_set["target_object"], "INPUT", "NodeSocketObject")
    socket = _new_socket(
        interface,
        socket_set["use_target_object"],
        "INPUT",
        "NodeSocketBool",
        parent=panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[
        socket_set["use_target_object"]
    ]
    socket = _new_socket(interface, socket_set["type"], "INPUT", "NodeSocketInt", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["type"]]
    socket.min_value = 0
    socket.max_value = 4
    socket = _new_socket(interface, socket_set["field"], "INPUT", "NodeSocketInt", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["field"]]
    socket.min_value = 0
    socket.max_value = 4
    socket = _new_socket(interface, socket_set["seed"], "INPUT", "NodeSocketInt", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["seed"]]
    socket.min_value = 0
    socket = _new_socket(interface, socket_set["enabled"], "INPUT", "NodeSocketBool", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["enabled"]]
    socket = _new_socket(interface, socket_set["invert"], "INPUT", "NodeSocketBool", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["invert"]]
    socket = _new_socket(interface, socket_set["strength"], "INPUT", "NodeSocketFloat", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["strength"]]
    socket.min_value = 0.0
    socket.max_value = 1.0
    socket = _new_socket(interface, socket_set["radius"], "INPUT", "NodeSocketFloat", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["radius"]]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    socket = _new_socket(interface, socket_set["height"], "INPUT", "NodeSocketFloat", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["height"]]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    socket = _new_socket(interface, socket_set["length"], "INPUT", "NodeSocketFloat", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["length"]]
    socket.min_value = 0.0
    socket.subtype = "DISTANCE"
    for name in (socket_set["box_x"], socket_set["box_y"], socket_set["box_z"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.0
        socket.subtype = "DISTANCE"
    _new_socket(interface, socket_set["shader_image"], "INPUT", "NodeSocketImage")
    for name in (socket_set["shader_tiles_x"], socket_set["shader_tiles_y"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketInt", parent=panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 1
    for name in (socket_set["shader_width"], socket_set["shader_height"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.001
        socket.subtype = "DISTANCE"
    socket = _new_socket(interface, socket_set["falloff"], "INPUT", "NodeSocketFloat", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["falloff"]]
    socket.min_value = 0.0
    socket.max_value = 100.0
    socket.subtype = "PERCENTAGE"

    socket = _new_socket(
        interface,
        socket_set["use_position"],
        "INPUT",
        "NodeSocketBool",
        parent=position_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["use_position"]]
    for name in (socket_set["position_x"], socket_set["position_y"], socket_set["position_z"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=position_panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.subtype = "DISTANCE"

    socket = _new_socket(
        interface,
        socket_set["use_rotation"],
        "INPUT",
        "NodeSocketBool",
        parent=rotation_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["use_rotation"]]
    for name in (socket_set["rotation_x"], socket_set["rotation_y"], socket_set["rotation_z"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=rotation_panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.subtype = "ANGLE"

    for name in (socket_set["target_axis"], socket_set["target_up_axis"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketInt", parent=panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0
        socket.max_value = 2

    socket = _new_socket(
        interface,
        socket_set["use_scale"],
        "INPUT",
        "NodeSocketBool",
        parent=scale_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["use_scale"]]
    for name in (socket_set["scale_x"], socket_set["scale_y"], socket_set["scale_z"]):
        socket = _new_socket(interface, name, "INPUT", "NodeSocketFloat", parent=scale_panel)
        socket.default_value = properties.GRID_INPUT_DEFAULTS[name]
        socket.min_value = 0.0


def _build_grid_distribution(
    nodes,
    links,
    *,
    source_node,
    source_socket: str,
    counts: tuple,
    spacings: tuple,
    origin: tuple[int, int],
    group_input,
    source_count,
) -> tuple:
    x, y = origin

    mesh_line_x = _new_mesh_line_node(nodes, (x, y))
    combine_x = _new_combine_xyz_node(nodes, (x - 200, y + 90))
    x_indexed = _build_store_index_attribute(
        nodes,
        links,
        mesh_line_x,
        "Mesh",
        "_cf_step_x",
        (x + 260, y - 220),
    )
    instance_x_on_y = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 780, y - 80))

    mesh_line_y = _new_mesh_line_node(nodes, (x + 520, y))
    combine_y = _new_combine_xyz_node(nodes, (x + 320, y + 90))
    y_indexed = _build_store_index_attribute(
        nodes,
        links,
        mesh_line_y,
        "Mesh",
        "_cf_step_y",
        (x + 780, y - 220),
    )

    mesh_line_z = _new_mesh_line_node(nodes, (x + 1040, y))
    combine_z = _new_combine_xyz_node(nodes, (x + 840, y + 90))
    z_indexed = _build_store_index_attribute(
        nodes,
        links,
        mesh_line_z,
        "Mesh",
        "_cf_step_z",
        (x + 1300, y - 220),
    )
    instance_xy_on_z = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 1300, y - 80))
    realize_points = _new_node(nodes, "GeometryNodeRealizeInstances", (x + 1560, y - 80))
    instance_source = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 1820, y - 80))

    _set_or_link_value(links, group_input, counts[0], mesh_line_x, "Count")
    _set_or_link_value(links, group_input, counts[1], mesh_line_y, "Count")
    _set_or_link_value(links, group_input, counts[2], mesh_line_z, "Count")

    spacing_x_node, spacing_x_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        counts[0],
        spacings[0],
        (x - 520, y + 240),
    )
    spacing_y_node, spacing_y_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        counts[1],
        spacings[1],
        (x, y + 240),
    )
    spacing_z_node, spacing_z_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        counts[2],
        spacings[2],
        (x + 520, y + 240),
    )

    _link(links, spacing_x_node, spacing_x_socket, combine_x, "X")
    _link(links, spacing_y_node, spacing_y_socket, combine_y, "Y")
    _link(links, spacing_z_node, spacing_z_socket, combine_z, "Z")
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_x,
        counts[0],
        (spacing_x_node, spacing_x_socket),
        "X",
        (x - 460, y - 90),
    )
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_y,
        counts[1],
        (spacing_y_node, spacing_y_socket),
        "Y",
        (x + 60, y - 90),
    )
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_z,
        counts[2],
        (spacing_z_node, spacing_z_socket),
        "Z",
        (x + 580, y - 90),
    )

    _link(links, combine_x, "Vector", mesh_line_x, "Offset")
    _link(links, combine_y, "Vector", mesh_line_y, "Offset")
    _link(links, combine_z, "Vector", mesh_line_z, "Offset")

    _link(links, y_indexed, "Geometry", instance_x_on_y, "Points")
    _link(links, x_indexed, "Geometry", instance_x_on_y, "Instance")

    _link(links, z_indexed, "Geometry", instance_xy_on_z, "Points")
    _link(links, instance_x_on_y, "Instances", instance_xy_on_z, "Instance")

    _link(links, instance_xy_on_z, "Instances", realize_points, "Geometry")
    step_index_node, step_index_socket = _build_grid_step_index(
        nodes,
        links,
        group_input,
        realize_points,
        "Geometry",
        counts,
        (x + 1540, y + 520),
    )
    points_node, points_socket, rotation_node, rotation_socket, scale_node, scale_socket = (
        _build_all_plain_effector_points(
            nodes,
            links,
            group_input,
            realize_points,
            "Geometry",
            (x + 1540, y + 180),
            step_index_node,
            step_index_socket,
        )
    )
    _link(links, points_node, points_socket, instance_source, "Points")
    _link(links, source_node, source_socket, instance_source, "Instance")
    _link(links, rotation_node, rotation_socket, instance_source, "Rotation")
    _link(links, scale_node, scale_socket, instance_source, "Scale")
    _configure_grid_instance_picker(
        nodes,
        links,
        group_input,
        instance_source,
        source_count,
        counts,
        (
            (spacing_x_node, spacing_x_socket),
            (spacing_y_node, spacing_y_socket),
            (spacing_z_node, spacing_z_socket),
        ),
        (x + 1540, y - 300),
    )

    return instance_source, "Instances"


def _build_brick_distribution(
    nodes,
    links,
    *,
    source_node,
    source_socket: str,
    counts: tuple,
    spacings: tuple,
    origin: tuple[int, int],
    group_input,
    source_count,
) -> tuple:
    x, y = origin

    mesh_line_x = _new_mesh_line_node(nodes, (x, y))
    combine_x = _new_combine_xyz_node(nodes, (x - 200, y + 90))
    x_indexed = _build_store_index_attribute(
        nodes,
        links,
        mesh_line_x,
        "Mesh",
        "_cf_step_x",
        (x + 260, y - 220),
    )
    instance_x_on_y = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 780, y - 80))

    mesh_line_y = _new_mesh_line_node(nodes, (x + 520, y))
    combine_y = _new_combine_xyz_node(nodes, (x + 320, y + 90))
    y_indexed = _build_store_index_attribute(
        nodes,
        links,
        mesh_line_y,
        "Mesh",
        "_cf_step_y",
        (x + 780, y - 220),
    )

    mesh_line_z = _new_mesh_line_node(nodes, (x + 1040, y))
    combine_z = _new_combine_xyz_node(nodes, (x + 840, y + 90))
    z_indexed = _build_store_index_attribute(
        nodes,
        links,
        mesh_line_z,
        "Mesh",
        "_cf_step_z",
        (x + 1300, y - 220),
    )
    instance_xy_on_z = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 1300, y - 80))
    realize_points = _new_node(nodes, "GeometryNodeRealizeInstances", (x + 1560, y - 80))
    instance_source = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 2080, y - 80))

    _set_or_link_value(links, group_input, counts[0], mesh_line_x, "Count")
    _set_or_link_value(links, group_input, counts[1], mesh_line_y, "Count")
    _set_or_link_value(links, group_input, counts[2], mesh_line_z, "Count")

    spacing_x_node, spacing_x_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        counts[0],
        spacings[0],
        (x - 520, y + 240),
    )
    spacing_y_node, spacing_y_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        counts[1],
        spacings[1],
        (x, y + 240),
    )
    spacing_z_node, spacing_z_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        counts[2],
        spacings[2],
        (x + 520, y + 240),
    )

    _link(links, spacing_x_node, spacing_x_socket, combine_x, "X")
    _link(links, spacing_y_node, spacing_y_socket, combine_y, "Y")
    _link(links, spacing_z_node, spacing_z_socket, combine_z, "Z")
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_x,
        counts[0],
        (spacing_x_node, spacing_x_socket),
        "X",
        (x - 460, y - 90),
    )
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_y,
        counts[1],
        (spacing_y_node, spacing_y_socket),
        "Y",
        (x + 60, y - 90),
    )
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_z,
        counts[2],
        (spacing_z_node, spacing_z_socket),
        "Z",
        (x + 580, y - 90),
    )

    _link(links, combine_x, "Vector", mesh_line_x, "Offset")
    _link(links, combine_y, "Vector", mesh_line_y, "Offset")
    _link(links, combine_z, "Vector", mesh_line_z, "Offset")

    _link(links, y_indexed, "Geometry", instance_x_on_y, "Points")
    _link(links, x_indexed, "Geometry", instance_x_on_y, "Instance")
    _link(links, z_indexed, "Geometry", instance_xy_on_z, "Points")
    _link(links, instance_x_on_y, "Instances", instance_xy_on_z, "Instance")
    _link(links, instance_xy_on_z, "Instances", realize_points, "Geometry")

    brick_points, brick_points_socket = _build_brick_offset_points(
        nodes,
        links,
        group_input,
        realize_points,
        "Geometry",
        (spacing_x_node, spacing_x_socket),
        (x + 1540, y + 520),
    )
    step_index_node, step_index_socket = _build_grid_step_index(
        nodes,
        links,
        group_input,
        brick_points,
        brick_points_socket,
        counts,
        (x + 1540, y + 300),
    )
    points_node, points_socket, rotation_node, rotation_socket, scale_node, scale_socket = (
        _build_all_plain_effector_points(
            nodes,
            links,
            group_input,
            brick_points,
            brick_points_socket,
            (x + 1800, y + 180),
            step_index_node,
            step_index_socket,
        )
    )
    _link(links, points_node, points_socket, instance_source, "Points")
    _link(links, source_node, source_socket, instance_source, "Instance")
    _link(links, rotation_node, rotation_socket, instance_source, "Rotation")
    _link(links, scale_node, scale_socket, instance_source, "Scale")
    _configure_grid_instance_picker(
        nodes,
        links,
        group_input,
        instance_source,
        source_count,
        counts,
        (
            (spacing_x_node, spacing_x_socket),
            (spacing_y_node, spacing_y_socket),
            (spacing_z_node, spacing_z_socket),
        ),
        (x + 1800, y - 300),
    )

    return instance_source, "Instances"


def _build_brick_offset_points(
    nodes,
    links,
    group_input,
    points_node,
    points_socket: str,
    spacing_x: tuple,
    origin: tuple[int, int],
):
    x, y = origin
    index_y = _new_named_float_attribute_node(nodes, "_cf_step_y", (x, y + 220))
    index_z = _new_named_float_attribute_node(nodes, "_cf_step_z", (x, y + 80))
    row_modulo = _new_math_node(nodes, (x + 240, y + 220), "MODULO")
    layer_modulo = _new_math_node(nodes, (x + 240, y + 80), "MODULO")
    row_active = _new_math_node(nodes, (x + 480, y + 220), "GREATER_THAN")
    layer_active = _new_math_node(nodes, (x + 480, y + 80), "GREATER_THAN")
    row_spacing = _new_math_node(nodes, (x + 720, y + 220), "MULTIPLY")
    layer_spacing = _new_math_node(nodes, (x + 720, y + 80), "MULTIPLY")
    row_offset = _new_math_node(nodes, (x + 960, y + 220), "MULTIPLY")
    layer_offset = _new_math_node(nodes, (x + 960, y + 80), "MULTIPLY")
    total_offset = _new_math_node(nodes, (x + 1200, y + 150), "ADD")
    offset_vector = _new_combine_xyz_node(nodes, (x + 1440, y + 150))
    set_position = _new_node(nodes, "GeometryNodeSetPosition", (x + 1680, y + 20))

    row_modulo.inputs[1].default_value = 2.0
    layer_modulo.inputs[1].default_value = 2.0
    row_active.inputs[1].default_value = 0.5
    layer_active.inputs[1].default_value = 0.5
    _link(links, index_y, "Attribute", row_modulo, "Value")
    _link(links, index_z, "Attribute", layer_modulo, "Value")
    _link(links, row_modulo, "Value", row_active, "Value")
    _link(links, layer_modulo, "Value", layer_active, "Value")
    _link(links, spacing_x[0], spacing_x[1], row_spacing, "Value")
    _link(links, group_input, properties.SOCKET_BRICK_ROW_OFFSET, row_spacing, "Value_001")
    _link(links, spacing_x[0], spacing_x[1], layer_spacing, "Value")
    _link(links, group_input, properties.SOCKET_BRICK_LAYER_OFFSET, layer_spacing, "Value_001")
    _link(links, row_active, "Value", row_offset, "Value")
    _link(links, row_spacing, "Value", row_offset, "Value_001")
    _link(links, layer_active, "Value", layer_offset, "Value")
    _link(links, layer_spacing, "Value", layer_offset, "Value_001")
    _link(links, row_offset, "Value", total_offset, "Value")
    _link(links, layer_offset, "Value", total_offset, "Value_001")
    _link(links, total_offset, "Value", offset_vector, "X")
    _link(links, points_node, points_socket, set_position, "Geometry")
    _link(links, offset_vector, "Vector", set_position, "Offset")
    return set_position, "Geometry"


def _build_grid_step_index(
    nodes,
    links,
    group_input,
    points_node,
    points_socket: str,
    counts,
    origin: tuple[int, int],
):
    x, y = origin
    index_x = _new_named_float_attribute_node(nodes, "_cf_step_x", (x, y + 220))
    index_y = _new_named_float_attribute_node(nodes, "_cf_step_y", (x, y + 80))
    index_z = _new_named_float_attribute_node(nodes, "_cf_step_z", (x, y - 60))
    count_x = _new_math_node(nodes, (x + 300, y + 220), "MAXIMUM")
    count_y = _new_math_node(nodes, (x + 300, y + 80), "MAXIMUM")
    count_z = _new_math_node(nodes, (x + 300, y - 60), "MAXIMUM")
    y_offset = _new_math_node(nodes, (x + 540, y + 100), "MULTIPLY")
    xy_count = _new_math_node(nodes, (x + 540, y - 80), "MULTIPLY")
    z_offset = _new_math_node(nodes, (x + 780, y - 20), "MULTIPLY")
    add_xy = _new_math_node(nodes, (x + 780, y + 160), "ADD")
    flat_index = _new_math_node(nodes, (x + 1020, y + 80), "ADD")
    total_xy = _new_math_node(nodes, (x + 540, y - 240), "MULTIPLY")
    total_xyz = _new_math_node(nodes, (x + 780, y - 240), "MULTIPLY")
    total_minus_one = _new_math_node(nodes, (x + 1020, y - 240), "SUBTRACT")
    safe_total = _new_math_node(nodes, (x + 1260, y - 240), "MAXIMUM")
    normalized = _new_math_node(nodes, (x + 1260, y + 80), "DIVIDE")

    count_x.inputs[1].default_value = 1.0
    count_y.inputs[1].default_value = 1.0
    count_z.inputs[1].default_value = 1.0
    total_minus_one.inputs[1].default_value = 1.0
    safe_total.inputs[1].default_value = 1.0

    _set_or_link_value(links, group_input, counts[0], count_x, "Value")
    _set_or_link_value(links, group_input, counts[1], count_y, "Value")
    _set_or_link_value(links, group_input, counts[2], count_z, "Value")
    _link(links, index_y, "Attribute", y_offset, "Value")
    links.new(count_x.outputs["Value"], y_offset.inputs[1])
    _link(links, count_x, "Value", xy_count, "Value")
    links.new(count_y.outputs["Value"], xy_count.inputs[1])
    _link(links, index_z, "Attribute", z_offset, "Value")
    links.new(xy_count.outputs["Value"], z_offset.inputs[1])
    _link(links, index_x, "Attribute", add_xy, "Value")
    links.new(y_offset.outputs["Value"], add_xy.inputs[1])
    _link(links, add_xy, "Value", flat_index, "Value")
    links.new(z_offset.outputs["Value"], flat_index.inputs[1])
    _link(links, count_x, "Value", total_xy, "Value")
    links.new(count_y.outputs["Value"], total_xy.inputs[1])
    _link(links, total_xy, "Value", total_xyz, "Value")
    links.new(count_z.outputs["Value"], total_xyz.inputs[1])
    _link(links, total_xyz, "Value", total_minus_one, "Value")
    _link(links, total_minus_one, "Value", safe_total, "Value")
    _link(links, flat_index, "Value", normalized, "Value")
    links.new(safe_total.outputs["Value"], normalized.inputs[1])

    return normalized, "Value"


def _build_normalized_point_index(
    nodes,
    links,
    points_node,
    points_socket: str,
    origin: tuple[int, int],
):
    x, y = origin
    point_count = _new_node(nodes, "GeometryNodeAttributeDomainSize", (x, y))
    point_count_minus_one = _new_math_node(nodes, (x + 240, y), "SUBTRACT")
    safe_point_count = _new_math_node(nodes, (x + 480, y), "MAXIMUM")
    index = _new_node(nodes, "GeometryNodeInputIndex", (x, y + 160))
    normalized = _new_math_node(nodes, (x + 720, y + 80), "DIVIDE")

    point_count_minus_one.inputs[1].default_value = 1.0
    safe_point_count.inputs[1].default_value = 1.0
    _link(links, points_node, points_socket, point_count, "Geometry")
    links.new(point_count.outputs["Point Count"], point_count_minus_one.inputs["Value"])
    _link(links, point_count_minus_one, "Value", safe_point_count, "Value")
    _link(links, index, "Index", normalized, "Value")
    links.new(safe_point_count.outputs["Value"], normalized.inputs[1])
    return normalized, "Value"


def _build_spacing_value(
    nodes,
    links,
    group_input,
    count,
    spacing,
    origin: tuple[int, int],
) -> tuple:
    x, y = origin
    if group_input is None:
        value = _new_node(nodes, "ShaderNodeValue", (x, y))
        value.outputs["Value"].default_value = spacing
        return value, "Value"

    count_minus_one = _new_math_node(nodes, (x, y), "SUBTRACT")
    safe_denominator = _new_math_node(nodes, (x + 240, y), "MAXIMUM")
    endpoint_step = _new_math_node(nodes, (x + 480, y), "DIVIDE")
    is_endpoint = _new_math_node(nodes, (x + 240, y - 140), "COMPARE")
    switch = _new_float_switch_node(nodes, (x + 720, y - 20))

    count_minus_one.inputs[1].default_value = 1.0
    safe_denominator.inputs[1].default_value = 1.0
    is_endpoint.inputs[1].default_value = 1.0
    is_endpoint.inputs[2].default_value = 0.001

    _set_or_link_value(links, group_input, count, count_minus_one, "Value")
    _link(links, count_minus_one, "Value", safe_denominator, "Value")
    _set_or_link_value(links, group_input, spacing, endpoint_step, "Value")
    links.new(safe_denominator.outputs["Value"], endpoint_step.inputs[1])
    _link(links, group_input, properties.SOCKET_SPACING_MODE, is_endpoint, "Value")
    _link(links, is_endpoint, "Value", switch, "Switch")
    _set_or_link_value(links, group_input, spacing, switch, "False")
    _link(links, endpoint_step, "Value", switch, "True")
    return switch, "Output"


def _build_linear_distribution(
    nodes,
    links,
    *,
    source_node,
    source_socket: str,
    origin: tuple[int, int],
    group_input,
    source_count,
) -> tuple:
    x, y = origin

    mesh_line = _new_mesh_line_node(nodes, (x, y))
    direction = _new_combine_xyz_node(nodes, (x - 220, y + 60))
    normalize = _new_vector_math_node(nodes, (x + 20, y + 60), "NORMALIZE")
    scale = _new_vector_math_node(nodes, (x + 260, y + 60), "SCALE")
    instance = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 560, y - 90))
    spacing_node, spacing_socket = _build_spacing_value(
        nodes,
        links,
        group_input,
        properties.SOCKET_LINEAR_COUNT,
        properties.SOCKET_LINEAR_SPACING,
        (x + 20, y + 240),
    )

    _link(links, group_input, properties.SOCKET_LINEAR_COUNT, mesh_line, "Count")
    _link(links, group_input, properties.SOCKET_LINEAR_DIRECTION_X, direction, "X")
    _link(links, group_input, properties.SOCKET_LINEAR_DIRECTION_Y, direction, "Y")
    _link(links, group_input, properties.SOCKET_LINEAR_DIRECTION_Z, direction, "Z")
    _link(links, direction, "Vector", normalize, "Vector")
    _link(links, normalize, "Vector", scale, "Vector")
    _link(links, spacing_node, spacing_socket, scale, "Scale")
    _link(links, scale, "Vector", mesh_line, "Offset")
    points_node, points_socket, rotation_node, rotation_socket, scale_node, scale_socket = (
        _build_all_plain_effector_points(
            nodes,
            links,
            group_input,
            mesh_line,
            "Mesh",
            (x + 300, y + 220),
        )
    )
    _link(links, points_node, points_socket, instance, "Points")
    _link(links, source_node, source_socket, instance, "Instance")
    _link(links, rotation_node, rotation_socket, instance, "Rotation")
    _link(links, scale_node, scale_socket, instance, "Scale")
    _configure_instance_picker(
        nodes,
        links,
        group_input,
        instance,
        source_count,
        (x + 320, y - 260),
    )

    return instance, "Instances"


def _build_radial_distribution(
    nodes,
    links,
    *,
    source_node,
    source_socket: str,
    origin: tuple[int, int],
    group_input,
    source_count,
) -> tuple:
    radial_z, radial_z_socket = _build_radial_axis_distribution(
        nodes,
        links,
        source_node=source_node,
        source_socket=source_socket,
        origin=origin,
        group_input=group_input,
        axis="Z",
        source_count=source_count,
    )
    radial_x, radial_x_socket = _build_radial_axis_distribution(
        nodes,
        links,
        source_node=source_node,
        source_socket=source_socket,
        origin=(origin[0], origin[1] - 420),
        group_input=group_input,
        axis="X",
        source_count=source_count,
    )
    radial_y, radial_y_socket = _build_radial_axis_distribution(
        nodes,
        links,
        source_node=source_node,
        source_socket=source_socket,
        origin=(origin[0], origin[1] - 840),
        group_input=group_input,
        axis="Y",
        source_count=source_count,
    )
    switch = _new_geometry_index_switch_node(nodes, (origin[0] + 1280, origin[1] - 360), 3)

    _link(links, group_input, properties.SOCKET_RADIAL_AXIS, switch, "Index")
    _link(links, radial_z, radial_z_socket, switch, "0")
    _link(links, radial_x, radial_x_socket, switch, "1")
    _link(links, radial_y, radial_y_socket, switch, "2")

    return switch, "Output"


def _build_radial_axis_distribution(
    nodes,
    links,
    *,
    source_node,
    source_socket: str,
    origin: tuple[int, int],
    group_input,
    axis: str,
    source_count,
) -> tuple:
    x, y = origin

    mesh_line = _new_mesh_line_node(nodes, (x, y))
    index = _new_node(nodes, "GeometryNodeInputIndex", (x - 260, y - 150))
    denominator = _new_math_node(nodes, (x + 220, y - 140), "MAXIMUM")
    factor = _new_math_node(nodes, (x + 460, y - 140), "DIVIDE")
    angle = _new_math_node(nodes, (x + 700, y - 140), "MULTIPLY")
    cosine = _new_math_node(nodes, (x + 940, y - 80), "COSINE")
    sine = _new_math_node(nodes, (x + 940, y - 200), "SINE")
    x_component = _new_math_node(nodes, (x + 1180, y - 80), "MULTIPLY")
    y_component = _new_math_node(nodes, (x + 1180, y - 200), "MULTIPLY")
    position = _new_combine_xyz_node(nodes, (x + 1420, y - 140))
    axis_vector = _new_combine_xyz_node(nodes, (x + 1420, y - 320))
    rotation = _new_node(nodes, "FunctionNodeAxisAngleToRotation", (x + 1660, y - 300))
    rotation_switch = _new_rotation_switch_node(nodes, (x + 1900, y - 300))
    set_position = _new_node(nodes, "GeometryNodeSetPosition", (x + 1660, y - 20))
    instance = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 2140, y - 20))

    denominator.inputs[1].default_value = 1.0
    _set_radial_axis_vector(axis, axis_vector)

    _link(links, group_input, properties.SOCKET_RADIAL_COUNT, mesh_line, "Count")
    _link(links, group_input, properties.SOCKET_RADIAL_COUNT, denominator, "Value")
    _link(links, index, "Index", factor, "Value")
    links.new(denominator.outputs["Value"], factor.inputs[1])
    _link(links, factor, "Value", angle, "Value")
    links.new(
        _socket(group_input.outputs, properties.SOCKET_RADIAL_ARC),
        angle.inputs[1],
    )
    _link(links, angle, "Value", cosine, "Value")
    _link(links, angle, "Value", sine, "Value")
    _link(links, cosine, "Value", x_component, "Value")
    links.new(
        _socket(group_input.outputs, properties.SOCKET_RADIAL_RADIUS),
        x_component.inputs[1],
    )
    _link(links, sine, "Value", y_component, "Value")
    links.new(
        _socket(group_input.outputs, properties.SOCKET_RADIAL_RADIUS),
        y_component.inputs[1],
    )

    _link_radial_axis_components(links, axis, x_component, y_component, position)
    _link(links, mesh_line, "Mesh", set_position, "Geometry")
    _link(links, position, "Vector", set_position, "Position")
    points_node, points_socket, effector_rotation_node, effector_rotation_socket, scale_node, scale_socket = (
        _build_all_plain_effector_points(
            nodes,
            links,
            group_input,
            set_position,
            "Geometry",
            (x + 1840, y + 220),
            base_rotation_node=rotation_switch,
            base_rotation_socket="Output",
        )
    )
    _link(links, points_node, points_socket, instance, "Points")
    _link(links, source_node, source_socket, instance, "Instance")
    _link(links, scale_node, scale_socket, instance, "Scale")
    _configure_instance_picker(
        nodes,
        links,
        group_input,
        instance,
        source_count,
        (x + 1900, y - 220),
    )
    _link(links, axis_vector, "Vector", rotation, "Axis")
    _link(links, angle, "Value", rotation, "Angle")
    _link(links, group_input, properties.SOCKET_RADIAL_ALIGN, rotation_switch, "Switch")
    _link(links, rotation, "Rotation", rotation_switch, "True")
    _link(links, effector_rotation_node, effector_rotation_socket, instance, "Rotation")

    return instance, "Instances"


def _link_radial_axis_components(
    links,
    axis: str,
    first_component,
    second_component,
    position,
) -> None:
    if axis == "X":
        links.new(first_component.outputs["Value"], position.inputs["Y"])
        links.new(second_component.outputs["Value"], position.inputs["Z"])
    elif axis == "Y":
        links.new(first_component.outputs["Value"], position.inputs["X"])
        links.new(second_component.outputs["Value"], position.inputs["Z"])
    else:
        links.new(first_component.outputs["Value"], position.inputs["X"])
        links.new(second_component.outputs["Value"], position.inputs["Y"])


def _build_global_curve_points(
    nodes,
    links,
    group_input,
    curve_node,
    curve_socket: str,
    origin: tuple[int, int],
) -> tuple:
    x, y = origin
    curve_length = _new_node(nodes, "GeometryNodeCurveLength", (x, y))
    divide_step = _new_math_node(nodes, (x + 200, y - 80), "DIVIDE")
    floor_step = _new_math_node(nodes, (x + 400, y - 80), "FLOOR")
    step_count = _new_math_node(nodes, (x + 600, y - 80), "ADD")
    step_count.inputs[1].default_value = 1.0
    is_step = _new_math_node(nodes, (x + 400, y - 240), "COMPARE")
    is_step.inputs[1].default_value = 2.0
    is_step.inputs[2].default_value = 0.1
    count_switch = _new_int_switch_node(nodes, (x + 780, y))
    points = _new_node(nodes, "GeometryNodePoints", (x + 980, y))
    index = _new_node(nodes, "GeometryNodeInputIndex", (x + 980, y - 220))
    count_minus_one = _new_math_node(nodes, (x + 980, y - 380), "SUBTRACT")
    count_minus_one.inputs[1].default_value = 1.0
    safe_denominator = _new_math_node(nodes, (x + 1180, y - 380), "MAXIMUM")
    safe_denominator.inputs[1].default_value = 1.0
    factor = _new_math_node(nodes, (x + 1180, y - 220), "DIVIDE")
    even_length = _new_math_node(nodes, (x + 1380, y - 300), "MULTIPLY")
    step_length = _new_math_node(nodes, (x + 1180, y - 520), "MULTIPLY")
    sample_length = _new_float_switch_node(nodes, (x + 1580, y - 300))
    sample = _new_node(nodes, "GeometryNodeSampleCurve", (x + 1380, y - 100))
    sample.mode = "LENGTH"
    sample.use_all_curves = True
    set_position = _new_node(nodes, "GeometryNodeSetPosition", (x + 1620, y))

    _link(links, curve_node, curve_socket, curve_length, "Curve")
    _link(links, curve_length, "Length", divide_step, "Value")
    links.new(
        _socket(group_input.outputs, properties.SOCKET_OBJECT_SPLINE_STEP),
        divide_step.inputs[1],
    )
    _link(links, divide_step, "Value", floor_step, "Value")
    _link(links, floor_step, "Value", step_count, "Value")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION, is_step, "Value")
    _link(links, is_step, "Value", count_switch, "Switch")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_COUNT, count_switch, "False")
    _link(links, step_count, "Value", count_switch, "True")
    _link(links, count_switch, "Output", points, "Count")
    _link(links, count_switch, "Output", count_minus_one, "Value")
    _link(links, count_minus_one, "Value", safe_denominator, "Value")
    _link(links, index, "Index", factor, "Value")
    links.new(safe_denominator.outputs["Value"], factor.inputs[1])
    _link(links, factor, "Value", even_length, "Value")
    links.new(curve_length.outputs["Length"], even_length.inputs[1])
    _link(links, index, "Index", step_length, "Value")
    links.new(
        _socket(group_input.outputs, properties.SOCKET_OBJECT_SPLINE_STEP),
        step_length.inputs[1],
    )
    _link(links, is_step, "Value", sample_length, "Switch")
    _link(links, even_length, "Value", sample_length, "False")
    _link(links, step_length, "Value", sample_length, "True")
    _link(links, curve_node, curve_socket, sample, "Curves")
    _link(links, sample_length, "Output", sample, "Length")
    _link(links, points, "Points", set_position, "Geometry")
    _link(links, sample, "Position", set_position, "Position")
    return set_position, sample


def _build_object_distribution(
    nodes,
    links,
    *,
    source_node,
    source_socket: str,
    origin: tuple[int, int],
    group_input,
    source_count,
) -> tuple:
    x, y = origin
    object_info = _new_node(nodes, "GeometryNodeObjectInfo", (x, y))
    object_info.transform_space = "RELATIVE"
    normal = _new_node(nodes, "GeometryNodeInputNormal", (x + 40, y + 300))
    capture_vertex_normal = _new_capture_vector_node(
        nodes,
        (x + 260, y + 260),
        "POINT",
        "Surface Normal",
    )
    capture_face_normal = _new_capture_vector_node(
        nodes,
        (x + 260, y + 40),
        "FACE",
        "Surface Normal",
    )
    mesh_vertices = _new_mesh_to_points_node(nodes, (x + 560, y + 260), "VERTICES")
    mesh_faces = _new_mesh_to_points_node(nodes, (x + 560, y + 40), "FACES")
    random_surface_points = _new_node(
        nodes,
        "GeometryNodeDistributePointsOnFaces",
        (x + 520, y - 120),
    )
    poisson_surface_points = _new_node(
        nodes,
        "GeometryNodeDistributePointsOnFaces",
        (x + 520, y - 300),
    )
    surface_points_switch = _new_geometry_index_switch_node(nodes, (x + 760, y - 180), 2)
    surface_normal_switch = _new_vector_index_switch_node(nodes, (x + 760, y - 320), 2)
    evaluated_points = _new_node(nodes, "GeometryNodeCurveToPoints", (x + 500, y - 280))
    count_points = _new_node(nodes, "GeometryNodeCurveToPoints", (x + 500, y - 420))
    step_points = _new_node(nodes, "GeometryNodeCurveToPoints", (x + 500, y - 560))
    sampled_points, sampled_curve = _build_global_curve_points(
        nodes,
        links,
        group_input,
        object_info,
        "Geometry",
        (x + 480, y - 900),
    )
    spline_points_switch = _new_geometry_index_switch_node(nodes, (x + 760, y - 460), 4)
    spline_tangent_switch = _new_vector_index_switch_node(nodes, (x + 760, y - 700), 4)
    spline_normal_switch = _new_vector_index_switch_node(nodes, (x + 760, y - 900), 4)
    per_spline_points = _new_geometry_switch_node(nodes, (x + 980, y - 500))
    per_spline_tangent = _new_vector_switch_node(nodes, (x + 980, y - 700))
    per_spline_normal = _new_vector_switch_node(nodes, (x + 980, y - 900))
    is_evaluated = _new_math_node(nodes, (x + 760, y - 1080), "COMPARE")
    is_evaluated.inputs[1].default_value = 0.0
    is_evaluated.inputs[2].default_value = 0.1
    use_per_spline = _new_boolean_math_node(nodes, (x + 980, y - 1080), "OR")
    curve_size = _new_node(nodes, "GeometryNodeAttributeDomainSize", (x + 260, y - 500))
    has_curve = _new_math_node(nodes, (x + 500, y - 500), "GREATER_THAN")
    effective_mode = _new_int_switch_node(nodes, (x + 700, y - 360))
    points_switch = _new_geometry_index_switch_node(nodes, (x + 900, y - 40), 4)
    normal_switch = _new_vector_index_switch_node(nodes, (x + 900, y + 260), 4)
    position = _new_node(nodes, "GeometryNodeInputPosition", (x + 900, y + 440))
    center_direction = _new_vector_math_node(nodes, (x + 1120, y + 440), "SUBTRACT")
    capture_direction = _new_capture_vector_node(nodes, (x + 1180, y + 160), "POINT", "Center Direction")
    normal_align_euler = _new_node(nodes, "FunctionNodeAlignEulerToVector", (x + 1420, y + 500))
    center_align_euler = _new_node(nodes, "FunctionNodeAlignEulerToVector", (x + 1420, y + 340))
    spline_align_euler = _new_node(nodes, "FunctionNodeAlignEulerToVector", (x + 1420, y + 180))
    smooth_spline_euler = _new_node(nodes, "FunctionNodeAlignEulerToVector", (x + 1580, y + 120))
    spline_euler_switch = _new_vector_switch_node(nodes, (x + 1740, y + 160))
    normal_up_align_euler = _new_node(nodes, "FunctionNodeAlignEulerToVector", (x + 1580, y + 500))
    center_up_align_euler = _new_node(nodes, "FunctionNodeAlignEulerToVector", (x + 1580, y + 340))
    normal_align_rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (x + 1760, y + 500))
    center_align_rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (x + 1760, y + 340))
    spline_align_rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (x + 1660, y + 180))
    alignment_rotation = _new_rotation_index_switch_node(nodes, (x + 1840, y + 300), 4)
    alignment_enabled = _new_math_node(nodes, (x + 1420, y - 140), "GREATER_THAN")
    curve_alignment_value = _new_math_node(nodes, (x + 1620, y - 140), "MULTIPLY")
    effective_alignment = _new_int_switch_node(nodes, (x + 1840, y - 20))
    zero_rotation_vector = _new_combine_xyz_node(nodes, (x + 1420, y + 20))
    zero_rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (x + 1660, y + 20))
    instance = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 2140, y - 40))

    evaluated_points.mode = "EVALUATED"
    count_points.mode = "COUNT"
    step_points.mode = "LENGTH"
    curve_size.component = "CURVE"
    has_curve.inputs[1].default_value = 0.0
    effective_mode.inputs["True"].default_value = 2
    alignment_enabled.inputs[1].default_value = 0.0
    curve_alignment_value.inputs[1].default_value = 3.0
    normal_align_euler.axis = "Z"
    center_align_euler.axis = "Z"
    normal_up_align_euler.axis = "Y"
    normal_up_align_euler.pivot_axis = "Z"
    center_up_align_euler.axis = "Y"
    center_up_align_euler.pivot_axis = "Z"
    spline_align_euler.axis = "X"
    smooth_spline_euler.axis = "Z"
    smooth_spline_euler.pivot_axis = "X"
    normal_align_euler.inputs["Factor"].default_value = 1.0
    center_align_euler.inputs["Factor"].default_value = 1.0
    normal_up_align_euler.inputs["Factor"].default_value = 1.0
    center_up_align_euler.inputs["Factor"].default_value = 1.0
    spline_align_euler.inputs["Factor"].default_value = 1.0
    smooth_spline_euler.inputs["Factor"].default_value = 1.0
    if hasattr(random_surface_points, "distribute_method"):
        random_surface_points.distribute_method = "RANDOM"
    if hasattr(poisson_surface_points, "distribute_method"):
        poisson_surface_points.distribute_method = "POISSON"

    _link(links, group_input, properties.SOCKET_OBJECT_DISTRIBUTION_OBJECT, object_info, "Object")
    _link(links, object_info, "Geometry", capture_vertex_normal, "Geometry")
    _link(links, normal, "Normal", capture_vertex_normal, "Surface Normal")
    _link(links, object_info, "Geometry", capture_face_normal, "Geometry")
    _link(links, normal, "Normal", capture_face_normal, "Surface Normal")
    _link(links, capture_vertex_normal, "Geometry", mesh_vertices, "Mesh")
    _link(links, capture_face_normal, "Geometry", mesh_faces, "Mesh")
    _link(links, object_info, "Geometry", random_surface_points, "Mesh")
    _link(links, object_info, "Geometry", poisson_surface_points, "Mesh")
    _link(links, group_input, properties.SOCKET_OBJECT_SURFACE_DENSITY, random_surface_points, "Density")
    _link(links, group_input, properties.SOCKET_OBJECT_SURFACE_DENSITY, poisson_surface_points, "Density Max")
    _link(
        links,
        group_input,
        properties.SOCKET_OBJECT_SURFACE_DISTANCE_MIN,
        poisson_surface_points,
        "Distance Min",
    )
    _link(links, group_input, properties.SOCKET_OBJECT_SURFACE_SEED, random_surface_points, "Seed")
    _link(links, group_input, properties.SOCKET_OBJECT_SURFACE_SEED, poisson_surface_points, "Seed")
    _link(
        links,
        group_input,
        properties.SOCKET_OBJECT_SURFACE_DISTRIBUTION,
        surface_points_switch,
        "Index",
    )
    _link(
        links,
        group_input,
        properties.SOCKET_OBJECT_SURFACE_DISTRIBUTION,
        surface_normal_switch,
        "Index",
    )
    _link(links, random_surface_points, "Points", surface_points_switch, "0")
    _link(links, poisson_surface_points, "Points", surface_points_switch, "1")
    _link(links, random_surface_points, "Normal", surface_normal_switch, "0")
    _link(links, poisson_surface_points, "Normal", surface_normal_switch, "1")
    _link(links, object_info, "Geometry", evaluated_points, "Curve")
    _link(links, object_info, "Geometry", count_points, "Curve")
    _link(links, object_info, "Geometry", step_points, "Curve")
    _link(links, object_info, "Geometry", curve_size, "Geometry")
    _link(links, curve_size, "Point Count", has_curve, "Value")
    _link(links, has_curve, "Value", effective_mode, "Switch")
    _link(links, group_input, properties.SOCKET_OBJECT_DISTRIBUTION_MODE, effective_mode, "False")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_COUNT, count_points, "Count")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_STEP, step_points, "Length")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION, spline_points_switch, "Index")
    _link(links, evaluated_points, "Points", spline_points_switch, "0")
    _link(links, count_points, "Points", spline_points_switch, "1")
    _link(links, step_points, "Points", spline_points_switch, "2")
    _link(links, count_points, "Points", spline_points_switch, "3")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION, spline_tangent_switch, "Index")
    _link(links, evaluated_points, "Tangent", spline_tangent_switch, "0")
    _link(links, count_points, "Tangent", spline_tangent_switch, "1")
    _link(links, step_points, "Tangent", spline_tangent_switch, "2")
    _link(links, count_points, "Tangent", spline_tangent_switch, "3")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION, spline_normal_switch, "Index")
    _link(links, evaluated_points, "Normal", spline_normal_switch, "0")
    _link(links, count_points, "Normal", spline_normal_switch, "1")
    _link(links, step_points, "Normal", spline_normal_switch, "2")
    _link(links, count_points, "Normal", spline_normal_switch, "3")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_DISTRIBUTION, is_evaluated, "Value")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_PER_SPLINE, use_per_spline, "Boolean")
    _link(links, is_evaluated, "Value", use_per_spline, "Boolean_001")
    _link(links, use_per_spline, "Boolean", per_spline_points, "Switch")
    _link(links, sampled_points, "Geometry", per_spline_points, "False")
    _link(links, spline_points_switch, "Output", per_spline_points, "True")
    _link(links, use_per_spline, "Boolean", per_spline_tangent, "Switch")
    _link(links, sampled_curve, "Tangent", per_spline_tangent, "False")
    _link(links, spline_tangent_switch, "Output", per_spline_tangent, "True")
    _link(links, use_per_spline, "Boolean", per_spline_normal, "Switch")
    _link(links, sampled_curve, "Normal", per_spline_normal, "False")
    _link(links, spline_normal_switch, "Output", per_spline_normal, "True")
    _link(links, effective_mode, "Output", points_switch, "Index")
    _link(links, mesh_vertices, "Points", points_switch, "0")
    _link(links, mesh_faces, "Points", points_switch, "1")
    _link(links, per_spline_points, "Output", points_switch, "2")
    _link(links, surface_points_switch, "Output", points_switch, "3")

    _link(links, effective_mode, "Output", normal_switch, "Index")
    _link(links, capture_vertex_normal, "Surface Normal", normal_switch, "0")
    _link(links, capture_face_normal, "Surface Normal", normal_switch, "1")
    _link(links, per_spline_normal, "Output", normal_switch, "2")
    _link(links, surface_normal_switch, "Output", normal_switch, "3")

    links.new(object_info.outputs["Location"], center_direction.inputs["Vector"])
    links.new(position.outputs["Position"], center_direction.inputs[1])
    _link(links, points_switch, "Output", capture_direction, "Geometry")
    _link(links, center_direction, "Vector", capture_direction, "Center Direction")
    _link(links, normal_switch, "Output", normal_align_euler, "Vector")
    _link(links, capture_direction, "Center Direction", center_align_euler, "Vector")
    _link(links, per_spline_tangent, "Output", spline_align_euler, "Vector")
    _link(links, spline_align_euler, "Rotation", smooth_spline_euler, "Rotation")
    _link(links, per_spline_normal, "Output", smooth_spline_euler, "Vector")
    _link(links, group_input, properties.SOCKET_OBJECT_SPLINE_SMOOTH_ROTATION, spline_euler_switch, "Switch")
    _link(links, spline_align_euler, "Rotation", spline_euler_switch, "False")
    _link(links, smooth_spline_euler, "Rotation", spline_euler_switch, "True")
    up_x = _new_combine_xyz_node(nodes, (x + 1200, y + 700))
    up_y = _new_combine_xyz_node(nodes, (x + 1200, y + 640))
    up_z = _new_combine_xyz_node(nodes, (x + 1200, y + 580))
    up_x.inputs["X"].default_value = 1.0
    up_y.inputs["Y"].default_value = 1.0
    up_z.inputs["Z"].default_value = 1.0
    use_center_direction = _new_math_node(nodes, (x + 980, y + 820), "COMPARE")
    use_center_direction.inputs[1].default_value = 2.0
    use_center_direction.inputs[2].default_value = 0.1
    primary_direction = _new_vector_switch_node(nodes, (x + 1160, y + 820))
    normal_dot_z = _new_vector_math_node(nodes, (x + 1340, y + 760), "DOT_PRODUCT")
    abs_normal_dot_z = _new_math_node(nodes, (x + 1360, y + 760), "ABSOLUTE")
    use_auto_y = _new_math_node(nodes, (x + 1540, y + 760), "GREATER_THAN")
    use_auto_y.inputs[1].default_value = 0.95
    auto_up = _new_vector_switch_node(nodes, (x + 1720, y + 700))
    up_vector = _new_vector_index_switch_node(nodes, (x + 1900, y + 700), 4)
    _link(links, group_input, properties.SOCKET_OBJECT_ALIGNMENT, use_center_direction, "Value")
    _link(links, use_center_direction, "Value", primary_direction, "Switch")
    _link(links, normal_switch, "Output", primary_direction, "False")
    _link(links, capture_direction, "Center Direction", primary_direction, "True")
    _link(links, primary_direction, "Output", normal_dot_z, "Vector")
    links.new(up_z.outputs["Vector"], normal_dot_z.inputs[1])
    _link(links, normal_dot_z, "Value", abs_normal_dot_z, "Value")
    _link(links, abs_normal_dot_z, "Value", use_auto_y, "Value")
    _link(links, use_auto_y, "Value", auto_up, "Switch")
    _link(links, up_z, "Vector", auto_up, "False")
    _link(links, up_y, "Vector", auto_up, "True")
    _link(links, group_input, properties.SOCKET_OBJECT_UP_VECTOR, up_vector, "Index")
    _link(links, auto_up, "Output", up_vector, "0")
    _link(links, up_x, "Vector", up_vector, "1")
    _link(links, up_y, "Vector", up_vector, "2")
    _link(links, up_z, "Vector", up_vector, "3")
    _link(links, normal_align_euler, "Rotation", normal_up_align_euler, "Rotation")
    _link(links, up_vector, "Output", normal_up_align_euler, "Vector")
    _link(links, center_align_euler, "Rotation", center_up_align_euler, "Rotation")
    _link(links, up_vector, "Output", center_up_align_euler, "Vector")
    _link(links, normal_up_align_euler, "Rotation", normal_align_rotation, "Euler")
    _link(links, center_up_align_euler, "Rotation", center_align_rotation, "Euler")
    _link(links, spline_euler_switch, "Output", spline_align_rotation, "Euler")
    _link(links, zero_rotation_vector, "Vector", zero_rotation, "Euler")
    _link(links, group_input, properties.SOCKET_OBJECT_ALIGNMENT, alignment_enabled, "Value")
    _link(links, alignment_enabled, "Value", curve_alignment_value, "Value")
    _link(links, has_curve, "Value", effective_alignment, "Switch")
    _link(links, group_input, properties.SOCKET_OBJECT_ALIGNMENT, effective_alignment, "False")
    _link(links, curve_alignment_value, "Value", effective_alignment, "True")
    _link(links, effective_alignment, "Output", alignment_rotation, "Index")
    _link(links, zero_rotation, "Rotation", alignment_rotation, "0")
    _link(links, normal_align_rotation, "Rotation", alignment_rotation, "1")
    _link(links, center_align_rotation, "Rotation", alignment_rotation, "2")
    _link(links, spline_align_rotation, "Rotation", alignment_rotation, "3")

    points_node, points_socket, effector_rotation_node, effector_rotation_socket, scale_node, scale_socket = (
        _build_all_plain_effector_points(
            nodes,
            links,
            group_input,
            capture_direction,
            "Geometry",
            (x + 1340, y + 420),
            base_rotation_node=alignment_rotation,
            base_rotation_socket="Output",
        )
    )
    _link(links, points_node, points_socket, instance, "Points")
    _link(links, source_node, source_socket, instance, "Instance")
    _link(links, effector_rotation_node, effector_rotation_socket, instance, "Rotation")
    _link(links, scale_node, scale_socket, instance, "Scale")
    _configure_instance_picker(
        nodes,
        links,
        group_input,
        instance,
        source_count,
        (x + 1840, y - 260),
    )
    return instance, "Instances"


def _build_all_plain_effector_points(
    nodes,
    links,
    group_input,
    points_node,
    points_socket: str,
    origin: tuple[int, int],
    step_index_node=None,
    step_index_socket: str | None = None,
    base_rotation_node=None,
    base_rotation_socket: str | None = None,
) -> tuple:
    if group_input is None:
        return _build_identity_instance_transform(
            nodes,
            links,
            points_node,
            points_socket,
            origin,
        )

    effector_group = _get_or_create_effector_stack_node_group()
    group_node = _new_node(nodes, "GeometryNodeGroup", origin)
    group_node.node_tree = effector_group
    if step_index_node is None or step_index_socket is None:
        step_index_node, step_index_socket = _build_normalized_point_index(
            nodes,
            links,
            points_node,
            points_socket,
            (origin[0] - 20, origin[1] + 420),
        )
    _link(links, points_node, points_socket, group_node, properties.SOCKET_GEOMETRY)
    _link(links, step_index_node, step_index_socket, group_node, properties.SOCKET_STEP_INDEX)
    if base_rotation_node is not None and base_rotation_socket is not None:
        _link(links, base_rotation_node, base_rotation_socket, group_node, "Base Rotation")
    for socket_set in properties.EFFECTOR_SOCKET_SETS:
        for socket_name in socket_set.values():
            if socket_name in group_node.inputs:
                _link(links, group_input, socket_name, group_node, socket_name)
    return (
        group_node,
        properties.SOCKET_GEOMETRY,
        group_node,
        "Rotation",
        group_node,
        "Scale",
    )


def _get_or_create_effector_stack_node_group() -> bpy.types.GeometryNodeTree:
    for node_group in bpy.data.node_groups:
        if (
            node_group.bl_idname == "GeometryNodeTree"
            and node_group.name == properties.EFFECTOR_STACK_NODE_GROUP_NAME
            and node_group.get(properties.PROP_NODE_GROUP_BUILD_VERSION)
            == properties.GRID_NODE_GROUP_BUILD_VERSION
        ):
            return node_group

    node_group = bpy.data.node_groups.new(
        properties.EFFECTOR_STACK_NODE_GROUP_NAME,
        "GeometryNodeTree",
    )
    node_group[properties.PROP_NODE_GROUP_BUILD_VERSION] = (
        properties.GRID_NODE_GROUP_BUILD_VERSION
    )
    interface = node_group.interface
    _new_socket(interface, properties.SOCKET_GEOMETRY, "INPUT", "NodeSocketGeometry")
    _new_socket(interface, properties.SOCKET_STEP_INDEX, "INPUT", "NodeSocketFloat")
    _new_socket(interface, "Base Rotation", "INPUT", "NodeSocketRotation")
    _new_socket(interface, properties.SOCKET_GEOMETRY, "OUTPUT", "NodeSocketGeometry")
    _new_socket(interface, "Rotation", "OUTPUT", "NodeSocketRotation")
    _new_socket(interface, "Scale", "OUTPUT", "NodeSocketVector")
    for index, socket_set in enumerate(properties.EFFECTOR_SOCKET_SETS, start=1):
        _create_effector_interface(interface, socket_set, index)
    _hide_modifier_inputs(interface)
    _create_effector_stack_nodes(node_group)
    return node_group


def _create_effector_stack_nodes(node_group: bpy.types.GeometryNodeTree) -> None:
    nodes = node_group.nodes
    links = node_group.links
    group_input = _new_node(nodes, "NodeGroupInput", (-3200, 0))
    group_output = _new_node(nodes, "NodeGroupOutput", (800, 0))

    current_node = group_input
    current_socket = properties.SOCKET_GEOMETRY
    rotation_node = group_input
    rotation_socket = "Base Rotation"
    scale_node = None
    scale_socket = None
    for index, socket_set in enumerate(properties.EFFECTOR_SOCKET_SETS):
        current_node, current_socket, slot_rotation_node, slot_rotation_socket, slot_scale_node, slot_scale_socket = (
            _build_plain_effector_points(
                nodes,
                links,
                group_input,
                current_node,
                current_socket,
                (-2800, 700 - (index * 760)),
                socket_set,
                rotation_node,
                rotation_socket,
            )
        )
        rotation_node = slot_rotation_node
        rotation_socket = slot_rotation_socket
        if scale_node is None:
            scale_node = slot_scale_node
            scale_socket = slot_scale_socket
        else:
            multiply_scale = _new_vector_math_node(
                nodes,
                (200, 420 - (index * 180)),
                "MULTIPLY",
            )
            _link(links, scale_node, scale_socket, multiply_scale, "Vector")
            links.new(slot_scale_node.outputs[slot_scale_socket], multiply_scale.inputs[1])
            scale_node = multiply_scale
            scale_socket = "Vector"
    _link(links, current_node, current_socket, group_output, properties.SOCKET_GEOMETRY)
    _link(links, rotation_node, rotation_socket, group_output, "Rotation")
    _link(links, scale_node, scale_socket, group_output, "Scale")


def _build_plain_effector_points(
    nodes,
    links,
    group_input,
    points_node,
    points_socket: str,
    origin: tuple[int, int],
    socket_set: dict,
    base_rotation_node,
    base_rotation_socket: str,
) -> tuple:
    x, y = origin
    object_info = _new_node(nodes, "GeometryNodeObjectInfo", (x, y))
    object_info.transform_space = "RELATIVE"
    target_info = _new_node(nodes, "GeometryNodeObjectInfo", (x, y + 180))
    target_info.transform_space = "RELATIVE"
    target_location = _new_vector_switch_node(nodes, (x + 240, y + 180))
    position = _new_node(nodes, "GeometryNodeInputPosition", (x, y - 170))
    distance = _new_vector_math_node(nodes, (x + 260, y - 80), "DISTANCE")
    local_offset = _new_vector_math_node(nodes, (x + 260, y - 250), "SUBTRACT")
    inverse_rotation = _new_node(nodes, "FunctionNodeInvertRotation", (x + 260, y - 420))
    local_position = _new_node(nodes, "FunctionNodeRotateVector", (x + 500, y - 300))
    absolute_local = _new_vector_math_node(nodes, (x + 740, y - 300), "ABSOLUTE")
    separate_local = _new_node(nodes, "ShaderNodeSeparateXYZ", (x + 980, y - 300))
    box_size = _new_combine_xyz_node(nodes, (x + 980, y - 460))
    box_half_size = _new_vector_math_node(nodes, (x + 1220, y - 460), "SCALE")
    safe_box_half_size = _new_vector_math_node(nodes, (x + 1460, y - 460), "MAXIMUM")
    normalized_box = _new_vector_math_node(nodes, (x + 1700, y - 460), "DIVIDE")
    separate_box = _new_node(nodes, "ShaderNodeSeparateXYZ", (x + 1940, y - 460))
    local_xy = _new_combine_xyz_node(nodes, (x + 1220, y - 620))
    radial_distance = _new_vector_math_node(nodes, (x + 1460, y - 620), "LENGTH")
    safe_radius = _new_math_node(nodes, (x + 1700, y - 620), "MAXIMUM")
    normalized_radial = _new_math_node(nodes, (x + 1940, y - 620), "DIVIDE")
    half_height = _new_math_node(nodes, (x + 1220, y - 760), "MULTIPLY")
    safe_half_height = _new_math_node(nodes, (x + 1460, y - 760), "MAXIMUM")
    normalized_height = _new_math_node(nodes, (x + 1700, y - 760), "DIVIDE")
    cylinder_normalized = _new_math_node(nodes, (x + 2180, y - 680), "MAXIMUM")
    cylinder_distance = _new_math_node(nodes, (x + 2420, y - 680), "MULTIPLY")
    half_length = _new_math_node(nodes, (x + 1220, y - 920), "MULTIPLY")
    safe_half_length = _new_math_node(nodes, (x + 1460, y - 920), "MAXIMUM")
    linear_distance = _new_math_node(nodes, (x + 1700, y - 920), "MINIMUM")
    max_xy = _new_math_node(nodes, (x + 2180, y - 460), "MAXIMUM")
    cubic_distance = _new_math_node(nodes, (x + 2420, y - 460), "MAXIMUM")
    is_cubic = _new_math_node(nodes, (x + 1220, y - 520), "COMPARE")
    is_cylinder = _new_math_node(nodes, (x + 1460, y - 520), "COMPARE")
    is_linear = _new_math_node(nodes, (x + 1700, y - 520), "COMPARE")
    is_none = _new_math_node(nodes, (x + 1940, y - 520), "COMPARE")
    box_or_sphere_distance = _new_float_switch_node(nodes, (x + 1700, y - 220))
    volume_distance = _new_float_switch_node(nodes, (x + 1940, y - 220))
    field_distance = _new_float_switch_node(nodes, (x + 2180, y - 220))
    field_size = _new_float_switch_node(nodes, (x + 2180, y - 360))
    cubic_field_size = _new_float_switch_node(nodes, (x + 2420, y - 360))
    radius_minus_distance = _new_math_node(nodes, (x + 500, y - 80), "SUBTRACT")
    falloff_percent = _new_math_node(nodes, (x + 500, y - 360), "MULTIPLY")
    falloff_range_factor = _new_math_node(nodes, (x + 740, y - 360), "SUBTRACT")
    scaled_falloff = _new_math_node(nodes, (x + 980, y - 360), "MULTIPLY")
    safe_falloff = _new_math_node(nodes, (x + 740, y - 80), "MAXIMUM")
    falloff_weight = _new_math_node(nodes, (x + 980, y - 80), "DIVIDE")
    inverted_weight = _new_math_node(nodes, (x + 1220, y - 80), "SUBTRACT")
    not_shader = _new_boolean_math_node(nodes, (x + 1220, y - 180), "NOT")
    invert_spatial_field = _new_boolean_math_node(nodes, (x + 1460, y - 180), "AND")
    inverse_switch = _new_float_switch_node(nodes, (x + 1460, y - 80))
    none_weight = _new_float_switch_node(nodes, (x + 1580, y + 40))
    strength = _new_math_node(nodes, (x + 1700, y - 80), "MULTIPLY")
    enabled_weight = _new_float_switch_node(nodes, (x + 1940, y - 80))
    position_weight = _new_float_switch_node(nodes, (x + 2180, y + 80))
    rotation_weight = _new_float_switch_node(nodes, (x + 2180, y + 620))
    scale_weight = _new_float_switch_node(nodes, (x + 2180, y + 340))
    is_random = _new_math_node(nodes, (x + 1940, y + 60), "COMPARE")
    is_target = _new_math_node(nodes, (x + 1940, y + 180), "COMPARE")
    is_shader = _new_math_node(nodes, (x + 1940, y + 300), "COMPARE")
    is_step = _new_math_node(nodes, (x + 1940, y + 420), "COMPARE")
    not_step = _new_boolean_math_node(nodes, (x + 1460, y - 300), "NOT")
    invertible_spatial_type = _new_boolean_math_node(nodes, (x + 1700, y - 180), "AND")
    image_texture = _new_node(nodes, "GeometryNodeImageTexture", (x + 1220, y + 1040))
    image_texture.extension = "CLIP"
    image_texture.interpolation = "Linear"
    shader_size = _new_combine_xyz_node(nodes, (x + 740, y + 1040))
    shader_uv = _new_vector_math_node(nodes, (x + 1220, y + 1180), "DIVIDE")
    shader_center = _new_vector_math_node(nodes, (x + 1460, y + 1180), "ADD")
    shader_center_separate = _new_node(nodes, "ShaderNodeSeparateXYZ", (x + 1700, y + 1320))
    shader_tiles = _new_combine_xyz_node(nodes, (x + 1700, y + 1460))
    tiled_uv = _new_vector_math_node(nodes, (x + 1940, y + 1320), "MULTIPLY")
    repeated_uv = _new_vector_math_node(nodes, (x + 2180, y + 1320), "FRACTION")
    inside_x_min = _new_math_node(nodes, (x + 1940, y + 1560), "GREATER_THAN")
    inside_x_max = _new_math_node(nodes, (x + 1940, y + 1680), "LESS_THAN")
    inside_y_min = _new_math_node(nodes, (x + 2180, y + 1560), "GREATER_THAN")
    inside_y_max = _new_math_node(nodes, (x + 2180, y + 1680), "LESS_THAN")
    inside_x = _new_math_node(nodes, (x + 2420, y + 1560), "MULTIPLY")
    inside_y = _new_math_node(nodes, (x + 2420, y + 1680), "MULTIPLY")
    inside_projection = _new_math_node(nodes, (x + 2660, y + 1620), "MULTIPLY")
    shader_channels = _new_node(nodes, "FunctionNodeSeparateColor", (x + 1700, y + 1040))
    shader_rg = _new_math_node(nodes, (x + 1940, y + 920), "ADD")
    shader_rgb = _new_math_node(nodes, (x + 2180, y + 920), "ADD")
    shader_luminance = _new_math_node(nodes, (x + 2420, y + 920), "MULTIPLY")
    clipped_shader_luminance = _new_math_node(nodes, (x + 2660, y + 800), "MULTIPLY")
    inverted_shader_luminance = _new_math_node(nodes, (x + 2660, y + 920), "SUBTRACT")
    shader_invert_switch = _new_float_switch_node(nodes, (x + 2900, y + 1040))
    shader_weight = _new_float_switch_node(nodes, (x + 1940, y + 1040))
    weighted_strength = _new_math_node(nodes, (x + 2180, y + 1040), "MULTIPLY")
    inverted_step_index = _new_math_node(nodes, (x + 1940, y + 760), "SUBTRACT")
    step_index = _new_float_switch_node(nodes, (x + 2420, y + 760))
    step_strength = _new_math_node(nodes, (x + 3140, y + 760), "MULTIPLY")
    type_weight = _new_float_switch_node(nodes, (x + 2420, y + 1040))
    index = _new_node(nodes, "GeometryNodeInputIndex", (x + 980, y + 980))

    offset = _new_combine_xyz_node(nodes, (x + 980, y + 160))
    negative_offset = _new_vector_math_node(nodes, (x + 1220, y + 160), "SCALE")
    random_offset = _new_random_vector_node(nodes, (x + 1460, y + 160))
    effector_offset = _new_vector_switch_node(nodes, (x + 2180, y + 160))
    weighted_offset = _new_vector_math_node(nodes, (x + 2420, y + 160), "SCALE")
    set_position = _new_node(nodes, "GeometryNodeSetPosition", (x + 2680, y + 120))

    desired_scale = _new_combine_xyz_node(nodes, (x + 980, y + 380))
    negative_scale_variation = _new_vector_math_node(nodes, (x + 1220, y + 300), "SUBTRACT")
    positive_scale_variation = _new_vector_math_node(nodes, (x + 1220, y + 420), "ADD")
    min_scale_floor = _new_combine_xyz_node(nodes, (x + 1220, y + 560))
    clamped_negative_scale = _new_vector_math_node(nodes, (x + 1460, y + 300), "MAXIMUM")
    random_scale = _new_random_vector_node(nodes, (x + 1460, y + 380))
    effector_scale = _new_vector_switch_node(nodes, (x + 1940, y + 420))
    one_scale = _new_combine_xyz_node(nodes, (x + 980, y + 520))
    scale_delta = _new_vector_math_node(nodes, (x + 1220, y + 420), "SUBTRACT")
    weighted_scale_delta = _new_vector_math_node(nodes, (x + 2420, y + 420), "SCALE")
    final_scale = _new_vector_math_node(nodes, (x + 2660, y + 420), "ADD")

    desired_rotation = _new_combine_xyz_node(nodes, (x + 980, y + 700))
    negative_rotation = _new_vector_math_node(nodes, (x + 1220, y + 700), "SCALE")
    random_rotation = _new_random_vector_node(nodes, (x + 1460, y + 700))
    effector_rotation = _new_vector_switch_node(nodes, (x + 2180, y + 700))
    weighted_rotation_euler = _new_vector_math_node(
        nodes,
        (x + 2420, y + 700),
        "SCALE",
    )
    weighted_rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (x + 2660, y + 700))
    basic_rotation = _new_node(nodes, "FunctionNodeRotateRotation", (x + 2900, y + 700))
    target_rotation = _build_target_rotation_nodes(
        nodes,
        links,
        group_input,
        socket_set,
        base_rotation_node,
        base_rotation_socket,
        target_location,
        position,
        rotation_weight,
        (x + 2420, y + 980),
    )
    rotation_type_switch = _new_rotation_switch_node(nodes, (x + 3380, y + 760))

    safe_falloff.inputs[1].default_value = 0.000001
    falloff_weight.use_clamp = True
    falloff_percent.inputs[1].default_value = 0.01
    safe_radius.inputs[1].default_value = 0.000001
    half_height.inputs[1].default_value = 0.5
    safe_half_height.inputs[1].default_value = 0.000001
    half_length.inputs[1].default_value = 0.5
    safe_half_length.inputs[1].default_value = 0.000001
    is_cubic.inputs[1].default_value = 1.0
    is_cubic.inputs[2].default_value = 0.001
    is_cylinder.inputs[1].default_value = 2.0
    is_cylinder.inputs[2].default_value = 0.001
    is_linear.inputs[1].default_value = 3.0
    is_linear.inputs[2].default_value = 0.001
    is_none.inputs[1].default_value = 4.0
    is_none.inputs[2].default_value = 0.001
    is_random.inputs[1].default_value = 1.0
    is_random.inputs[2].default_value = 0.001
    is_target.inputs[1].default_value = 2.0
    is_target.inputs[2].default_value = 0.001
    is_shader.inputs[1].default_value = 3.0
    is_shader.inputs[2].default_value = 0.001
    is_step.inputs[1].default_value = 4.0
    is_step.inputs[2].default_value = 0.001
    inverted_step_index.inputs[0].default_value = 1.0
    box_half_size.inputs["Scale"].default_value = 0.5
    safe_box_half_size.inputs[1].default_value = (0.000001, 0.000001, 0.000001)
    shader_center.inputs[1].default_value = (0.5, 0.5, 0.5)
    shader_tiles.inputs["Z"].default_value = 1.0
    inside_x_min.inputs[1].default_value = -0.000001
    inside_x_max.inputs[1].default_value = 1.000001
    inside_y_min.inputs[1].default_value = -0.000001
    inside_y_max.inputs[1].default_value = 1.000001
    shader_luminance.inputs[1].default_value = 1.0 / 3.0
    cubic_field_size.inputs["True"].default_value = 1.0
    inverted_weight.inputs[0].default_value = 1.0
    inverted_shader_luminance.inputs[0].default_value = 1.0
    falloff_range_factor.inputs[0].default_value = 1.0
    one_scale.inputs["X"].default_value = 1.0
    one_scale.inputs["Y"].default_value = 1.0
    one_scale.inputs["Z"].default_value = 1.0
    min_scale_floor.inputs["X"].default_value = 0.001
    min_scale_floor.inputs["Y"].default_value = 0.001
    min_scale_floor.inputs["Z"].default_value = 0.001
    _link(links, group_input, socket_set["object"], object_info, "Object")
    _link(links, group_input, socket_set["target_object"], target_info, "Object")
    _link(
        links,
        group_input,
        socket_set["use_target_object"],
        target_location,
        "Switch",
    )
    links.new(object_info.outputs["Location"], target_location.inputs["False"])
    links.new(target_info.outputs["Location"], target_location.inputs["True"])
    negative_offset.inputs["Scale"].default_value = -1.0
    negative_rotation.inputs["Scale"].default_value = -1.0

    _link(links, group_input, socket_set["type"], is_random, "Value")
    _link(links, group_input, socket_set["type"], is_target, "Value")
    _link(links, group_input, socket_set["type"], is_shader, "Value")
    _link(links, group_input, socket_set["type"], is_step, "Value")
    _link(links, position, "Position", distance, "Vector")
    links.new(object_info.outputs["Location"], distance.inputs[1])
    _link(links, position, "Position", local_offset, "Vector")
    links.new(object_info.outputs["Location"], local_offset.inputs[1])
    links.new(object_info.outputs["Rotation"], inverse_rotation.inputs["Rotation"])
    _link(links, local_offset, "Vector", local_position, "Vector")
    links.new(inverse_rotation.outputs["Rotation"], local_position.inputs["Rotation"])
    _link(links, local_position, "Vector", absolute_local, "Vector")
    _link(links, absolute_local, "Vector", separate_local, "Vector")
    _link(links, group_input, socket_set["box_x"], box_size, "X")
    _link(links, group_input, socket_set["box_y"], box_size, "Y")
    _link(links, group_input, socket_set["box_z"], box_size, "Z")
    _link(links, box_size, "Vector", box_half_size, "Vector")
    _link(links, box_half_size, "Vector", safe_box_half_size, "Vector")
    _link(links, absolute_local, "Vector", normalized_box, "Vector")
    links.new(safe_box_half_size.outputs["Vector"], normalized_box.inputs[1])
    _link(links, normalized_box, "Vector", separate_box, "Vector")
    links.new(separate_local.outputs["X"], local_xy.inputs["X"])
    links.new(separate_local.outputs["Y"], local_xy.inputs["Y"])
    _link(links, local_xy, "Vector", radial_distance, "Vector")
    links.new(_socket(group_input.outputs, socket_set["radius"]), safe_radius.inputs["Value"])
    _link(links, radial_distance, "Value", normalized_radial, "Value")
    links.new(safe_radius.outputs["Value"], normalized_radial.inputs[1])
    links.new(_socket(group_input.outputs, socket_set["height"]), half_height.inputs["Value"])
    _link(links, half_height, "Value", safe_half_height, "Value")
    links.new(separate_local.outputs["Z"], normalized_height.inputs["Value"])
    links.new(safe_half_height.outputs["Value"], normalized_height.inputs[1])
    _link(links, normalized_radial, "Value", cylinder_normalized, "Value")
    links.new(normalized_height.outputs["Value"], cylinder_normalized.inputs[1])
    _link(links, cylinder_normalized, "Value", cylinder_distance, "Value")
    links.new(_socket(group_input.outputs, socket_set["radius"]), cylinder_distance.inputs[1])
    links.new(_socket(group_input.outputs, socket_set["length"]), half_length.inputs["Value"])
    _link(links, half_length, "Value", safe_half_length, "Value")
    links.new(separate_local.outputs["X"], linear_distance.inputs["Value"])
    links.new(safe_half_length.outputs["Value"], linear_distance.inputs[1])
    links.new(separate_box.outputs["X"], max_xy.inputs["Value"])
    links.new(separate_box.outputs["Y"], max_xy.inputs[1])
    _link(links, max_xy, "Value", cubic_distance, "Value")
    links.new(separate_box.outputs["Z"], cubic_distance.inputs[1])
    _link(links, group_input, socket_set["field"], is_cubic, "Value")
    _link(links, group_input, socket_set["field"], is_cylinder, "Value")
    _link(links, group_input, socket_set["field"], is_linear, "Value")
    _link(links, group_input, socket_set["field"], is_none, "Value")
    _link(links, is_cubic, "Value", box_or_sphere_distance, "Switch")
    links.new(distance.outputs["Value"], box_or_sphere_distance.inputs["False"])
    _link(links, cubic_distance, "Value", box_or_sphere_distance, "True")
    _link(links, is_cylinder, "Value", volume_distance, "Switch")
    _link(links, box_or_sphere_distance, "Output", volume_distance, "False")
    _link(links, cylinder_distance, "Value", volume_distance, "True")
    _link(links, is_linear, "Value", field_distance, "Switch")
    _link(links, volume_distance, "Output", field_distance, "False")
    _link(links, linear_distance, "Value", field_distance, "True")
    _link(links, is_linear, "Value", field_size, "Switch")
    links.new(_socket(group_input.outputs, socket_set["radius"]), field_size.inputs["False"])
    links.new(safe_half_length.outputs["Value"], field_size.inputs["True"])
    _link(links, is_cubic, "Value", cubic_field_size, "Switch")
    _link(links, field_size, "Output", cubic_field_size, "False")
    links.new(
        _socket(group_input.outputs, socket_set["falloff"]),
        falloff_percent.inputs["Value"],
    )
    links.new(falloff_percent.outputs["Value"], falloff_range_factor.inputs[1])
    links.new(cubic_field_size.outputs["Output"], scaled_falloff.inputs["Value"])
    links.new(falloff_range_factor.outputs["Value"], scaled_falloff.inputs[1])
    links.new(cubic_field_size.outputs["Output"], radius_minus_distance.inputs["Value"])
    links.new(field_distance.outputs["Output"], radius_minus_distance.inputs[1])
    _link(links, scaled_falloff, "Value", safe_falloff, "Value")
    _link(links, radius_minus_distance, "Value", falloff_weight, "Value")
    links.new(safe_falloff.outputs["Value"], falloff_weight.inputs[1])
    links.new(falloff_weight.outputs["Value"], inverted_weight.inputs[1])
    _link(links, is_shader, "Value", not_shader, "Boolean")
    _link(links, is_step, "Value", not_step, "Boolean")
    _link(links, not_shader, "Boolean", invertible_spatial_type, "Boolean")
    _link(links, not_step, "Boolean", invertible_spatial_type, "Boolean_001")
    _link(links, group_input, socket_set["invert"], invert_spatial_field, "Boolean")
    _link(links, invertible_spatial_type, "Boolean", invert_spatial_field, "Boolean_001")
    _link(links, invert_spatial_field, "Boolean", inverse_switch, "Switch")
    _link(links, falloff_weight, "Value", inverse_switch, "False")
    _link(links, inverted_weight, "Value", inverse_switch, "True")
    _link(links, is_none, "Value", none_weight, "Switch")
    _link(links, inverse_switch, "Output", none_weight, "False")
    none_weight.inputs["True"].default_value = 1.0
    _link(links, none_weight, "Output", strength, "Value")
    links.new(
        _socket(group_input.outputs, socket_set["strength"]),
        strength.inputs[1],
    )
    _link(links, group_input, socket_set["shader_image"], image_texture, "Image")
    _link(links, group_input, socket_set["shader_width"], shader_size, "X")
    _link(links, group_input, socket_set["shader_height"], shader_size, "Y")
    _link(links, group_input, socket_set["shader_width"], shader_size, "Z")
    _link(links, local_position, "Vector", shader_uv, "Vector")
    links.new(shader_size.outputs["Vector"], shader_uv.inputs[1])
    _link(links, shader_uv, "Vector", shader_center, "Vector")
    _link(links, shader_center, "Vector", shader_center_separate, "Vector")
    _link(links, group_input, socket_set["shader_tiles_x"], shader_tiles, "X")
    _link(links, group_input, socket_set["shader_tiles_y"], shader_tiles, "Y")
    _link(links, shader_center, "Vector", tiled_uv, "Vector")
    links.new(shader_tiles.outputs["Vector"], tiled_uv.inputs[1])
    _link(links, tiled_uv, "Vector", repeated_uv, "Vector")
    _link(links, repeated_uv, "Vector", image_texture, "Vector")
    links.new(shader_center_separate.outputs["X"], inside_x_min.inputs["Value"])
    links.new(shader_center_separate.outputs["X"], inside_x_max.inputs["Value"])
    links.new(shader_center_separate.outputs["Y"], inside_y_min.inputs["Value"])
    links.new(shader_center_separate.outputs["Y"], inside_y_max.inputs["Value"])
    _link(links, inside_x_min, "Value", inside_x, "Value")
    _link(links, inside_x_max, "Value", inside_x, "Value_001")
    _link(links, inside_y_min, "Value", inside_y, "Value")
    _link(links, inside_y_max, "Value", inside_y, "Value_001")
    _link(links, inside_x, "Value", inside_projection, "Value")
    _link(links, inside_y, "Value", inside_projection, "Value_001")
    links.new(image_texture.outputs["Color"], shader_channels.inputs["Color"])
    links.new(shader_channels.outputs["Red"], shader_rg.inputs["Value"])
    links.new(shader_channels.outputs["Green"], shader_rg.inputs[1])
    _link(links, shader_rg, "Value", shader_rgb, "Value")
    links.new(shader_channels.outputs["Blue"], shader_rgb.inputs[1])
    _link(links, shader_rgb, "Value", shader_luminance, "Value")
    _link(links, shader_luminance, "Value", inverted_shader_luminance, "Value_001")
    _link(links, group_input, socket_set["invert"], shader_invert_switch, "Switch")
    _link(links, shader_luminance, "Value", shader_invert_switch, "False")
    _link(links, inverted_shader_luminance, "Value", shader_invert_switch, "True")
    _link(links, shader_invert_switch, "Output", clipped_shader_luminance, "Value")
    _link(links, inside_projection, "Value", clipped_shader_luminance, "Value_001")
    _link(links, is_shader, "Value", shader_weight, "Switch")
    shader_weight.inputs["False"].default_value = 1.0
    _link(links, clipped_shader_luminance, "Value", shader_weight, "True")
    _link(links, strength, "Value", weighted_strength, "Value")
    _link(links, shader_weight, "Output", weighted_strength, "Value_001")
    _link(links, group_input, properties.SOCKET_STEP_INDEX, inverted_step_index, "Value_001")
    _link(links, group_input, socket_set["invert"], step_index, "Switch")
    _link(links, group_input, properties.SOCKET_STEP_INDEX, step_index, "False")
    _link(links, inverted_step_index, "Value", step_index, "True")
    _link(links, strength, "Value", step_strength, "Value")
    _link(links, step_index, "Output", step_strength, "Value_001")
    _link(links, is_step, "Value", type_weight, "Switch")
    _link(links, weighted_strength, "Value", type_weight, "False")
    _link(links, step_strength, "Value", type_weight, "True")
    _link(links, group_input, socket_set["enabled"], enabled_weight, "Switch")
    _link(links, type_weight, "Output", enabled_weight, "True")
    _link(links, group_input, socket_set["use_position"], position_weight, "Switch")
    _link(links, enabled_weight, "Output", position_weight, "True")
    _link(links, group_input, socket_set["use_rotation"], rotation_weight, "Switch")
    _link(links, enabled_weight, "Output", rotation_weight, "True")
    _link(links, group_input, socket_set["use_scale"], scale_weight, "Switch")
    _link(links, enabled_weight, "Output", scale_weight, "True")

    _link(links, group_input, socket_set["position_x"], offset, "X")
    _link(links, group_input, socket_set["position_y"], offset, "Y")
    _link(links, group_input, socket_set["position_z"], offset, "Z")
    _link(links, offset, "Vector", negative_offset, "Vector")
    links.new(negative_offset.outputs["Vector"], random_offset.inputs[0])
    _link(links, offset, "Vector", random_offset, "Max")
    _link(links, index, "Index", random_offset, "ID")
    _link(links, group_input, socket_set["seed"], random_offset, "Seed")
    _link(links, is_random, "Value", effector_offset, "Switch")
    _link(links, offset, "Vector", effector_offset, "False")
    links.new(random_offset.outputs[0], effector_offset.inputs["True"])
    _link(links, effector_offset, "Output", weighted_offset, "Vector")
    _link(links, position_weight, "Output", weighted_offset, "Scale")
    _link(links, points_node, points_socket, set_position, "Geometry")
    _link(links, weighted_offset, "Vector", set_position, "Offset")

    _link(links, group_input, socket_set["scale_x"], desired_scale, "X")
    _link(links, group_input, socket_set["scale_y"], desired_scale, "Y")
    _link(links, group_input, socket_set["scale_z"], desired_scale, "Z")
    _link(links, one_scale, "Vector", negative_scale_variation, "Vector")
    links.new(desired_scale.outputs["Vector"], negative_scale_variation.inputs[1])
    _link(links, one_scale, "Vector", positive_scale_variation, "Vector")
    links.new(desired_scale.outputs["Vector"], positive_scale_variation.inputs[1])
    _link(links, negative_scale_variation, "Vector", clamped_negative_scale, "Vector")
    links.new(min_scale_floor.outputs["Vector"], clamped_negative_scale.inputs[1])
    _link(links, clamped_negative_scale, "Vector", random_scale, "Min")
    _link(links, positive_scale_variation, "Vector", random_scale, "Max")
    _link(links, index, "Index", random_scale, "ID")
    _link(links, group_input, socket_set["seed"], random_scale, "Seed")
    _link(links, is_random, "Value", effector_scale, "Switch")
    _link(links, desired_scale, "Vector", effector_scale, "False")
    links.new(random_scale.outputs[0], effector_scale.inputs["True"])
    _link(links, effector_scale, "Output", scale_delta, "Vector")
    links.new(one_scale.outputs["Vector"], scale_delta.inputs[1])
    _link(links, scale_delta, "Vector", weighted_scale_delta, "Vector")
    _link(links, scale_weight, "Output", weighted_scale_delta, "Scale")
    _link(links, one_scale, "Vector", final_scale, "Vector")
    links.new(weighted_scale_delta.outputs["Vector"], final_scale.inputs[1])

    _link(links, group_input, socket_set["rotation_x"], desired_rotation, "X")
    _link(links, group_input, socket_set["rotation_y"], desired_rotation, "Y")
    _link(links, group_input, socket_set["rotation_z"], desired_rotation, "Z")
    _link(links, desired_rotation, "Vector", negative_rotation, "Vector")
    links.new(negative_rotation.outputs["Vector"], random_rotation.inputs[0])
    _link(links, desired_rotation, "Vector", random_rotation, "Max")
    _link(links, index, "Index", random_rotation, "ID")
    _link(links, group_input, socket_set["seed"], random_rotation, "Seed")
    _link(links, is_random, "Value", effector_rotation, "Switch")
    _link(links, desired_rotation, "Vector", effector_rotation, "False")
    links.new(random_rotation.outputs[0], effector_rotation.inputs["True"])
    _link(links, effector_rotation, "Output", weighted_rotation_euler, "Vector")
    _link(links, rotation_weight, "Output", weighted_rotation_euler, "Scale")
    _link(links, weighted_rotation_euler, "Vector", weighted_rotation, "Euler")
    _link(links, base_rotation_node, base_rotation_socket, basic_rotation, "Rotation")
    _link(links, weighted_rotation, "Rotation", basic_rotation, "Rotate By")
    _link(links, is_target, "Value", rotation_type_switch, "Switch")
    _link(links, basic_rotation, "Rotation", rotation_type_switch, "False")
    _link(links, target_rotation, "Output", rotation_type_switch, "True")

    return set_position, "Geometry", rotation_type_switch, "Output", final_scale, "Vector"


def _build_target_rotation_nodes(
    nodes,
    links,
    group_input,
    socket_set: dict,
    base_rotation_node,
    base_rotation_socket: str,
    target_location,
    position,
    weight_node,
    origin: tuple[int, int],
):
    x, y = origin
    direction = _new_vector_math_node(nodes, (x, y), "SUBTRACT")
    global_up = _new_combine_xyz_node(nodes, (x, y - 180))
    target_index_scale = _new_math_node(nodes, (x + 720, y - 260), "MULTIPLY")
    target_index = _new_math_node(nodes, (x + 960, y - 260), "ADD")
    rotation_switch = _new_rotation_index_switch_node(nodes, (x + 1200, y), 9)

    global_up.inputs["Z"].default_value = 1.0
    target_index_scale.inputs[1].default_value = 3.0
    links.new(target_location.outputs["Output"], direction.inputs[0])
    links.new(position.outputs["Position"], direction.inputs[1])
    _link(links, group_input, socket_set["target_axis"], target_index_scale, "Value")
    _link(links, target_index_scale, "Value", target_index, "Value")
    links.new(_socket(group_input.outputs, socket_set["target_up_axis"]), target_index.inputs[1])
    _link(links, target_index, "Value", rotation_switch, "Index")

    axes = ("X", "Y", "Z")
    for aim_index, aim_axis in enumerate(axes):
        aim = _new_node(
            nodes,
            "FunctionNodeAlignRotationToVector",
            (x + 240, y + 260 - (aim_index * 220)),
        )
        aim.axis = aim_axis
        aim.pivot_axis = "AUTO"
        _link(links, base_rotation_node, base_rotation_socket, aim, "Rotation")
        _link(links, weight_node, "Output", aim, "Factor")
        _link(links, direction, "Vector", aim, "Vector")

        for up_index, up_axis in enumerate(axes):
            if up_axis == aim_axis:
                _link(
                    links,
                    aim,
                    "Rotation",
                    rotation_switch,
                    str(aim_index * 3 + up_index),
                )
                continue
            stabilize = _new_node(
                nodes,
                "FunctionNodeAlignRotationToVector",
                (x + 720, y + 500 - ((aim_index * 3 + up_index) * 140)),
            )
            stabilize.axis = up_axis
            stabilize.pivot_axis = aim_axis
            _link(links, aim, "Rotation", stabilize, "Rotation")
            _link(links, weight_node, "Output", stabilize, "Factor")
            _link(links, global_up, "Vector", stabilize, "Vector")
            _link(
                links,
                stabilize,
                "Rotation",
                rotation_switch,
                str(aim_index * 3 + up_index),
            )

    return rotation_switch


def _build_identity_instance_transform(
    nodes,
    links,
    points_node,
    points_socket: str,
    origin: tuple[int, int],
) -> tuple:
    x, y = origin
    zero_rotation = _new_combine_xyz_node(nodes, (x, y + 120))
    rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (x + 240, y + 120))
    scale = _new_combine_xyz_node(nodes, (x, y - 20))
    scale.inputs["X"].default_value = 1.0
    scale.inputs["Y"].default_value = 1.0
    scale.inputs["Z"].default_value = 1.0
    _link(links, zero_rotation, "Vector", rotation, "Euler")
    return points_node, points_socket, rotation, "Rotation", scale, "Vector"


def _configure_instance_picker(
    nodes,
    links,
    group_input,
    instance_node,
    source_count,
    origin: tuple[int, int],
) -> None:
    instance_node.inputs["Pick Instance"].default_value = True

    x, y = origin
    index = _new_node(nodes, "GeometryNodeInputIndex", (x, y))
    source_count_float = _new_math_node(nodes, (x + 240, y), "MAXIMUM")
    modulo = _new_math_node(nodes, (x + 480, y), "MODULO")

    source_count_float.inputs[1].default_value = 1.0
    _set_or_link_value(links, group_input, source_count, source_count_float, "Value")
    _link(links, index, "Index", modulo, "Value")
    links.new(source_count_float.outputs["Value"], modulo.inputs[1])
    _link(links, modulo, "Value", instance_node, "Instance Index")


def _configure_grid_instance_picker(
    nodes,
    links,
    group_input,
    instance_node,
    source_count,
    counts,
    spacings,
    origin: tuple[int, int],
) -> None:
    instance_node.inputs["Pick Instance"].default_value = True

    x, y = origin
    position = _new_node(nodes, "GeometryNodeInputPosition", (x, y + 120))
    separate = _new_node(nodes, "ShaderNodeSeparateXYZ", (x + 220, y + 120))
    index_x = _build_axis_index(
        nodes,
        links,
        group_input,
        separate,
        "X",
        counts[0],
        spacings[0],
        (x + 460, y + 220),
    )
    index_y = _build_axis_index(
        nodes,
        links,
        group_input,
        separate,
        "Y",
        counts[1],
        spacings[1],
        (x + 460, y + 60),
    )
    index_z = _build_axis_index(
        nodes,
        links,
        group_input,
        separate,
        "Z",
        counts[2],
        spacings[2],
        (x + 460, y - 100),
    )
    add_xy = _new_math_node(nodes, (x + 980, y + 110), "ADD")
    add_xyz = _new_math_node(nodes, (x + 1220, y + 40), "ADD")
    source_count_float = _new_math_node(nodes, (x + 1220, y - 120), "MAXIMUM")
    modulo = _new_math_node(nodes, (x + 1460, y + 20), "MODULO")

    source_count_float.inputs[1].default_value = 1.0
    _link(links, position, "Position", separate, "Vector")
    _link(links, index_x, "Value", add_xy, "Value")
    links.new(index_y.outputs["Value"], add_xy.inputs[1])
    _link(links, add_xy, "Value", add_xyz, "Value")
    links.new(index_z.outputs["Value"], add_xyz.inputs[1])
    _set_or_link_value(links, group_input, source_count, source_count_float, "Value")
    _link(links, add_xyz, "Value", modulo, "Value")
    links.new(source_count_float.outputs["Value"], modulo.inputs[1])
    _link(links, modulo, "Value", instance_node, "Instance Index")


def _build_axis_index(
    nodes,
    links,
    group_input,
    separate_xyz,
    axis: str,
    count,
    spacing,
    origin: tuple[int, int],
):
    x, y = origin
    denominator = _new_math_node(nodes, (x, y), "MAXIMUM")
    divide = _new_math_node(nodes, (x + 240, y), "DIVIDE")
    rounded = _new_math_node(nodes, (x + 480, y), "ROUND")
    center_offset = _build_center_offset(
        nodes,
        links,
        group_input,
        count,
        (x + 240, y - 120),
    )
    add_center_offset = _new_math_node(nodes, (x + 720, y), "ADD")

    denominator.inputs[1].default_value = 0.000001
    _set_or_link_value(links, group_input, spacing, denominator, "Value")
    _link(links, separate_xyz, axis, divide, "Value")
    links.new(denominator.outputs["Value"], divide.inputs[1])
    _link(links, divide, "Value", rounded, "Value")
    _link(links, rounded, "Value", add_center_offset, "Value")
    links.new(center_offset.outputs["Value"], add_center_offset.inputs[1])
    return add_center_offset


def _set_centered_line_start(
    nodes,
    links,
    group_input,
    mesh_line,
    count,
    spacing,
    axis: str,
    origin: tuple[int, int],
) -> None:
    x, y = origin
    center_offset = _build_center_offset(nodes, links, group_input, count, (x, y))
    negative_spacing = _new_math_node(nodes, (x + 260, y), "MULTIPLY")
    start_component = _new_math_node(nodes, (x + 500, y), "MULTIPLY")
    start_vector = _new_combine_xyz_node(nodes, (x + 740, y))

    negative_spacing.inputs[1].default_value = -1.0
    _set_or_link_value(links, group_input, spacing, negative_spacing, "Value")
    _link(links, center_offset, "Value", start_component, "Value")
    links.new(negative_spacing.outputs["Value"], start_component.inputs[1])
    _link(links, start_component, "Value", start_vector, axis)
    _link(links, start_vector, "Vector", mesh_line, "Start Location")


def _build_center_offset(
    nodes,
    links,
    group_input,
    count,
    origin: tuple[int, int],
):
    x, y = origin
    count_minus_one = _new_math_node(nodes, (x, y), "SUBTRACT")
    half_count = _new_math_node(nodes, (x + 240, y), "MULTIPLY")

    count_minus_one.inputs[1].default_value = 1.0
    half_count.inputs[1].default_value = 0.5
    _set_or_link_value(links, group_input, count, count_minus_one, "Value")
    _link(links, count_minus_one, "Value", half_count, "Value")
    return half_count


def _set_radial_axis_vector(axis: str, axis_vector) -> None:
    if axis == "X":
        axis_vector.inputs["X"].default_value = 1.0
    elif axis == "Y":
        axis_vector.inputs["Y"].default_value = 1.0
    else:
        axis_vector.inputs["Z"].default_value = 1.0


def _build_distribution_switch(
    nodes,
    links,
    group_input,
    *,
    grid: tuple,
    brick: tuple,
    linear: tuple,
    radial: tuple,
    object_distribution: tuple,
    location: tuple[int, int],
) -> tuple:
    switch = _new_geometry_index_switch_node(nodes, location, 5)

    _link(links, group_input, properties.SOCKET_DISTRIBUTION_MODE, switch, "Index")
    _link(links, grid[0], grid[1], switch, "0")
    _link(links, linear[0], linear[1], switch, "1")
    _link(links, radial[0], radial[1], switch, "2")
    _link(links, object_distribution[0], object_distribution[1], switch, "3")
    _link(links, brick[0], brick[1], switch, "4")
    return switch, "Output"


def _build_source_transform(
    nodes,
    links,
    group_input,
    source_node,
    source_socket: str,
    origin: tuple[int, int],
) -> tuple:
    x, y = origin
    position = _new_combine_xyz_node(nodes, (x, y + 200))
    rotation_x = _new_combine_xyz_node(nodes, (x, y + 40))
    rotation_y = _new_combine_xyz_node(nodes, (x, y - 80))
    rotation_z = _new_combine_xyz_node(nodes, (x, y - 200))
    scale = _new_combine_xyz_node(nodes, (x, y - 320))
    scale_transform = _new_node(nodes, "GeometryNodeTransform", (x + 260, y - 120))
    rotate_z_transform = _new_node(nodes, "GeometryNodeTransform", (x + 520, y - 120))
    rotate_y_transform = _new_node(nodes, "GeometryNodeTransform", (x + 780, y - 120))
    rotate_x_transform = _new_node(nodes, "GeometryNodeTransform", (x + 1040, y - 120))
    position_transform = _new_node(nodes, "GeometryNodeTransform", (x + 1300, y - 120))

    _link(links, group_input, properties.SOCKET_SOURCE_POSITION_X, position, "X")
    _link(links, group_input, properties.SOCKET_SOURCE_POSITION_Y, position, "Y")
    _link(links, group_input, properties.SOCKET_SOURCE_POSITION_Z, position, "Z")
    _link(links, group_input, properties.SOCKET_SOURCE_ROTATION_X, rotation_x, "X")
    _link(links, group_input, properties.SOCKET_SOURCE_ROTATION_Y, rotation_y, "Y")
    _link(links, group_input, properties.SOCKET_SOURCE_ROTATION_Z, rotation_z, "Z")
    _link(links, group_input, properties.SOCKET_SOURCE_SCALE_X, scale, "X")
    _link(links, group_input, properties.SOCKET_SOURCE_SCALE_Y, scale, "Y")
    _link(links, group_input, properties.SOCKET_SOURCE_SCALE_Z, scale, "Z")
    _link(links, source_node, source_socket, scale_transform, "Geometry")
    _link(links, scale, "Vector", scale_transform, "Scale")
    _link(links, scale_transform, "Geometry", rotate_z_transform, "Geometry")
    _link(links, rotation_z, "Vector", rotate_z_transform, "Rotation")
    _link(links, rotate_z_transform, "Geometry", rotate_y_transform, "Geometry")
    _link(links, rotation_y, "Vector", rotate_y_transform, "Rotation")
    _link(links, rotate_y_transform, "Geometry", rotate_x_transform, "Geometry")
    _link(links, rotation_x, "Vector", rotate_x_transform, "Rotation")
    _link(links, rotate_x_transform, "Geometry", position_transform, "Geometry")
    _link(links, position, "Vector", position_transform, "Translation")

    return position_transform, "Geometry"


def _new_panel(interface, name: str, parent=None, default_closed: bool = False):
    panel = interface.new_panel(name=name, default_closed=default_closed)
    if parent is not None:
        interface.move_to_parent(panel, parent, len(parent.interface_items))
    return panel


def _new_socket(interface, name: str, in_out: str, socket_type: str, parent=None):
    return interface.new_socket(
        name=name,
        in_out=in_out,
        socket_type=socket_type,
        parent=parent,
    )


def _hide_modifier_inputs(interface) -> None:
    for item in interface.items_tree:
        if (
            getattr(item, "item_type", None) == "SOCKET"
            and getattr(item, "in_out", None) == "INPUT"
            and item.name != properties.SOCKET_GEOMETRY
        ):
            item.hide_in_modifier = True


def _new_node(nodes, bl_idname: str, location: tuple[int, int]):
    node = nodes.new(bl_idname)
    node.location = location
    return node


def _new_combine_xyz_node(nodes, location: tuple[int, int]):
    return _new_node(nodes, "ShaderNodeCombineXYZ", location)


def _new_vector_math_node(nodes, location: tuple[int, int], operation: str):
    node = _new_node(nodes, "ShaderNodeVectorMath", location)
    node.operation = operation
    return node


def _new_math_node(nodes, location: tuple[int, int], operation: str):
    node = _new_node(nodes, "ShaderNodeMath", location)
    node.operation = operation
    return node


def _new_boolean_math_node(nodes, location: tuple[int, int], operation: str):
    node = _new_node(nodes, "FunctionNodeBooleanMath", location)
    node.operation = operation
    return node


def _new_rotation_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "ROTATION"
    return node


def _new_float_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "FLOAT"
    return node


def _new_int_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "INT"
    return node


def _new_geometry_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "GEOMETRY"
    return node


def _new_vector_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "VECTOR"
    return node


def _new_random_vector_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "FunctionNodeRandomValue", location)
    node.data_type = "FLOAT_VECTOR"
    return node


def _build_store_index_attribute(
    nodes,
    links,
    geometry_node,
    geometry_socket: str,
    name: str,
    location: tuple[int, int],
):
    store = _new_node(nodes, "GeometryNodeStoreNamedAttribute", location)
    store.data_type = "FLOAT"
    store.domain = "POINT"
    index = _new_node(nodes, "GeometryNodeInputIndex", (location[0] - 240, location[1] - 120))
    store.inputs["Name"].default_value = name
    store.inputs["Selection"].default_value = True
    _link(links, geometry_node, geometry_socket, store, "Geometry")
    _link(links, index, "Index", store, "Value")
    return store


def _new_named_float_attribute_node(nodes, name: str, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeInputNamedAttribute", location)
    node.data_type = "FLOAT"
    node.inputs["Name"].default_value = name
    return node


def _new_geometry_index_switch_node(
    nodes,
    location: tuple[int, int],
    item_count: int,
):
    node = _new_node(nodes, "GeometryNodeIndexSwitch", location)
    node.data_type = "GEOMETRY"
    while len(node.index_switch_items) < item_count:
        node.index_switch_items.new()
    return node


def _new_rotation_index_switch_node(
    nodes,
    location: tuple[int, int],
    item_count: int,
):
    node = _new_node(nodes, "GeometryNodeIndexSwitch", location)
    node.data_type = "ROTATION"
    while len(node.index_switch_items) < item_count:
        node.index_switch_items.new()
    return node


def _new_vector_index_switch_node(
    nodes,
    location: tuple[int, int],
    item_count: int,
):
    node = _new_node(nodes, "GeometryNodeIndexSwitch", location)
    node.data_type = "VECTOR"
    while len(node.index_switch_items) < item_count:
        node.index_switch_items.new()
    return node


def _new_mesh_line_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeMeshLine", location)
    if hasattr(node, "mode"):
        node.mode = "OFFSET"
    if hasattr(node, "count_mode"):
        node.count_mode = "TOTAL"
    return node


def _new_mesh_to_points_node(nodes, location: tuple[int, int], mode: str):
    node = _new_node(nodes, "GeometryNodeMeshToPoints", location)
    node.mode = mode
    return node


def _new_capture_vector_node(
    nodes,
    location: tuple[int, int],
    domain: str,
    name: str = "Normal",
):
    node = _new_node(nodes, "GeometryNodeCaptureAttribute", location)
    node.domain = domain
    node.capture_items.new("VECTOR", name)
    return node


def _set_or_link_value(
    links,
    group_input,
    value_or_socket_name,
    to_node,
    to_socket_name: str,
) -> None:
    if isinstance(value_or_socket_name, tuple):
        _link(links, value_or_socket_name[0], value_or_socket_name[1], to_node, to_socket_name)
        return
    if group_input is None:
        to_node.inputs[to_socket_name].default_value = value_or_socket_name
        return

    _link(links, group_input, value_or_socket_name, to_node, to_socket_name)


def _set_or_link_vector_component(
    links,
    group_input,
    value_or_socket_name,
    to_node,
    to_socket_name: str,
) -> None:
    if isinstance(value_or_socket_name, tuple):
        _link(links, value_or_socket_name[0], value_or_socket_name[1], to_node, to_socket_name)
        return
    if group_input is None:
        to_node.inputs[to_socket_name].default_value = value_or_socket_name
        return

    _link(links, group_input, value_or_socket_name, to_node, to_socket_name)


def _link(links, from_node, from_socket_name: str, to_node, to_socket_name: str) -> None:
    links.new(
        _socket(from_node.outputs, from_socket_name),
        _socket(to_node.inputs, to_socket_name),
    )


def _socket(sockets, name: str):
    socket = sockets.get(name)
    if socket is None:
        socket = next((candidate for candidate in sockets if candidate.name == name), None)
    if socket is None:
        available = ", ".join(socket.name for socket in sockets)
        raise RuntimeError(f"Missing socket {name!r}. Available sockets: {available}")
    return socket
