# -*- coding: utf-8 -*-
"""S5 引擎：资产包 → Godot 可玩工程（结构 + 场景 + 导入脚本）
用法: python export-godot.py <package_dir> --out <godot_dir> [--godot <exe>]
"""
import argparse, json, os, shutil, sys, datetime

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

    os.makedirs(args.out, exist_ok=True)
    # 复制 atlas 资产
    for name in ("skeleton.png", "skeleton.atlas", "manifest.json"):
        s = os.path.join(pkg, name)
        if os.path.isfile(s):
            shutil.copy(s, os.path.join(args.out, name))

    # 生成 project.godot
    project = """[application]
config/name="CharAILin Demo"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.2")
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
"""
    open(os.path.join(args.out, "project.godot"), "w", encoding="utf-8").write(project)

    # main.tscn：显示 atlas + 呼吸动画
    tscn = """[gd_scene load_steps=3 format=3 uid="uid://charainpc1"]

[ext_resource type="Texture2D" path="res://skeleton.png" id="1"]
[ext_resource type="Script" path="res://main.gd" id="2"]

[node name="Main" type="Node2D"]
script = ExtResource("2")

[node name="Sprite" type="Sprite2D" parent="."]
texture = ExtResource("1")
centered = false
position = Vector2(80, 40)

[node name="Label" type="Label" parent="."]
offset_left = 20.0
offset_top = 640.0
offset_right = 1260.0
offset_bottom = 700.0
text = "Char AILin - atlas loaded | manifest: {animations} anims / {bones} bones"
theme_override_font_sizes/font_size = 16
""".format(animations=len(manifest.get("skeleton", {}).get("animations", [])), bones=manifest.get("skeleton", {}).get("bones", 0))
    open(os.path.join(args.out, "main.tscn"), "w", encoding="utf-8").write(tscn)

    gd = """extends Node2D
var t := 0.0
func _process(delta):
    t += delta
    # 简易呼吸演示（接入 spine-godot 后替换为真实骨骼动画）
    $Sprite.scale = Vector2(1.0, 1.0 + 0.02 * sin(t * 2.0))
"""
    open(os.path.join(args.out, "main.gd"), "w", encoding="utf-8").write(gd)

    info = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "package": os.path.basename(pkg), "files": sorted(os.listdir(args.out))}
    json.dump(info, open(os.path.join(args.out, "export-info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("OK: Godot 工程已生成 ->", args.out)
    print("    打开方式: Godot 编辑器 -> Import -> 选择该目录 project.godot")

if __name__ == "__main__":
    main()
