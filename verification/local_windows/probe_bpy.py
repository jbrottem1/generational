# Blender/bpy probe for Generational workstation certification.
# Invoked as: blender -b --python probe_bpy.py
import json

import bpy

info = {
    "version": bpy.app.version_string,
    "version_cycle": getattr(bpy.app, "version_cycle", ""),
    "binary_path": bpy.app.binary_path,
    "build_platform": str(getattr(bpy.app, "build_platform", "")),
}

engine_ids = []
try:
    rna = bpy.context.scene.render.bl_rna.properties.get("engine")
    if rna and hasattr(rna, "enum_items"):
        engine_ids = [i.identifier for i in rna.enum_items]
except Exception as ex:  # noqa: BLE001
    engine_ids = ["error:" + str(ex)]

joined = ",".join(engine_ids).upper()
info["render_engines"] = engine_ids
info["has_cycles"] = "CYCLES" in joined
info["has_eevee"] = "EEVEE" in joined

devices = []
try:
    cycles_prefs = bpy.context.preferences.addons["cycles"].preferences
    for dtype in ("CUDA", "OPTIX", "HIP", "ONEAPI", "METAL", "CPU"):
        try:
            cycles_prefs.get_devices_for_type(dtype)
        except Exception:  # noqa: BLE001
            pass
    try:
        cycles_prefs.get_devices()
    except Exception:  # noqa: BLE001
        pass
    for d in getattr(cycles_prefs, "devices", []):
        devices.append(
            {
                "name": getattr(d, "name", ""),
                "type": getattr(d, "type", ""),
                "use": bool(getattr(d, "use", False)),
            }
        )
    info["cycles_devices"] = devices
    info["cycles_compute_device"] = str(getattr(cycles_prefs, "compute_device_type", ""))
except Exception as ex:  # noqa: BLE001
    info["cycles_devices"] = []
    info["cycles_devices_error"] = str(ex)

print("GENERATIONAL_BLENDER_PROBE=" + json.dumps(info))
