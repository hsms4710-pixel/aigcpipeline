# -*- coding: utf-8 -*-
"""S4 打包：Spine ZIP → atlas 图集 + 资产清单 manifest + 校验
用法: python package-assets.py <spine.zip> --out <dir> [--atlas-size 2048]
"""
import argparse, json, os, sys, zipfile, hashlib, datetime

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zipf")
    ap.add_argument("--out", required=True)
    ap.add_argument("--atlas-size", type=int, default=2048)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    raw = os.path.join(args.out, "raw")
    os.makedirs(raw, exist_ok=True)

    with zipfile.ZipFile(args.zipf) as z:
        z.extractall(raw)

    skeleton = os.path.join(raw, "skeleton.json")
    if not os.path.isfile(skeleton):
        # 尝试从子目录找
        for root, _, files in os.walk(raw):
            if "skeleton.json" in files:
                skeleton = os.path.join(root, "skeleton.json"); break
    if not os.path.isfile(skeleton):
        print("ERROR: skeleton.json 缺失"); sys.exit(1)

    data = json.load(open(skeleton, encoding="utf-8"))
    imgs = {}
    img_dir = os.path.join(raw, "images")
    if os.path.isdir(img_dir):
        for f in os.listdir(img_dir):
            imgs[f] = os.path.join(img_dir, f)
    print(f"bones={len(data.get('bones', []))} slots={len(data.get('slots', []))} anims={list(data.get('animations', {}).keys())} images={len(imgs)}")

    # ── 打包 atlas（PIL 网格打包 + Spine .atlas）──────────────────────
    from PIL import Image
    size = args.atlas_size
    atlas_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    entries = []
    x = y = 0
    max_h = 0
    for name in sorted(imgs):
        im = Image.open(imgs[name]).convert("RGBA")
        w, h = im.size
        if w > size or h > size:
            print(f"WARN {name} {w}x{h} 超过图集尺寸，跳过"); continue
        if x + w > size:
            x = 0; y += max_h; max_h = 0
        if y + h > size:
            print(f"WARN 图集 {size} 不够大，{name} 未打包"); continue
        atlas_im.paste(im, (x, y))
        entries.append({"name": name, "x": x, "y": y, "w": w, "h": h,
                        "orig_w": w, "orig_h": h, "offset_x": 0, "offset_y": 0, "rotate": False})
        x += w; max_h = max(max_h, h)

    atlas_png = os.path.join(args.out, "skeleton.png")
    atlas_im.save(atlas_png)
    # Spine .atlas 格式
    atlas_lines = [os.path.basename(atlas_png), "", f"size: {size}, {size}", "format: RGBA8888",
                   "filter: Linear,Linear", "repeat: none", ""]
    for e in entries:
        atlas_lines += [e["name"], "rotate: false", f"xy: {e['x']}, {e['y']}",
                        f"size: {e['w']}, {e['h']}", f"orig: {e['orig_w']}, {e['orig_h']}",
                        f"offset: {e['offset_x']}, {e['offset_y']}", "index: 0", ""]
    open(os.path.join(args.out, "skeleton.atlas"), "w", encoding="utf-8").write("\n".join(atlas_lines))

    # ── manifest ──────────────────────────────────────────────────────
    def sha(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    manifest = {
        "schema": "asset-package-v1",
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "input_zip": os.path.basename(args.zipf),
        "skeleton": {"bones": len(data.get("bones", [])), "slots": len(data.get("slots", [])),
                     "animations": list(data.get("animations", {}).keys()),
                     "images": len(imgs), "sha": sha(skeleton)},
        "atlas": {"png": os.path.basename(atlas_png), "size": size, "entries": len(entries),
                  "sha": sha(atlas_png)},
        "outputs": sorted(os.listdir(args.out)),
    }
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ── 校验 gate ─────────────────────────────────────────────────────
    ok = True
    if not data.get("bones"): print("FAIL: 无骨骼"); ok = False
    if not data.get("slots"): print("FAIL: 无插槽"); ok = False
    if not data.get("animations"): print("WARN: 无动画"); 
    if len(entries) < len(imgs): print(f"WARN: 图集缺 {len(imgs)-len(entries)} 张"); 
    print(f"OK: atlas={len(entries)} entries, manifest written")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
