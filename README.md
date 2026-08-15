# Clone Fields

Clone Fields is a free Blender extension for procedural cloning using Geometry
Nodes. Its workflow is inspired by procedural modeling systems such as Cinema
4D's Cloner and Effectors, with an interface designed for Blender modeling and
3D-printing workflows.

![Clone Fields cloner grid in Blender](docs/ClonerFieldsScreenshot.png)

## For Users

### Install

Download `dist/clone_fields.zip`. Do not unzip it.

In Blender 4.2 or newer:

1. Open `Edit > Preferences > Extensions`.
2. Choose `Install from Disk...`.
3. Select `clone_fields.zip`.
4. Enable `Clone Fields` if Blender does not enable it automatically.

### Create a Cloner

Select a source object, then choose:

```text
Add > Clone Fields > Cloner
```

The new Cloner is created immediately as a centered 3 by 3 grid. Its source is parented under
the Cloner and hidden while the modifier is enabled. Edit Clone Fields from the
Cloner's Modifier tab; opening Geometry Nodes is not required.

### Distribution Modes

- **Grid:** Count and Spacing on X, Y, and Z.
- **Brick:** Grid counts and spacing with row and layer offsets along X.
- **Linear:** Count, Spacing, and a direction vector.
- **Radial:** Count, Radius, Arc, Axis, and optional alignment.
- **Object:** Place clones on mesh vertices or polygon centers, or along curves,
  text, and Grease Pencil strokes.

Grid and Linear support two spacing conventions. `Per Step` is the distance
between neighboring clones, so changing Count changes the total size.
`Endpoint` is the total distance from the first clone to the last, so changing
Count redistributes clones inside the same size.

Grid, Brick, and Radial distributions are centered on the Cloner origin. Brick
can orient its staggered pattern on the local `Z (XY)`, `X (ZY)`, or `Y (XZ)`
plane. Selected Cloners display viewport guides. Grid handles edit axis
spacing, and the Radial handle edits Radius.

Radial 360-degree arcs divide the circle by Count, so the last clone does not
overlap the first. `Align` makes the source transform follow each radial step.

### Object and Spline Distribution

Mesh objects support `Vertices`, `Polygon Centers`, and `Surface` scatter.
Surface distribution can be density-driven with `Random` or `Poisson`, or
target-count driven with `Count` or `Even`. `UV Grid` uses the named UV map
to place an exact `U Count` by `V Count` grid where that UV map is valid.
Mesh Object modes can be limited by a named vertex group with a threshold,
including vertex, polygon-center, and surface scatter placement.
Alignment can follow surface normals or point toward the distribution object's
center. `Up Vector` controls banking. Its default `None`
automatically keeps clones visually upright while avoiding pole singularities;
`+X`, `+Y`, and `+Z` use a fixed Cloner axis.

Curve-like objects provide:

- **Points:** Use evaluated curve points.
- **Count:** Request a clone count on each spline.
- **Step:** Use a fixed distance along the path.
- **Even:** Distribute a requested count by accumulated curve length.

`Per Spline` restarts Count, Step, or Even on every contour or stroke. Disable
it to treat a multi-contour object as one accumulated path. `Smooth Rotation`
uses the curve normal to stabilize roll around the tangent.

Distribution objects remain visible unless you hide them manually.

### Multiple Sources

Parent additional source objects directly under the Cloner. Clone Fields cycles
through child sources by clone index. Empty objects can serve as blank or spacer
sources.

### Effectors

Select a Cloner and use `New Basic`, `New Random`, `New Target`, `New Shader`,
or `New Step` in its Clone Fields panel.
Effectors are visible controller objects that can be moved or keyframed.

Field shapes include None, Spherical, Cubic, Cylindrical, and Linear. `None`
affects every clone and is the Random Effector default. Cylindrical fields add
Height, while Linear fields use Length between two viewport planes.

The Effector stack lets you:

- Select one Effector for editing.
- Select its controller in the scene.
- Enable, reorder, remove, or delete Effectors.
- Use `Link Existing` to share one Effector across multiple Cloners.

Effector properties are stored on the Effector object, so shared Radius, Height,
Length, Falloff, Strength, Field, and transform values update every linked
Cloner. Each stack entry has an independent `Cloner Influence`. Global Strength,
Cloner Influence, and Falloff use 0-100% controls.
The selected entry separates Effector behavior from its optional Field shape,
dimensions, falloff, and spatial inversion.

Random Effectors add Seed and Position, Rotation, and Scale Variation ranges.
Step Effectors apply Position, Rotation, and Scale progressively by generated
clone order. `Reverse` flips the progression.
Shader Effectors use image luminance to control transform strength. `Invert`
swaps black and white influence. Planar projection follows the visible image
controller, and Tiles X/Y repeats the image inside that projection. Preserve
Aspect keeps the projection matched to the image, while Fit to Grid centers and
sizes it to the evaluated Grid Cloner bounds using Cover or Contain. Switching
Cover or Contain refits immediately after the first fit. The viewport draws an
exact tiled preview while the Effector Empty remains the selectable controller.
Shader Effectors affect
transforms only, not clone color or materials.
Box Fields provide independent X, Y, and Z dimensions with an optional Uniform
size control.
Target Effectors orient clones toward their visible controller by default. Set
the optional `Target` to aim at another scene object, such as a Camera, while
the controller continues to define the field position and falloff. Choose the
local Aim Axis and Up Axis. A `None` field targets every clone; other field
shapes limit the effect with the usual Falloff, Global Strength, and per-Cloner
Influence controls.
Effector object scale is locked because Radius, Size, Height, or Length defines
the field dimensions.

## For Developers

### Architecture

Python owns installation, object relationships, UI, parameter synchronization,
viewport controls, and generation of the Geometry Nodes implementation.
Geometry Nodes owns live geometry, instances, distributions, alignment, and
Effector evaluation.

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

See `docs/DESIGN.md` for the project goals and scope.
