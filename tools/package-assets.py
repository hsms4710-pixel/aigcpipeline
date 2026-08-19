# -*- coding: utf-8 -*-
"""S4 打包：Spine ZIP → 资产包（trimmed atlas + 每部件图 + manifest + 校验）
用法: python package-assets.py <spine.zip> --out <dir> [--atlas-size 2048]

产物结构（供 S5 引擎 / 未来 Spine runtime 使用）：
  images/          每部件全画布图（SpinePlayer 直接使用，见 tools/spine-player.gd）
  skeleton.json    Spine 4.0 骨骼/动画（原始，与 images/ 匹配）
  atlas.png        trimmed 图集（把每部件 alpha bbox 裁剪后打包，工业级小图集）
  skeleton.atlas   Spine atlas 元数据（供官方 Spine runtime）
  manifest.json    资产清单 + 校验结果
"""
import argparse, json, os, sys, zipfile, hashlib, datetime
from PIL import Image

def pack_trimmed(imgs, size):
    """裁剪 alpha bbox → shelf 打包，返回 (atlas_img, entries[(name,x,y,w,h,orig_w,orig_h)])"""
    items = []
    for name in sorted(imgs):
        im = Image.open(imgs[name]).convert("RGBA")
        bbox = im.getbbox()
        if bbox is None:
            continue
        x0, y0, x1, y1 = bbox
        trimmed = im.crop(bbox)
        items.append({"name": name, "im": trimmed, "x0": x0, "y0": y0, "w": x1 - x0, "h": y1 - y0})
    items.sort(key=lambda it: -max(it["w"], it["h"]))
    atlas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    entries = []
    shelves = []  # (y, h, x_used)
    def find_shelf(h):
        for s in shelves:
            if h <= s["h"] and s["x"] + h <= size:  # heuristic: try fit by height
                pass
        best = None
        for s in shelves:
            if h <= s["h"] and s["x"] + s["w_avail"] >= 0:
                pass
        return best
    # simple shelf: place in row, new row when overflow
    x = y = 0; row_h = 0
    placed = []
    for it in items:
        w, h = it["w"], it["h"]
        if x + w > size:
            x = 0; y += row_h; row_h = 0
        if y + h > size:
            print(f"WARN 图集 {size} 不够大，{it['name']} 未打包"); continue
        atlas.paste(it["im"], (x, y))
        entries.append({"name": it["name"], "x": x, "y": y, "w": w, "h": h,
                        "orig_w": it["im"].width, "orig_h": it["im"].height,
                        "trim_x": it["x0"], "trim_y": it["y0"]})
        x += w; row_h = max(row_h, h)
        placed.append(it["name"])
    return atlas, entries, placed

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

    # ── 1) 每部件全画布图（SpinePlayer 使用）───────────────────────────
    imgs_out = os.path.join(args.out, "images")
    os.makedirs(imgs_out, exist_ok=True)
    for f in imgs:
        shutil_ = __import__("shutil")
        shutil_.copy(imgs[f], os.path.join(imgs_out, f))

    # ── 2) trimmed atlas（工业级小图集）────────────────────────────────
    atlas_im, entries, placed = pack_trimmed(imgs, args.atlas_size)
    atlas_png = os.path.join(args.out, "atlas.png")
    atlas_im.save(atlas_png)
    atlas_lines = [os.path.basename(atlas_png), "", f"size: {atlas_im.size[0]}, {atlas_im.size[1]}",
                   "format: RGBA8888", "filter: Linear,Linear", "repeat: none", ""]
    for e in entries:
        atlas_lines += [e["name"], "rotate: false", f"xy: {e['x']}, {e['y']}",
                        f"size: {e['w']}, {e['h']}", f"orig: {e['w']}, {e['h']}",
                        f"offset: {e['trim_x']}, {e['trim_y']}", "index: 0", ""]
    open(os.path.join(args.out, "skeleton.atlas"), "w", encoding="utf-8").write("\n".join(atlas_lines))

    # ── 3) manifest + 校验 gate ────────────────────────────────────────
    def sha(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    manifest = {
        "schema": "asset-package-v2",
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "input_zip": os.path.basename(args.zipf),
        "skeleton": {"bones": len(data.get("bones", [])), "slots": len(data.get("slots", [])),
                     "animations": list(data.get("animations", {}).keys()),
                     "images": len(imgs), "sha": sha(skeleton)},
        "atlas": {"png": os.path.basename(atlas_png), "size": atlas_im.size[0], "entries": len(entries),
                  "packed": len(placed), "sha": sha(atlas_png)},
        "images_dir": "images/", "images_count": len(imgs),
        "outputs": sorted(os.listdir(args.out)),
    }
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    ok = True
    if not data.get("bones"): print("FAIL: 无骨骼"); ok = False
    if not data.get("slots"): print("FAIL: 无插槽"); ok = False
    if not data.get("animations"): print("WARN: 无动画")
    if len(entries) < len(imgs): print(f"WARN: 图集缺 {len(imgs)-len(entries)} 张")
    print(f"OK: atlas={len(entries)}/{len(imgs)} 张打包 | images/={len(imgs)} 张 | manifest written")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
