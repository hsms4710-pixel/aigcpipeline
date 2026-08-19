# -*- coding: utf-8 -*-
"""split-spine-arm.py — M0-6 手臂弯曲集成：把 Spine zip 中 handwear 拆 upper/forearm
- 沿手臂主轴（PCA）在 55% 处切分（肩→肘→手），14px 关节重叠带
- 原 slot 保留（upper，继续挂 leftArm/rightArm），新增 <part>-forearm slot（mesh quad，绑定 leftElbow/rightElbow）
- 重建 zip（原文件保留，替换/新增图像 + skeleton.json）
用法: python split-spine-arm.py <spine.zip> [--out zip] [--ratio 0.55] [--overlap 14]
"""
import os, sys, json, zipfile, argparse, tempfile, shutil
from PIL import Image
import numpy as np

def split_img(im, ratio, overlap):
    """im: RGBA Image（全画布）→ (upper, forearm, meta)。沿主轴、以肩端为 0 切分。"""
    arr = np.asarray(im).astype(np.float32)
    alpha = arr[:, :, 3] > 10
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return None, None, None
    H, W = arr.shape[:2]
    pts = np.column_stack([xs, ys]).astype(float)
    pc = pts - pts.mean(axis=0)
    cov = np.cov(pc.T)
    evals, evecs = np.linalg.eigh(cov)
    m = evecs[:, np.argmax(evals)]
    # 锚点 = 最顶端内容像素（手臂下垂时即肩端）
    anchor = pts[np.argmin(ys)]
    t_raw = (pts - anchor) @ m
    tmin, tmax = t_raw.min(), t_raw.max()
    if tmax - tmin < 5:
        return None, None, None
    # 若主轴指向肩端（锚点 t 在远端）→ 反转，使锚点=0 侧
    if t_raw[np.argmin(ys)] > (tmin + tmax) / 2:
        m = -m
        t_raw = (pts - anchor) @ m
        tmin, tmax = t_raw.min(), t_raw.max()
    t = t_raw - tmin
    range_len = float(t.max())
    cut = range_len * ratio
    # 全画布投影
    gy, gx = np.mgrid[0:H, 0:W]
    gpts = np.column_stack([gx.ravel(), gy.ravel()])
    gtop = ((gpts - anchor) @ m - tmin).reshape(H, W)
    upper = arr.copy(); forearm = arr.copy()
    upper[gtop >= (cut + overlap / 2.0), 3] = 0
    forearm[gtop <= (cut - overlap / 2.0), 3] = 0
    meta = {"cut": cut, "range": range_len, "anchor": (float(anchor[0]), float(anchor[1])),
            "main": (float(m[0]), float(m[1]))}
    return Image.fromarray(upper.astype(np.uint8)), Image.fromarray(forearm.astype(np.uint8)), meta

def mesh_quad(bbox, w, h):
    x0, y0, x1, y1 = bbox
    verts = [{"x": x0, "y": y0, "restX": x0, "restY": y0},
             {"x": x1, "y": y0, "restX": x1, "restY": y0},
             {"x": x1, "y": y1, "restX": x1, "restY": y1},
             {"x": x0, "y": y1, "restX": x0, "restY": y1}]
    uvs = [x0 / w, y0 / h, x1 / w, y0 / h, x1 / w, y1 / h, x0 / w, y1 / h]
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
    parts = [("handwear-l", "leftArm", "leftElbow"), ("handwear-r", "rightArm", "rightElbow")]
    bone_names = [b.get("name") for b in data.get("bones", [])]
    changed = []
    pivots = {}
    for part, arm_bone, elbow_bone in parts:
        img_path = os.path.join(imgs_dir, part + ".png")
        if not os.path.isfile(img_path):
            print(f"WARN: 缺 {part}.png，跳过"); continue
        if elbow_bone not in bone_names:
            print(f"WARN: 缺骨 {elbow_bone}，跳过 {part}"); continue
        im = Image.open(img_path).convert("RGBA")
        upper, forearm, meta = split_img(im, a.ratio, a.overlap)
        if upper is None or forearm is None:
            print(f"WARN: {part} 主轴过短/为空，跳过"); continue
        # M0-11 真实关节枢轴：肩=手臂根端（topmost 内容点）
        ax, ay = meta["anchor"]; mx, my = meta["main"]; cut = meta["cut"]
        pivots[arm_bone] = [round(ax, 1), round(ay, 1)]
        # 肘=前臂内容中离肩最近的点（真实附着点，保证在部件上）
        fa = np.asarray(forearm)
        fys, fxs = np.where(fa[:, :, 3] > 10)
        if len(fxs) > 0:
            d = (fxs - ax) ** 2 + (fys - ay) ** 2
            i = int(np.argmin(d))
            pivots[elbow_bone] = [round(float(fxs[i]), 1), round(float(fys[i]), 1)]
        else:
            pivots[elbow_bone] = [round(ax + mx * cut, 1), round(ay + my * cut, 1)]
        # 1) 替换原图为 upper（原 slot 保留）
        upper.save(img_path)
        # 2) 新增 forearm 图像
        forearm_name = part + "-forearm"
        forearm.save(os.path.join(imgs_dir, forearm_name + ".png"))
        # 3) 新增 slot（紧跟原 slot 之后，绑定肘骨）
        slots = data.get("slots", [])
        idx = next((i for i, s in enumerate(slots) if s.get("name") == part), None)
        new_slot = {"name": forearm_name, "bone": elbow_bone, "attachment": forearm_name}
        if idx is not None:
            slots.insert(idx + 1, new_slot)
        else:
            slots.append(new_slot)
        # 4) 新增 mesh attachment（forearm 内容 bbox quad）
        fa = np.asarray(forearm)
        sa = fa[:, :, 3] > 10
        ys2, xs2 = np.where(sa)
        if len(xs2) == 0:
            print(f"WARN: {forearm_name} 无内容"); continue
        bbox = (int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max()))
        att = mesh_quad(bbox, img_w, img_h)
        att["name"] = forearm_name
        data["skins"][0]["attachments"].setdefault(forearm_name, {})[forearm_name] = att
        changed.append((part, forearm_name, meta))
    # M0-9 脚部重绑：footwear 绑定到 footTarget 骨（脚独立驱动、可锁地），与运行时 foot 拆分一致
    foot_rebind = []
    slots = data.get("slots", [])
    foot_map = {"footwear-l": "leftFootTarget", "footwear-r": "rightFootTarget"}
    for s in slots:
        nm = s.get("name", "")
        tgt = foot_map.get(nm)
        if tgt and tgt in bone_names and s.get("bone") != tgt:
            foot_rebind.append((nm, s.get("bone"), tgt))
            s["bone"] = tgt
    if not changed and not foot_rebind:
        print("RESULT: 无部件可拆分"); shutil.rmtree(tmp); return 2
    # M0-11 膝/踝枢轴（内容感知）
    def _content_top_center(png):
        a = np.asarray(Image.open(os.path.join(imgs_dir, png)).convert("RGBA"))
        ys, xs = np.where(a[:, :, 3] > 10)
        if len(xs) == 0:
            return None
        return [round(float((xs.min() + xs.max()) / 2), 1), round(float(ys.min()), 1)]
    for shin_name, knee_bone in [("legwear-l-shin", "leftKnee"), ("legwear-r-shin", "rightKnee")]:
        p = shin_name + ".png"
        if os.path.isfile(os.path.join(imgs_dir, p)):
            tc = _content_top_center(p)
            if tc:
                pivots[knee_bone] = tc
    for foot_name, foot_bone in [("footwear-l", "leftFootTarget"), ("footwear-r", "rightFootTarget")]:
        p = foot_name + ".png"
        if os.path.isfile(os.path.join(imgs_dir, p)):
            tc = _content_top_center(p)
            if tc:
                pivots[foot_bone] = tc
    if pivots:
        data["_pivots"] = pivots
    with open(sk, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    out = a.out or os.path.splitext(a.src)[0] + "_arm_split.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmp):
            for fn in files:
                p = os.path.join(root, fn)
                z.write(p, os.path.relpath(p, tmp))
    for part, forearm_name, meta in changed:
        print(f"拆分: {part} → upper(原slot) + {forearm_name}，肘线 t={meta['cut']:.0f}/{meta['range']:.0f} 主轴=({meta['main'][0]:.2f},{meta['main'][1]:.2f})")
    for nm, ob, nb in foot_rebind:
        print(f"重绑: {nm} {ob} → {nb}")
    print("pivots:", json.dumps(pivots, ensure_ascii=False))
    print("输出:", out)
    print("RESULT: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())