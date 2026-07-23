# Blender/bpy probe for Generational workstation certification.
# Usage:
#   blender --background --python probe_bpy.py -- <output.json>
import json
import sys

import bpy


def main() -> int:
    out_path = ""
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        if idx + 1 < len(sys.argv):
            out_path = sys.argv[idx + 1]

    engine_ids = []
    try:
        rna = bpy.context.scene.render.bl_rna.properties.get("engine")
        if rna and hasattr(rna, "enum_items"):
            engine_ids = [i.identifier for i in rna.enum_items]
    except Exception as ex:  # noqa: BLE001
        engine_ids = ["error:" + str(ex)]

    joined = ",".join(engine_ids).upper()
    eevee = ("EEVEE" in joined)
    cycles = ("CYCLES" in joined)

    ffmpeg_support = False
    try:
        fmt_prop = bpy.context.scene.render.image_settings.bl_rna.properties.get("file_format")
        if fmt_prop and hasattr(fmt_prop, "enum_items"):
            formats = [i.identifier.upper() for i in fmt_prop.enum_items]
            ffmpeg_support = "FFMPEG" in formats
    except Exception:  # noqa: BLE001
        ffmpeg_support = False

    devices = []
    optix = cuda = hip = oneapi = metal = False
    device_summary = "none"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for dtype in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL", "CPU"):
            try:
                prefs.get_devices_for_type(dtype)
            except Exception:  # noqa: BLE001
                pass
        try:
            prefs.get_devices()
        except Exception:  # noqa: BLE001
            pass
        for d in list(getattr(prefs, "devices", [])):
            dtype = str(getattr(d, "type", "")).upper()
            name = str(getattr(d, "name", ""))
            devices.append({"name": name, "type": dtype, "use": bool(getattr(d, "use", False))})
            if dtype == "OPTIX":
                optix = True
            elif dtype == "CUDA":
                cuda = True
            elif dtype == "HIP":
                hip = True
            elif dtype == "ONEAPI":
                oneapi = True
            elif dtype == "METAL":
                metal = True
        if devices:
            device_summary = "; ".join("%s:%s" % (d["type"], d["name"]) for d in devices)
        else:
            device_summary = "CPU (no GPU devices enumerated)"
    except Exception as ex:  # noqa: BLE001
        device_summary = "cycles prefs error: %s" % ex

    cpu_only = not (optix or cuda or hip or oneapi or metal)

    info = {
        "background_ok": True,
        "bpy_ok": True,
        "version": bpy.app.version_string,
        "binary_path": bpy.app.binary_path,
        "render_engines": engine_ids,
        "eevee_available": eevee,
        "cycles_available": cycles,
        "ffmpeg_support": ffmpeg_support,
        "optix": optix,
        "cuda": cuda,
        "hip": hip,
        "oneapi": oneapi,
        "metal": metal,
        "cpu_only": cpu_only,
        "device_summary": device_summary,
        "cycles_devices": devices,
    }

    text = json.dumps(info, indent=2)
    print("GENERATIONAL_BLENDER_PROBE=" + json.dumps(info))
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
