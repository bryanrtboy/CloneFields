"""Exercise property-driven updates and preview discovery using curvesTest.blend."""
from pathlib import Path
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
import CloneFields
from CloneFields import curve_fields as cf, viewport_guides as guides

CloneFields.register()
fixture = ROOT / "curvesTest.blend"
if not fixture.exists():
    raise RuntimeError("This regression check needs the local curvesTest.blend fixture")
bpy.ops.wm.open_mainfile(filepath=str(fixture))
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    # Saved user fixtures may be in source Edit Mode; live generation pauses
    # there until the edits are committed. Only change this test's in-memory scene.
    bpy.ops.object.mode_set(mode="OBJECT")
controller = next(obj for obj in bpy.data.objects if obj.get(cf.CONTROLLER))
settings = controller.clone_curve_fields
settings.enabled = True
primary = cf.shader_link(settings)
eff = primary.effector.clone_fields_effector
eff.shader_show_image = True
eff.use_position = True
eff.use_rotation = False
eff.use_scale = False
image = eff.shader_image
if image is None or not len(image.pixels):
    # The saved fixture links a Desktop image that macOS may deny to the
    # background test process. Substitute in memory; never rewrite the fixture.
    image = bpy.data.images.new("Live Test Gradient", width=4, height=4, float_buffer=True)
    image.pixels = [value for y in range(4) for x in range(4) for value in (x / 3, x / 3, x / 3, 1)]
    eff.shader_image = image
initial_count = len(cf._children(controller))
# No manual refresh/evaluate calls: property callbacks must produce the output.
settings.count_z += 2
expected_count = settings.count_x * settings.count_y * settings.count_z
assert len(cf._children(controller)) == expected_count
assert len(cf._children(controller)) > initial_count
def ys():
    result = []
    for obj in cf._children(controller):
        for spline in obj.data.splines:
            points = spline.bezier_points if spline.type == "BEZIER" else spline.points
            result.extend(point.co.y for point in points)
    return result
eff.position_y = 0
before = ys()
eff.position_y = 2
after = ys()
assert max(abs(a - b) for a, b in zip(before, after)) > 0.01
assert bpy.app.timers.is_registered(cf.refresh)
# An edit also restores polling if Blender has dropped the timer.
bpy.app.timers.unregister(cf.refresh)
settings.spacing_z += 0.01
assert bpy.app.timers.is_registered(cf.refresh)
after = ys()
settings.enabled = False
eff.position_y = 0
assert ys() == after
bpy.ops.object.select_all(action="DESELECT")
controller.select_set(True)
bpy.context.view_layer.objects.active = controller
assert bpy.ops.clone_fields.curve_reload_image() == {"FINISHED"}
assert np.allclose(ys(), before, atol=1e-6)
settings.enabled = True
sources = list(guides._shader_preview_sources(set(bpy.data.objects)))
assert (primary.effector, cf.preview_image(controller)) in sources
assert controller in guides._curve_cloners_for_selection([primary.effector])
assert controller in guides._curve_cloners_for_selection([cf._children(controller)[0]])
assert controller in guides._curve_cloners_for_selection([controller])
CloneFields.unregister()
print("CLONE_FIELDS_CURVE_LIVE_OK")
