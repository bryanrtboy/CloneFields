"""Source hierarchy, visibility, and recursion helpers for cloners."""

from __future__ import annotations

import bpy
import uuid

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

    if source is not None:
        _parent_source_to_cloner(cloner, source)
        source[properties.PROP_MANAGED_SOURCE] = True
        source[properties.PROP_SOURCE_OWNER] = cloner.name

    _configure_modifier_for_source(modifier)
    _sync_source_collection(cloner, modifier)
    sync_cloner_source_visibility(cloner)
    return True


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
    _ensure_unique_cloner_identities()
    for obj in bpy.data.objects:
        if modifier_inputs.is_cloner_object(obj):
            sync_cloner_source_visibility(obj)


def sync_cloner_source_visibility(cloner: bpy.types.Object) -> None:
    modifier = modifier_inputs.get_cloner_modifier(cloner)
    if modifier is None:
        return

    _sync_source_collection(cloner, modifier)
    sources = _source_children(cloner)
    if not sources:
        return

    should_hide_source = modifier.show_viewport
    for source in sources:
        source.hide_set(should_hide_source)
        source.hide_render = should_hide_source


def _parent_source_to_cloner(
    cloner: bpy.types.Object,
    source: bpy.types.Object,
) -> None:
    if source.parent == cloner:
        return

    matrix_world = source.matrix_world.copy()
    source.parent = cloner
    source.matrix_world = matrix_world


def _release_source(cloner: bpy.types.Object, source: bpy.types.Object) -> None:
    if source.get(properties.PROP_SOURCE_OWNER) != cloner.name:
        return

    source.hide_set(False)
    source.hide_render = False
    source.pop(properties.PROP_MANAGED_SOURCE, None)
    source.pop(properties.PROP_SOURCE_OWNER, None)

    if source.parent == cloner:
        matrix_world = source.matrix_world.copy()
        source.parent = None
        source.matrix_world = matrix_world


def _sync_source_collection(
    cloner: bpy.types.Object,
    modifier: bpy.types.NodesModifier,
) -> None:
    _ensure_sources_for_duplicate(cloner, modifier)
    collection = _source_collection_for_cloner(cloner)
    sources = _source_children(cloner)
    changed = False

    for obj in list(collection.objects):
        if obj not in sources:
            collection.objects.unlink(obj)
            changed = True

    for source in sources:
        if source.name not in collection.objects:
            collection.objects.link(source)
            changed = True
        source[properties.PROP_MANAGED_SOURCE] = True
        source[properties.PROP_SOURCE_OWNER] = cloner.name

    source_count = max(1, len(sources))
    current_source = modifier_inputs.get_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_OBJECT,
    )
    current_collection = modifier_inputs.get_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_COLLECTION,
    )
    current_source_count = modifier_inputs.get_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_COUNT,
    )
    first_source = sources[0] if sources else None
    changed = changed or current_source != first_source
    changed = changed or current_collection != collection
    changed = changed or current_source_count != source_count

    modifier_inputs.set_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_OBJECT,
        first_source,
    )
    modifier_inputs.set_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_COLLECTION,
        collection,
    )
    modifier_inputs.set_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_COUNT,
        source_count,
    )
    if changed:
        _tag_cloner_for_source_update(cloner, modifier)


def _ensure_sources_for_duplicate(
    cloner: bpy.types.Object,
    modifier: bpy.types.NodesModifier,
) -> None:
    if _source_children(cloner):
        return

    inherited_collection = modifier_inputs.get_modifier_input(
        modifier,
        properties.SOCKET_SOURCE_COLLECTION,
    )
    if inherited_collection is None:
        name = cloner.get(properties.PROP_SOURCE_COLLECTION)
        inherited_collection = bpy.data.collections.get(name) if name else None
    if inherited_collection is None:
        return

    source_candidates = [
        obj
        for obj in inherited_collection.objects
        if obj.type in {"MESH", "CURVE", "SURFACE", "FONT", "EMPTY"}
        and not modifier_inputs.is_cloner_object(obj)
    ]
    if not source_candidates:
        return

    for source in source_candidates:
        duplicate = source.copy()
        if source.data is not None:
            duplicate.data = source.data.copy()
        duplicate.animation_data_clear()
        duplicate.name = source.name
        matrix_world = source.matrix_world.copy()
        _link_object_with_cloner(duplicate, cloner)
        duplicate.parent = cloner
        duplicate.matrix_world = matrix_world
        duplicate.hide_set(True)
        duplicate.hide_render = True
        duplicate[properties.PROP_MANAGED_SOURCE] = True
        duplicate[properties.PROP_SOURCE_OWNER] = cloner.name


def _link_object_with_cloner(
    duplicate: bpy.types.Object,
    cloner: bpy.types.Object,
) -> None:
    collections = cloner.users_collection
    if collections:
        collections[0].objects.link(duplicate)
    else:
        bpy.context.collection.objects.link(duplicate)


def _tag_cloner_for_source_update(
    cloner: bpy.types.Object,
    modifier: bpy.types.NodesModifier,
) -> None:
    cloner.update_tag()
    if modifier.node_group is not None:
        modifier.node_group.update_tag()


def _source_children(cloner: bpy.types.Object) -> list[bpy.types.Object]:
    return [
        child
        for child in cloner.children
        if child.type in {"MESH", "CURVE", "SURFACE", "FONT", "EMPTY"}
        and not modifier_inputs.is_cloner_object(child)
    ]


def _source_collection_for_cloner(cloner: bpy.types.Object) -> bpy.types.Collection:
    cloner_id = _ensure_cloner_id(cloner)
    name = cloner.get(properties.PROP_SOURCE_COLLECTION)
    collection = bpy.data.collections.get(name) if name else None
    if collection is not None:
        owner_id = collection.get(properties.PROP_SOURCE_COLLECTION_OWNER_ID)
        if owner_id is None:
            if _collection_referenced_by_other_cloner(collection, cloner):
                collection = None
            else:
                collection[properties.PROP_SOURCE_COLLECTION_OWNER_ID] = cloner_id
        elif owner_id != cloner_id:
            collection = None

    if collection is None:
        collection = bpy.data.collections.new(f"{cloner.name} Sources")
        collection[properties.PROP_SOURCE_COLLECTION_OWNER_ID] = cloner_id
        cloner[properties.PROP_SOURCE_COLLECTION] = collection.name
    return collection


def _ensure_unique_cloner_identities() -> None:
    seen_ids = set()
    cloners = sorted(
        (obj for obj in bpy.data.objects if modifier_inputs.is_cloner_object(obj)),
        key=lambda obj: obj.name,
    )
    for cloner in cloners:
        cloner_id = cloner.get(properties.PROP_CLONER_ID)
        if not cloner_id or cloner_id in seen_ids:
            cloner[properties.PROP_CLONER_ID] = uuid.uuid4().hex
            cloner.pop(properties.PROP_SOURCE_COLLECTION, None)
        seen_ids.add(cloner[properties.PROP_CLONER_ID])


def _ensure_cloner_id(cloner: bpy.types.Object) -> str:
    cloner_id = cloner.get(properties.PROP_CLONER_ID)
    if not cloner_id:
        cloner_id = uuid.uuid4().hex
        cloner[properties.PROP_CLONER_ID] = cloner_id
    return cloner_id


def _collection_referenced_by_other_cloner(
    collection: bpy.types.Collection,
    cloner: bpy.types.Object,
) -> bool:
    for obj in bpy.data.objects:
        if obj == cloner or not modifier_inputs.is_cloner_object(obj):
            continue
        modifier = modifier_inputs.get_cloner_modifier(obj)
        if modifier is None:
            continue
        current_collection = modifier_inputs.get_modifier_input(
            modifier,
            properties.SOCKET_SOURCE_COLLECTION,
        )
        if current_collection == collection:
            return True
        if obj.get(properties.PROP_SOURCE_COLLECTION) == collection.name:
            return True
    return False


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
    for socket_name in modifier_inputs.GRID_SOCKET_NAMES:
        if socket_name in {
            properties.SOCKET_SOURCE_OBJECT,
            properties.SOCKET_SOURCE_COLLECTION,
        }:
            continue
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
