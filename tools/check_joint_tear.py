# -*- coding: utf-8 -*-
"""check_joint_tear.py — 校验肘/膝关节区域内容连续（不断裂）
对 render_fk_frames.py 输出的帧：在每个肘/膝关节世界位置取圆盘，检查不透明占比。
"""
import json, os, sys
import numpy as np
from PIL import Image

frames_dir = sys.argv[1]
joints_path = os.path.join(frames_dir, 'joints.json')
if not os.path.isfile(joints_path):
    print('no joints.json -> run render_fk_frames.py first'); sys.exit(2)
joints = json.load(open(joints_path, encoding='utf-8'))
joint_keys = ['leftElbow', 'rightElbow', 'leftKnee', 'rightKnee']
fails = []
for clip, times in joints.items():
    for t, pose in times.items():
        img_path = os.path.join(frames_dir, f'{clip}_{int(float(t)*100):03d}.png')
        if not os.path.isfile(img_path):
            continue
        im = np.asarray(Image.open(img_path).convert('RGBA'))
        alpha = im[:, :, 3]
        for jk in joint_keys:
            j = pose.get(jk)
            if not j:
                continue
            x, y = int(j[0]), int(j[1])
            r = 22
            x0, x1 = max(0, x-r), min(im.shape[1], x+r+1)
            y0, y1 = max(0, y-r), min(im.shape[0], y+r+1)
            if x0 >= x1 or y0 >= y1:
                fails.append(f'{clip} t={t} {jk} 关节在画布外 ({x},{y})'); continue
            disc = alpha[y0:y1, x0:x1]
            ys, xs = np.ogrid[y0:y1, x0:x1]
            mask = (xs - x)**2 + (ys - y)**2 <= r*r
            opaque = (disc > 40)
            ratio = float((opaque & mask).sum()) / max(1.0, float(mask.sum()))
            if ratio < 0.5:
                fails.append(f'{clip} t={t} {jk} 关节区域透明占比高: opaque={ratio:.2f} @({x},{y})')
            else:
                print(f'{clip} t={t} {jk} opaque={ratio:.2f} @({x},{y}) OK')
if fails:
    print('FAIL:')
    for f in fails: print(' -', f)
    sys.exit(1)
print('JOINT_TEAR_CHECK: PASS (no torn joints)')