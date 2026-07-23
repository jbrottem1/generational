# Real Blender scene render probe for Generational workstation certification.
# Creates mesh + camera + light, renders one PNG and a short animation.
#
# Usage (preferred):
#   blender --background --python probe_scene_render.py -- <out_dir> <result.json>
#
# Env fallback (install_and_certify.ps1):
#   GENERATIONAL_RENDER_OUT, GENERATIONAL_ANIM_OUT, GENERATIONAL_ANIM_DIR
import json
import os
import sys
import time

import bpy


def _arg_after_dash(n: int) -> str:
    if "--" not in sys.argv:
        return ""
    idx = sys.argv.index("--")
    pos = idx + n
    if pos < len(sys.argv):
        return sys.argv[pos]
    return ""


def main() -> int:
    out_dir = _arg_after_dash(1).strip()
    result_json = _arg_after_dash(2).strip()

    png_out = os.environ.get("GENERATIONAL_RENDER_OUT", "").strip()
    anim_out = os.environ.get("GENERATIONAL_ANIM_OUT", "").strip()
    anim_dir = os.environ.get("GENERATIONAL_ANIM_DIR", "").strip()

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        if not png_out:
            png_out = os.path.join(out_dir, "blender_verification_frame.png")
        if not anim_out:
            anim_out = os.path.join(out_dir, "blender_verification_animation.mp4")
        if not anim_dir:
            anim_dir = os.path.join(out_dir, "blender_anim_frames")
        if not result_json:
            result_json = os.path.join(out_dir, "scene_render.json")

    if not png_out or not anim_out:
        raise SystemExit("Need CLI out_dir or GENERATIONAL_RENDER_OUT + GENERATIONAL_ANIM_OUT")

    os.makedirs(os.path.dirname(png_out) or ".", exist_ok=True)
    if anim_dir:
        os.makedirs(anim_dir, exist_ok=True)
    if result_json:
        os.makedirs(os.path.dirname(result_json) or ".", exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 1.0))
    cube = bpy.context.active_object
    cube.name = "CertCube"

    bpy.ops.object.light_add(type="AREA", location=(4.0, -3.0, 6.0))
    light = bpy.context.active_object
    light.data.energy = 400.0
    light.name = "CertLight"

    bpy.ops.object.camera_add(location=(6.0, -6.0, 4.5), rotation=(1.1, 0.0, 0.8))
    cam = bpy.context.active_object
    cam.name = "CertCamera"
    scene = bpy.context.scene
    scene.camera = cam

    mat = bpy.data.materials.new(name="CertMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.15, 0.45, 0.85, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
    if cube.data.materials:
        cube.data.materials[0] = mat
    else:
        cube.data.materials.append(mat)

    scene.frame_start = 1
    scene.frame_end = 12
    scene.frame_current = 1
    cube.rotation_euler = (0.0, 0.0, 0.0)
    cube.keyframe_insert(data_path="rotation_euler", frame=1)
    cube.rotation_euler = (0.0, 0.0, 3.14159)
    cube.keyframe_insert(data_path="rotation_euler", frame=12)

    engine = "BLENDER_EEVEE"
    engine_ids = []
    try:
        rna = scene.render.bl_rna.properties.get("engine")
        if rna and hasattr(rna, "enum_items"):
            engine_ids = [i.identifier for i in rna.enum_items]
    except Exception:  # noqa: BLE001
        engine_ids = []

    joined = ",".join(engine_ids).upper()
    if "BLENDER_EEVEE_NEXT" in joined:
        engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in joined:
        engine = "BLENDER_EEVEE"
    elif "EEVEE" in joined:
        for e in engine_ids:
            if "EEVEE" in e.upper():
                engine = e
                break
    elif "CYCLES" in joined:
        engine = "CYCLES"

    scene.render.engine = engine
    compute_device = "N/A"

    if engine == "CYCLES":
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            chosen = None
            for compute in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
                try:
                    prefs.compute_device_type = compute
                    prefs.get_devices()
                    devices = list(getattr(prefs, "devices", []))
                    gpu = [d for d in devices if str(getattr(d, "type", "")).upper() == compute]
                    if gpu:
                        for d in devices:
                            d.use = str(getattr(d, "type", "")).upper() == compute
                        chosen = compute
                        break
                except Exception:  # noqa: BLE001
                    continue
            if chosen:
                scene.cycles.device = "GPU"
                compute_device = chosen
            else:
                scene.cycles.device = "CPU"
                compute_device = "CPU"
            scene.cycles.samples = 32
        except Exception as ex:  # noqa: BLE001
            compute_device = "CPU (cycles prefs error: %s)" % ex
    else:
        compute_device = "raster (Eevee)"

    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = png_out

    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    still_sec = time.time() - t0

    anim_mode = "none"
    anim_sec = 0.0
    anim_exists = False
    anim_path_final = anim_out
    anim_error = ""

    try:
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
        scene.render.filepath = anim_out
        t1 = time.time()
        bpy.ops.render.render(animation=True)
        anim_sec = time.time() - t1
        anim_exists = os.path.exists(anim_out) and os.path.getsize(anim_out) > 0
        anim_mode = "blender_ffmpeg_mp4"
        anim_path_final = anim_out
    except Exception as ex:  # noqa: BLE001
        anim_error = str(ex)
        if not anim_dir:
            anim_dir = os.path.join(os.path.dirname(anim_out) or ".", "blender_anim_frames")
        os.makedirs(anim_dir, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.join(anim_dir, "frame_")
        t1 = time.time()
        bpy.ops.render.render(animation=True)
        anim_sec = time.time() - t1
        frames = sorted(
            f for f in os.listdir(anim_dir) if f.lower().endswith(".png")
        )
        anim_exists = len(frames) >= 1
        anim_mode = "blender_png_sequence:%s" % len(frames)
        if frames:
            anim_path_final = os.path.join(anim_dir, frames[0])
        print("GENERATIONAL_ANIM_FALLBACK=" + anim_error)

    png_ok = os.path.exists(png_out) and os.path.getsize(png_out) > 0
    anim_ok = bool(anim_exists)
    png_bytes = os.path.getsize(png_out) if png_ok else 0
    anim_bytes = os.path.getsize(anim_path_final) if anim_ok and os.path.exists(anim_path_final) else 0

    result = {
        "png_ok": png_ok,
        "anim_ok": anim_ok,
        "engine": engine,
        "device": compute_device,
        "png_path": png_out,
        "anim_path": anim_path_final,
        "png_seconds": round(still_sec, 3),
        "anim_seconds": round(anim_sec, 3),
        "png_bytes": png_bytes,
        "anim_bytes": anim_bytes,
        "has_mesh": True,
        "has_camera": True,
        "has_light": True,
        "anim_mode": anim_mode,
        "anim_dir": anim_dir,
        "mesh": cube.name,
        "camera": cam.name,
        "light": light.name,
        "anim_error": anim_error,
    }
    print("GENERATIONAL_SCENE_RENDER=" + json.dumps(result))
    print("GENERATIONAL_RENDER_EXISTS=" + str(png_ok))
    print("GENERATIONAL_ANIM_EXISTS=" + str(anim_ok))

    if result_json:
        with open(result_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
            fh.write("\n")
    return 0 if png_ok and anim_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
