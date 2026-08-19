# -*- coding: utf-8 -*-
"""rebuild-review-collages.py — 从当前帧重建审查拼图"""
import os
from PIL import Image, ImageDraw
BASE = r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路\assets\demo\style_batch\transparent_v2"
out_dir = os.path.join(BASE, "_review")
os.makedirs(out_dir, exist_ok=True)
subs = {"hd2d_v2": "frames_hd2d_v2", "pixel_v2": "frames_pixel_hard"}
actions = {"walk": 6, "attack": 4, "idle": 3, "hurt": 3}
for sub, folder in subs.items():
    src = os.path.join(BASE, folder)
    for action, n in actions.items():
        ims = []
        for i in range(1, n + 1):
            p = os.path.join(src, f"{action}_{i}.png")
            if os.path.exists(p):
                ims.append(Image.open(p).convert("RGBA"))
        if not ims:
            continue
        # 拼成 1 行，标注序号
        w = sum(im.width for im in ims)
        h = max(im.height for im in ims) + 30
        canvas = Image.new("RGBA", (w, h), (32, 32, 40, 255))
        x = 0
        d = ImageDraw.Draw(canvas)
        for i, im in enumerate(ims):
            canvas.paste(im, (x, 0), im)
            d.text((x + 8, im.height + 4), f"{action}_{i+1}", fill=(255, 255, 255))
            x += im.width
        canvas.convert("RGB").save(os.path.join(out_dir, f"v2_{sub}_{action}.jpg"), quality=90)
        print("built", f"v2_{sub}_{action}.jpg", canvas.size)
print("DONE")
