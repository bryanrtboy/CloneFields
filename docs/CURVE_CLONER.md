# Curve Cloner Guide

[Back to the quick start](../README.md)

`Add > Clone Fields > Curve Cloner` creates an independent grid of native
Blender Curve objects. Select a subdivided **2D Curve** before adding it, or
choose one in the controller's **Object Properties > Curve Cloner** panel.
The original mesh/Geometry Nodes Cloner keeps its existing evaluation path.

The Curve Cloner supports one source and an ordered stack of Shader, Basic,
Random, and Step Effectors. Target is intentionally unavailable for curves. Add
**Shader**, or link an existing Shader Effector. Its image,
projection size, tiling, strength, position amounts, and falloff controls drive
displacement at each control point by default. **Affect: Points / Objects** is
an assignment setting: Shader defaults to Points, and the additional effectors
default to Objects. Add or link them under **Effector Stack**; shared
settings and falloff controls match the ordinary cloner. Each assignment has
a named header, enable switch, and **Strength Here**, and can be collapsed,
reordered, or removed with the trash button without deleting the shared
Effector object. Image/Elevation, Projection, Transform, Field/Falloff, and
Shared Effector Settings are separately collapsible sections.

**Strength Here** affects only this stack entry. **Shared Strength**, inside
Shared Effector Settings, changes every cloner using that Effector object.
The strengths multiply: 50% here × 50% shared = 25% before image/falloff
weighting. The UI shows that combined strength when the shared value is below
100%. The Effector Object picker is also in Shared Effector Settings.

Point effects support local XY position/scale and local Z rotation; local Z
coordinates remain zero. The stored point mask applies to all point effects.
Object effects support full XYZ position, rotation, and scale. The stack
executes from top to bottom: every effect samples the result of earlier effects.
Move Basic above Shader to reposition a clone before sampling its image; move
Basic below Shader to offset the already-deformed profile. Stack multiple
Shaders to deform points successively, with a separate image/DEM, projection,
normalization, and influence for each assignment. The arrows reorder all
effect types, including Shaders. Trailing object effects reuse cached curve
coordinates; moving/changing an object effect before a point effect correctly
recomputes downstream deformation.
Random uses a repeatable seed with stable samples for each clone/point index.
Step progresses from the first to last clone (or control point in Points mode),
and Reverse changes its direction. Existing scenes migrate their original
Shader to the top of the stack, followed by their additional effectors.

The source's own local rotation and scale orient the profiles; inherited parent
transforms are applied through the controller only, so grouping the source,
controller, and effectors does not rotate/scale curves twice. Source location
does not offset the centered grid. New effectors are siblings of the controller
under its parent and keep the same parent-inverse frame. To group existing
objects, use Blender's **Ctrl+P > Object (Keep Transform)**; changing the Parent
dropdown alone can change an object's world transform.

**Spacing Mode: Per Step / Endpoint** works like the ordinary cloner. Per Step
is the distance between adjacent clones; Endpoint is the total distance from
first to last clone. Switching modes converts the displayed spacing without
moving the grid. Changing count in Endpoint mode keeps the endpoints fixed.
A single clone stays at the center on that axis. Projection fitting uses the
same spacing convention.

**Projection > Fit Across Stack** aligns the image with the controller's X/Z
plane and fits the grid. This suits XY profiles stacked along Z. Rotate or
move the Shader Effector for a different projection, using its normal Blender
transforms. The field shape limits influence independently of the image.

To deform only a top edge, use **Point Selection > Edit Source Point Selection**
in the Curve Cloner panel. Select the control points in Edit Mode, then use
**Store Selection & Return to Cloner**. These controls are also available in
the viewport: press **N**, open the **Clone Fields** tab, and find **Curve Point
Selection**. **Use Points: Stored Selection** applies the mask to all point
effects; choose **All** to deform the entire outline. F3 > **Store Deformation
Selection** remains available on the source curve in Edit Mode.
After changing point count/order, store the selection again. The cloner never
adds subdivisions. The source stays available in the scene; hide it in the
Outliner when viewing only the generated profiles.

**Image / Elevation > Load Image / DEM** supports ordinary Blender images such as PNG. Displacement
images loaded here use Non-Color data. Compatible single-band uncompressed
float32 TIFFs use direct numeric sampling instead, with missing-data values
excluded. **Normalize Image** maps the valid input range to 0–1; the loader
enables it for numeric DEMs. This uses elevations, not GeoTIFF georeferencing.
The optional **DEM TIFF** path overrides the Effector image. Other TIFF layouts
fall back to Blender's normal image loader. Use **Refresh Image / Curves** after
reloading or editing pixels to clear cached samples.

Each output is a real, independent 2D Curve. Extrude, fill, bevel, taper,
materials, and resolution come from the source Curve Data. Change those on
the source to update all outputs. Point edits rebuild from the source rather
than accumulating displacement. Source modifier output is not copied: this
workflow uses the native Curve datablock, including ParametricSplines updates
to that datablock. Non-node source modifiers must be disabled before cloning.

Count, spacing, and Shader Effector edits update curves directly when Live
Update is enabled. Source geometry and object transforms are also polled at
150 ms intervals; unchanged results are cached. Disable Live Update to pause
automatic changes and use Refresh Image / Curves to update manually. Frame
changes and rendering also refresh live curves. The Shader Effector image is
shown in the panel and projected in the viewport using the same drawing path
as the ordinary cloner. Numeric DEMs get a small normalized preview, leaving
the original elevation data unchanged. DEM previews have explicitly populated
thumbnails and packed preview pixels; they rebuild after loading a scene even
when Live Update is paused or the source is in Edit Mode. Both cloners expose **Show Image in
Viewport** on the Shader Effector; turning it off hides the projection while
keeping deformation, field guides, and the panel thumbnail. Generated objects and curve
data are reused during displacement changes. This costs more than instancing;
the initial integration test with the supplied 15001 × 15001 DEM and 128 curves
of 1000 top points took about 0.43 s initially and 0.08 s for strength updates
in background mode. These timings do not measure viewport drawing. Gradients,
formulas, and other distributions remain future work.

Local `textures/` inputs are excluded from Git and extension packaging.
