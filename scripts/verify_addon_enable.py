"""Enable/disable the actual packaged ZIP under Blender's RestrictBlend guard."""
from pathlib import Path
import sys
import tempfile
import zipfile

import addon_utils
import bpy

root = Path(__file__).resolve().parents[1]
archive = root / "dist/clone_fields.zip"
fixture = root / "curvesTest.blend"
if fixture.exists():
    bpy.ops.wm.open_mainfile(filepath=str(fixture))

with tempfile.TemporaryDirectory(prefix="clone-fields-enable-") as directory:
    package = Path(directory) / "CloneFields"
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(package)
    sys.path.insert(0, directory)
    for cycle in range(2):
        errors = []
        module = addon_utils.enable("CloneFields", default_set=False, handle_error=lambda: errors.append(sys.exc_info()[1]))
        assert module is not None and not errors, errors
        cf = module.curve_fields
        assert bpy.app.timers.is_registered(cf.refresh)
        # Run the deferred callback after addon_utils has released RestrictBlend.
        cf.refresh()
        for controller in bpy.data.objects:
            if controller.get(cf.CONTROLLER):
                assert controller.get("curve_stack_version") == 2
                assert any(entry.effector and entry.effector.clone_fields_effector.type == "SHADER"
                           for entry in controller.clone_curve_fields.effects)
        addon_utils.disable("CloneFields", default_set=False)
        assert not bpy.app.timers.is_registered(cf.refresh)
        assert not hasattr(bpy.types.Object, "clone_curve_fields")
    sys.path.remove(directory)

print("CLONE_FIELDS_PACKAGED_ENABLE_OK")
