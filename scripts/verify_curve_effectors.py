"""Verify spacing and mixed point/object effectors on native Curve Cloner."""
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import CloneFields
from CloneFields import curve_fields as cf, viewport_guides

CloneFields.register()
data = bpy.data.curves.new("Curve Effects Source", "CURVE")
data.dimensions = "2D"
data.extrude = 0.1
spline = data.splines.new("POLY")
spline.points.add(5)
source_co = np.array([(-1,-1,0,1),(1,-1,0,1),(1,1,0,1),(.3,1,0,1),(-.3,1,0,1),(-1,1,0,1)], dtype=np.float32)
spline.points.foreach_set("co", source_co.ravel())
spline.use_cyclic_u = True
data[cf.MASK] = [0,0,1,1,1,1]
source = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(source)
bpy.context.view_layer.objects.active = source
source.select_set(True)
bpy.ops.clone_fields.add_curve_cloner()
controller = bpy.context.object
settings = controller.clone_curve_fields
settings.count_z = 3
settings.spacing_z = 2
settings.points = "MASK"
def children():
    return cf._children(controller)
def xyz(obj):
    return np.array([tuple(p.co)[:3] for p in obj.data.splines[0].points])
def z_positions():
    return [o.matrix_basis.translation.z for o in children()]
assert z_positions() == [-2, 0, 2]
settings.spacing_mode = "ENDPOINT"
assert settings.spacing_z == 4 and z_positions() == [-2, 0, 2]
settings.count_z = 5
assert np.allclose(z_positions(), [-2,-1,0,1,2])
settings.spacing_mode = "PER_STEP"
assert settings.spacing_z == 1 and np.allclose(z_positions(), [-2,-1,0,1,2])
settings.count_z = 1
assert z_positions() == [0]
settings.count_z = 3
bpy.ops.clone_fields.curve_new_shader()
shader_link = cf.shader_link(settings)
shader = shader_link.effector.clone_fields_effector
image = bpy.data.images.new("Constant Displacement", width=2, height=2, float_buffer=True)
image.pixels = [1.] * 16
shader.shader_image = image
shader.position_y = 0.5
deformed = [xyz(o) for o in children()]
assert np.allclose(deformed[0][:2], source_co[:2,:3])
assert np.allclose(deformed[0][2:,1], 1.5)
stamps = [o["points_signature"] for o in children()]
ids = [o.data.as_pointer() for o in children()]
bpy.ops.clone_fields.curve_add_effector(kind="BASIC")
basic_link = settings.effects[1]
assert basic_link.affect == "OBJECTS"
basic = basic_link.effector.clone_fields_effector
basic.position_y = 1.25
basic.position_z = 0
assert all(abs(o.matrix_basis.translation.y - 1.25) < 1e-6 for o in children())
assert [o["points_signature"] for o in children()] == stamps
assert [o.data.as_pointer() for o in children()] == ids
assert all(np.array_equal(xyz(o), co) for o,co in zip(children(), deformed))
basic.use_rotation = True
basic.rotation_x = 0.3
basic.use_scale = True
basic.scale_x = 0.2
assert all(np.allclose(xyz(o)[:,2], 0) and o.data.extrude == data.extrude for o in children())
basic_link.enabled = False
bpy.ops.clone_fields.curve_add_effector(kind="RANDOM")
random_link = settings.effects[2]
random = random_link.effector.clone_fields_effector
random.seed = 14
positions = [tuple(o.matrix_basis.translation) for o in children()]
cf.evaluate(controller, force=True)
assert [tuple(o.matrix_basis.translation) for o in children()] == positions
random.seed = 28
assert [tuple(o.matrix_basis.translation) for o in children()] != positions
random.seed = 14
assert [tuple(o.matrix_basis.translation) for o in children()] == positions
settings.count_z = 5
assert abs(children()[0].matrix_basis.translation.x - positions[0][0]) < 1e-6
settings.count_z = 3
random_link.affect = "POINTS"
random.position_z = 100
randomized = [xyz(o) for o in children()]
assert any(not np.allclose(a,b) for a,b in zip(randomized,deformed))
assert all(np.allclose(co[:2], source_co[:2,:3]) and np.allclose(co[:,2], 0) for co in randomized)
random.seed = 25
random.seed = 14
assert all(np.array_equal(xyz(o), co) for o,co in zip(children(),randomized))
random_link.enabled = False
bpy.ops.clone_fields.curve_add_effector(kind="STEP")
step_link = settings.effects[3]
step = step_link.effector.clone_fields_effector
step.position_z = 0
step.position_y = 3
assert np.allclose([o.matrix_basis.translation.y for o in children()], [0,1.5,3])
step.invert = True
assert np.allclose([o.matrix_basis.translation.y for o in children()], [3,1.5,0])
step_link.influence = 50
assert np.allclose([o.matrix_basis.translation.y for o in children()], [1.5,.75,0])
assert controller in viewport_guides._curve_cloners_for_selection([step_link.effector])
# Object-mode Shader also keeps source point data intact.
step_link.enabled = False
shader_link.affect = "OBJECTS"
assert all(np.allclose(xyz(o), source_co[:,:3]) for o in children())
assert all(abs(o.matrix_basis.translation.y - 0.5) < 1e-6 for o in children())
shader_link.affect = "POINTS"
assert all(np.allclose(xyz(o), co) for o,co in zip(children(), deformed))
# Spacing-mode changes must leave projection fitting consistent with the grid.
settings.spacing_mode = "ENDPOINT"
bpy.ops.clone_fields.curve_fit_projection()
assert abs(shader.shader_height - settings.spacing_z) < 1e-5
linked_object = step_link.effector
bpy.ops.clone_fields.curve_remove_effector(index=3)
assert linked_object.name in bpy.data.objects and len(settings.effects) == 3
bpy.ops.wm.save_as_mainfile(filepath="/private/tmp/clone_curve_effectors.blend")
bpy.ops.wm.open_mainfile(filepath="/private/tmp/clone_curve_effectors.blend")
controller = next(o for o in bpy.data.objects if o.get(cf.CONTROLLER))
cf.evaluate(controller)
assert controller.clone_curve_fields.spacing_mode == "ENDPOINT"
assert len(controller.clone_curve_fields.effects) == 3
CloneFields.unregister()
print("CLONE_FIELDS_CURVE_EFFECTORS_OK")
