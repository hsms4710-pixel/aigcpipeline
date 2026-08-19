# -*- coding: utf-8 -*-
"""S5 引擎：资产包 → Godot 可玩工程（SpinePlayer 迷你骨骼运行时 + 动画切换）
用法: python export-godot.py <package_dir> --out <godot_dir> [--godot <exe>]
产物流转：S4 打包产物（manifest.json + skeleton.json + images/）→ 本脚本
  → Godot 工程：SpinePlayer 解析 skeleton.json，播放 idle/walk/attack/hurt
"""
import argparse, json, os, shutil, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYER_SRC = os.path.join(HERE, "spine-player.gd")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--godot", default="")
    args = ap.parse_args()

    pkg = args.package_dir
    manifest_f = os.path.join(pkg, "manifest.json")
    if not os.path.isfile(manifest_f):
        print("ERROR: 资产包无 manifest.json"); sys.exit(1)
    manifest = json.load(open(manifest_f, encoding="utf-8"))

    # 找 skeleton.json
    sk = os.path.join(pkg, "skeleton.json")
    imgs_dir = os.path.join(pkg, "images")
    if not os.path.isfile(sk):
        raw = os.path.join(pkg, "raw")
        if os.path.isfile(os.path.join(raw, "skeleton.json")):
            sk = os.path.join(raw, "skeleton.json")
        else:
            for root, _, files in os.walk(pkg):
                if "skeleton.json" in files:
                    sk = os.path.join(root, "skeleton.json"); break
    if not os.path.isfile(sk):
        print("ERROR: skeleton.json 缺失，请先跑 S4 打包"); sys.exit(1)
    data = json.load(open(sk, encoding="utf-8"))
    clips = list(data.get("animations", {}).keys())
    bone_n = len(data.get("bones", []))
    slot_n = len(data.get("slots", []))
    if not os.path.isdir(imgs_dir):
        print("ERROR: images/ 目录缺失，请先跑 S4 打包"); sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    # 生成 lite 骨架（GDScript 解析快：去掉超大 mesh 顶点，只留 bbox + 动画轨道）
    lite = {
        "bones": [{"name": b.get("name", ""), "parent": b.get("parent", "")} for b in data.get("bones", [])],
        "slots": [{"name": s.get("name", ""), "bone": s.get("bone", "")} for s in data.get("slots", [])],
        "skins": [{"attachments": {}}],
        "animations": data.get("animations", {}),
        "_pivots": data.get("_pivots", {}),
    }
    if data.get("skins"):
        for slot_name, atts in data["skins"][0].get("attachments", {}).items():
            lite["skins"][0]["attachments"][slot_name] = {}
            for att_name, a in atts.items():
                entry = {"x": float(a.get("x", 0.0)), "y": float(a.get("y", 0.0))}
                verts = a.get("vertices", [])
                if isinstance(verts, list) and verts:
                    xs = [float(v["x"]) if isinstance(v, dict) else float(v) for v in verts]
                    ys = [float(v["y"]) if isinstance(v, dict) else float(v) for v in verts]
                    entry["bbox"] = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
                lite["skins"][0]["attachments"][slot_name][att_name] = entry
    with open(os.path.join(args.out, "skeleton.lite.json"), "w", encoding="utf-8") as lf:
        json.dump(lite, lf, ensure_ascii=False)
    # 复制资产
    shutil.copy(sk, os.path.join(args.out, "skeleton.json"))
    shutil.copytree(imgs_dir, os.path.join(args.out, "images"), dirs_exist_ok=True)
    shutil.copy(PLAYER_SRC, os.path.join(args.out, "spine_player.gd"))

    # project.godot
    project = """[application]
config/name="SpinePlayer Demo"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.2")
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
"""
    open(os.path.join(args.out, "project.godot"), "w", encoding="utf-8").write(project)

    # main.tscn
    tscn = """[gd_scene load_steps=3 format=3 uid="uid://spineplayer1"]

[ext_resource type="Script" path="res://main.gd" id="1"]
[ext_resource type="Script" path="res://spine_player.gd" id="2"]

[node name="Main" type="Node2D"]
script = ExtResource("1")

[node name="Spine" type="Node2D" parent="."]
script = ExtResource("2")

[node name="Label" type="Label" parent="."]
offset_left = 16.0
offset_top = 640.0
offset_right = 1264.0
offset_bottom = 700.0
theme_override_font_sizes/font_size = 15
"""
    open(os.path.join(args.out, "main.tscn"), "w", encoding="utf-8").write(tscn)

    # main.gd — 加载 + 播放 + 按键切换动画
    gd = """extends Node2D
## S5 引擎 demo：用 SpinePlayer 播放 pipeline 产出的骨骼动画
## 按键：1=idle 2=walk 3=attack 4=hurt 0=暂停/继续

@onready var player = $Spine  # SpinePlayer (spine_player.gd)
@onready var label: Label = $Label

var clip_names: Array = []

func _ready():
    var ok = player.setup("res://skeleton.lite.json", "res://images")
    if not ok:
        label.text = "SpinePlayer 初始化失败"
        return
    clip_names = player.get_clips()
    # 去掉编辑器内部 clip（Parameters）
    clip_names = clip_names.filter(func(c): return not c.begins_with("Parameters"))
    if clip_names.is_empty():
        clip_names = player.get_clips()
    # 角色画布 1280x1280，缩放到视口并居中
    player.scale = Vector2(0.55, 0.55)
    player.position = Vector2(240, 60)
    var prefer = ["walk", "idle", "attack", "hurt"]
    for p in prefer:
        if p in clip_names:
            player.play(p, true)
            break
    update_label()

func _unhandled_input(event):
    if event is InputEventKey and event.pressed:
        var idx = -1
        if event.keycode == KEY_1: idx = 0
        elif event.keycode == KEY_2: idx = 1
        elif event.keycode == KEY_3: idx = 2
        elif event.keycode == KEY_4: idx = 3
        elif event.keycode == KEY_0:
            player._paused = not player._paused
            return
        if idx >= 0 and idx < clip_names.size():
            player.play(clip_names[idx], true)
            update_label()

func update_label():
    var parts = []
    for i in range(clip_names.size()):
        var mark = "→" if clip_names[i] == player._clip_name else " "
        parts.push_back("%s%s=%d" % [mark, clip_names[i], i + 1])
    label.text = "SpinePlayer | 动画: %s | %s | 按键切换" % [player._clip_name, "  ".join(parts)]
"""
    open(os.path.join(args.out, "main.gd"), "w", encoding="utf-8").write(gd)

    # 自检脚本（headless 可用）：解析 + 采样
    test = """extends SceneTree
## 自检：godot --headless --path <proj> --script test_spine.gd
func _init():
    var player = Node2D.new()
    player.set_script(load("res://spine_player.gd"))
    var ok = player.setup("res://skeleton.lite.json", "res://images")
    print("SETUP_OK=", ok)
    if not ok:
        quit(1); return
    var clips = player.get_clips()
    print("CLIPS=", clips)
    for c in clips:
        player.play(c, true)
        var dur = player.get_clip_duration()
        var s0 = player._sample_bone(player._clips[c], "leftLeg")
        print("CLIP=", c, " DUR=", dur, " leftLeg.rot@0=", s0.rot)
    print("PARSE_OK")
    quit(0)
"""
    open(os.path.join(args.out, "test_spine.gd"), "w", encoding="utf-8").write(test)

    info = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "package": os.path.basename(pkg),
            "clips": clips, "bones": bone_n, "slots": slot_n,
            "files": sorted(os.listdir(args.out))}
    json.dump(info, open(os.path.join(args.out, "export-info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK: Godot 工程已生成 -> {args.out}")
    print(f"    动画 clips: {clips} | bones={bone_n} slots={slot_n}")
    print("    打开方式: Godot 编辑器 -> Import -> 选择 project.godot")
    print("    自检: godot --headless --path <proj> --script test_spine.gd")

if __name__ == "__main__":
    main()
