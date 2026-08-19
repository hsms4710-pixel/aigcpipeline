# -*- coding: utf-8 -*-
"""split-spine-limb.py — M0-1 膝盖弯曲集成：把 Spine zip 中 legwear 拆 thigh/shin
- 拆分图像（内容 bbox 55% 处，14px 重叠带）
- 原 slot 保留（thigh），新增 <part>-shin slot（mesh quad，绑定 leftKnee/rightKnee）
- 重建 zip（原文件保留，替换/新增图像 + skeleton.json）
用法: python split-spine-limb.py <spine.zip> [--out zip] [--ratio 0.55] [--overlap 14]
"""
import os, sys, json, zipfile, argparse, tempfile, shutil
from PIL import Image
import numpy as np

def split_img(im, ratio, overlap):
    """im: RGBA Image（全画布）→ (thigh, shin, knee_line)"""
    arr = np.asarray(im)
    alpha = arr[:, :, 3] > 10
    ys, _ = np.where(alpha)
    if len(ys) == 0:
        return None, None, None
    y0, y1 = ys.min(), ys.max()
    cut = y0 + int((y1 - y0) * ratio)
    thigh = arr.copy(); shin = arr.copy()
    thigh[cut + overlap:, :, 3] = 0
    shin[:cut - overlap, :, 3] = 0
    return Image.fromarray(thigh), Image.fromarray(shin), (y0, y1, cut)

def mesh_quad(bbox, w, h):
    x0, y0, x1, y1 = bbox
    verts = [{"x": x0, "y": y0, "restX": x0, "restY": y0},
             {"x": x1, "y": y0, "restX": x1, "restY": y0},
             {"x": x1, "y": y1, "restX": x1, "restY": y1},
             {"x": x0, "y": y1, "restX": x0, "restY": y1}]
    uvs = [x0/w, y0/h, x1/w, y0/h, x1/w, y1/h, x0/w, y1/h]
    return {"type": "mesh", "name": None, "x": 0, "y": 0, "width": w, "height": h,
            "vertices": verts, "uvs": uvs, "triangles": [0, 1, 2, 0, 2, 3]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    ap.add_argument("--ratio", type=float, default=0.55)
    ap.add_argument("--overlap", type=int, default=14)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(a.src) as z:
        z.extractall(tmp)
    sk = os.path.join(tmp, "skeleton.json")
    data = json.load(open(sk, encoding="utf-8"))
    imgs_dir = os.path.join(tmp, "images")
    img_w = img_h = 1280
    parts = [("legwear-l", "leftLeg", "leftKnee"), ("legwear-r", "rightLeg", "rightKnee")]
    bone_names = [b.get("name") for b in data.get("bones", [])]
    changed = []
    for part, leg_bone, knee_bone in parts:
        img_path = os.path.join(imgs_dir, part + ".png")
        if not os.path.isfile(img_path):
            print(f"WARN: 缺 {part}.png，跳过"); continue
        if knee_bone not in bone_names:
            print(f"WARN: 缺骨 {knee_bone}，跳过 {part}"); continue
        im = Image.open(img_path).convert("RGBA")
        thigh, shin, (y0, y1, cut) = split_img(im, a.ratio, a.overlap)
        if thigh is None:
            print(f"WARN: {part} 为空，跳过"); continue
        # 1) 替换原图为 thigh（thigh 保留原 slot 名）
        thigh.save(img_path)
        # 2) 新增 shin 图像
        shin_name = part + "-shin"
        shin.save(os.path.join(imgs_dir, shin_name + ".png"))
        # 3) 新增 slot（紧跟原 slot 之后）
        slots = data.get("slots", [])
        idx = next((i for i, s in enumerate(slots) if s.get("name") == part), None)
        new_slot = {"name": shin_name, "bone": knee_bone, "attachment": shin_name}
        if idx is not None:
            slots.insert(idx + 1, new_slot)
        else:
            slots.append(new_slot)
        # 4) 新增 mesh attachment（shin bbox quad）
        shin_arr = np.asarray(shin)
        sa = shin_arr[:, :, 3] > 10
        ys2, xs2 = np.where(sa)
        if len(xs2) == 0:
            print(f"WARN: {shin_name} 无内容"); continue
        bbox = (int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max()))
        att = mesh_quad(bbox, img_w, img_h)
        att["name"] = shin_name
        data["skins"][0]["attachments"].setdefault(shin_name, {})[shin_name] = att
        changed.append((part, shin_name, cut))
    if not changed:
        print("RESULT: 无部件可拆分"); shutil.rmtree(tmp); return 2
    with open(sk, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    out = a.out or os.path.splitext(a.src)[0] + "_limb_split.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmp):
            for fn in files:
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, tmp))
    for part, shin_name, cut in changed:
        print(f"拆分: {part} → thigh(原slot) + {shin_name}，膝线 y={cut}")
    print("输出:", out)
    print("RESULT: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
