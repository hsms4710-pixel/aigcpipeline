# -*- coding: utf-8 -*-
"""align-game-frames.py — 把 v2 帧对齐为统一画布，解决"忽大忽小/模糊"
核心身体高度归一 + 中心X + 地面线 → 统一画布裁边 → 1:1 显示
"""
import io, os, json, collections
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(BASE, "assets", "demo", "godot-game-base")
SRC = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2")
TARGET_H = 128
MARGIN = 8

def _core_bbox(a, core_ratio=0.55, center_frac=0.55):
    """核心身体检测：只用中心区域列（排除两侧弓/披风/武器延伸），
    使 attack/walk 帧不被弓干扰导致高度误判（忽大忽小根因）"""
    h, w = a.shape
    x0 = int(w * (1 - center_frac) / 2)
    x1 = int(w * (1 + center_frac) / 2)
    center = a[:, max(x0, 0):min(x1, w)]
    rw = center.sum(axis=1)
    mx = rw.max() if rw.max() > 0 else 1
    core_rows = rw > core_ratio * mx
    if not core_rows.any():
        ys, xs = np.where(center)
        return (w / 2.0, ys.max(), ys.max() - ys.min() + 1)
    y0 = int(np.argmax(core_rows)); y1 = int(len(core_rows) - 1 - np.argmax(core_rows[::-1]))
    sub = center[y0:y1+1, :]
    ys2, xs2 = np.where(sub)
    cx = xs2.mean() + x0
    return (cx, y1, y1 - y0 + 1)

def align_frames(files, target_h=128, margin=8, core_ratio=0.55, center_frac=0.55):
    ims = [Image.open(f).convert("RGBA") for f in files]
    cores = []
    for im in ims:
        a = np.asarray(im)[:, :, 3]
        cores.append(_core_bbox(a, core_ratio, center_frac))
    scaled = []
    for im, core in zip(ims, cores):
        s = target_h / max(core[2], 1)
        nw = max(1, int(im.width * s)); nh = max(1, int(im.height * s))
        scaled.append(im.resize((nw, nh), Image.LANCZOS))
    W = max(s.width for s in scaled) + 2 * margin
    H = max(s.height for s in scaled) + 2 * margin
    out = []
    feet_stats = []
    for s, core in zip(scaled, cores):
        a = np.asarray(s)[:, :, 3]
        sc = target_h / max(core[2], 1)
        cx_s = core[0] * sc
        bottom_s = core[1] * sc
        dx = int(W // 2 - cx_s)
        dy = int((H - margin - 1) - bottom_s)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.paste(s, (dx, dy), s)
        out.append(c)
        ca = np.asarray(c)[:, :, 3]
        feet_n = int((ca[int(H*0.90):, :] > 40).sum())
        feet_stats.append(feet_n)
    return out, W, H, feet_stats

def build(style_src, out_dir, label):
    groups = collections.defaultdict(list)
    for f in sorted(os.listdir(style_src)):
        if not f.endswith(".png"):
            continue
        stem = f[:-4]
        if "_" not in stem:
            continue
        action, _, idx = stem.rpartition("_")
        if idx.isdigit():
            groups[action].append((int(idx), os.path.join(style_src, f)))
    files = []
    for action in sorted(groups):
        for _, fp in sorted(groups[action]):
            files.append(fp)
    if not files:
        print("no frames in", style_src); return
    aligned, W, H, feet_stats = align_frames(files, target_h=TARGET_H, margin=MARGIN)
    alphas = [np.asarray(im)[:, :, 3] > 40 for im in aligned]
    stack = np.stack(alphas).any(axis=0)
    ys, xs = np.where(stack)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    x0 = max(0, x0 - 2); y0 = max(0, y0 - 2)
    x1 = min(W, x1 + 2); y1 = min(H, y1 + 2)
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".png") or f.endswith(".import"):
            os.remove(os.path.join(out_dir, f))
    i = 0
    for action in sorted(groups):
        for _ in sorted(groups[action]):
            aligned[i].crop((x0, y0, x1, y1)).save(os.path.join(out_dir, f"{action}_{i}.png"), "PNG")
            i += 1
    cw, ch = x1 - x0, y1 - y0
    print(f"{label}: canvas {W}x{H} -> cropped {cw}x{ch}, frames={i}")
    low = [(os.path.basename(files[j]), feet_stats[j]) for j in range(len(feet_stats)) if feet_stats[j] < 500]
    if low:
        print(f"  [脚部不足帧] {low}")
    with io.open(os.path.join(out_dir, "canvas.json"), "w", encoding="utf-8") as f:
        json.dump({"w": int(cw), "h": int(ch), "target_h": TARGET_H}, f)

build(os.path.join(SRC, "frames_hd2d_v2"), os.path.join(GAME, "assets", "ailin"), "HD2D")
build(os.path.join(SRC, "frames_pixel_hard"), os.path.join(GAME, "assets", "ailin_pixel"), "PIXEL")
print("DONE")

