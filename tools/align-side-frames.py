# -*- coding: utf-8 -*-
"""align-side-frames.py — 对齐侧视帧到统一画布（清理边缘杂点 + 核心对齐）"""
import io, os, json, collections
import numpy as np
from PIL import Image

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--style", default="pixel", choices=["pixel", "hd2d"])
a = ap.parse_args()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(BASE, "assets", "demo", "godot-game-base")
SRC = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2",
                   "frames_pixel_side" if a.style == "pixel" else "frames_hd2d_side")
OUT = os.path.join(GAME, "assets", "ailin_pixel_side" if a.style == "pixel" else "ailin_hd2d_side")
TARGET_H = 128
MARGIN = 8

def _clean_alpha(a, thr=12, min_comp=3):
    """清理孤立杂点（bbox 显示整帧内容的原因）：移除连通分量过小的 alpha 区域"""
    from scipy import ndimage
    mask = a > thr
    lab, n = ndimage.label(mask)
    if n == 0:
        return a
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes >= min_comp
    keep_lab = keep[lab]
    out = np.zeros_like(a)
    out[keep_lab] = a[keep_lab]
    return out

def _core_bbox(a, core_ratio=0.55, center_frac=0.55):
    h, w = a.shape
    x0 = int(w * (1 - center_frac) / 2)
    x1 = int(w * (1 + center_frac) / 2)
    center = a[:, max(x0, 0):min(x1, w)]
    rw = center.sum(axis=1)
    mx = rw.max() if rw.max() > 0 else 1
    core_rows = rw > core_ratio * mx
    if not core_rows.any():
        return (w / 2.0, a.shape[0] - 1, 1)
    y0 = int(np.argmax(core_rows)); y1 = int(len(core_rows) - 1 - np.argmax(core_rows[::-1]))
    sub = center[y0:y1+1, :]
    ys2, xs2 = np.where(sub)
    cx = xs2.mean() + x0
    return (cx, y1, y1 - y0 + 1)

def align(files, target_h=128, margin=8):
    ims = []
    for f in files:
        im = Image.open(f).convert("RGBA")
        a = np.asarray(im).copy()
        a[:, :, 3] = _clean_alpha(a[:, :, 3])
        ims.append(Image.fromarray(a, "RGBA"))
    cores = [_core_bbox(np.asarray(im)[:, :, 3]) for im in ims]
    scaled = []
    for im, core in zip(ims, cores):
        s = target_h / max(core[2], 1)
        nw = max(1, int(im.width * s)); nh = max(1, int(im.height * s))
        scaled.append(im.resize((nw, nh), Image.LANCZOS))
    W = max(s.width for s in scaled) + 2 * margin
    H = max(s.height for s in scaled) + 2 * margin
    out = []
    for s, core in zip(scaled, cores):
        sc = target_h / max(core[2], 1)
        cx_s = core[0] * sc
        bottom_s = core[1] * sc
        dx = int(W // 2 - cx_s)
        dy = int((H - margin - 1) - bottom_s)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        c.paste(s, (dx, dy), s)
        out.append(c)
    return out, W, H

groups = collections.defaultdict(list)
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".png"): continue
    stem = f[:-4]
    action, _, idx = stem.rpartition("_")
    if idx.isdigit():
        groups[action].append((int(idx), os.path.join(SRC, f)))
files = []
for action in sorted(groups):
    for _, fp in sorted(groups[action]):
        files.append(fp)
print("files:", {k: len(v) for k, v in groups.items()})
aligned, W, H = align(files, TARGET_H, MARGIN)
# 裁到内容并集
alphas = [np.asarray(im)[:, :, 3] > 40 for im in aligned]
stack = np.stack(alphas).any(axis=0)
ys, xs = np.where(stack)
x0, y0 = max(0, xs.min()-2), max(0, ys.min()-2)
x1, y1 = min(W, xs.max()+3), min(H, ys.max()+3)
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".png") or f.endswith(".import"):
        os.remove(os.path.join(OUT, f))
i = 0
for action in sorted(groups):
    for _ in sorted(groups[action]):
        aligned[i].crop((x0, y0, x1, y1)).save(os.path.join(OUT, f"{action}_{i}.png"), "PNG")
        i += 1
print("side aligned ->", OUT, "canvas", x1-x0, "x", y1-y0, "frames", i)
