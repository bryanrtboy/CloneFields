"""Generate the bundled Clone Fields Geometry Nodes library inside Blender."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "geometry_nodes" / "assets" / "clone_fields_nodes.blend"


def _arguments_after_double_dash() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(_arguments_after_double_dash())

    sys.path.insert(0, str(REPO_ROOT.parent))
    from CloneFields import properties
    from CloneFields.geometry_nodes import create_grid_node_group

    for node_group in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(node_group)

    started = time.perf_counter()
    master = create_grid_node_group(use_bundled=False)
    build_seconds = time.perf_counter() - started
    expected_groups = {
        properties.GRID_NODE_GROUP_NAME,
        properties.SOURCE_TRANSFORM_NODE_GROUP_NAME,
        properties.GRID_DISTRIBUTION_NODE_GROUP_NAME,
        properties.BRICK_DISTRIBUTION_NODE_GROUP_NAME,
        properties.LINEAR_DISTRIBUTION_NODE_GROUP_NAME,
        properties.RADIAL_DISTRIBUTION_NODE_GROUP_NAME,
        properties.OBJECT_DISTRIBUTION_NODE_GROUP_NAME,
        properties.EFFECTOR_STACK_NODE_GROUP_NAME,
    }
    built_groups = {node_group.name for node_group in bpy.data.node_groups}
    missing = expected_groups - built_groups
    if missing:
        raise RuntimeError(f"Node library is missing groups: {sorted(missing)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.data.libraries.write(str(args.output), {master}, fake_user=True)
    print(
        f"{args.output} "
        f"({len(master.nodes)} master nodes, {build_seconds:.3f}s build)"
    )


if __name__ == "__main__":
    main()
