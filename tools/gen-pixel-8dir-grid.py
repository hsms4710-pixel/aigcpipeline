"""gen-pixel-8dir-grid.py — 生成统一风格（32px db32）艾琳 8 向像素精灵
锚点 = style_px/ailin_32.png（已 PASS 的 32px 角色），网格法一次生成 8 向 → 切分 → 32px db32 量化
"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHOR = os.path.join(REPO, "assets", "demo", "pokemon_map", "style_px", "ailin_32.png")
OUT = os.path.join(REPO, "assets", "demo", "pokemon_map", "char_8dir_px")
ORDER = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]

PROMPT = (
    "A sprite sheet of ONE pixel-art chibi elf archer in EXACTLY 8 cells, 2 rows x 4 columns, "
    "same character in every cell (silver-white big high ponytail, pointed elf ears, green eyes, "
    "dark green tunic, small bow): Row1 left->right facing down / down-left / left / up-left; "
    "Row2 left->right facing up / up-right / right / down-right. All cells same size, same scale, "
    "feet on same baseline, flat bright lighting, no text, no labels, no borders, white background, "
    "chunky pixel style."
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-gen", action="store_true")
    ap.add_argument("--size", default="1024x1024")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(OUT, "_raw")
    os.makedirs(raw, exist_ok=True)
    src = os.path.join(raw, "grid_8dir.png")
    if not args.skip_gen:
        # 锚点放大到 512 作 ref（保持角色）
        anchor_big = os.path.join(raw, "anchor_512.png")
        im = Image.open(ANCHOR).convert("RGBA")
        im.resize((512, 512), Image.NEAREST).save(anchor_big)
        print("[8dir] 生成 4x2 网格（锚点保持角色）...")
        n, dt = gen_image(PROMPT, src, ref=anchor_big, size=args.size, quality="high")
        print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
    im = Image.open(src).convert("RGB")
    per = im.size[0] // 4
    import subprocess
    px_script = os.path.join(REPO, "tools", "vendor", "ai-pixel-art", "scripts", "pixelize.py")
    for i, name in enumerate(ORDER):
        r, c = divmod(i, 4)
        cell = im.crop((c*per, r*per, (c+1)*per, (r+1)*per))
        cell_path = os.path.join(raw, f"cell_{name}.png")
        cell.save(cell_path)
        out = os.path.join(OUT, f"{name}.png")
        subprocess.run([sys.executable, px_script, "--input", cell_path, "--output", out,
                        "--size", "32", "--palette", "db32"], check=True, capture_output=True)
        print(f"  {name}.png")
    print("[8dir] done ->", OUT)

if __name__ == "__main__":
    main()