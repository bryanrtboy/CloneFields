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

The Modifier tab shows a Clone Fields panel with named mode controls for Grid,
Linear, and Radial. Only the controls for the selected distribution mode are
shown.

Grid and Radial distributions are centered on the Cloner origin. Selected
Cloners draw lightweight viewport guides for grid bounds or radial radius.
Grid axis handles update spacing, and the Radial handle updates radius.

360-degree arcs use the clone count as the angular step divisor, so a count of
8 produces 8 evenly spaced clones without an overlapping endpoint. `Align`
makes the source transform follow the radial step.

To use multiple sources, parent additional source objects directly under the
Cloner. Clone Fields alternates through the child sources by clone index. Empty
objects can be used as blank/spacer sources.

To add Plain Effectors, select a Cloner and use the `Add Plain Effector` button
in the Clone Fields modifier panel. This creates visible sphere controller
objects in the scene. Move, scale, or keyframe the controller objects, then use
the stack controls to select, enable, reorder, and tune each effector. Only the
selected effector's settings are shown. Falloff is a 0-100% slider where 100%
gives a hard field edge and 0% blends across the full field radius. The Cloner's
source Offset controls are hidden until enabled.

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
