# -*- coding: utf-8 -*-
"""build-godot-anim-demo.py — 关键帧 → 统一对齐画布 → Godot AnimatedSprite2D 动画工程
解决"切帧跳动/动作不衔接"：所有帧按内容中心 X + 地面线(底部) + 统一内容高度对齐。
用法:
  python build-godot-anim-demo.py --frames <dir> --out <godot_dir> --name <title>
  --target-h 560  统一角色显示高度
  --fps idle=4,walk=8,attack=10,hurt=10  各动画 fps
帧文件命名：<action>_<n>.png（如 idle_1.png, walk_1.png...）。
"""
import os, sys, json, argparse, shutil, io
import numpy as np
from PIL import Image

def _core_bbox(a, core_ratio=0.60):
    """核心身体 bbox：取行宽 > core_ratio*max 的行的范围（忽略细弓/发梢等细长延伸）。
    返回 (cx, cy_bottom, core_h)：核心中心 X、核心底部 Y、核心高度。"""
    h, w = a.shape
    rw = a.sum(axis=1)
    mx = rw.max() if rw.max() > 0 else 1
    core_rows = rw > core_ratio * mx
    if not core_rows.any():
        ys, xs = np.where(a)
        return (xs.mean(), ys.max(), ys.max() - ys.min() + 1)
    y0 = int(np.argmax(core_rows)); y1 = h - 1 - int(np.argmax(core_rows[::-1]))
    sub = a[y0:y1+1, :]
    ys2, xs2 = np.where(sub)
    cx = int(xs2.mean())
    return (cx, y1, y1 - y0 + 1)

def align_frames(files, target_h=560, margin=40, core_ratio=0.60):
    ims = [Image.open(f).convert("RGBA") for f in files]
    # 每帧核心身体（不缩放前先算原图核心高度）→ 缩放目标
    cores = []
    for im in ims:
        a = np.asarray(im)[:, :, 3]
        cores.append(_core_bbox(a, core_ratio))
    scaled = []
    for im, core in zip(ims, cores):
        s = target_h / max(core[2], 1)
        nw = max(1, int(im.width * s)); nh = max(1, int(im.height * s))
        scaled.append(im.resize((nw, nh), Image.LANCZOS))
    W = max(s.width for s in scaled) + 2 * margin
    H = max(s.height for s in scaled) + 2 * margin
    out = []
    for s, core in zip(scaled, cores):
        a = np.asarray(s)[:, :, 3]
        # 缩放后的核心：用原核心位置 * 缩放比（更稳）
        sc = target_h / max(core[2], 1)
        cx_s = core[0] * sc
        bottom_s = core[1] * sc
        dx = int(W // 2 - cx_s)
        dy = int((H - margin - 1) - bottom_s)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.paste(s, (dx, dy), s)
        out.append(c)
    return out, W, H

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="Ailin Anim Demo")
    ap.add_argument("--target-h", type=int, default=560)
    ap.add_argument("--fps", default="idle=4,walk=8,attack=10,hurt=10")
    a = ap.parse_args()
    fps_map = {}
    for kv in a.fps.split(","):
        k, v = kv.split("="); fps_map[k.strip()] = int(v.strip())
    groups = {}
    for f in sorted(os.listdir(a.frames)):
        if not f.endswith(".png"): continue
        stem = f[:-4]
        if "_" not in stem: continue
        action, _, idx = stem.rpartition("_")
        if idx.isdigit():
            groups.setdefault(action, []).append((int(idx), os.path.join(a.frames, f)))
    if not groups:
        print("no action_n.png frames found in", a.frames); return 1
    print("actions:", {k: len(v) for k, v in groups.items()})
    all_files = []
    for action in sorted(groups):
        for _, fp in sorted(groups[action]):
            all_files.append(fp)
    aligned, W, H = align_frames(all_files, target_h=a.target_h)
    os.makedirs(os.path.join(a.out, "assets"), exist_ok=True)
    aligned_map = {}
    i = 0
    for action in sorted(groups):
        for _, _ in sorted(groups[action]):
            dst = os.path.join(a.out, "assets", action + "_" + str(i) + ".png")
            aligned[i].save(dst, "PNG")
            aligned_map.setdefault(action, []).append("res://assets/" + action + "_" + str(i) + ".png")
            i += 1
    # ---- GDScript ----
    lines = []
    lines.append("extends Node2D")
    lines.append("")
    lines.append("const ANIMS = {")
    for action in sorted(aligned_map):
        fr = ", ".join('preload("' + f + '")' for f in aligned_map[action])
        loop = "true" if action in ("idle", "walk", "back") else "false"
        fps = fps_map.get(action, 8)
        lines.append('    "' + action + '": { "frames": [' + fr + '], "fps": ' + str(fps) + ', "loop": ' + loop + ' },')
    lines.append("}")
    lines.append("")
    lines.append("const SPEED = 340.0")
    lines.append("const TARGET_H = float(" + str(a.target_h) + ")")
    lines.append("")
    lines.append("@onready var chibi: AnimatedSprite2D = $Chibi")
    lines.append("@onready var hint: Label = $Hint")
    lines.append("@onready var info: Label = $Info")
    lines.append("")
    lines.append("var _facing := Vector2.DOWN")
    lines.append("var _transition := false")
    lines.append("")
    lines.append("func _fit_all() -> void:")
    lines.append("    var frames: Array = ANIMS.idle.frames")
    lines.append("    if frames.is_empty(): return")
    lines.append("    var rect: Rect2i = frames[0].get_image().get_used_rect()")
    lines.append("    var s := TARGET_H / float(max(rect.size.y, 1))")
    lines.append("    chibi.scale = Vector2(s, s)")
    lines.append("")
    lines.append("func _play(name: String) -> void:")
    lines.append("    if chibi.animation == name and chibi.is_playing(): return")
    lines.append("    chibi.animation = name")
    lines.append("    chibi.play()")
    lines.append("    _transition = not ANIMS.get(name, { \"loop\": true }).loop")
    lines.append("")
    lines.append("func _ready() -> void:")
    lines.append("    chibi.sprite_frames = SpriteFrames.new()")
    lines.append("    for k in ANIMS:")
    lines.append("        chibi.sprite_frames.add_animation(k)")
    lines.append("        for f in ANIMS[k].frames:")
    lines.append("            chibi.sprite_frames.add_frame(k, f)")
    lines.append("        chibi.sprite_frames.set_animation_speed(k, ANIMS[k].fps)")
    lines.append("        chibi.sprite_frames.set_animation_loop(k, ANIMS[k].loop)")
    lines.append("    _fit_all()")
    lines.append("    _play(\"idle\")")
    lines.append("    hint.text = \"WASD/方向键=移动(下=idle/上=back/左右=翻转walk)  空格=attack  H=hurt\"")
    lines.append("")
    lines.append("func _process(delta: float) -> void:")
    lines.append("    var dir := Vector2.ZERO")
    lines.append("    if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A): dir.x -= 1.0")
    lines.append("    if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D): dir.x += 1.0")
    lines.append("    if Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W): dir.y -= 1.0")
    lines.append("    if Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S): dir.y += 1.0")
    lines.append("    if Input.is_key_pressed(KEY_SPACE): _play(\"attack\")")
    lines.append("    if Input.is_key_pressed(KEY_H): _play(\"hurt\")")
    lines.append("    if not chibi.is_playing(): _transition = false")
    lines.append("    if dir != Vector2.ZERO:")
    lines.append("        _facing = dir.normalized()")
    lines.append("        if not _transition:")
    lines.append("            if _facing.x < -0.5:")
    lines.append("                chibi.flip_h = true; _play(\"walk\")")
    lines.append("            elif _facing.x > 0.5:")
    lines.append("                chibi.flip_h = false; _play(\"walk\")")
    lines.append("            elif _facing.y < -0.5:")
    lines.append("                _play(\"back\")")
    lines.append("            else:")
    lines.append("                _play(\"idle\")")
    lines.append("        position += dir * SPEED * delta")
    lines.append("    else:")
    lines.append("        if not _transition:")
    lines.append("            chibi.flip_h = false")
    lines.append("            _play(\"idle\")")
    lines.append("    var st: String = \"transition\" if _transition else str(chibi.animation)")
    lines.append("    info.text = \"朝向:\" + _facing_desc() + \" 动画:\" + st + \" 位置(\" + str(int(position.x)) + \",\" + str(int(position.y)) + \")\"")
    lines.append("")
    lines.append("func _facing_desc() -> String:")
    lines.append("    if _facing.x < -0.5: return \"左\"")
    lines.append("    elif _facing.x > 0.5: return \"右\"")
    lines.append("    elif _facing.y < -0.5: return \"背\"")
    lines.append("    return \"正\"")
    gd = "\n".join(lines)
    io.open(os.path.join(a.out, "demo.gd"), "w", encoding="utf-8").write(gd)
    # ---- tscn / project.godot / start-demo.cmd ----
    tscn = (
        "[gd_scene load_steps=2 format=3]\n\n"
        "[ext_resource type=\"Script\" path=\"res://demo.gd\" id=\"1\"]\n\n"
        "[node name=\"Demo\" type=\"Node2D\"]\n"
        "script = ExtResource(\"1\")\n\n"
        "[node name=\"Chibi\" type=\"AnimatedSprite2D\" parent=\".\"]\n"
        "position = Vector2(800, 480)\n"
        "scale = Vector2(1, 1)\n\n"
        "[node name=\"Title\" type=\"Label\" parent=\".\"]\n"
        "offset_left = 20.0\noffset_top = 14.0\noffset_right = 1200.0\noffset_bottom = 46.0\n"
        "text = \"" + a.name + "\"\n"
        "theme_override_font_sizes/font_size = 24\n\n"
        "[node name=\"Hint\" type=\"Label\" parent=\".\"]\n"
        "offset_left = 20.0\noffset_top = 840.0\noffset_right = 1580.0\noffset_bottom = 890.0\n"
        "text = \"WASD=移动  空格=attack  H=hurt\"\n\n"
        "[node name=\"Info\" type=\"Label\" parent=\".\"]\n"
        "offset_left = 1180.0\noffset_top = 14.0\noffset_right = 1580.0\noffset_bottom = 46.0\n"
        "text = \"朝向 / 动画 / 位置\"\n"
        "theme_override_font_sizes/font_size = 18\n"
    )
    io.open(os.path.join(a.out, "demo.tscn"), "w", encoding="utf-8").write(tscn)
    proj = (
        "config_version=5\n\n[application]\n\n"
        "config/name=\"" + a.name + "\"\n"
        "config/features=PackedStringArray(\"4.7\")\n"
        "run/main_scene=\"res://demo.tscn\"\n\n[display]\n\n"
        "window/size/viewport_width=1600\nwindow/size/viewport_height=900\n\n[rendering]\n\n"
        "environment/defaults/default_clear_color=Color(0.13, 0.16, 0.2, 1)\n"
    )
    io.open(os.path.join(a.out, "project.godot"), "w", encoding="utf-8").write(proj)
    cmd = '@echo off\r\ncd /d "%~dp0"\r\n"C:\\Users\\26046\\Documents\\lovegaming\\Godot_v4.7.1-stable_win64.exe\\Godot_v4.7.1-stable_win64.exe" --path "%cd%" --resolution 1600x900\r\n'
    io.open(os.path.join(a.out, "start-demo.cmd"), "w", encoding="ascii").write(cmd)
    print("GODOT PROJECT ->", a.out, "canvas", W, "x", H)
    return 0

if __name__ == "__main__":
    sys.exit(main())
