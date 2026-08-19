# -*- coding: utf-8 -*-
"""build-spine-from-image.py — 从单张 A-pose 透明小人自动切分部件并构建 Spine 骨架
阶段1: 几何切分（头/躯干/双臂/双腿，逐行段分析）
阶段2: 肢段拆分（上臂/前臂，大腿/小腿/脚）
阶段3: Spine JSON（标准骨层级 + slot + mesh attachment + 真实枢轴 _pivots）
阶段4: 基础循环动画（idle/walk/attack/hurt）→ zip
用法: python build-spine-from-image.py <png> --out <zip> [--diag <dir>]
"""
import os, sys, json, argparse, zipfile, io, math
import numpy as np
from PIL import Image

# ---------- 阶段1：切分 ----------
def load_alpha(path):
    im = Image.open(path).convert('RGBA')
    arr = np.asarray(im)
    return im, (arr[:, :, 3] > 40)

def find_neck(alpha, y0, y1):
    rw = alpha.sum(axis=1)
    hw = int(rw[y0:y1].max())
    peak = y0 + int(np.argmax(rw[y0:y1]))
    for y in range(max(peak, y0), min(y1, alpha.shape[0]) - 6):
        if all(rw[y + k] < 0.62 * hw for k in range(6)):
            return y
    return peak + int(0.32 * (y1 - y0))

def row_segments(row):
    segs = []
    in_seg = False
    for x, v in enumerate(row):
        if v and not in_seg:
            start = x; in_seg = True
        elif not v and in_seg:
            segs.append((start, x - 1)); in_seg = False
    if in_seg:
        segs.append((start, len(row) - 1))
    return segs

def find_armpit(alpha, neck, leg_start, min_w=30, need_rows=3):
    streak = 0
    for y in range(neck, leg_start):
        segs = row_segments(alpha[y])
        wide = len(segs) >= 3 and (segs[0][1]-segs[0][0]+1) >= min_w and (segs[-1][1]-segs[-1][0]+1) >= min_w
        if wide:
            streak += 1
            if streak >= need_rows:
                return y - streak + 1
        else:
            streak = 0
    return neck + int((leg_start - neck) * 0.5)

def find_leg_start(alpha, neck, y1, min_gap=14, need_rows=10):
    streak = 0
    for y in range(neck, y1):
        segs = row_segments(alpha[y])
        if len(segs) == 2 and (segs[1][0] - segs[0][1] - 1) >= min_gap:
            streak += 1
            if streak >= need_rows:
                return y - streak + 1
        else:
            streak = 0
    return y1

def segment_parts(alpha, neck, leg_start, armpit, gap):
    H, W = alpha.shape
    head = alpha.copy(); head[neck:, :] = False
    torso = np.zeros_like(alpha); left_arm = np.zeros_like(alpha); right_arm = np.zeros_like(alpha)
    left_leg = np.zeros_like(alpha); right_leg = np.zeros_like(alpha)
    for y in range(neck, leg_start):
        segs = row_segments(alpha[y])
        if not segs:
            continue
        central = None
        for s in segs:
            if s[0] <= gap <= s[1]:
                central = s; break
        if central is None:
            central = max(segs, key=lambda s: s[1]-s[0])
        for s in segs:
            if s[0] >= central[0] and s[1] <= central[1]:
                torso[y, s[0]:s[1]+1] = True
                continue
            left = s[1] < central[0]
            gap_to_c = (central[0] - s[1] - 1) if left else (s[0] - central[1] - 1)
            width = s[1] - s[0] + 1
            is_arm = (y >= armpit and width >= 8) or (gap_to_c >= 15)
            (left_arm if left else right_arm)[y, s[0]:s[1]+1] = True if is_arm else False
            if not is_arm:
                torso[y, s[0]:s[1]+1] = True
    for y in range(leg_start, H):
        for s in row_segments(alpha[y]):
            mid = (s[0]+s[1])//2
            (left_leg if mid < gap else right_leg)[y, s[0]:s[1]+1] = True
    return head, torso, left_arm, right_arm, left_leg, right_leg

# ---------- 阶段2：肢段拆分 ----------
def split_vertical(mask, ratios, overlaps=8):
    """按 y 高度比例把 mask 切成 len(ratios)+1 段，相邻段带重叠带。"""
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return [mask.copy() for _ in range(len(ratios) + 1)]
    y0, y1 = ys.min(), ys.max()
    cuts = [y0] + [y0 + int((y1 - y0) * r) for r in ratios] + [y1]
    parts = []
    for i in range(len(cuts) - 1):
        lo, hi = cuts[i], cuts[i + 1]
        p = mask.copy()
        p[:max(y0, lo - overlaps), :] = False
        p[min(y1, hi + overlaps) + 1:, :] = False
        parts.append(p)
    return parts

def bbox_of(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

def mask_to_png(mask, rgb=None):
    """mask→RGBA PNG；rgb 为原图 RGB 数组时保留颜色（否则纯黑+alpha）"""
    H, W = mask.shape
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    if rgb is not None:
        arr[..., :3] = np.where(mask[:, :, None], rgb, 0)
    return Image.fromarray(arr, 'RGBA')

# ---------- 阶段3：Spine JSON ----------
def mesh_quad(bbox, w, h):
    x0, y0, x1, y1 = bbox
    verts = [{"x": x0, "y": y0, "restX": x0, "restY": y0},
             {"x": x1, "y": y0, "restX": x1, "restY": y0},
             {"x": x1, "y": y1, "restX": x1, "restY": y1},
             {"x": x0, "y": y1, "restX": x0, "restY": y1}]
    uvs = [x0 / w, y0 / h, x1 / w, y0 / h, x1 / w, y1 / h, x0 / w, y1 / h]
    return {"type": "mesh", "name": None, "x": 0, "y": 0, "width": w, "height": h,
            "vertices": verts, "uvs": uvs, "triangles": [0, 1, 2, 0, 2, 3]}

def build_skeleton(bones_def, slots_def, W, H):
    bones = [{"name": n, "parent": p, "x": x, "y": y} for n, p, x, y in bones_def]
    slots = [{"name": nm, "bone": bn, "attachment": nm} for nm, bn in slots_def]
    return {
        "skeleton": {"spine": "4.0", "width": W, "height": H, "fps": 24, "hash": "autobuild"},
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": {}}],
        "ik": [
            {"name": "leftFootTarget", "order": 0, "bones": ["leftLeg", "leftKnee"], "target": "leftFootTarget", "bendPositive": True, "mix": 1.0, "compress": 1.0, "stretch": 1.0},
            {"name": "rightFootTarget", "order": 1, "bones": ["rightLeg", "rightKnee"], "target": "rightFootTarget", "bendPositive": True, "mix": 1.0, "compress": 1.0, "stretch": 1.0},
        ],
        "animations": {},
        "_pivots": {},
    }

def make_anim(data, clip_name, tracks, dur_ms, fps=24):
    """tracks: {bone: {prop: [(time_ms, value), ...]}} — 关键帧时间转秒（播放器/门禁均用秒）"""
    bones_t = {}
    for bone, props in tracks.items():
        bt = {}
        for prop, kfs in props.items():
            arr = []
            for t, v in kfs:
                kf = {"time": float(t) / 1000.0}
                if isinstance(v, (list, tuple)):
                    kf["x"] = float(v[0]); kf["y"] = float(v[1])
                else:
                    kf["value"] = float(v)
                kf["curve"] = [0.42, 0.0, 0.58, 1.0]
                arr.append(kf)
            bt[prop] = arr
        if bt:
            bones_t[bone] = bt
    data["animations"][clip_name] = {"bones": bones_t, "slots": {}, "duration": dur_ms / 1000.0}

# ---------- 阶段4：主流程 ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("--out", default=None)
    ap.add_argument("--diag", default=None)
    a = ap.parse_args()
    im, alpha = load_alpha(a.png)
    H, W = alpha.shape
    ys, xs = np.where(alpha)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    neck = find_neck(alpha, y0, y1)
    leg_start = find_leg_start(alpha, neck, y1)
    leg_cols = np.where(alpha[leg_start:, :].any(axis=0))[0]
    lc = (leg_cols.min() + leg_cols.max()) // 2
    gap = None
    for g in range(lc, leg_cols.min() - 1, -1):
        if not alpha[leg_start:, g].any():
            gap = g; break
    if gap is None:
        for g in range(lc, leg_cols.max() + 1):
            if not alpha[leg_start:, g].any():
                gap = g; break
    gap = gap if gap is not None else lc
    armpit = find_armpit(alpha, neck, leg_start)
    print(f"neck={neck} armpit={armpit} leg_start={leg_start} gap_x={gap}")
    head, torso, la, ra, ll, rl = segment_parts(alpha, neck, leg_start, armpit, gap)
    rgb_arr = np.asarray(im.convert('RGB'))
    # 肢段拆分
    la_u, la_f = split_vertical(la, [0.60])
    ra_u, ra_f = split_vertical(ra, [0.60])
    ll_thigh, ll_shin, ll_foot = split_vertical(ll, [0.52, 0.82])
    rl_thigh, rl_shin, rl_foot = split_vertical(rl, [0.52, 0.82])

    part_masks = {
        "topwear": torso, "face": head,
        "handwear-l": la_u, "handwear-l-forearm": la_f,
        "handwear-r": ra_u, "handwear-r-forearm": ra_f,
        "legwear-l": ll_thigh, "legwear-l-shin": ll_shin, "footwear-l": ll_foot,
        "legwear-r": rl_thigh, "legwear-r-shin": rl_shin, "footwear-r": rl_foot,
    }
    # 诊断：每个部件 bbox + 像素
    for nm, m in part_masks.items():
        bb = bbox_of(m)
        print(f"  part {nm}: bbox={bb} px={int(m.sum())}")
    if a.diag:
        os.makedirs(a.diag, exist_ok=True)
        for nm, m in part_masks.items():
            mask_to_png(m, rgb_arr).save(os.path.join(a.diag, nm + ".png"))

    # Spine JSON
    bones_def = [
        ("root", "", 0, 0), ("rig_root", "root", W/2, H*0.55),
        ("torso", "rig_root", 0, 0), ("head", "rig_root", 0, -H*0.28),
        ("leftArm", "root", 0, 0), ("rightArm", "root", 0, 0),
        ("leftElbow", "leftArm", 0, 0), ("rightElbow", "rightArm", 0, 0),
        ("leftLeg", "rig_root", 0, 0), ("rightLeg", "rig_root", 0, 0),
        ("leftKnee", "leftLeg", 0, 0), ("rightKnee", "rightLeg", 0, 0),
        ("leftFootTarget", "leftKnee", 0, 0), ("rightFootTarget", "rightKnee", 0, 0),
    ]
    slots_def = [
        ("topwear", "torso"), ("face", "head"),
        ("handwear-l", "leftArm"), ("handwear-l-forearm", "leftElbow"),
        ("handwear-r", "rightArm"), ("handwear-r-forearm", "rightElbow"),
        ("legwear-l", "leftLeg"), ("legwear-l-shin", "leftKnee"), ("footwear-l", "leftFootTarget"),
        ("legwear-r", "rightLeg"), ("legwear-r-shin", "rightKnee"), ("footwear-r", "rightFootTarget"),
    ]
    data = build_skeleton(bones_def, slots_def, W, H)
    atts = data["skins"][0]["attachments"]
    for nm, m in part_masks.items():
        bb = bbox_of(m)
        if bb is None:
            continue
        att = mesh_quad(bb, W, H)
        att["name"] = nm
        atts[nm] = {nm: att}
    # 枢轴
    def closest_point(mask, target):
        ys2, xs2 = np.where(mask)
        if len(xs2) == 0:
            return (target[0], target[1])
        d = (xs2 - target[0])**2 + (ys2 - target[1])**2
        i = int(np.argmin(d))
        return (int(xs2[i]), int(ys2[i]))
    # 肩 = 手臂内容中离躯干最近的点
    torso_bb = bbox_of(torso)
    torso_center = ((torso_bb[0]+torso_bb[2])//2, (torso_bb[1]+torso_bb[3])//2)
    def nearest_torso(mask):
        ys2, xs2 = np.where(mask)
        if len(xs2) == 0:
            return (0, 0)
        d = (xs2 - torso_center[0])**2 + (ys2 - torso_center[1])**2
        i = int(np.argmin(d))
        return (int(xs2[i]), int(ys2[i]))
    pv = data["_pivots"]
    pv["leftArm"] = list(nearest_torso(la_u))
    pv["rightArm"] = list(nearest_torso(ra_u))
    pv["leftElbow"] = list(closest_point(la_f, pv["leftArm"]))
    pv["rightElbow"] = list(closest_point(ra_f, pv["rightArm"]))
    def top_center(bb):
        return [(bb[0] + bb[2]) // 2, bb[1]]
    pv["leftKnee"] = top_center(bbox_of(ll_shin))
    pv["rightKnee"] = top_center(bbox_of(rl_shin))
    pv["leftFootTarget"] = top_center(bbox_of(ll_foot))
    pv["rightFootTarget"] = top_center(bbox_of(rl_foot))
    print("pivots:", json.dumps(pv, ensure_ascii=False))
    # 基础动画（M0-12 规范关键帧：walk 4 姿态摆臂 / attack 蓄力+转体 / hurt 受击后仰 / idle 呼吸）
    D = 2000.0
    def c(D, *pts):
        out = [list(p) for p in pts]
        out.append([D, pts[0][1]])
        return out
    # idle：呼吸（torso 缩放+微摆）、头微动、手臂轻微起伏（不僵硬）
    make_anim(data, "idle", {
        "torso": {"rotate": c(D, (0, 0), (500, -2), (1000, 0), (1500, 2)),
                  "scale": c(D, (0, (1, 1)), (500, (1, 1.03)), (1000, (1, 1)), (1500, (1, 0.98)))},
        "head": {"rotate": c(D, (0, 0), (500, -2), (1000, 0), (1500, 2))},
        "leftArm": {"rotate": c(D, (0, 0), (500, 3), (1000, 0), (1500, -3))},
        "rightArm": {"rotate": c(D, (0, 0), (500, -3), (1000, 0), (1500, 3))},
    }, D)
    # walk：4 姿态（Contact/Down/Passing/Up）；手臂=自然摆臂（与腿反相，幅度小）
    # 注意：正面视角，摆臂体现为轻微外摆+节奏；腿前后交替（图像平面内左右摆）
    make_anim(data, "walk", {
        "leftLeg":  {"rotate": c(D, (0, -22), (500, -8), (1000, 14), (1500, 4))},
        "rightLeg": {"rotate": c(D, (0, 22), (500, 8), (1000, -14), (1500, -4))},
        "leftKnee": {"rotate": c(D, (0, 6), (500, 30), (1000, 8), (1500, 26))},
        "rightKnee":{"rotate": c(D, (0, 26), (500, 8), (1000, 30), (1500, 8))},
        "leftArm":  {"rotate": c(D, (0, 12), (500, -6), (1000, -12), (1500, 6))},
        "rightArm": {"rotate": c(D, (0, -12), (500, 6), (1000, 12), (1500, -6))},
        "torso": {"rotate": c(D, (0, 0), (500, -3), (1000, 0), (1500, 3)),
                  "translate": c(D, (0, (0, 0)), (500, (0, 5)), (1000, (0, 0)), (1500, (0, -4)))},
        "head": {"rotate": c(D, (0, 0), (500, 2), (1000, 0), (1500, -2))},
    }, D)
    # attack：蓄力（后拉+转体）→ 挥击（明确方向+前倾）→ 跟随回位
    make_anim(data, "attack", {
        "rightArm":  {"rotate": c(D, (0, 0), (300, -30), (600, 55), (900, 15), (1200, 0))},
        "rightElbow": {"rotate": c(D, (0, 0), (300, -65), (600, -8), (900, -18), (1200, 0))},
        "leftArm":   {"rotate": c(D, (0, 0), (300, 18), (600, -22), (900, -8), (1200, 0))},
        "leftElbow": {"rotate": c(D, (0, 0), (300, 20), (600, 10), (900, 5), (1200, 0))},
        "torso": {"rotate": c(D, (0, 0), (300, 12), (600, -16), (900, -4), (1200, 0)),
                  "translate": c(D, (0, (0, 0)), (300, (0, 3)), (600, (4, -2)), (900, (1, 0)), (1200, (0, 0)))},
        "head": {"rotate": c(D, (0, 0), (300, 6), (600, -10), (900, -3), (1200, 0))},
        "leftLeg": {"rotate": c(D, (0, 0), (300, 8), (600, -14), (900, -6), (1200, 0))},
        "rightLeg": {"rotate": c(D, (0, 0), (300, -4), (600, 10), (900, 4), (1200, 0))},
    }, D)
    # hurt：受击后仰（躯干+头滞后）+ 双臂外甩 + 弹性回位
    make_anim(data, "hurt", {
        "torso": {"rotate": c(D, (0, 0), (100, 14), (400, 18), (800, -4), (1200, 0)),
                  "translate": c(D, (0, (0, 0)), (100, (0, -3)), (400, (0, -5)), (800, (0, -1)), (1200, (0, 0)))},
        "head": {"rotate": c(D, (0, 0), (200, 20), (500, 24), (900, -4), (1300, 0))},
        "leftArm": {"rotate": c(D, (0, 0), (150, 24), (500, 30), (900, -8), (1300, 0))},
        "rightArm": {"rotate": c(D, (0, 0), (150, -24), (500, -30), (900, 8), (1300, 0))},
    }, D)

    # 写 zip
    out = a.out or os.path.splitext(a.png)[0] + "_spine.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("skeleton.json", json.dumps(data, ensure_ascii=False))
        for nm, m in part_masks.items():
            buf = io.BytesIO()
            mask_to_png(m, rgb_arr).save(buf, format="PNG")
            z.writestr(f"images/{nm}.png", buf.getvalue())
    print("OUT:", out)
    print("RESULT: OK")

if __name__ == "__main__":
    main()