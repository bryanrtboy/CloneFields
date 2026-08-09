"""Source hierarchy, visibility, and recursion helpers for cloners."""

from __future__ import annotations

import bpy

from . import modifier_inputs, properties


HANDLER_NAME = "_clone_fields_sync_source_visibility"


def assign_source(
    cloner: bpy.types.Object,
    source: bpy.types.Object | None,
) -> bool:
    """Attach a source object under a cloner and sync its visibility."""

    modifier = modifier_inputs.get_cloner_modifier(cloner)
    if modifier is None:
        return False

    if source is not None and (
        modifier_inputs.is_cloner_object(source) or would_create_cycle(cloner, source)
    ):
        return False

    old_source = modifier_inputs.get_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_OBJECT,
    )
    if old_source is not None and old_source != source:
        _release_source(cloner, old_source)

    if source is not None:
        _parent_source_to_cloner(cloner, source)
        source[properties.PROP_MANAGED_SOURCE] = True
        source[properties.PROP_SOURCE_OWNER] = cloner.name

    _configure_modifier_for_source(modifier)
    modifier_inputs.set_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_OBJECT,
        source,
    )
    sync_cloner_source_visibility(cloner)
    return True


def setup_cloner_collections(
    context: bpy.types.Context,
    cloner: bpy.types.Object,
) -> None:
    parent_collection = context.collection
    cloner_collection = bpy.data.collections.new(cloner.name)
    output_collection = bpy.data.collections.new(f"{cloner.name} Output")
    source_collection = bpy.data.collections.new(f"{cloner.name} Sources")

    parent_collection.children.link(cloner_collection)
    cloner_collection.children.link(output_collection)
    cloner_collection.children.link(source_collection)
    _move_object_to_collection(cloner, output_collection)

    cloner[properties.PROP_CLONER_COLLECTION] = cloner_collection.name
    cloner[properties.PROP_OUTPUT_COLLECTION] = output_collection.name
    cloner[properties.PROP_SOURCE_COLLECTION] = source_collection.name


def would_create_cycle(
    cloner: bpy.types.Object,
    source: bpy.types.Object | None,
) -> bool:
    if source is None:
        return False
    if source == cloner:
        return True
    if not modifier_inputs.is_cloner_object(source):
        return False

    stack = [source]
    visited = set()
    while stack:
        current = stack.pop()
        pointer = current.as_pointer()
        if pointer in visited:
            continue
        visited.add(pointer)

        if current == cloner:
            return True

        modifier = modifier_inputs.get_cloner_modifier(current)
        if modifier is None:
            continue

        nested_source = modifier_inputs.get_modifier_input(
            modifier,
            properties.SOCKET_SOURCE_OBJECT,
        )
        if nested_source is not None:
            stack.append(nested_source)

    return False


def sync_all_source_visibility(*_args) -> None:
    for obj in bpy.data.objects:
        if modifier_inputs.is_cloner_object(obj):
            sync_cloner_source_visibility(obj)


def sync_cloner_source_visibility(cloner: bpy.types.Object) -> None:
    modifier = modifier_inputs.get_cloner_modifier(cloner)
    if modifier is None:
        return

    source = modifier_inputs.get_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_OBJECT,
    )
    if source is None:
        return

    should_hide_source = modifier.show_viewport
    source.hide_set(should_hide_source)
    source.hide_render = should_hide_source


def _parent_source_to_cloner(
    cloner: bpy.types.Object,
    source: bpy.types.Object,
) -> None:
    source_collection = _source_collection_for_cloner(cloner)
    if source_collection is None:
        return

    if modifier_inputs.is_cloner_object(source):
        cloner_collection = _cloner_collection_for_cloner(source)
        if cloner_collection is not None:
            _move_collection_to_parent(cloner_collection, source_collection)
            return

    _move_object_to_collection(source, source_collection)


def _release_source(cloner: bpy.types.Object, source: bpy.types.Object) -> None:
    if source.get(properties.PROP_SOURCE_OWNER) != cloner.name:
        return

    source.hide_set(False)
    source.hide_render = False
    source.pop(properties.PROP_MANAGED_SOURCE, None)
    source.pop(properties.PROP_SOURCE_OWNER, None)

    if modifier_inputs.is_cloner_object(source):
        cloner_collection = _cloner_collection_for_cloner(source)
        if cloner_collection is not None:
            _move_collection_to_parent(cloner_collection, bpy.context.scene.collection)
        return

    _move_object_to_collection(source, bpy.context.scene.collection)


def _source_collection_for_cloner(
    cloner: bpy.types.Object,
) -> bpy.types.Collection | None:
    name = cloner.get(properties.PROP_SOURCE_COLLECTION)
    if not name:
        return None
    return bpy.data.collections.get(name)


def _cloner_collection_for_cloner(
    cloner: bpy.types.Object,
) -> bpy.types.Collection | None:
    name = cloner.get(properties.PROP_CLONER_COLLECTION)
    if not name:
        return None
    return bpy.data.collections.get(name)


def _move_object_to_collection(
    obj: bpy.types.Object,
    target_collection: bpy.types.Collection,
) -> None:
    if obj.name not in target_collection.objects:
        target_collection.objects.link(obj)

    for collection in list(obj.users_collection):
        if collection != target_collection and obj.name in collection.objects:
            collection.objects.unlink(obj)


def _move_collection_to_parent(
    child: bpy.types.Collection,
    target_parent: bpy.types.Collection,
) -> None:
    if child.name not in target_parent.children:
        target_parent.children.link(child)

    for parent in _collection_parents(child):
        if parent != target_parent and child.name in parent.children:
            parent.children.unlink(child)


def _collection_parents(child: bpy.types.Collection) -> list[bpy.types.Collection]:
    parents = []
    scene_collection = bpy.context.scene.collection
    if child.name in scene_collection.children:
        parents.append(scene_collection)

    for collection in bpy.data.collections:
        if child.name in collection.children:
            parents.append(collection)

    return parents


def _configure_modifier_for_source(modifier: bpy.types.NodesModifier) -> None:
    values = _current_grid_values(modifier)

    from .geometry_nodes import create_grid_node_group

    old_group = modifier.node_group
    modifier.node_group = create_grid_node_group()
    _remove_unused_node_group(old_group)

    for socket_name, value in values.items():
        modifier_inputs.set_modifier_input(modifier, socket_name, value)


def _current_grid_values(modifier: bpy.types.NodesModifier) -> dict:
    values = {}
    for socket_name in (
        properties.SOCKET_COUNT_X,
        properties.SOCKET_COUNT_Y,
        properties.SOCKET_COUNT_Z,
        properties.SOCKET_SPACING_X,
        properties.SOCKET_SPACING_Y,
        properties.SOCKET_SPACING_Z,
    ):
        value = modifier_inputs.get_modifier_input(modifier, socket_name)
        values[socket_name] = (
            value
            if value is not None
            else properties.GRID_INPUT_DEFAULTS[socket_name]
        )
    return values


def _remove_unused_node_group(node_group: bpy.types.GeometryNodeTree | None) -> None:
    if node_group is not None and node_group.users == 0:
        bpy.data.node_groups.remove(node_group)


def register() -> None:
    unregister()
    sync_all_source_visibility.__name__ = HANDLER_NAME
    bpy.app.handlers.depsgraph_update_post.append(sync_all_source_visibility)


def unregister() -> None:
    handlers = bpy.app.handlers.depsgraph_update_post
    for handler in list(handlers):
        if getattr(handler, "__name__", "") == HANDLER_NAME:
            handlers.remove(handler)
