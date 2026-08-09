"""Shared names for Clone Fields data and node group sockets."""

ADDON_NAME = "Clone Fields"

CLONER_OBJECT_NAME = "Cloner"
CLONER_MESH_NAME = "Clone Fields Output"
CLONER_MODIFIER_NAME = "Cloner"
GRID_NODE_GROUP_NAME = ".Clone Fields Grid Cloner"

PROP_CLONER_TYPE = "clone_fields_type"
PROP_CLONER_MODE = "clone_fields_mode"
PROP_MANAGED_SOURCE = "clone_fields_managed_source"
PROP_SOURCE_OWNER = "clone_fields_source_owner"
PROP_CLONER_COLLECTION = "clone_fields_cloner_collection"
PROP_OUTPUT_COLLECTION = "clone_fields_output_collection"
PROP_SOURCE_COLLECTION = "clone_fields_source_collection"

SOCKET_GEOMETRY = "Geometry"
SOCKET_SOURCE_OBJECT = "Source Object"
SOCKET_COUNT_X = "Count X"
SOCKET_COUNT_Y = "Count Y"
SOCKET_COUNT_Z = "Count Z"
SOCKET_SPACING_X = "Spacing X"
SOCKET_SPACING_Y = "Spacing Y"
SOCKET_SPACING_Z = "Spacing Z"

GRID_INPUT_DEFAULTS = {
    SOCKET_COUNT_X: 3,
    SOCKET_COUNT_Y: 1,
    SOCKET_COUNT_Z: 1,
    SOCKET_SPACING_X: 2.0,
    SOCKET_SPACING_Y: 2.0,
    SOCKET_SPACING_Z: 2.0,
}
