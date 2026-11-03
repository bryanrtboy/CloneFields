# Object Cloner Guide

[Back to the quick start](../README.md)

Select a source object and choose **Add > Clone Fields > Cloner**. Edit its
settings in **Properties > Modifiers > Clone Fields**.

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
sources. When an Empty has direct object children, Clone Fields treats those
children as one compound source positioned relative to the Empty's anchor. This
hierarchy traversal is limited to one level; grandchildren are not included.

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
Cloner. Each stack entry has an independent `Cloner Influence`. Effector Strength,
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
shapes limit the effect with the usual Falloff, Effector Strength, and per-Cloner
Influence controls.
Effector object scale is locked because Radius, Size, Height, or Length defines
the field dimensions.
