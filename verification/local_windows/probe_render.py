# One-frame Cycles render probe for Generational workstation certification.
# Invoked as: blender -b --python probe_render.py
# Output path is passed via env GENERATIONAL_RENDER_OUT
import os

import bpy

out = os.environ.get("GENERATIONAL_RENDER_OUT", "").strip()
if not out:
    raise SystemExit("GENERATIONAL_RENDER_OUT is not set")

bpy.ops.wm.read_factory_settings(use_empty=False)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for compute in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = compute
            prefs.get_devices()
            break
        except Exception:  # noqa: BLE001
            continue
    scene.cycles.device = "GPU"
except Exception:  # noqa: BLE001
    pass

scene.cycles.samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("GENERATIONAL_RENDER_OK=" + out)
print("GENERATIONAL_RENDER_EXISTS=" + str(os.path.exists(out)))
