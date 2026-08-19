# -*- coding: utf-8 -*-
"""split-limb.py — M0-1 程序化膝盖/肘部切分（thigh/shin、upperArm/foreArm 预研）
输入：部件 PNG（如 legwear-l.png）+ 切分比例（y 方向，膝线默认 55%）
输出：<name>_upper.png（大腿）+ <name>_lower.png（小腿）+ 重建校验报告
切分带重叠（joint_overlap_px），保证旋转时关节不露缝。
用法: python split-limb.py <part.png> [--ratio 0.55] [--overlap 14] [--out 目录]
"""
import os, sys, argparse
from PIL import Image
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="部件 PNG")
    ap.add_argument("--ratio", type=float, default=0.55, help="切分线在内容 bbox 高度比例（0.55=大腿 55%）")
    ap.add_argument("--overlap", type=int, default=14, help="关节重叠像素")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    im = Image.open(a.src).convert("RGBA")
    arr = np.asarray(im)
    alpha = arr[:, :, 3] > 10
    ys, xs = np.where(alpha)
    if len(ys) == 0:
        print("FAIL: 空部件"); return 1
    y0, y1 = ys.min(), ys.max()
    cut = y0 + int((y1 - y0) * a.ratio)
    ov = a.overlap
    upper = arr.copy(); lower = arr.copy()
    # upper: 保留 cut+ov 以上，以下清透明
    upper[cut + ov:, :, 3] = 0
    # lower: 保留 cut-ov 以下，以上清透明
    lower[:cut - ov, :, 3] = 0
    # 重叠带：两段都保留（关节覆盖）
    u_img = Image.fromarray(upper); l_img = Image.fromarray(lower)
    base = os.path.splitext(os.path.basename(a.src))[0]
    outdir = a.out or os.path.dirname(os.path.abspath(a.src))
    os.makedirs(outdir, exist_ok=True)
    up = os.path.join(outdir, base + "_thigh.png")
    lo = os.path.join(outdir, base + "_shin.png")
    u_img.save(up); l_img.save(lo)
    # 重建校验：upper∪lower 的 alpha 是否覆盖原部件
    rec = np.maximum(upper, lower)
    orig_alpha = alpha
    covered = (rec[:, :, 3] > 10)
    coverage = (covered & orig_alpha).sum() / max(1, orig_alpha.sum())
    overlap_px = ((upper[:, :, 3] > 10) & (lower[:, :, 3] > 10)).sum()
    print(f"部件 bbox y[{y0}..{y1}] 高{y1-y0} | 膝线 y={cut} (ratio {a.ratio}) | 重叠带 {ov}px")
    print(f"输出: {up} / {lo}")
    print(f"重建覆盖: {coverage*100:.1f}% | 重叠像素: {overlap_px}")
    ok = coverage >= 0.995
    print(f"RESULT: {'OK' if ok else 'WARN(覆盖不足)'}")
    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
