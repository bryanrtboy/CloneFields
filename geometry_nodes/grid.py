"""Build the Geometry Nodes graph for the first Clone Fields grid cloner."""

from __future__ import annotations

import bpy

from .. import properties


def create_grid_node_group(nested_grid: dict | None = None) -> bpy.types.GeometryNodeTree:
    """Create a fresh grid cloner node group.

    The group intentionally exposes only milestone parameters. Additional
    distribution modes should be implemented as separate builders rather than
    branching this graph into a general-purpose system too early.
    """
    if nested_grid is None:
        reusable = _reusable_grid_node_group()
        if reusable is not None:
            return reusable

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
    linear_panel = _new_panel(interface, "Linear", default_closed=True)
    linear_direction_panel = _new_panel(
        interface,
        "Direction",
        parent=linear_panel,
    )
    radial_panel = _new_panel(interface, "Radial", default_closed=True)
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
    socket = _new_socket(
        interface,
        properties.SOCKET_EFFECTOR_FIELD,
        "INPUT",
        "NodeSocketInt",
        parent=effector_panel,
    )
    socket.default_value = properties.GRID_INPUT_DEFAULTS[properties.SOCKET_EFFECTOR_FIELD]
    socket.min_value = 0
    socket.max_value = 3
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
    socket.min_value = 0
    socket.max_value = 2

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
    socket.max_value = 2

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
        source_node, source_socket = _build_source_transform(
            nodes,
            links,
            group_input,
            collection_info,
            "Instances",
            (-420, -180),
        )
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

    grid_node, grid_socket = _build_grid_distribution(
        nodes,
        links,
        source_node=source_node,
        source_socket=source_socket,
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
        origin=(x_offset, 250),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )
    linear_node, linear_socket = _build_linear_distribution(
        nodes,
        links,
        source_node=source_node,
        source_socket=source_socket,
        origin=(x_offset, -350),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )
    radial_node, radial_socket = _build_radial_distribution(
        nodes,
        links,
        source_node=source_node,
        source_socket=source_socket,
        origin=(x_offset, -900),
        group_input=group_input,
        source_count=properties.SOCKET_SOURCE_COUNT,
    )
    output_node, output_socket = _build_distribution_switch(
        nodes,
        links,
        group_input,
        grid=(grid_node, grid_socket),
        linear=(linear_node, linear_socket),
        radial=(radial_node, radial_socket),
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
    socket = _new_socket(interface, socket_set["field"], "INPUT", "NodeSocketInt", parent=panel)
    socket.default_value = properties.GRID_INPUT_DEFAULTS[socket_set["field"]]
    socket.min_value = 0
    socket.max_value = 3
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
    instance_x_on_y = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 780, y - 80))

    mesh_line_y = _new_mesh_line_node(nodes, (x + 520, y))
    combine_y = _new_combine_xyz_node(nodes, (x + 320, y + 90))

    mesh_line_z = _new_mesh_line_node(nodes, (x + 1040, y))
    combine_z = _new_combine_xyz_node(nodes, (x + 840, y + 90))
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

    _link(links, mesh_line_y, "Mesh", instance_x_on_y, "Points")
    _link(links, mesh_line_x, "Mesh", instance_x_on_y, "Instance")

    _link(links, mesh_line_z, "Mesh", instance_xy_on_z, "Points")
    _link(links, instance_x_on_y, "Instances", instance_xy_on_z, "Instance")

    _link(links, instance_xy_on_z, "Instances", realize_points, "Geometry")
    points_node, points_socket, rotation_node, rotation_socket, scale_node, scale_socket = (
        _build_all_plain_effector_points(
            nodes,
            links,
            group_input,
            realize_points,
            "Geometry",
            (x + 1540, y + 180),
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
    combined_rotation = _new_node(nodes, "FunctionNodeRotateRotation", (x + 2140, y - 300))
    _link(links, rotation_switch, "Output", combined_rotation, "Rotation")
    _link(links, effector_rotation_node, effector_rotation_socket, combined_rotation, "Rotate By")
    _link(links, combined_rotation, "Rotation", instance, "Rotation")

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


def _build_all_plain_effector_points(
    nodes,
    links,
    group_input,
    points_node,
    points_socket: str,
    origin: tuple[int, int],
) -> tuple:
    if group_input is None:
        return _build_identity_instance_transform(
            nodes,
            links,
            points_node,
            points_socket,
            origin,
        )

    current_node = points_node
    current_socket = points_socket
    rotation_vector_node = None
    rotation_vector_socket = None
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
                (origin[0], origin[1] - (index * 760)),
                socket_set,
            )
        )
        if rotation_vector_node is None:
            rotation_vector_node = slot_rotation_node
            rotation_vector_socket = slot_rotation_socket
        else:
            add_rotation = _new_vector_math_node(
                nodes,
                (origin[0] + 2960, origin[1] + 700 - (index * 180)),
                "ADD",
            )
            _link(links, rotation_vector_node, rotation_vector_socket, add_rotation, "Vector")
            links.new(slot_rotation_node.outputs[slot_rotation_socket], add_rotation.inputs[1])
            rotation_vector_node = add_rotation
            rotation_vector_socket = "Vector"
        if scale_node is None:
            scale_node = slot_scale_node
            scale_socket = slot_scale_socket
        else:
            multiply_scale = _new_vector_math_node(
                nodes,
                (origin[0] + 2960, origin[1] + 420 - (index * 180)),
                "MULTIPLY",
            )
            _link(links, scale_node, scale_socket, multiply_scale, "Vector")
            links.new(slot_scale_node.outputs[slot_scale_socket], multiply_scale.inputs[1])
            scale_node = multiply_scale
            scale_socket = "Vector"
    rotation = _new_node(nodes, "FunctionNodeEulerToRotation", (origin[0] + 3240, origin[1] + 700))
    _link(links, rotation_vector_node, rotation_vector_socket, rotation, "Euler")
    return current_node, current_socket, rotation, "Rotation", scale_node, scale_socket


def _build_plain_effector_points(
    nodes,
    links,
    group_input,
    points_node,
    points_socket: str,
    origin: tuple[int, int],
    socket_set: dict,
) -> tuple:
    x, y = origin
    object_info = _new_node(nodes, "GeometryNodeObjectInfo", (x, y))
    object_info.transform_space = "RELATIVE"
    position = _new_node(nodes, "GeometryNodeInputPosition", (x, y - 170))
    distance = _new_vector_math_node(nodes, (x + 260, y - 80), "DISTANCE")
    local_offset = _new_vector_math_node(nodes, (x + 260, y - 250), "SUBTRACT")
    inverse_rotation = _new_node(nodes, "FunctionNodeInvertRotation", (x + 260, y - 420))
    local_position = _new_node(nodes, "FunctionNodeRotateVector", (x + 500, y - 300))
    absolute_local = _new_vector_math_node(nodes, (x + 740, y - 300), "ABSOLUTE")
    separate_local = _new_node(nodes, "ShaderNodeSeparateXYZ", (x + 980, y - 300))
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
    max_xy = _new_math_node(nodes, (x + 1220, y - 300), "MAXIMUM")
    cubic_distance = _new_math_node(nodes, (x + 1460, y - 300), "MAXIMUM")
    is_cubic = _new_math_node(nodes, (x + 1220, y - 520), "COMPARE")
    is_cylinder = _new_math_node(nodes, (x + 1460, y - 520), "COMPARE")
    is_linear = _new_math_node(nodes, (x + 1700, y - 520), "COMPARE")
    box_or_sphere_distance = _new_float_switch_node(nodes, (x + 1700, y - 220))
    volume_distance = _new_float_switch_node(nodes, (x + 1940, y - 220))
    field_distance = _new_float_switch_node(nodes, (x + 2180, y - 220))
    field_size = _new_float_switch_node(nodes, (x + 2180, y - 360))
    radius_minus_distance = _new_math_node(nodes, (x + 500, y - 80), "SUBTRACT")
    falloff_percent = _new_math_node(nodes, (x + 500, y - 360), "MULTIPLY")
    falloff_range_factor = _new_math_node(nodes, (x + 740, y - 360), "SUBTRACT")
    scaled_falloff = _new_math_node(nodes, (x + 980, y - 360), "MULTIPLY")
    safe_falloff = _new_math_node(nodes, (x + 740, y - 80), "MAXIMUM")
    falloff_weight = _new_math_node(nodes, (x + 980, y - 80), "DIVIDE")
    inverted_weight = _new_math_node(nodes, (x + 1220, y - 80), "SUBTRACT")
    inverse_switch = _new_float_switch_node(nodes, (x + 1460, y - 80))
    strength = _new_math_node(nodes, (x + 1700, y - 80), "MULTIPLY")
    enabled_weight = _new_float_switch_node(nodes, (x + 1940, y - 80))
    position_weight = _new_float_switch_node(nodes, (x + 2180, y + 80))
    rotation_weight = _new_float_switch_node(nodes, (x + 2180, y + 620))
    scale_weight = _new_float_switch_node(nodes, (x + 2180, y + 340))

    offset = _new_combine_xyz_node(nodes, (x + 980, y + 160))
    weighted_offset = _new_vector_math_node(nodes, (x + 2420, y + 160), "SCALE")
    set_position = _new_node(nodes, "GeometryNodeSetPosition", (x + 2680, y + 120))

    desired_scale = _new_combine_xyz_node(nodes, (x + 980, y + 380))
    one_scale = _new_combine_xyz_node(nodes, (x + 980, y + 520))
    scale_delta = _new_vector_math_node(nodes, (x + 1220, y + 420), "SUBTRACT")
    weighted_scale_delta = _new_vector_math_node(nodes, (x + 2420, y + 420), "SCALE")
    final_scale = _new_vector_math_node(nodes, (x + 2660, y + 420), "ADD")

    desired_rotation = _new_combine_xyz_node(nodes, (x + 980, y + 700))
    weighted_rotation = _new_vector_math_node(nodes, (x + 2420, y + 700), "SCALE")

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
    inverted_weight.inputs[0].default_value = 1.0
    falloff_range_factor.inputs[0].default_value = 1.0
    one_scale.inputs["X"].default_value = 1.0
    one_scale.inputs["Y"].default_value = 1.0
    one_scale.inputs["Z"].default_value = 1.0

    _link(links, group_input, socket_set["object"], object_info, "Object")
    _link(links, position, "Position", distance, "Vector")
    links.new(object_info.outputs["Location"], distance.inputs[1])
    _link(links, position, "Position", local_offset, "Vector")
    links.new(object_info.outputs["Location"], local_offset.inputs[1])
    links.new(object_info.outputs["Rotation"], inverse_rotation.inputs["Rotation"])
    _link(links, local_offset, "Vector", local_position, "Vector")
    links.new(inverse_rotation.outputs["Rotation"], local_position.inputs["Rotation"])
    _link(links, local_position, "Vector", absolute_local, "Vector")
    _link(links, absolute_local, "Vector", separate_local, "Vector")
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
    links.new(separate_local.outputs["X"], max_xy.inputs["Value"])
    links.new(separate_local.outputs["Y"], max_xy.inputs[1])
    _link(links, max_xy, "Value", cubic_distance, "Value")
    links.new(separate_local.outputs["Z"], cubic_distance.inputs[1])
    _link(links, group_input, socket_set["field"], is_cubic, "Value")
    _link(links, group_input, socket_set["field"], is_cylinder, "Value")
    _link(links, group_input, socket_set["field"], is_linear, "Value")
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
    links.new(
        _socket(group_input.outputs, socket_set["falloff"]),
        falloff_percent.inputs["Value"],
    )
    links.new(falloff_percent.outputs["Value"], falloff_range_factor.inputs[1])
    links.new(field_size.outputs["Output"], scaled_falloff.inputs["Value"])
    links.new(falloff_range_factor.outputs["Value"], scaled_falloff.inputs[1])
    links.new(field_size.outputs["Output"], radius_minus_distance.inputs["Value"])
    links.new(field_distance.outputs["Output"], radius_minus_distance.inputs[1])
    _link(links, scaled_falloff, "Value", safe_falloff, "Value")
    _link(links, radius_minus_distance, "Value", falloff_weight, "Value")
    links.new(safe_falloff.outputs["Value"], falloff_weight.inputs[1])
    links.new(falloff_weight.outputs["Value"], inverted_weight.inputs[1])
    _link(links, group_input, socket_set["invert"], inverse_switch, "Switch")
    _link(links, falloff_weight, "Value", inverse_switch, "False")
    _link(links, inverted_weight, "Value", inverse_switch, "True")
    _link(links, inverse_switch, "Output", strength, "Value")
    links.new(
        _socket(group_input.outputs, socket_set["strength"]),
        strength.inputs[1],
    )
    _link(links, group_input, socket_set["enabled"], enabled_weight, "Switch")
    _link(links, strength, "Value", enabled_weight, "True")
    _link(links, group_input, socket_set["use_position"], position_weight, "Switch")
    _link(links, enabled_weight, "Output", position_weight, "True")
    _link(links, group_input, socket_set["use_rotation"], rotation_weight, "Switch")
    _link(links, enabled_weight, "Output", rotation_weight, "True")
    _link(links, group_input, socket_set["use_scale"], scale_weight, "Switch")
    _link(links, enabled_weight, "Output", scale_weight, "True")

    _link(links, group_input, socket_set["position_x"], offset, "X")
    _link(links, group_input, socket_set["position_y"], offset, "Y")
    _link(links, group_input, socket_set["position_z"], offset, "Z")
    _link(links, offset, "Vector", weighted_offset, "Vector")
    _link(links, position_weight, "Output", weighted_offset, "Scale")
    _link(links, points_node, points_socket, set_position, "Geometry")
    _link(links, weighted_offset, "Vector", set_position, "Offset")

    _link(links, group_input, socket_set["scale_x"], desired_scale, "X")
    _link(links, group_input, socket_set["scale_y"], desired_scale, "Y")
    _link(links, group_input, socket_set["scale_z"], desired_scale, "Z")
    _link(links, desired_scale, "Vector", scale_delta, "Vector")
    links.new(one_scale.outputs["Vector"], scale_delta.inputs[1])
    _link(links, scale_delta, "Vector", weighted_scale_delta, "Vector")
    _link(links, scale_weight, "Output", weighted_scale_delta, "Scale")
    _link(links, one_scale, "Vector", final_scale, "Vector")
    links.new(weighted_scale_delta.outputs["Vector"], final_scale.inputs[1])

    _link(links, group_input, socket_set["rotation_x"], desired_rotation, "X")
    _link(links, group_input, socket_set["rotation_y"], desired_rotation, "Y")
    _link(links, group_input, socket_set["rotation_z"], desired_rotation, "Z")
    _link(links, desired_rotation, "Vector", weighted_rotation, "Vector")
    _link(links, rotation_weight, "Output", weighted_rotation, "Scale")

    return set_position, "Geometry", weighted_rotation, "Vector", final_scale, "Vector"


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
    linear: tuple,
    radial: tuple,
    location: tuple[int, int],
) -> tuple:
    switch = _new_geometry_index_switch_node(nodes, location, 3)

    _link(links, group_input, properties.SOCKET_DISTRIBUTION_MODE, switch, "Index")
    _link(links, grid[0], grid[1], switch, "0")
    _link(links, linear[0], linear[1], switch, "1")
    _link(links, radial[0], radial[1], switch, "2")
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


def _new_rotation_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "ROTATION"
    return node


def _new_float_switch_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeSwitch", location)
    node.input_type = "FLOAT"
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


def _new_mesh_line_node(nodes, location: tuple[int, int]):
    node = _new_node(nodes, "GeometryNodeMeshLine", location)
    if hasattr(node, "mode"):
        node.mode = "OFFSET"
    if hasattr(node, "count_mode"):
        node.count_mode = "TOTAL"
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
        available = ", ".join(socket.name for socket in sockets)
        raise RuntimeError(f"Missing socket {name!r}. Available sockets: {available}")
    return socket
