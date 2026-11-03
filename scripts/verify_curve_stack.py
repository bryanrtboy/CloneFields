"""Ordered Shader stacking, object-before-point sampling, visible mask workflow."""
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import CloneFields
from CloneFields import curve_fields as cf, viewport_guides as vg

CloneFields.register()
data = bpy.data.curves.new("Stack Source", "CURVE")
data.dimensions = "2D"
data.extrude = 0.1
spline = data.splines.new("POLY")
spline.points.add(5)
base = np.array([(-1,-1,0,1),(1,-1,0,1),(1,.5,0,1),(.3,.5,0,1),(-.3,.5,0,1),(-1,.5,0,1)],dtype=np.float32)
spline.points.foreach_set("co", base.ravel())
spline.use_cyclic_u = True
source = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(source)
bpy.context.view_layer.objects.active = source
source.select_set(True)
bpy.ops.clone_fields.add_curve_cloner()
controller = bpy.context.object
settings = controller.clone_curve_fields
settings.count_z = 1
for _ in range(2):
    bpy.ops.clone_fields.curve_add_effector(kind="SHADER")
assert len(settings.effects) == 2
first, second = settings.effects[0], settings.effects[1]
for entry in settings.effects:
    entry.effector.matrix_world = Matrix.Identity(4)
    eff = entry.effector.clone_fields_effector
    eff.shader_preserve_aspect = False
    eff.shader_width = eff.shader_height = 4
    eff.position_x = eff.position_y = eff.position_z = 0
constant = bpy.data.images.new("Constant Stack Image", width=4, height=4, float_buffer=True)
constant.pixels = [1.] * 64
gradient = bpy.data.images.new("Gradient Stack Image", width=16, height=4, float_buffer=True)
gradient.pixels = [value for y in range(4) for x in range(16) for value in (x/15,x/15,x/15,1)]
first.effector.clone_fields_effector.shader_image = constant
first.effector.clone_fields_effector.position_x = .4
second.effector.clone_fields_effector.shader_image = gradient
second.effector.clone_fields_effector.position_y = 1
def output():
    return np.array([tuple(p.co)[:3] for p in cf._children(controller)[0].data.splines[0].points])
cf.evaluate(controller)
ordered = output()
assert np.allclose(ordered[:,0],base[:,0]+.4)
bpy.ops.clone_fields.curve_move_effector(index=1,direction=-1)
reversed_output = output()
assert not np.allclose(ordered[:,1],reversed_output[:,1])
assert np.allclose(ordered[:,1]-reversed_output[:,1],.1,atol=1e-6)
bpy.ops.clone_fields.curve_move_effector(index=0,direction=1)
assert np.allclose(output(),ordered)
bpy.ops.clone_fields.curve_add_effector(kind="BASIC")
basic = settings.effects[-1].effector.clone_fields_effector
basic.position_z = 0
basic.position_x = .5
after = output()
old_stamp = cf._children(controller)[0]["points_signature"]
basic.position_x = .6
assert np.array_equal(output(),after)
assert cf._children(controller)[0]["points_signature"] == old_stamp
# Move Basic above both shaders: image sampling follows the new object origin.
bpy.ops.clone_fields.curve_move_effector(index=2,direction=-1)
bpy.ops.clone_fields.curve_move_effector(index=1,direction=-1)
assert np.allclose(output()[:,1]-after[:,1],.15,atol=1e-6)
# Both projection previews must be discovered independently.
pairs = list(vg._shader_preview_sources(set(bpy.data.objects)))
assert len(pairs) == 2 and {image for _,image in pairs} == {constant,gradient}
# Buttons are available on the controller and while editing the source.
assert cf.CurveSelectionSidebar.poll(bpy.context)
source.hide_set(True)
assert bpy.ops.clone_fields.curve_edit_selection() == {"FINISHED"}
assert bpy.context.object == source and source.mode == "EDIT"
assert cf.CurveSourceSelectionPanel.poll(bpy.context)
assert cf.CurveSelectionSidebar.poll(bpy.context)
for index, point in enumerate(source.data.splines[0].points):
    point.select = index >= 2
assert bpy.ops.clone_fields.curve_finish_selection() == {"FINISHED"}
assert bpy.context.object == controller and settings.points == "MASK"
assert source.hide_get()
assert list(data[cf.MASK]) == [0,0,1,1,1,1]
assert np.allclose(output()[:2],base[:2,:3])
assert np.allclose(output()[:,2],0)
assert all(obj.type == "CURVE" and abs(obj.data.extrude - .1) < 1e-6 for obj in cf._children(controller))
# Disabling one shader leaves the other active, including its viewport preview.
settings.effects[1].enabled = False
assert len(list(vg._shader_preview_sources(set(bpy.data.objects)))) == 1
constant.pack()
gradient.pack()
expected = output()
bpy.ops.wm.save_as_mainfile(filepath="/private/tmp/clone_curve_ordered_stack.blend")
bpy.ops.wm.open_mainfile(filepath="/private/tmp/clone_curve_ordered_stack.blend")
controller = next(obj for obj in bpy.data.objects if obj.get(cf.CONTROLLER))
assert len(controller.clone_curve_fields.effects) == 3
cf.evaluate(controller)
assert np.allclose(output(), expected)
CloneFields.unregister()
print("CLONE_FIELDS_CURVE_STACK_OK")
