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

    node_group = bpy.data.node_groups.new(
        properties.GRID_NODE_GROUP_NAME,
        "GeometryNodeTree",
    )
    _create_interface(node_group)
    _create_nodes(node_group, nested_grid)

    return node_group


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

    _set_or_link_vector_component(links, group_input, spacings[0], combine_x, "X")
    _set_or_link_vector_component(links, group_input, spacings[1], combine_y, "Y")
    _set_or_link_vector_component(links, group_input, spacings[2], combine_z, "Z")
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_x,
        counts[0],
        spacings[0],
        "X",
        (x - 460, y - 90),
    )
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_y,
        counts[1],
        spacings[1],
        "Y",
        (x + 60, y - 90),
    )
    _set_centered_line_start(
        nodes,
        links,
        group_input,
        mesh_line_z,
        counts[2],
        spacings[2],
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
    _link(links, realize_points, "Geometry", instance_source, "Points")
    _link(links, source_node, source_socket, instance_source, "Instance")
    _configure_grid_instance_picker(
        nodes,
        links,
        group_input,
        instance_source,
        source_count,
        counts,
        spacings,
        (x + 1540, y - 300),
    )

    return instance_source, "Instances"


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

    _link(links, group_input, properties.SOCKET_LINEAR_COUNT, mesh_line, "Count")
    _link(links, group_input, properties.SOCKET_LINEAR_DIRECTION_X, direction, "X")
    _link(links, group_input, properties.SOCKET_LINEAR_DIRECTION_Y, direction, "Y")
    _link(links, group_input, properties.SOCKET_LINEAR_DIRECTION_Z, direction, "Z")
    _link(links, direction, "Vector", normalize, "Vector")
    _link(links, normalize, "Vector", scale, "Vector")
    _link(links, group_input, properties.SOCKET_LINEAR_SPACING, scale, "Scale")
    _link(links, scale, "Vector", mesh_line, "Offset")
    _link(links, mesh_line, "Mesh", instance, "Points")
    _link(links, source_node, source_socket, instance, "Instance")
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
    _link(links, set_position, "Geometry", instance, "Points")
    _link(links, source_node, source_socket, instance, "Instance")
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
    _link(links, rotation_switch, "Output", instance, "Rotation")

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
