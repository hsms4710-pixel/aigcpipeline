# -*- coding: utf-8 -*-
"""build-frame-anim-godot.py — 关键帧 → 对齐 → Godot AnimatedSprite2D 帧动画工程
用法: python build-frame-anim-godot.py <keyframes_dir> <walk_pose_names...> --out <godot_dir> [--fps 6]
对齐：水平按内容中心、垂直按底部(地面)对齐，防循环跳变。
"""
import os, sys, argparse, json, shutil
import numpy as np
from PIL import Image

def align(imgs, pad=24):
    """返回 (aligned RGBA list, W, H)。按内容底部 y（地面）与水平中心对齐。"""
    boxes = []
    for im in imgs:
        a = np.asarray(im.convert('RGBA'))
        ys, xs = np.where(a[:, :, 3] > 20)
        boxes.append((xs.min(), ys.min(), xs.max(), ys.max(), xs.mean()))
    # 目标：底部最大 y 对齐（地面线），水平中心对齐
    max_bottom = max(b[3] for b in boxes)
    max_center = max(abs(b[4] - (b[0]+b[2])/2) for b in boxes)
    # 画布：宽度 = max width + 2*pad, 高度 = max height + 2*pad
    W = max(b[2]-b[0] for b in boxes) + 2 * pad
    H = max(b[3]-b[1] for b in boxes) + 2 * pad
    cx = W // 2
    out = []
    for im, b in zip(imgs, boxes):
        a = np.asarray(im.convert('RGBA'))
        # 平移：内容中心→画布中心；底部→pad 之上（底部对齐到同一地面线）
        dx = int(round(cx - (b[0]+b[2])/2))
        dy = int(round((H - pad - 1) - b[3]))  # 底部对齐到 (H-pad-1)
        canvas = np.zeros((H, W, 4), dtype=np.uint8)
        y0 = max(0, b[1]+dy); y1 = min(H, b[3]+dy+1)
        x0 = max(0, b[0]+dx); x1 = min(W, b[2]+dx+1)
        sy0 = max(0, -dy + y0 - b[1]); 
        # 复制内容
        src_y0 = max(0, b[1] - (b[1]+dy - y0))
        canvas[y0:y1, x0:x1] = a[b[1]+(y0-(b[1]+dy)): b[1]+(y0-(b[1]+dy))+(y1-y0),
                                b[0]+(x0-(b[0]+dx)): b[0]+(x0-(b[0]+dx))+(x1-x0)]
        out.append(Image.fromarray(canvas, 'RGBA'))
    return out, W, H

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyframes_dir")
    ap.add_argument("poses", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=6)
    ap.add_argument("--anim-name", default="walk")
    a = ap.parse_args()
    imgs = []
    for p in a.poses:
        f = os.path.join(a.keyframes_dir, p + '.png')
        if not os.path.exists(f):
            print('MISSING', f); sys.exit(1)
        imgs.append(Image.open(f))
    aligned, W, H = align(imgs)
    os.makedirs(a.out, exist_ok=True)
    frames_dir = os.path.join(a.out, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    names = []
    for i, im in enumerate(aligned):
        nm = f"{a.anim_name}_{i:02d}.png"
        im.save(os.path.join(frames_dir, nm))
        names.append(nm)
    # project.godot
    project = f"""[application]
config/name="Chibi Frame Anim"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.2")
[display]
window/size/viewport_width=480
window/size/viewport_height=640
"""
    open(os.path.join(a.out, 'project.godot'), 'w', encoding='utf-8').write(project)
    # main.tscn
    tscn = f"""[gd_scene load_steps=3 format=3 uid="uid://chibiframe1"]

[ext_resource type="Script" path="res://main.gd" id="1"]
[ext_resource type="Texture2D" path="res://frames/{names[0]}" id="2"]

[node name="Main" type="Node2D"]
script = ExtResource("1")

[node name="Sprite" type="AnimatedSprite2D" parent="."]
frames = SubResource("frames")

[sub_resource type="SpriteFrames" id="frames"]
"""
    # SpriteFrames 在 tscn 里配置动画帧（文本方式）
    anim_lines = []
    for i, nm in enumerate(names):
        anim_lines.append(f'animations = [{{"name": "walk", "speed": {a.fps}.0, "loop": true, "frames": [{i}]}}]')
    # 用简单方式：tscn 用 SpriteFrames 的 data
    # 这里直接构造 SpriteFrames 的动画资源比较繁琐，改为主脚本动态构建
    tscn = f"""[gd_scene load_steps=2 format=3 uid="uid://chibiframe1"]

[ext_resource type="Script" path="res://main.gd" id="1"]

[node name="Main" type="Node2D"]
script = ExtResource("1")

[node name="Sprite" type="AnimatedSprite2D" parent="."]
"""
    open(os.path.join(a.out, 'main.tscn'), 'w', encoding='utf-8').write(tscn)
    # main.gd：动态加载帧 + 播放
    gd = f'''extends Node2D
## 关键帧帧动画 demo（walk 循环）
var sprite: AnimatedSprite2D
var frames: SpriteFrames
var names: Array = {json.dumps(names)}
func _ready():
    sprite = $Sprite
    frames = SpriteFrames.new()
    var fps = {a.fps}
    var duration = 1.0 / fps
    for i in range(names.size()):
        var tex = load("res://frames/" + names[i])
        frames.add_frame("walk", tex, duration)
    sprite.sprite_frames = frames
    sprite.play("walk")
    sprite.scale = Vector2(3.0, 3.0)
    sprite.position = Vector2(240, 340)
'''
    open(os.path.join(a.out, 'main.gd'), 'w', encoding='utf-8').write(gd)
    # 自检脚本
    test = '''extends SceneTree
func _init():
    var frames = SpriteFrames.new()
    var names = ['%s']
    for i in range(names.size()):
        var tex = load("res://frames/" + names[i])
        frames.add_frame("walk", tex, 1.0/6.0)
    print("FRAME_COUNT=", frames.get_frame_count("walk"))
    print("FRAME_SIZE=", frames.get_frame_texture("walk", 0).get_size())
    print("FRAME_ANIM_OK")
    quit(0)
''' % "','".join(names)
    open(os.path.join(a.out, 'test_frames.gd'), 'w', encoding='utf-8').write(test)
    print("OK ->", a.out, "frames:", names, "canvas", W, "x", H)

if __name__ == '__main__':
    main()