"""Interactive viewport gizmos for Clone Fields cloners."""

from __future__ import annotations

import bpy
from mathutils import Matrix, Vector

from . import modifier_inputs
from .viewport_guides import source_bounds_half_extents


AXIS_TO_INDEX = {
    "X": 0,
    "Y": 1,
    "Z": 2,
}


class CLONE_FIELDS_GGT_cloner_handles(bpy.types.GizmoGroup):
    bl_idname = "CLONE_FIELDS_GGT_cloner_handles"
    bl_label = "Clone Fields Handles"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT"}

    @classmethod
    def poll(cls, context) -> bool:
        return modifier_inputs.is_cloner_object(context.object)

    def setup(self, context) -> None:
        self.axis_gizmos = {
            axis: self._new_axis_gizmo(axis)
            for axis in ("X", "Y", "Z")
        }
        self.radius_gizmo = self._new_axis_gizmo("R")

    def refresh(self, context) -> None:
        self._configure_gizmos(context)

    def draw_prepare(self, context) -> None:
        self._configure_gizmos(context)

    def _new_axis_gizmo(self, axis: str):
        gizmo = self.gizmos.new("GIZMO_GT_arrow_3d")
        gizmo.use_draw_modal = True
        gizmo.use_draw_value = False
        gizmo.color = (1.0, 0.82, 0.05)
        gizmo.alpha = 0.5
        gizmo.color_highlight = (1.0, 0.95, 0.25)
        gizmo.alpha_highlight = 0.95
        gizmo.scale_basis = 1.15
        if hasattr(gizmo, "line_width"):
            gizmo.line_width = 5.0
        gizmo.target_set_handler(
            "offset",
            get=lambda axis=axis: self._get_handle_offset(axis),
            set=lambda value, axis=axis: self._set_handle_offset(axis, value),
            range=lambda axis=axis: self._get_handle_range(axis),
        )
        return gizmo

    def _configure_gizmos(self, context) -> None:
        cloner = context.object
        if not modifier_inputs.is_cloner_object(cloner):
            return

        settings = cloner.clone_fields_cloner
        is_grid = settings.distribution_mode == "GRID"
        is_radial = settings.distribution_mode == "RADIAL"
        for axis, gizmo in self.axis_gizmos.items():
            gizmo.hide = not is_grid
            if is_grid:
                gizmo.matrix_basis = _axis_matrix(cloner, axis)
        self.radius_gizmo.hide = not is_radial
        if is_radial:
            self.radius_gizmo.matrix_basis = _axis_matrix(cloner, _radial_handle_axis(settings))

    def _get_handle_offset(self, axis: str) -> float:
        cloner = bpy.context.object
        if not modifier_inputs.is_cloner_object(cloner):
            return 0.0

        settings = cloner.clone_fields_cloner
        if axis == "R":
            return settings.radial_radius + _radial_source_radius(cloner)

        count = getattr(settings, f"count_{axis.lower()}")
        spacing = getattr(settings, f"spacing_{axis.lower()}")
        source_half = getattr(source_bounds_half_extents(cloner), axis.lower())
        if settings.spacing_mode == "ENDPOINT":
            return max(0.0, spacing * 0.5) + source_half
        return max(0.0, (count - 1) * spacing * 0.5) + source_half

    def _set_handle_offset(self, axis: str, value: float) -> None:
        cloner = bpy.context.object
        if not modifier_inputs.is_cloner_object(cloner):
            return

        apply_handle_offset(cloner, axis, value)
        _refresh_cloner(cloner)

    def _get_handle_range(self, axis: str) -> tuple[float, float]:
        return (0.0, 100000.0)


def _axis_matrix(cloner: bpy.types.Object, axis: str) -> Matrix:
    basis = cloner.matrix_world.to_3x3().normalized()
    if axis == "X":
        rotation = basis @ Matrix.Rotation(1.5707963267948966, 3, "Y")
    elif axis == "Y":
        rotation = basis @ Matrix.Rotation(-1.5707963267948966, 3, "X")
    else:
        rotation = basis
    matrix = rotation.to_4x4()
    matrix.translation = cloner.matrix_world.translation
    return matrix


def _radial_handle_axis(settings) -> str:
    if settings.radial_axis == "X":
        return "Y"
    return "X"


def _radial_source_radius(cloner: bpy.types.Object) -> float:
    source_half = source_bounds_half_extents(cloner)
    return max(source_half.x, source_half.y, source_half.z)


def apply_handle_offset(cloner: bpy.types.Object, axis: str, value: float) -> None:
    settings = cloner.clone_fields_cloner
    value = max(0.0, value)
    if axis == "R":
        settings.radial_radius = max(0.0, value - _radial_source_radius(cloner))
        return

    count = getattr(settings, f"count_{axis.lower()}")
    source_half = getattr(source_bounds_half_extents(cloner), axis.lower())
    point_half_extent = max(0.0, value - source_half)
    if settings.spacing_mode == "ENDPOINT":
        setattr(settings, f"spacing_{axis.lower()}", point_half_extent * 2.0)
        return
    if count > 1:
        setattr(settings, f"spacing_{axis.lower()}", (point_half_extent * 2.0) / (count - 1))
    else:
        setattr(settings, f"spacing_{axis.lower()}", point_half_extent * 2.0)


def _refresh_cloner(cloner: bpy.types.Object) -> None:
    modifier = modifier_inputs.get_cloner_modifier(cloner)
    cloner.update_tag()
    if modifier is not None and modifier.node_group is not None:
        modifier.node_group.update_tag()
    if bpy.context.view_layer is not None:
        bpy.context.view_layer.update()


classes = (CLONE_FIELDS_GGT_cloner_handles,)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
