"""Integration checks for native Curve Cloner and shared Shader Effectors."""
from pathlib import Path
import math
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import CloneFields
from CloneFields import curve_fields as cf

CloneFields.register()
curve = bpy.data.curves.new("Subdivided Rectangle", "CURVE")
curve.dimensions = "2D"
curve.fill_mode = "BOTH"
curve.extrude = 0.02
spline = curve.splines.new("POLY")
points = [(-5, -1, 0), (5, -1, 0)] + [(x, 1, 0) for x in np.linspace(5, -5, 100)]
spline.points.add(len(points) - 1)
for point, co in zip(spline.points, points):
    point.co = (*co, 1)
spline.use_cyclic_u = True
source = bpy.data.objects.new("Subdivided Rectangle", curve)
bpy.context.collection.objects.link(source)
bpy.context.view_layer.objects.active = source
source.select_set(True)
assert bpy.ops.clone_fields.add_curve_cloner() == {"FINISHED"}
controller = bpy.context.object
settings = controller.clone_curve_fields
settings.count_z = 3
settings.spacing_z = 0.2
assert bpy.ops.clone_fields.curve_new_shader() == {"FINISHED"}
primary = cf.shader_link(settings)
effector = primary.effector
eff = effector.clone_fields_effector
eff.shader_width = 12
eff.shader_preserve_aspect = False
eff.shader_height = 2
# Project X/Z over the stack, with local Y displacement on each profile.
effector.rotation_euler.x = math.pi / 2
image = bpy.data.images.new("Curve Test Gradient", width=4, height=4, float_buffer=True)
pixels = np.ones((4, 4, 4), dtype=np.float32)
pixels[:, :, :3] = np.linspace(0, 1, 4)[None, :, None]
image.pixels.foreach_set(pixels.ravel())
eff.shader_image = image
bpy.ops.object.select_all(action="DESELECT")
source.select_set(True)
bpy.context.view_layer.objects.active = source
for index, point in enumerate(spline.points):
    point.select = index >= 2
bpy.ops.object.mode_set(mode="EDIT")
assert bpy.ops.clone_fields.curve_store_selection() == {"FINISHED"}
bpy.ops.object.mode_set(mode="OBJECT")
spline = curve.splines[0]
assert list(curve[cf.MASK]) == [0, 0] + [1] * 100
bpy.ops.object.select_all(action="DESELECT")
controller.select_set(True)
bpy.context.view_layer.objects.active = controller
bpy.context.view_layer.update()
cf.evaluate(controller)
bpy.context.view_layer.update()
children = cf._children(controller)
assert len(children) == 3
assert len({o.data.as_pointer() for o in children}) == 3
assert all(o.type == "CURVE" and o.data.dimensions == "2D" for o in children)
for obj in children:
    output = obj.data.splines[0].points
    assert all(abs(p.co.z) < 1e-8 for p in output)
    assert output[0].co.y == output[1].co.y == -1
    assert max(p.co.y for p in output) > 1.5
    assert output[2].co.y > output[-1].co.y
first_ids = [o.as_pointer() for o in children]
eff.strength = 0
cf.evaluate(controller)
assert max(p.co.y for p in children[0].data.splines[0].points) == 1
assert [o.as_pointer() for o in cf._children(controller)] == first_ids
eff.strength = 100
curve.extrude = 0.04
curve.bevel_depth = 0.01
curve.bevel_resolution = 3
cf.evaluate(controller)
bpy.context.view_layer.update()
assert abs(children[0].dimensions.z - 0.1) < 1e-5
assert children[0].data.bevel_resolution == 3
eff.shape = "SPHERE"
eff.radius = 0.01
cf.evaluate(controller)
assert max(p.co.y for p in children[0].data.splines[0].points) == 1
eff.shape = "NONE"
# Source changes replace data but reuse objects, with no accumulated offsets.
spline.points[0].co.y = -2
cf.evaluate(controller)
assert children[0].data.splines[0].points[0].co.y == -2
settings.count_z = 1
cf.evaluate(controller)
assert len(cf._children(controller)) == 1
bpy.context.scene.frame_set(2)
assert len(cf._children(controller)) == 1
# Unchanged input must not touch Curve data, and Bezier handles must follow
# control points while preserving corner types and native curve generation.
cf.evaluate(controller)
unchanged_data = cf._children(controller)[0].data.as_pointer()
cf.evaluate(controller)
assert cf._children(controller)[0].data.as_pointer() == unchanged_data
bezier = bpy.data.curves.new("Bezier Source", "CURVE")
bezier.dimensions = "2D"
bs = bezier.splines.new("BEZIER")
bs.bezier_points.add(3)
bs.use_cyclic_u = True
for point, coordinate in zip(bs.bezier_points, ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))):
    point.co = coordinate
    point.handle_left_type = point.handle_right_type = "VECTOR"
bezier_obj = bpy.data.objects.new("Bezier Source", bezier)
bpy.context.collection.objects.link(bezier_obj)
settings.source = bezier_obj
settings.points = "ALL"
cf.evaluate(controller)
bpy.context.view_layer.update()
bz_output = cf._children(controller)[0].data.splines[0]
assert bz_output.type == "BEZIER"
assert all(point.co.z == 0 and point.handle_left.z == 0 and point.handle_right.z == 0 for point in bz_output.bezier_points)
assert max(p.co.y for p in bz_output.bezier_points) > 1
assert all(p.handle_left_type == p.handle_right_type == "VECTOR" for p in bz_output.bezier_points)
settings.source = source
settings.points = "MASK"
bpy.data.objects.remove(bezier_obj, do_unlink=True)
bpy.data.curves.remove(bezier)
image.filepath_raw = "/private/tmp/curve_cloner_gradient.png"
image.file_format = "PNG"
image.save()
assert bpy.ops.clone_fields.curve_load_image(filepath=image.filepath_raw) == {"FINISHED"}
assert primary.effector.clone_fields_effector.shader_image is not None
cf.evaluate(controller)
assert max(p.co.y for p in cf._children(controller)[0].data.splines[0].points) > 1
from CloneFields.curve_images import sample
sampled = sample(np.array([[0., -32767.], [1., 1.]]), -32767., np.array([0.5]), np.array([0.5]))
assert abs(sampled[0] - 2 / 3) < 1e-6
# The supplied DEM is optional so this check also runs in packaged installations.
dem = Path(__file__).resolve().parents[1] / "textures/n39w104d7dsm.tif"
if dem.exists():
    settings.enabled = False
    assert bpy.ops.clone_fields.curve_load_image(filepath=str(dem)) == {"FINISHED"}
    assert primary.dem_path == str(dem) and primary.normalize
    settings.count_z = 128
    curve.bevel_depth = 0
    curve.extrude = 0.015
    # Increase the source to 1000 top points; regenerate the explicit mask.
    curve.splines.clear()
    spline = curve.splines.new("POLY")
    points = [(-5, -1, 0), (5, -1, 0)] + [(x, 1, 0) for x in np.linspace(5, -5, 1000)]
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    spline.use_cyclic_u = True
    curve[cf.MASK] = [0, 0] + [1] * 1000
    eff.shader_height = 30
    bpy.context.view_layer.update()
    started = time.perf_counter()
    settings.enabled = True
    cf.evaluate(controller)
    bpy.context.view_layer.update()
    print("CURVE_CLONER_DEM_INITIAL", time.perf_counter() - started)
    started = time.perf_counter()
    eff.strength = 80
    cf.evaluate(controller)
    bpy.context.view_layer.update()
    print("CURVE_CLONER_DEM_UPDATE", time.perf_counter() - started)
    children = cf._children(controller)
    assert len(children) == 128
    assert max(p.co.y for o in children for p in o.data.splines[0].points) > 1.1
    assert all(p.co.z == 0 for o in children for p in o.data.splines[0].points)
    assert all(o.data.splines[0].points[0].co.y == -1 for o in children)
    preview = cf.preview_image(controller)
    assert preview is not None and max(preview.size) <= 512
    from CloneFields import viewport_guides
    assert (primary.effector, preview) in list(viewport_guides._shader_preview_sources(set(bpy.data.objects)))
    point_stamps = [o["points_signature"] for o in children]
    bpy.ops.clone_fields.curve_add_effector(kind="BASIC")
    basic = settings.effects[-1].effector.clone_fields_effector
    started = time.perf_counter()
    basic.position_y = 0.1
    bpy.context.view_layer.update()
    print("CURVE_CLONER_OBJECT_UPDATE", time.perf_counter() - started)
    assert [o["points_signature"] for o in children] == point_stamps
    bpy.ops.wm.save_as_mainfile(filepath="/private/tmp/clone_curve_fields_integrated.blend")
CloneFields.unregister()
print("CLONE_FIELDS_CURVE_CLONER_OK")
