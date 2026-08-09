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

    count_panel = _new_panel(interface, "Count")
    spacing_panel = _new_panel(interface, "Spacing")
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


def _create_nodes(
    node_group: bpy.types.GeometryNodeTree,
    nested_grid: dict | None = None,
) -> None:
    nodes = node_group.nodes
    links = node_group.links
    nodes.clear()

    group_input = _new_node(nodes, "NodeGroupInput", (-900, 100))
    object_info = _new_node(nodes, "GeometryNodeObjectInfo", (-680, -180))
    node_group.interface_update(bpy.context)
    object_info.inputs["As Instance"].default_value = True

    if nested_grid is None:
        _link(links, group_input, properties.SOCKET_SOURCE_OBJECT, object_info, "Object")
        source_node, source_socket = _build_source_transform(
            nodes,
            links,
            group_input,
            object_info,
            "Geometry",
            (-420, -180),
        )
        x_offset = -680
    else:
        object_info.inputs["Object"].default_value = nested_grid["source_object"]
        source_node, source_socket = _build_grid_distribution(
            nodes,
            links,
            source_node=object_info,
            source_socket="Geometry",
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
        )
        realize_nested = _new_node(nodes, "GeometryNodeRealizeInstances", (780, -260))
        _link(links, source_node, source_socket, realize_nested, "Geometry")
        source_node = realize_nested
        source_socket = "Geometry"
        x_offset = 180

    output_node, output_socket = _build_grid_distribution(
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
    )
    realize_output = _new_node(
        nodes,
        "GeometryNodeRealizeInstances",
        (x_offset + 1560, 20),
    )
    group_output = _new_node(nodes, "NodeGroupOutput", (x_offset + 1560, 170))
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
) -> tuple:
    x, y = origin

    mesh_line_x = _new_mesh_line_node(nodes, (x, y))
    combine_x = _new_combine_xyz_node(nodes, (x - 200, y + 90))
    instance_x = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 260, y - 80))

    mesh_line_y = _new_mesh_line_node(nodes, (x + 520, y))
    combine_y = _new_combine_xyz_node(nodes, (x + 320, y + 90))
    instance_y = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 780, y - 80))

    mesh_line_z = _new_mesh_line_node(nodes, (x + 1040, y))
    combine_z = _new_combine_xyz_node(nodes, (x + 840, y + 90))
    instance_z = _new_node(nodes, "GeometryNodeInstanceOnPoints", (x + 1300, y - 80))

    _set_or_link_value(links, group_input, counts[0], mesh_line_x, "Count")
    _set_or_link_value(links, group_input, counts[1], mesh_line_y, "Count")
    _set_or_link_value(links, group_input, counts[2], mesh_line_z, "Count")

    _set_or_link_vector_component(links, group_input, spacings[0], combine_x, "X")
    _set_or_link_vector_component(links, group_input, spacings[1], combine_y, "Y")
    _set_or_link_vector_component(links, group_input, spacings[2], combine_z, "Z")

    _link(links, combine_x, "Vector", mesh_line_x, "Offset")
    _link(links, combine_y, "Vector", mesh_line_y, "Offset")
    _link(links, combine_z, "Vector", mesh_line_z, "Offset")

    _link(links, mesh_line_x, "Mesh", instance_x, "Points")
    _link(links, source_node, source_socket, instance_x, "Instance")

    _link(links, mesh_line_y, "Mesh", instance_y, "Points")
    _link(links, instance_x, "Instances", instance_y, "Instance")

    _link(links, mesh_line_z, "Mesh", instance_z, "Points")
    _link(links, instance_y, "Instances", instance_z, "Instance")

    return instance_z, "Instances"


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
    negative_location = _new_vector_math_node(nodes, (x + 260, y + 160), "SCALE")
    restore_location = _new_vector_math_node(nodes, (x + 1040, y + 160), "ADD")
    to_origin = _new_node(nodes, "GeometryNodeTransform", (x + 260, y - 120))
    scale_transform = _new_node(nodes, "GeometryNodeTransform", (x + 520, y - 120))
    rotate_z_transform = _new_node(nodes, "GeometryNodeTransform", (x + 780, y - 120))
    rotate_y_transform = _new_node(nodes, "GeometryNodeTransform", (x + 1040, y - 120))
    rotate_x_transform = _new_node(nodes, "GeometryNodeTransform", (x + 1300, y - 120))
    from_origin = _new_node(nodes, "GeometryNodeTransform", (x + 1560, y - 120))

    negative_location.inputs["Scale"].default_value = -1.0
    _link(links, source_node, source_socket, to_origin, "Geometry")
    _link(links, source_node, "Location", negative_location, "Vector")
    _link(links, negative_location, "Vector", to_origin, "Translation")
    _link(links, group_input, properties.SOCKET_SOURCE_POSITION_X, position, "X")
    _link(links, group_input, properties.SOCKET_SOURCE_POSITION_Y, position, "Y")
    _link(links, group_input, properties.SOCKET_SOURCE_POSITION_Z, position, "Z")
    _link(links, group_input, properties.SOCKET_SOURCE_ROTATION_X, rotation_x, "X")
    _link(links, group_input, properties.SOCKET_SOURCE_ROTATION_Y, rotation_y, "Y")
    _link(links, group_input, properties.SOCKET_SOURCE_ROTATION_Z, rotation_z, "Z")
    _link(links, group_input, properties.SOCKET_SOURCE_SCALE_X, scale, "X")
    _link(links, group_input, properties.SOCKET_SOURCE_SCALE_Y, scale, "Y")
    _link(links, group_input, properties.SOCKET_SOURCE_SCALE_Z, scale, "Z")
    _link(links, to_origin, "Geometry", scale_transform, "Geometry")
    _link(links, scale, "Vector", scale_transform, "Scale")
    _link(links, scale_transform, "Geometry", rotate_z_transform, "Geometry")
    _link(links, rotation_z, "Vector", rotate_z_transform, "Rotation")
    _link(links, rotate_z_transform, "Geometry", rotate_y_transform, "Geometry")
    _link(links, rotation_y, "Vector", rotate_y_transform, "Rotation")
    _link(links, rotate_y_transform, "Geometry", rotate_x_transform, "Geometry")
    _link(links, rotation_x, "Vector", rotate_x_transform, "Rotation")
    _link(links, rotate_x_transform, "Geometry", from_origin, "Geometry")
    _link(links, source_node, "Location", restore_location, "Vector")
    links.new(position.outputs["Vector"], restore_location.inputs[1])
    _link(links, restore_location, "Vector", from_origin, "Translation")

    return from_origin, "Geometry"


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
