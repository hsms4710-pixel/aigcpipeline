"""generate-pixel-tiles.py — G1 v2：单纹理无缝瓦片方案
每类地形生成 1 张 512x512 无缝 repeating texture → offset-wrap 完美无缝
→ 中值降噪 → 16x16 最近邻降采样 + 调色板量化 → 4 个程序化变体（原版/hflip/vflip/rot180）
用法: python tools/generate-pixel-tiles.py --terrains grass dirt
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageFilter
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROMPT_TMPL = (
    "A seamless tileable 2D pixel art {t} texture for a top-down SNES-style RPG overworld, "
    "512x512 px, perfectly repeating pattern with matching edges (left==right, top==bottom), "
    "flat top-down ground view, {desc}, crisp hard pixel edges, limited 16-color palette, "
    "organized pixel clusters (no scattered single-pixel noise), no characters, no objects, "
    "no grid lines, no text, no anti-aliasing, no blur."
)
DESC = {
    "grass": "green grass with subtle lighter blades and darker soil patches",
    "dirt": "brown dirt with small stones and darker moist patches",
    "stone": "grey flagstone blocks with visible cracks between them",
    "water": "blue water with gentle horizontal wave lines and lighter highlights",
    "sand": "tan sand with tiny darker speckles",
}

def make_seamless(im, band_ratio=0.25):
    """offset-wrap 完美无缝：180° 翻转副本，边缘带加宽混合"""
    w, h = im.size
    out = im.convert("RGB")
    arr = out.load()
    off = Image.new("RGB", (w, h))
    off_l = off.load()
    for y in range(h):
        for x in range(w):
            off_l[(x + w//2) % w, (y + h//2) % h] = arr[x, y]
    band = max(4, int(w * band_ratio))
    for y in range(h):
        for x in range(band):
            for (xx, yy) in ((x, y), (w-1-x, y), (x, h-1-y), (w-1-x, h-1-y)):
                c1 = arr[xx, yy]; c2 = off_l[xx, yy]
                arr[xx, yy] = tuple((c1[i] + c2[i]) // 2 for i in range(3))
    return out

def tile_seam_diff(im):
    w, h = im.size
    px = im.convert("RGB")
    left = [px.getpixel((0, y)) for y in range(h)]
    right = [px.getpixel((w-1, y)) for y in range(h)]
    top = [px.getpixel((x, 0)) for x in range(w)]
    bottom = [px.getpixel((x, h-1)) for x in range(w)]
    def d(a, b):
        total = 0
        for p, q in zip(a, b):
            total += abs(p[0]-q[0]) + abs(p[1]-q[1]) + abs(p[2]-q[2])
        return total / (len(a) * 3)
    return d(left, right), d(top, bottom)

def pixelize(im, target):
    im = im.convert("RGB").filter(ImageFilter.MedianFilter(3))
    small = im.resize((target, target), Image.NEAREST)
    return small.quantize(colors=16, method=Image.Quantize.MEDIANCUT).convert("RGB")

def variants(im):
    """4 个无缝变体：原版 / 水平翻转 / 垂直翻转 / 旋转180"""
    return [im, im.transpose(Image.FLIP_LEFT_RIGHT),
            im.transpose(Image.FLIP_TOP_BOTTOM), im.rotate(180)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--terrains", nargs="+", default=["grass", "dirt"])
    ap.add_argument("--tile", type=int, default=16)
    ap.add_argument("--size", default="512x512")
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip-gen", action="store_true")
    args = ap.parse_args()
    tile = args.tile
    out_dir = args.out or os.path.join(REPO, "assets", "demo", "godot-game-base", "assets", "tiles_ai")
    raw_dir = os.path.join(out_dir, "_raw")
    os.makedirs(raw_dir, exist_ok=True)

    tiles, report, all_meta = [], [], {}
    idx = 0
    for t in args.terrains:
        src = os.path.join(raw_dir, f"tex_{t}.png")
        if not args.skip_gen:
            prompt = PROMPT_TMPL.format(t=t, desc=DESC.get(t, "natural ground texture"))
            print(f"[G1] 生图 {t}: {prompt[:100]}...")
            n, dt = gen_image(prompt, src, size=args.size, quality="high")
            print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
        im = Image.open(src).convert("RGB")
        # 无缝门禁（512px 上测）→ 需要则修复
        lr, tb = tile_seam_diff(im)
        fixed = make_seamless(im) if (lr > 6 or tb > 6) else im
        lr2, tb2 = tile_seam_diff(fixed)
        p = pixelize(fixed, tile)
        for vi, v in enumerate(variants(p)):
            name = f"tile_{t}_{vi}"
            v.save(os.path.join(out_dir, f"{name}.png"))
            tiles.append((t, name))
            idx += 1
        report.append({"terrain": t, "seam_lr_raw": round(lr,2), "seam_tb_raw": round(tb,2),
                       "seam_lr_fixed": round(lr2,2), "seam_tb_fixed": round(tb2,2)})
        all_meta[t] = {"prompt": PROMPT_TMPL.format(t=t, desc=DESC.get(t, "")),
                       "generated": time.strftime("%Y-%m-%d %H:%M:%S")}

    # atlas：按地形分组 4 变体排成 4 列，行 = 地形
    n_terr = len(args.terrains)
    atlas = Image.new("RGB", (4*tile, n_terr*tile), (0,0,0))
    for r in range(n_terr):
        for c in range(4):
            p = os.path.join(out_dir, f"tile_{args.terrains[r]}_{c}.png")
            atlas.paste(Image.open(p), (c*tile, r*tile))
    atlas.save(os.path.join(out_dir, "atlas.png"))
    meta = {"tile_size": tile, "src_ts": tile, "cols": 4, "rows": n_terr,
            "scheme": "single-texture + offset-wrap seamless + 4 procedural variants",
            "report": report, "meta": all_meta}
    with open(os.path.join(out_dir, "atlas.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n[G1 v2] 产物: {out_dir}")
    print(f"[G1 v2] atlas {4*tile}x{n_terr*tile}px, 瓦片 {tile}px, {n_terr*4} 块")
    for r in report:
        print(f"  {r['terrain']}: lr {r['seam_lr_fixed']} tb {r['seam_tb_fixed']} "
              f"({'PASS' if r['seam_lr_fixed']<=6 and r['seam_tb_fixed']<=6 else 'FAIL'})")

if __name__ == "__main__":
    main()