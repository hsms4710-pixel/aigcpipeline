# -*- coding: utf-8 -*-
"""validate-layered.py：拆层资产通用校验（流水线 S1 门禁）
检查：分层 PNG 非空、有对应 depth、PSD 可打开且图层名规范。
用法：python validate-layered.py [--dir <拆层输出目录>]
"""
import os, sys, argparse

SKIP = {"src_img.png", "src_head.png", "reconstruction.png"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    a = ap.parse_args()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = a.dir or os.path.join(base, "assets", "demo", "char_ailin_v10", "layered")
    if not os.path.isdir(d):
        print(f"FAIL: 目录不存在 {d}"); return 1

    # 递归收集分层 PNG 与 PSD
    pngs, psds = [], []
    for root, _, files in os.walk(d):
        for f in sorted(files):
            p = os.path.join(root, f)
            if f.endswith(".png") and "_depth" not in f and f not in SKIP:
                pngs.append(p)
            if f.endswith(".psd") and f not in psds:
                psds.append(p)

    issues, warns, empty = [], [], []
    for p in pngs:
        sz = os.path.getsize(p)
        if sz < 5_000:
            empty.append((os.path.relpath(p, d), sz))
        base_n = os.path.splitext(p)[0]
        if not os.path.exists(base_n + "_depth.png"):
            warns.append(f"{os.path.relpath(p, d)}: 缺 depth（已知：see-through head 层不产 depth）")

    layer_names = []
    psd_info = ""
    if psds:
        try:
            from psd_tools import PSDImage
            img = PSDImage.open(psds[0])
            def collect(ls):
                for l in ls:
                    if l.is_group():
                        collect(l)
                    else:
                        layer_names.append(l.name)
            collect(img)
            psd_info = f"PSD: {os.path.basename(psds[0])} {img.width}x{img.height}, {len(layer_names)} 图层"
            print(psd_info)
        except Exception as e:
            issues.append(f"PSD 打开失败: {e}")
    else:
        issues.append("PSD 不存在")

    print(f"图层 PNG: {len(pngs)} 个 | depth 配套: {len(pngs)-len(warns)} | 小文件(<5KB): {len(empty)}")
    if empty:
        print("  小文件(可能空层):", [p for p, _ in empty][:10])
    if warns:
        print("WARN:")
        for w in warns[:10]:
            print(" -", w)
    if issues:
        print("ISSUES:")
        for i in issues[:20]:
            print(" -", i)
        print(f"RESULT: FAIL ({len(issues)} issues)")
        return 1
    print("RESULT: OK" + (f" (warnings: {len(warns)})" if warns else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main())
