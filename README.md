# Clone Fields

Clone Fields is a free Blender extension for procedural cloning using Geometry
Nodes.

![Clone Fields cloner grid in Blender](docs/ClonerFieldsScreenshot.png)

## Install

Download the installable extension zip:

```text
dist/clone_fields.zip
```

In Blender 4.2 or newer:

1. Open `Edit > Preferences > Extensions`.
2. Choose `Install from Disk...`.
3. Select `clone_fields.zip`.
4. Enable `Clone Fields` if Blender does not enable it automatically.

To use it, select a source object and choose:

```text
Add > Clone Fields > Cloner
```

The created `Cloner` object contains the live Geometry Nodes modifier and starts
as a 3 by 3 grid. The source object is parented under the cloner and hidden
while the modifier is enabled.

The Cloner modifier currently supports:

- Grid distribution
- Linear distribution
- Radial distribution
- Object distribution

The Modifier tab shows a Clone Fields panel with named mode controls for Grid,
Linear, Radial, and Object. Only the controls for the selected distribution mode
are shown.

Grid and Radial distributions are centered on the Cloner origin. Selected
Cloners draw lightweight viewport guides for grid bounds or radial radius.
Grid axis handles update spacing, and the Radial handle updates radius.
Grid and Linear modes have a Spacing Mode. `Per Step` treats the value as the
distance between neighboring clones, so changing Count grows or shrinks the
field. `Endpoint` treats the value as the total distance from the first clone to
the last clone, so changing Count redistributes clones inside the same span.

360-degree arcs use the clone count as the angular step divisor, so a count of
8 produces 8 evenly spaced clones without an overlapping endpoint. `Align`
makes the source transform follow the radial step.

Object distribution places clones on a chosen mesh, curve, text, or Grease
Pencil object. Mesh objects support Vertices and Polygon Centers. Curve-like
objects provide four distribution choices: Points uses the curve's evaluated
points, Count samples a requested number on each spline, Step uses a fixed
distance, and Even distributes a requested count by arc length. `Per Spline`
restarts Count, Step, or Even on every contour or stroke; turn it off to treat a
multi-contour object as one accumulated path. `Smooth Rotation` uses the curve
normal to stabilize roll around the tangent. The distribution object is not
hidden automatically, so you can leave it visible for modeling context or hide
it manually.

For mesh alignment, `Up Vector` controls banking around the aligned local Z
axis. The default `None` automatically keeps clones visually upright while
avoiding pole singularities. `+X`, `+Y`, and `+Z` use a fixed Cloner axis when
a specific orientation is needed.

To use multiple sources, parent additional source objects directly under the
Cloner. Clone Fields alternates through the child sources by clone index. Empty
objects can be used as blank/spacer sources.

To add Effectors, select a Cloner and use `New Basic` or `New Random` in the
Clone Fields modifier panel. This creates a visible controller object in the
scene named like `Basic Effector [Spherical]` or `Random Effector [None]`.
The Field menu supports None, Spherical, Cubic, Cylindrical, and Linear fields;
changing it renames the Effector and updates the viewport guide. `None` affects
all clones without drawing a field shape, and is the default for Random
Effectors. Cylindrical fields add a Height control, and Linear fields use Length
to separate two boundary planes along the Effector's local X axis. Random
Effectors use Seed plus Position, Rotation, and Scale Variation ranges. Move or
keyframe the controller objects
directly, or use the Effector stack's scene-select icon to make one active for
movement. The stack also lets you select an effector for editing, enable it,
reorder it, or remove it. Use `Link Existing` to share one Effector object across
multiple Cloners. Effector settings are stored on the Effector object, so editing
Radius, Height, Length, Falloff, Strength, Field, or transform amounts from any
linked Cloner updates that shared Effector everywhere. Each Cloner stack entry
keeps its own `Cloner Influence` value for reducing that Effector's local impact.
Effector size is controlled by field dimensions and Falloff, so object scale is
locked and reset to keep the field predictable. Cubic fields show this size
control as `Size`.
Only the selected effector's settings are shown. Global Strength, Cloner
Influence, and Falloff are 0-100% sliders. Global Strength controls the amount
of the effector transform, and Falloff is 100% for a hard field edge or 0% to
blend across the full field radius. The Cloner's source Offset controls are
hidden until enabled.

## Build the Zip

From the repository root:

```bash
python3 scripts/package_extension.py
```

This writes:

```text
dist/clone_fields.zip
```

It also copies the same zip to your Desktop when a Desktop folder exists.
