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
    gpu.state.line_width_set(2.0)
    for cloner in selected_cloners:
        settings = cloner.clone_fields_cloner
        if settings.distribution_mode == "GRID":
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


def _draw_lines(batch_for_shader, shader, lines, color) -> None:
    if not lines:
        return
    batch = batch_for_shader(shader, "LINES", {"pos": lines})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _grid_guide_lines(cloner: bpy.types.Object, settings) -> list[tuple[float, float, float]]:
    source_half = source_bounds_half_extents(cloner)
    half_x = _grid_axis_half_extent(settings.count_x, settings.spacing_x, settings) + source_half.x
    half_y = _grid_axis_half_extent(settings.count_y, settings.spacing_y, settings) + source_half.y
    half_z = _grid_axis_half_extent(settings.count_z, settings.spacing_z, settings) + source_half.z
    matrix = cloner.matrix_world

    corners = [
        Vector((x, y, z))
        for x in (-half_x, half_x)
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

    dot_radius = max(0.05, max(half_x, half_y, half_z) * 0.025)
    for local in (
        Vector((half_x, 0.0, 0.0)),
        Vector((0.0, half_y, 0.0)),
        Vector((0.0, 0.0, half_z)),
        Vector((half_x, half_y, half_z)),
    ):
        lines.extend(_sphere_lines(matrix, local, dot_radius))
    return lines


def _grid_axis_half_extent(count: int, spacing: float, settings) -> float:
    if settings.spacing_mode == "ENDPOINT":
        return max(0.0, spacing * 0.5)
    return max(0.0, (count - 1) * spacing * 0.5)


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
