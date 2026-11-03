# Native Curve DEM prototype

This standalone benchmark explores a separate Curve Cloner evaluation path.
It does not register a new cloner or change the existing CloneFields evaluator.

Run with Blender 5.1.2:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/benchmark_curve_dem.py -- --save /private/tmp/clone_curve_dem_1000.blend
```

The default input is `textures/n39w104d7dsm.tif`: a 15001 × 15001,
single-channel float32, uncompressed GeoTIFF. Missing data is -32767.
The reader memory-maps contiguous strips and samples numeric elevations with
bilinear interpolation. Invalid neighbors are excluded and weights normalized;
fully missing samples become the sampled minimum for this preview only.
This is a deliberately restricted reader for the supplied test file, not a
general TIFF importer. PNG and compressed TIFF support remain future work.

Each row is an independent native 2D Curve object, with two bottom points and
the requested number of top points. All point Z coordinates stay zero; object
translations arrange the rows along Z. Only top points receive displacement.
Native Curve Data supplies fill and extrusion. The benchmark temporarily
evaluates meshes to check that extrusion caps stay planar; it does not store
or construct mesh output. It also checks that changing native extrusion and
bevel after displacement changes the object's thickness as expected.

Initial measurements on the development machine (seconds):

| Rows | Top points per row | Sample | Create | Initial evaluation | Strength update |
| --- | --- | --- | --- | --- | --- |
| 32 | 100 | 0.0016 | 0.0005 | 0.0018 | 0.0010 |
| 128 | 100 | 0.0021 | 0.0022 | 0.0044 | 0.0026 |
| 128 | 1000 | 0.0094 | 0.0029 | 0.0166 | 0.0157 |
| 128 | 2000 | 0.0090 | 0.0034 | 0.0346 | 0.0337 |

Strength update includes batched point writes and view-layer update, reusing
objects and previously sampled heights. Initial evaluation excludes the
separate exhaustive Python mesh verification (0.13 s for 128 × 1000 and
0.27 s for 128 × 2000). File opening, cold disk I/O, viewport drawing, animation,
effector falloff, source synchronization, and interactive dependency handlers
are not represented by these timings. These results establish feasibility,
not interactive frame rates or final performance guarantees.

The sampled elevation range was approximately 1781.6–2044.8, with no missing
values at sampled positions. This is not a scan of the entire raster. Preview
relief is normalized to two Blender units above a flat baseline. The saved
1000-point preview shows the final strength-update value, 80% relief.

Next milestone: integrate one Shader Effector and its spatial falloff into a
separate Curve Cloner, with cached source coordinates and image samples,
then benchmark native extrusion and viewport updates in that actual workflow.
Persistent point masks and source geometry-setting synchronization still
need implementation; this prototype tests only a fixed top-edge mask.
