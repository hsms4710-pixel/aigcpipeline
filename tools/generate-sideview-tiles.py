"""generate-sideview-tiles.py — G1 v3：HD-2D 横板地形瓦片集（匹配 2D 横板 demo + 艾琳 HD-2D 风格）
生成 1024x1024 横板平台游戏地形瓦片集（8x8 网格，每块 128x128）→ 切块 → atlas
参考: ai-pixel-art-image-generation、agent-sprite-forge（Godot TileMap 落地）
用法: python tools/generate-sideview-tiles.py [--grid 8] [--tile 128] [--out <dir>]
"""
import os, sys, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROMPT = (
    "A 2D side-scrolling platformer game terrain tileset, HD-2D art style similar to Octopath Traveler, "
    "exactly 8x8 grid of 64 square tiles (128x128 px each) for building platformer levels. "
    "Include tile types: grass-topped dirt ground blocks (green grass strip on top edge, brown dirt body), "
    "plain dirt blocks, grey stone/brick blocks, wooden platform blocks, background foliage tiles, "
    "all drawn in a consistent painterly pixel style, crisp edges, no characters, no enemies, "
    "no grid lines, no borders between tiles, no text, no watermark, no UI."
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=int, default=8)
    ap.add_argument("--tile", type=int, default=128)
    ap.add_argument("--out", default=None)
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--skip-gen", action="store_true")
    args = ap.parse_args()
    grid, tile = args.grid, args.tile
    out_dir = args.out or os.path.join(REPO, "assets", "demo", "godot-game-base", "assets", "tiles_hd2d")
    raw_dir = os.path.join(out_dir, "_raw")
    os.makedirs(raw_dir, exist_ok=True)
    src = os.path.join(raw_dir, "sideview_src.png")

    if not args.skip_gen:
        print("[G1 v3] 生图 (1024, 横板地形瓦片集)...")
        n, dt = gen_image(PROMPT, src, size=args.size, quality="high")
        print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
    else:
        print("[G1 v3] skip-gen，使用已有源图", src)

    im = Image.open(src).convert("RGB")
    print("[G1 v3] 源图尺寸:", im.size)
    per_tile = im.size[0] // grid
    os.makedirs(out_dir, exist_ok=True)
    tiles = []
    for r in range(grid):
        for c in range(grid):
            t = im.crop((c*per_tile, r*per_tile, (c+1)*per_tile, (r+1)*per_tile))
            name = f"tile_{r}_{c}"
            t.save(os.path.join(out_dir, f"{name}.png"))
            tiles.append((r, c, name))
    atlas = Image.new("RGB", (grid*tile, grid*tile), (0,0,0))
    for r, c, name in tiles:
        atlas.paste(Image.open(os.path.join(out_dir, f"{name}.png")), (c*tile, r*tile))
    atlas.save(os.path.join(out_dir, "atlas.png"))
    meta = {"tile_size": tile, "cols": grid, "rows": grid, "src": src,
            "prompt": PROMPT, "generated": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(out_dir, "atlas.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[G1 v3] 产物: {out_dir}")
    print(f"[G1 v3] atlas {grid*tile}x{grid*tile}px, 瓦片 {tile}px, {grid*grid} 块")
    print("[G1 v3] 下一步: vision 验收瓦片类型/风格 -> 挑选可用瓦片 -> Godot TileMapLayer")

if __name__ == "__main__":
    main()