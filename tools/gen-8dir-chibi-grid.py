"""gen-8dir-chibi-grid.py — H1 v2：sprute 式网格模板法生成 8 向精灵
生成 4x2 网格（每格 512x512，同角色 8 个方向）→ 切分 → 背景 flood-fill 抠透明 → 对齐
用法: python tools/gen-8dir-chibi-grid.py [--skip-gen]
"""
import os, sys, time, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHOR = os.path.join(REPO, "assets", "demo", "char_ailin_chibi_v4", "portrait", "front_b.png")
OUT_DIR = os.path.join(REPO, "assets", "demo", "char_ailin_chibi_8dir")

# 8 向布局：4 列 x 2 行（行优先）
ORDER = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]

PROMPT = (
    "A sprite sheet of ONE pixel-art chibi character in EXACTLY 8 cells arranged in a 2-row x 4-column grid, "
    "4 cells per row, 2 rows, each cell showing the SAME character (same face, silver-white hair, green eyes, "
    "dark green ranger outfit, cape, bow) from a DIFFERENT viewing direction. "
    "Row 1 (top row) left to right: facing down, facing down-left (3/4), facing left (profile), facing up-left (3/4 back). "
    "Row 2 (bottom row) left to right: facing up (from behind), facing up-right (3/4 back), facing right (profile), facing down-right (3/4). "
    "All cells same size, same character scale, feet on same baseline, no text, no labels, no borders, "
    "no background, solid white background only, flat color shading, crisp edges, no anti-aliasing."
)

def flood_fill_alpha(im, tol=28):
    """背景 flood-fill 抠图：从四角背景色扩散抠透明（复用项目 Z3 方法）"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = px[0, 0]
    stack = [(0, 0)]
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or x < 0 or y < 0 or x >= w or y >= h:
            continue
        c = px[x, y]
        if abs(c[0]-bg[0]) > tol or abs(c[1]-bg[1]) > tol or abs(c[2]-bg[2]) > tol:
            continue
        seen.add((x, y))
        px[x, y] = (c[0], c[1], c[2], 0)
        stack.append((x+1, y)); stack.append((x-1, y)); stack.append((x, y+1)); stack.append((x, y-1))
    return im

def align_center(im):
    """按内容 bbox 居中到统一画布（保留 alpha）"""
    bbox = im.getbbox()
    if bbox is None:
        return im
    crop = im.crop(bbox)
    # 统一画布 512x512，内容居中
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(crop, ((512 - crop.width)//2, (512 - crop.height)//2), crop)
    return canvas

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-gen", action="store_true")
    ap.add_argument("--size", default="1024x1024")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    raw = os.path.join(OUT_DIR, "_raw")
    os.makedirs(raw, exist_ok=True)
    src = os.path.join(raw, "grid_8dir.png")

    if not args.skip_gen:
        print("[H1 v2] 生图 8 向网格（1024）...")
        n, dt = gen_image(PROMPT, src, ref=ANCHOR, size=args.size, quality="high")
        print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
    else:
        print("[H1 v2] skip-gen")

    im = Image.open(src).convert("RGB")
    print("[H1 v2] 源图:", im.size)
    per = im.size[0] // 4  # 每格 256x256（1024 源）
    cells = []
    for i, name in enumerate(ORDER):
        r, c = divmod(i, 4)
        cell = im.crop((c*per, r*per, (c+1)*per, (r+1)*per))
        cell = flood_fill_alpha(cell)
        cell = align_center(cell)
        out = os.path.join(OUT_DIR, f"{name}.png")
        cell.save(out)
        cells.append((name, out))
        print(f"  [切分] {name}.png")
    # 拼一张审阅图（4x2，透明底换棋盘格）
    review = Image.new("RGB", (4*256, 2*256), (200, 200, 200))
    for i, (name, p) in enumerate(cells):
        r, c = divmod(i, 4)
        cell = Image.open(p)
        review.paste(cell, (c*256, r*256), cell)
    review_path = os.path.join(OUT_DIR, "_review_grid.png")
    review.save(review_path)
    print("[H1 v2] 审阅图:", review_path)

if __name__ == "__main__":
    main()