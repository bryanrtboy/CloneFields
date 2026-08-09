"""Clone Fields Blender extension."""

from __future__ import annotations

import importlib

from . import (
    cloner,
    gizmos,
    geometry_nodes,
    menus,
    modifier_inputs,
    object_settings,
    operators,
    panels,
    properties,
    source_management,
    viewport_guides,
)
from .geometry_nodes import grid


modules = (
    properties,
    modifier_inputs,
    source_management,
    object_settings,
    grid,
    geometry_nodes,
    cloner,
    gizmos,
    operators,
    panels,
    menus,
    viewport_guides,
)


def register() -> None:
    for module in modules:
        importlib.reload(module)
    object_settings.register()
    operators.register()
    panels.register()
    menus.register()
    gizmos.register()
    source_management.register()
    viewport_guides.register()


def unregister() -> None:
    viewport_guides.unregister()
    source_management.unregister()
    gizmos.unregister()
    menus.unregister()
    panels.unregister()
    operators.unregister()
    object_settings.unregister()
