"""Benchmark native 2D Curve clones against the supplied float DEM.

Run in Blender background mode, optionally with ``-- --save /tmp/terrain.blend``.
This is an architecture experiment, not a registered cloner implementation.
The small TIFF reader deliberately accepts only uncompressed, single-channel,
32-bit float, strip-based classic TIFFs (the supplied DEM's format).
"""

from pathlib import Path
import argparse
import json
import struct
import sys
import time

import bpy
import numpy as np


def open_dem(path):
    with path.open("rb") as stream:
        header = stream.read(8)
        endian = {b"II": "<", b"MM": ">"}[header[:2]]
        magic, directory = struct.unpack(endian + "HI", header[2:])
        if magic != 42:
            raise ValueError("Expected classic TIFF")
        stream.seek(directory)
        count = struct.unpack(endian + "H", stream.read(2))[0]
        entries = [stream.read(12) for _ in range(count)]
        tags = {}
        for entry in entries:
            tag, kind, length = struct.unpack(endian + "HHI", entry[:8])
            formats = {2: "c", 3: "H", 4: "I", 11: "f"}
            if kind not in formats:
                continue
            fmt = endian + str(length) + formats[kind]
            size = struct.calcsize(fmt)
            raw = entry[8:]
            if size > 4:
                stream.seek(struct.unpack(endian + "I", raw)[0])
                raw = stream.read(size)
            tags[tag] = struct.unpack(fmt, raw[:size])
    scalar = lambda tag, default: tags.get(tag, (default,))[0]
    if (scalar(258, 0), scalar(259, 1), scalar(277, 1), scalar(339, 1)) != (32, 1, 1, 3):
        raise ValueError("Expected uncompressed single-channel float32 TIFF")
    if scalar(274, 1) != 1 or 273 not in tags:
        raise ValueError("Expected top-left strip-based TIFF")
    width, height = scalar(256, 0), scalar(257, 0)
    rows = scalar(278, height)
    offsets = np.array(tags[273], dtype=np.int64)
    expected = offsets[0] + np.arange(len(offsets)) * rows * width * 4
    if not np.array_equal(offsets, expected):
        raise ValueError("This benchmark requires contiguous TIFF strips")
    nodata = float(b"".join(tags[42113]).rstrip(b"\0")) if 42113 in tags else None
    data = np.memmap(path, dtype=endian + "f4", mode="r", offset=int(offsets[0]), shape=(height, width))
    return data, nodata


def sample(data, nodata, u, v):
    """Bilinear samples; missing neighbors do not bias valid elevations."""
    x, y = u * (data.shape[1] - 1), v * (data.shape[0] - 1)
    ix, iy = x.astype(np.int64), y.astype(np.int64)
    jx, jy = np.minimum(ix + 1, data.shape[1] - 1), np.minimum(iy + 1, data.shape[0] - 1)
    fx, fy = x - ix, y - iy
    result, weights = np.zeros_like(x), np.zeros_like(x)
    for values, weight in (
        (data[iy, ix], (1 - fx) * (1 - fy)),
        (data[iy, jx], fx * (1 - fy)),
        (data[jy, ix], (1 - fx) * fy),
        (data[jy, jx], fx * fy),
    ):
        valid = np.isfinite(values)
        if nodata is not None:
            valid &= values != nodata
        weight = weight * valid
        result += np.where(valid, values, 0) * weight
        weights += weight
    return np.divide(result, weights, out=np.full_like(result, np.nan), where=weights > 0)


def run(data, nodata, rows, points, save=None):
    collection = bpy.data.collections.new(f"DEM {rows} rows {points} top points")
    bpy.context.scene.collection.children.link(collection)
    started = time.perf_counter()
    u, v = np.meshgrid(np.linspace(0, 1, points), np.linspace(0, 1, rows))
    heights = sample(data, nodata, u, v)
    valid = np.isfinite(heights)
    if not valid.any():
        raise ValueError("No valid elevation samples")
    minimum, maximum = float(heights[valid].min()), float(heights[valid].max())
    heights = np.where(valid, heights, minimum)
    # Preview maps the sampled relief to 2 Blender units above a flat base.
    heights = 1 + 2 * (heights - minimum) / max(maximum - minimum, 1e-6)
    sampled = time.perf_counter()
    coordinates = np.ones((points + 2, 4), dtype=np.float32)
    coordinates[:, 2] = 0
    coordinates[:2, :2] = ((-5, 0), (5, 0))
    coordinates[2:, 0] = np.linspace(5, -5, points)
    objects = []
    for row in range(rows):
        curve = bpy.data.curves.new(f"DEM Profile {row:04}", "CURVE")
        curve.dimensions = "2D"
        curve.fill_mode = "BOTH"
        curve.extrude = 0.015
        spline = curve.splines.new("POLY")
        spline.points.add(points + 1)
        spline.use_cyclic_u = True
        coordinates[2:, 1] = heights[row, ::-1]
        spline.points.foreach_set("co", coordinates.ravel())
        obj = bpy.data.objects.new(curve.name, curve)
        collection.objects.link(obj)
        obj.location.z = row * 0.05
        objects.append(obj)
    created = time.perf_counter()
    bpy.context.view_layer.update()
    evaluated = time.perf_counter()
    # Evaluate every native extrusion and verify each cap stays in its plane.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    vertex_count = 0
    for obj in objects:
        evaluated_obj = obj.evaluated_get(depsgraph)
        mesh = evaluated_obj.to_mesh()
        try:
            vertex_count += len(mesh.vertices)
            assert mesh.polygons and len(mesh.vertices) > points
            assert all(abs(abs(vertex.co.z) - 0.015) < 1e-5 for vertex in mesh.vertices)
        finally:
            evaluated_obj.to_mesh_clear()
    verified = time.perf_counter()
    # A repeated strength update reuses Curve objects and batches point writes.
    for row, obj in enumerate(objects):
        coordinates[2:, 1] = 1 + (heights[row, ::-1] - 1) * 0.8
        obj.data.splines[0].points.foreach_set("co", coordinates.ravel())
        obj.data.update_tag()
    bpy.context.view_layer.update()
    updated = time.perf_counter()
    # Native data properties must remain live after point deformation.
    objects[0].data.extrude = 0.025
    objects[0].data.bevel_depth = 0.005
    objects[0].data.bevel_resolution = 2
    bpy.context.view_layer.update()
    assert abs(objects[0].dimensions.z - 0.06) < 1e-4, objects[0].dimensions.z
    objects[0].data.extrude = 0.015
    objects[0].data.bevel_depth = 0
    result = dict(rows=rows, top_points=points, control_points=rows * (points + 2),
                  elevation_min=minimum, elevation_max=maximum, missing_samples=int((~valid).sum()),
                  sample_s=sampled-started, create_s=created-sampled, evaluate_s=evaluated-created,
                  verify_s=verified-evaluated, update_s=updated-verified, mesh_vertices=vertex_count)
    print("CURVE_DEM_BENCHMARK " + json.dumps(result), flush=True)
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=str(save))
    for obj in objects:
        curve = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.curves.remove(curve)
    bpy.data.collections.remove(collection)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dem", type=Path, default=Path(__file__).resolve().parents[1] / "textures/n39w104d7dsm.tif")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    # Run only in a disposable background scene; the saved preview contains
    # profiles alone, without factory Cube/Camera/Light objects.
    if not bpy.app.background:
        raise RuntimeError("Run this benchmark in Blender background mode")
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    data, nodata = open_dem(args.dem)
    print("CURVE_DEM_INPUT " + json.dumps(dict(path=str(args.dem), size=data.shape, nodata=nodata)), flush=True)
    for rows, points in ((32, 100), (128, 100), (128, 1000), (128, 2000)):
        run(data, nodata, rows, points, args.save if points == 1000 else None)
    print("CURVE_DEM_OK", flush=True)


if __name__ == "__main__":
    main()
