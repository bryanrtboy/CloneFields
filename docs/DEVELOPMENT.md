# Development

[Back to the quick start](../README.md)

### Architecture

Python owns installation, object relationships, UI, parameter synchronization,
viewport controls, and generation of the Geometry Nodes implementation.
Geometry Nodes owns the original Cloner's live geometry, instances,
distributions, alignment, and Effector evaluation. Curve Cloner uses a separate
Python evaluator in `curve_fields.py`, with native Curve datablocks and
Blender's own extrusion/bevel. Numeric raster sampling is in `curve_images.py`.

The Cloner modifier shares one master node group across all Cloners. The master
group is intentionally small and delegates work to hidden reusable groups:

```text
Source Collection
    -> Source Transform
    -> Grid / Linear / Radial / Object Distribution
    -> Distribution Switch
    -> Realize Output
```

Each distribution uses the shared `.Clone Fields Effector Stack` group. Internal
groups begin with `.` so they stay out of normal Blender menus while remaining
inspectable in the Geometry Node Editor.

The Python builder in `geometry_nodes/grid.py` is the source of truth. The file
`geometry_nodes/assets/clone_fields_nodes.blend` is generated build output used
to make the first Cloner fast. Runtime loading validates its build version and
falls back to the Python builder if the library is unavailable or incompatible.

### Build the Extension

From the repository root:

```bash
python3 scripts/package_extension.py
```

This command:

1. Runs Blender in the background to regenerate the node library.
2. Creates `dist/clone_fields.zip`.
3. Copies the same ZIP to the Desktop when available.

Set `BLENDER_BIN` when Blender is not in the default macOS location or on PATH:

```bash
BLENDER_BIN="/path/to/blender" python3 scripts/package_extension.py
```

Use `--skip-node-library` only when intentionally packaging an already generated
library. Use `--no-desktop-copy` to skip the convenience Desktop copy.

Release libraries should be generated with the oldest Blender version supported
by `blender_manifest.toml`. Newer Blender versions may write `.blend` files that
older supported versions cannot open. Runtime loading falls back to the Python
builder when the bundled library is incompatible, so the extension remains
usable while rebuilding the release asset with the minimum version.

### Tests

Run Blender commands separately; on some macOS systems, launching Blender after
another command in the same shell expression can trigger an unrelated USD
startup crash.

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup \
  --python scripts/verify_node_library.py
```

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup \
  --python scripts/smoke_test_blender.py
```

The first test verifies both bundled loading and Python fallback generation.
The smoke test covers Cloner modes, source management, Effectors, mesh and spline
alignment, multi-spline sampling, generated curves, and Grease Pencil geometry.

### Changing the Node Graph

1. Edit the builders in `geometry_nodes/grid.py`.
2. Increment `GRID_NODE_GROUP_BUILD_VERSION` in `properties.py`.
3. Regenerate and verify the node library.
4. Run the full smoke test.
5. Rebuild and inspect `dist/clone_fields.zip`.

The build version lets existing Cloners upgrade to the current shared group.
Modifier socket names are the compatibility contract: rename or remove them only
with an explicit migration plan.

### Future Extension Points

- **Target and Shader extensions:** add richer target/up-vector controls or
  additional image remapping while preserving the shared Effector stage.
- **Clones of Clones:** extend source management with cycle-safe Cloner references
  and decide where nested instances are realized. Keep this out of distribution
  builders; it belongs in the Source stage.

See [DESIGN.md](DESIGN.md) for the project goals and scope.

### Curve Cloner checks

Use Blender's real add-on enable process to catch restricted-registration
errors, as well as checking direct runtime behavior:

```bash
/Applications/Blender.app/Contents/MacOS/Blender \\
  --background --factory-startup --python-exit-code 1 \\
  --python scripts/verify_addon_enable.py
```

Run the same command with these scripts for focused checks:

- `scripts/verify_curve_cloner.py`: native curve geometry, masks, PNG/DEM input,
  extrusion and bevel, and the 128 × 1000-point workload.
- `scripts/verify_curve_effectors.py`: spacing, deterministic Random, Step,
  per-point/per-object modes, and persistence.
- `scripts/verify_curve_stack.py`: ordered Shaders, object-before-point sampling,
  selection buttons, and stack reload.
- `scripts/verify_curve_parenting.py`: grouped transforms, parented effector
  creation, and DEM thumbnail persistence.
- `scripts/verify_curve_live.py`: live edits using the local `curvesTest.blend`
  fixture, when present.

The DEM stress checks use `textures/n39w104d7dsm.tif` when available. Local
textures, test scenes, and scene backups are excluded from the extension ZIP.
See [CURVE_DEM_BENCHMARK.md](CURVE_DEM_BENCHMARK.md) for the initial prototype
measurements and their limitations.
