#!/usr/bin/env python3
"""校验资产包目录结构。用法：python validate-asset-package.py <character_id_dir>"""
import json, os, sys

def main():
    if len(sys.argv) < 2:
        print("用法: python validate-asset-package.py <character_id_dir>"); sys.exit(2)
    d = sys.argv[1]
    errors = []
    if not os.path.isdir(d):
        print(f"FAIL: 目录不存在 {d}"); sys.exit(1)
    # persona
    if not os.path.exists(os.path.join(d, "persona.json")):
        errors.append("缺 persona.json")
    # metadata
    mp = os.path.join(d, "metadata.json")
    if os.path.exists(mp):
        try:
            json.load(open(mp, encoding="utf-8-sig"))
        except Exception as e:
            errors.append(f"metadata.json 非法: {e}")
    else:
        errors.append("缺 metadata.json")
    # 至少一个资产目录
    has_asset = any(os.path.isdir(os.path.join(d, x)) for x in ("portrait", "pixel", "splash", "voice"))
    if not has_asset:
        errors.append("至少需要一个资产目录 (portrait/pixel/splash/voice)")
    # 像素场景 front 锚点
    front = os.path.join(d, "pixel", "front_anchor.png")
    if os.path.isdir(os.path.join(d, "pixel")) and not os.path.exists(front):
        errors.append("pixel/ 存在但缺 front_anchor.png（锚点必须）")
    if errors:
        print("FAIL: " + d)
        for e in errors: print("  - " + e)
        return 1
    print(f"OK: {d} 资产包结构校验通过")
    return 0

if __name__ == "__main__":
    sys.exit(main())

