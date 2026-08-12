"""Measure first and repeated Cloner creation in a clean Blender process."""

from __future__ import annotations

from pathlib import Path
import sys
import time

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT.parent))

import CloneFields
from CloneFields import cloner, properties


def _create_source(name: str, offset: float) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name} Mesh")
    mesh.from_pydata(
        [
            (-0.5, -0.5, -0.5),
            (0.5, -0.5, -0.5),
            (0.5, 0.5, -0.5),
            (-0.5, 0.5, -0.5),
            (-0.5, -0.5, 0.5),
            (0.5, -0.5, 0.5),
            (0.5, 0.5, 0.5),
            (-0.5, 0.5, 0.5),
        ],
        [],
        [
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (4, 0, 3, 7),
        ],
    )
    source = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(source)
    source.location.x = offset
    return source


def _create_cloner(source: bpy.types.Object) -> bpy.types.Object:
    return cloner.create_grid_cloner(
        bpy.context,
        source_object=source,
        count_x=3,
        count_y=3,
        count_z=1,
        spacing_x=2.0,
        spacing_y=2.0,
        spacing_z=2.0,
    )


CloneFields.register()
elapsed = []
for index in range(2):
    source = _create_source(f"Benchmark Source {index + 1}", index * 4.0)
    started = time.perf_counter()
    created = _create_cloner(source)
    bpy.context.view_layer.update()
    elapsed.append(time.perf_counter() - started)

master = created.modifiers[properties.CLONER_MODIFIER_NAME].node_group
print(
    "CLONE_FIELDS_BENCHMARK "
    f"first={elapsed[0]:.4f}s second={elapsed[1]:.4f}s "
    f"master_nodes={len(master.nodes)} master_links={len(master.links)}"
)
