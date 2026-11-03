"""Native parenting, grouped effector creation, and numeric DEM thumbnail reload."""
from pathlib import Path
import math
import sys

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
import CloneFields
from CloneFields import curve_fields as cf

CloneFields.register()
data = bpy.data.curves.new("Parent Test Source", "CURVE")
data.dimensions = "2D"
data.extrude = 0.05
spline = data.splines.new("POLY")
spline.points.add(5)
for p, co in zip(spline.points, ((-1,-1,0),(1,-1,0),(1,1,0),(.3,1,0),(-.3,1,0),(-1,1,0))):
    p.co = (*co,1)
spline.use_cyclic_u = True
source = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(source)
source.rotation_euler.z = 0.2
source.scale = (1.2,0.8,1)
bpy.context.view_layer.objects.active = source
source.select_set(True)
bpy.ops.clone_fields.add_curve_cloner()
controller = bpy.context.object
settings = controller.clone_curve_fields
settings.count_z = 3
controller.location = (2,3,4)
bpy.context.view_layer.update()
bpy.ops.clone_fields.curve_add_effector(kind="SHADER")
entry = settings.effects[0]
effector = entry.effector
image = bpy.data.images.new("Parent Test Gradient", width=8,height=8,float_buffer=True)
image.pixels = [v for y in range(8) for x in range(8) for v in (x/7,x/7,x/7,1)]
image.pack()
effector.clone_fields_effector.shader_image = image
def update():
    bpy.context.view_layer.update()
    cf.evaluate(controller)
    bpy.context.view_layer.update()
def local_points():
    return [np.array([tuple(p.co)[:3] for p in obj.data.splines[0].points]) for obj in cf._children(controller)]
def world_points():
    return [cf._transform(co,obj.matrix_world) for obj,co in zip(cf._children(controller),local_points())]
update()
original_local, original_world = local_points(),world_points()
group = bpy.data.objects.new("Parent Test Group", None)
bpy.context.collection.objects.link(group)
group.location = (8,-4,2)
group.rotation_euler.x = math.pi / 2
bpy.context.view_layer.update()
original_group = group.matrix_world.copy()
bpy.ops.object.select_all(action="DESELECT")
for obj in (source,controller,effector,group): obj.select_set(True)
bpy.context.view_layer.objects.active = group
assert bpy.ops.object.parent_set(type="OBJECT",keep_transform=True) == {"FINISHED"}
update()
assert all(np.allclose(a,b,atol=1e-5) for a,b in zip(original_world,world_points()))
group.rotation_euler = (math.pi/2,.3,.4)
group.scale = (1.4,.9,1.2)
update()
delta = group.matrix_world @ original_group.inverted()
expected = [cf._transform(co,delta) for co in original_world]
assert all(np.allclose(a,b,atol=1e-5) for a,b in zip(expected,world_points()))
assert all(np.allclose(a,b,atol=1e-5) for a,b in zip(original_local,local_points()))
assert entry.effector == effector and settings.source == source
bpy.ops.object.select_all(action="DESELECT")
controller.select_set(True)
bpy.context.view_layer.objects.active = controller
bpy.ops.clone_fields.curve_add_effector(kind="BASIC")
new_basic = settings.effects[-1].effector
bpy.context.view_layer.update()
assert new_basic.parent == group
assert np.allclose(np.array(new_basic.matrix_world),np.array(controller.matrix_world),atol=1e-5)
bpy.ops.clone_fields.curve_add_effector(kind="SHADER")
new_shader = settings.effects[-1].effector
bpy.context.view_layer.update()
assert new_shader.parent == group
assert np.allclose(np.array(new_shader.matrix_world),np.array(controller.matrix_world @ Matrix.Rotation(math.pi/2,4,"X")),atol=1e-5)
assert settings.effects[0].effector == effector
dem = ROOT / "textures/n39w104d7dsm.tif"
if dem.exists():
    index = len(settings.effects)-1
    bpy.ops.clone_fields.curve_load_image(index=index,filepath=str(dem))
    cf.refresh()
    preview = cf.preview_image(controller,index)
    assert preview and preview.packed_file
    assert preview.preview.is_image_custom
    rgb = np.array(preview.preview.image_pixels_float).reshape(-1,4)[:,:3]
    assert np.ptp(rgb) > 0.1 and rgb.max() > 0.5
    # Preview must also recover independently of live generation.
    settings.enabled = False
    bpy.ops.wm.save_as_mainfile(filepath="/private/tmp/clone_curve_parenting.blend")
    bpy.ops.wm.open_mainfile(filepath="/private/tmp/clone_curve_parenting.blend")
    controller = next(o for o in bpy.data.objects if o.get(cf.CONTROLLER))
    cf.refresh()
    preview = cf.preview_image(controller,index)
    rgb = np.array(preview.preview.image_pixels_float).reshape(-1,4)[:,:3]
    assert np.ptp(rgb) > 0.1
    assert all(entry.effector is not None for entry in controller.clone_curve_fields.effects)
CloneFields.unregister()
print("CLONE_FIELDS_CURVE_PARENTING_OK")
