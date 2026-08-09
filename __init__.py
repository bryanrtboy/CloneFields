"""Clone Fields Blender extension."""

from __future__ import annotations

import importlib

from . import (
    cloner,
    geometry_nodes,
    menus,
    modifier_inputs,
    object_settings,
    operators,
    properties,
    source_management,
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
    operators,
    menus,
)


def register() -> None:
    for module in modules:
        importlib.reload(module)
    object_settings.register()
    operators.register()
    menus.register()
    source_management.register()


def unregister() -> None:
    source_management.unregister()
    menus.unregister()
    operators.unregister()
    object_settings.unregister()
