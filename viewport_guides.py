"""Viewport guides for selected Clone Fields cloners."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from . import effectors, modifier_inputs


_DRAW_HANDLE = None


def register() -> None:
    global _DRAW_HANDLE
    unregister()
    _DRAW_HANDLE = bpy.types.SpaceView3D.draw_handler_add(
        _draw_viewport_guides,
        (),
        "WINDOW",
        "POST_VIEW",
    )


def unregister() -> None:
    global _DRAW_HANDLE
    if _DRAW_HANDLE is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_DRAW_HANDLE, "WINDOW")
        _DRAW_HANDLE = None


def _draw_viewport_guides() -> None:
    try:
        import gpu
        from gpu_extras.batch import batch_for_shader
    except Exception:
        return

    selected_objects = list(bpy.context.selected_objects)
    selected_cloners = [
        obj for obj in bpy.context.selected_objects if modifier_inputs.is_cloner_object(obj)
    ]
    effector_guides = _effector_guides_for_selection(selected_objects)
    if not selected_cloners and not effector_guides:
        return

    try:
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    except Exception:
        return

    gpu.state.blend_set("ALPHA")
    _draw_shader_previews(gpu, batch_for_shader)
    gpu.state.line_width_set(2.0)
    for cloner in selected_cloners:
        settings = cloner.clone_fields_cloner
        if settings.distribution_mode in {"GRID", "BRICK"}:
            lines = _grid_guide_lines(cloner, settings)
            _draw_lines(batch_for_shader, shader, lines, (1.0, 0.85, 0.1, 0.9))
        elif settings.distribution_mode == "RADIAL":
            lines = _radial_guide_lines(cloner, settings)
            _draw_lines(batch_for_shader, shader, lines, (1.0, 0.85, 0.1, 0.9))
        for index, slot in enumerate(effectors.EFFECTOR_SLOT_PROPERTIES):
            _draw_effector_guides(
                batch_for_shader,
                shader,
                settings,
                slot,
                selected=index == settings.selected_effector_slot,
            )
    for settings in effector_guides:
        for index, slot in enumerate(effectors.EFFECTOR_SLOT_PROPERTIES):
            _draw_effector_guides(
                batch_for_shader,
                shader,
                settings,
                slot,
                selected=index == settings.selected_effector_slot,
            )
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set("NONE")


def _draw_shader_previews(gpu, batch_for_shader) -> None:
    try:
        image_shader = gpu.shader.from_builtin("IMAGE_SCENE_LINEAR_TO_REC709_SRGB")
    except Exception:
        image_shader = gpu.shader.from_builtin("IMAGE")

    visible = set(bpy.context.visible_objects)
    drawn = set()
    for cloner in bpy.data.objects:
        if cloner not in visible or not modifier_inputs.is_cloner_object(cloner):
            continue
        settings = cloner.clone_fields_cloner
        for slot in effectors.EFFECTOR_SLOT_PROPERTIES:
            effector = getattr(settings, slot["object"])
            if effector in drawn or effector not in visible:
                continue
            effector_settings = getattr(effector, "clone_fields_effector", None)
            if (
                effector_settings is None
                or effector_settings.type != effectors.EFFECTOR_TYPE_SHADER
                or effector_settings.shader_image is None
            ):
                continue
            try:
                texture = gpu.texture.from_image(effector_settings.shader_image)
            except Exception:
                continue
            _draw_tiled_image(
                gpu,
                batch_for_shader,
                image_shader,
                texture,
                effector.matrix_world,
                effector_settings.shader_width,
                effector_settings.shader_height,
                effector_settings.shader_tiles_x,
                effector_settings.shader_tiles_y,
            )
            drawn.add(effector)


def _draw_tiled_image(
    gpu,
    batch_for_shader,
    shader,
    texture,
    matrix,
    width: float,
    height: float,
    tiles_x: int,
    tiles_y: int,
) -> None:
    tiles_x = max(1, tiles_x)
    tiles_y = max(1, tiles_y)
    tile_width = width / tiles_x
    tile_height = height / tiles_y
    indices = ((0, 1, 2), (2, 3, 0))
    with gpu.matrix.push_pop():
        gpu.matrix.multiply_matrix(matrix)
        shader.bind()
        shader.uniform_sampler("image", texture)
        for tile_y in range(tiles_y):
            y0 = -height * 0.5 + tile_y * tile_height
            y1 = y0 + tile_height
            for tile_x in range(tiles_x):
                x0 = -width * 0.5 + tile_x * tile_width
                x1 = x0 + tile_width
                batch = batch_for_shader(
                    shader,
                    "TRIS",
                    {
                        "pos": ((x0, y0), (x1, y0), (x1, y1), (x0, y1)),
                        "texCoord": ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
                    },
                    indices=indices,
                )
                batch.draw(shader)


def _draw_lines(batch_for_shader, shader, lines, color) -> None:
    if not lines:
        return
    batch = batch_for_shader(shader, "LINES", {"pos": lines})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _grid_guide_lines(cloner: bpy.types.Object, settings) -> list[tuple[float, float, float]]:
    source_half = source_bounds_half_extents(cloner)
    point_half_x = _grid_axis_half_extent(settings.count_x, settings.spacing_x, settings)
    brick_min_x, brick_max_x = _brick_x_offset_range(settings)
    min_x = -point_half_x + brick_min_x - source_half.x
    max_x = point_half_x + brick_max_x + source_half.x
    half_y = _grid_axis_half_extent(settings.count_y, settings.spacing_y, settings) + source_half.y
    half_z = _grid_axis_half_extent(settings.count_z, settings.spacing_z, settings) + source_half.z
    matrix = cloner.matrix_world

    corners = [
        Vector((x, y, z))
        for x in (min_x, max_x)
        for y in (-half_y, half_y)
        for z in (-half_z, half_z)
    ]
    world = [matrix @ corner for corner in corners]
    lines = []
    for first, second in (
        (0, 1),
        (0, 2),
        (0, 4),
        (3, 1),
        (3, 2),
        (3, 7),
        (5, 1),
        (5, 4),
        (5, 7),
        (6, 2),
        (6, 4),
        (6, 7),
    ):
        lines.extend((tuple(world[first]), tuple(world[second])))

    dot_radius = max(0.05, max(abs(min_x), abs(max_x), half_y, half_z) * 0.025)
    for local in (
        Vector((max_x, 0.0, 0.0)),
        Vector((0.0, half_y, 0.0)),
        Vector((0.0, 0.0, half_z)),
        Vector((max_x, half_y, half_z)),
    ):
        lines.extend(_sphere_lines(matrix, local, dot_radius))
    return lines


def _grid_axis_half_extent(count: int, spacing: float, settings) -> float:
    if settings.spacing_mode == "ENDPOINT":
        return max(0.0, spacing * 0.5)
    return max(0.0, (count - 1) * spacing * 0.5)


def _grid_axis_step_spacing(count: int, spacing: float, settings) -> float:
    if settings.spacing_mode == "ENDPOINT":
        return spacing / max(1, count - 1)
    return spacing


def _brick_x_offset_range(settings) -> tuple[float, float]:
    if settings.distribution_mode != "BRICK":
        return 0.0, 0.0
    step_x = _grid_axis_step_spacing(settings.count_x, settings.spacing_x, settings)
    row_offset = settings.brick_row_offset * step_x if settings.count_y > 1 else 0.0
    layer_offset = settings.brick_layer_offset * step_x if settings.count_z > 1 else 0.0
    offsets = (0.0, row_offset, layer_offset, row_offset + layer_offset)
    return min(offsets), max(offsets)


def _radial_guide_lines(cloner: bpy.types.Object, settings) -> list[tuple[float, float, float]]:
    matrix = cloner.matrix_world
    source_half = source_bounds_half_extents(cloner)
    source_radius = max(source_half.x, source_half.y, source_half.z)
    radius = max(0.0, settings.radial_radius)
    outer_radius = radius + source_radius
    axis = settings.radial_axis
    lines = _circle_lines(matrix, Vector((0.0, 0.0, 0.0)), outer_radius, axis, segments=96)
    if axis == "X":
        dot = Vector((0.0, outer_radius, 0.0))
    elif axis == "Y":
        dot = Vector((outer_radius, 0.0, 0.0))
    else:
        dot = Vector((outer_radius, 0.0, 0.0))
    lines.extend(_sphere_lines(matrix, dot, max(0.05, outer_radius * 0.025)))
    return lines


def _effector_guides_for_selection(selected_objects) -> list:
    selected_effectors = {
        obj
        for obj in selected_objects
        if effectors.is_effector_object(obj)
    }
    if not selected_effectors:
        return []

    settings = []
    for cloner in bpy.data.objects:
        if not modifier_inputs.is_cloner_object(cloner):
            continue
        cloner_settings = cloner.clone_fields_cloner
        if any(
            getattr(cloner_settings, slot["object"]) in selected_effectors
            for slot in effectors.EFFECTOR_SLOT_PROPERTIES
        ):
            settings.append(cloner_settings)
    return settings


def _draw_effector_guides(batch_for_shader, shader, settings, slot, *, selected: bool) -> None:
    effector = getattr(settings, slot["object"])
    if effector is None:
        return

    effector_settings = getattr(effector, "clone_fields_effector", None)
    if (
        effector_settings is not None
        and effector_settings.shape == effectors.FIELD_SHAPE_NONE
    ):
        return
    outer_radius = max(
        0.0,
        effector_settings.radius if effector_settings is not None else getattr(settings, slot["radius"]),
    )
    falloff = (
        effector_settings.falloff
        if effector_settings is not None
        else getattr(settings, slot["falloff"])
    )
    inner_radius = outer_radius * min(1.0, max(0.0, falloff / 100.0))
    if (
        effector_settings is not None
        and effector_settings.shape == effectors.FIELD_SHAPE_CUBE
    ):
        outer_size = Vector(
            (effector_settings.box_x, effector_settings.box_y, effector_settings.box_z)
        )
        inner_size = outer_size * min(1.0, max(0.0, falloff / 100.0))
        outer = _box_lines(effector.matrix_world, outer_size * 0.5)
        inner = _box_lines(effector.matrix_world, inner_size * 0.5)
    elif (
        effector_settings is not None
        and effector_settings.shape == effectors.FIELD_SHAPE_CYLINDER
    ):
        outer_height = max(0.0, effector_settings.height)
        inner_height = outer_height * min(1.0, max(0.0, falloff / 100.0))
        outer = _cylinder_lines(effector.matrix_world, outer_radius, outer_height)
        inner = _cylinder_lines(effector.matrix_world, inner_radius, inner_height)
    elif (
        effector_settings is not None
        and effector_settings.shape == effectors.FIELD_SHAPE_LINEAR
    ):
        outer_length = max(0.0, effector_settings.length)
        inner_length = outer_length * min(1.0, max(0.0, falloff / 100.0))
        guide_size = max(outer_radius * 2.0, outer_length * 0.5, 0.1)
        outer = _linear_lines(effector.matrix_world, outer_length, guide_size)
        inner = _linear_lines(effector.matrix_world, inner_length, guide_size * 0.85)
    else:
        outer = _sphere_lines(effector.matrix_world, Vector((0.0, 0.0, 0.0)), outer_radius)
        inner = _sphere_lines(effector.matrix_world, Vector((0.0, 0.0, 0.0)), inner_radius)
    outer_color = (0.35, 0.75, 1.0, 0.95) if selected else (0.35, 0.75, 1.0, 0.35)
    inner_color = (1.0, 0.55, 0.15, 0.9) if selected else (1.0, 0.55, 0.15, 0.3)
    _draw_lines(batch_for_shader, shader, outer, outer_color)
    _draw_lines(batch_for_shader, shader, inner, inner_color)


def source_bounds_half_extents(cloner: bpy.types.Object) -> Vector:
    local_points = []
    cloner_inverse = cloner.matrix_world.inverted()
    for child in cloner.children:
        if modifier_inputs.is_cloner_object(child):
            continue
        if not hasattr(child, "bound_box"):
            continue
        for corner in child.bound_box:
            local_points.append(cloner_inverse @ (child.matrix_world @ Vector(corner)))

    if not local_points:
        return Vector((0.0, 0.0, 0.0))

    min_x = min(point.x for point in local_points)
    max_x = max(point.x for point in local_points)
    min_y = min(point.y for point in local_points)
    max_y = max(point.y for point in local_points)
    min_z = min(point.z for point in local_points)
    max_z = max(point.z for point in local_points)
    return Vector(
        (
            max(abs(min_x), abs(max_x)),
            max(abs(min_y), abs(max_y)),
            max(abs(min_z), abs(max_z)),
        )
    )


def _sphere_lines(
    matrix,
    center: Vector,
    radius: float,
) -> list[tuple[float, float, float]]:
    lines = []
    for axis in ("X", "Y", "Z"):
        lines.extend(_circle_lines(matrix, center, radius, axis))
    return lines


def _box_lines(matrix, half_extent: Vector) -> list[tuple[float, float, float]]:
    if min(half_extent) <= 0.0:
        return []

    corners = [
        Vector((x, y, z))
        for x in (-half_extent.x, half_extent.x)
        for y in (-half_extent.y, half_extent.y)
        for z in (-half_extent.z, half_extent.z)
    ]
    world = [matrix @ corner for corner in corners]
    lines = []
    for first, second in (
        (0, 1),
        (0, 2),
        (0, 4),
        (3, 1),
        (3, 2),
        (3, 7),
        (5, 1),
        (5, 4),
        (5, 7),
        (6, 2),
        (6, 4),
        (6, 7),
    ):
        lines.extend((tuple(world[first]), tuple(world[second])))
    return lines


def _cylinder_lines(
    matrix,
    radius: float,
    height: float,
    segments: int = 48,
) -> list[tuple[float, float, float]]:
    if radius <= 0.0 or height <= 0.0:
        return []

    half_height = height * 0.5
    top_center = Vector((0.0, 0.0, half_height))
    bottom_center = Vector((0.0, 0.0, -half_height))
    lines = []
    lines.extend(_circle_lines(matrix, top_center, radius, "Z", segments=segments))
    lines.extend(_circle_lines(matrix, bottom_center, radius, "Z", segments=segments))

    for index in range(segments):
        if index % 6 != 0:
            continue
        angle = (math.tau * index) / segments
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        top = matrix @ Vector((x, y, half_height))
        bottom = matrix @ Vector((x, y, -half_height))
        lines.extend((tuple(top), tuple(bottom)))
    return lines


def _linear_lines(
    matrix,
    length: float,
    plane_size: float,
) -> list[tuple[float, float, float]]:
    if length <= 0.0 or plane_size <= 0.0:
        return []

    half_length = length * 0.5
    half_size = plane_size * 0.5
    lines = []
    positive_plane = [
        Vector((half_length, y, z))
        for y, z in (
            (-half_size, -half_size),
            (half_size, -half_size),
            (half_size, half_size),
            (-half_size, half_size),
        )
    ]
    negative_plane = [Vector((-half_length, point.y, point.z)) for point in positive_plane]
    for ring in (positive_plane, negative_plane):
        world = [matrix @ point for point in ring]
        for index, point in enumerate(world):
            lines.extend((tuple(point), tuple(world[(index + 1) % len(world)])))
        lines.extend((tuple(world[0]), tuple(world[2])))
        lines.extend((tuple(world[1]), tuple(world[3])))

    axis_positive = matrix @ Vector((half_length, 0.0, 0.0))
    axis_negative = matrix @ Vector((-half_length, 0.0, 0.0))
    lines.extend((tuple(axis_positive), tuple(axis_negative)))
    return lines


def _circle_lines(
    matrix,
    center: Vector,
    radius: float,
    axis: str,
    segments: int = 24,
) -> list[tuple[float, float, float]]:
    if radius <= 0.0:
        return []

    points = []
    for index in range(segments):
        angle = (math.tau * index) / segments
        cosine = math.cos(angle) * radius
        sine = math.sin(angle) * radius
        if axis == "X":
            point = center + Vector((0.0, cosine, sine))
        elif axis == "Y":
            point = center + Vector((cosine, 0.0, sine))
        else:
            point = center + Vector((cosine, sine, 0.0))
        points.append(matrix @ point)

    lines = []
    for index, point in enumerate(points):
        lines.extend((tuple(point), tuple(points[(index + 1) % len(points)])))
    return lines
