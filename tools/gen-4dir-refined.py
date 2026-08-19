"""gen-4dir-refined.py — 逐向独立生成 4 主轴像素角色（down 用已 PASS 正面，left/up/right 以正面为锚点生成）
输出 assets/demo/pokemon_map/char_4dir_px/（32px db32，透明居中）
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "assets", "demo", "pokemon_map")
ANCHOR = os.path.join(BASE, "style_px", "ailin_32.png")
OUT = os.path.join(BASE, "char_4dir_px")
RAW = os.path.join(BASE, "style_px", "_raw4")
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
PIX = os.path.join(REPO, "tools", "vendor", "ai-pixel-art", "scripts", "pixelize.py")

VIEWS = {
    "down": None,  # 用锚点
    "left": "same 32px pixel-art elf archer character, PROFILE view facing LEFT (side view, body and head turned left, bow visible), full body feet on baseline",
    "up":   "same 32px pixel-art elf archer character, seen FROM BEHIND (back view, back of head with silver ponytail, cape), full body feet on baseline",
    "right":"same 32px pixel-art elf archer character, PROFILE view facing RIGHT (side view, body and head turned right, bow visible), full body feet on baseline",
}
HEAD = ("Keep the EXACT same pixel-art elf archer (silver-white big high ponytail, pointed elf ears, green eyes, "
        "dark green tunic, small bow), same coarse 32px pixel style, db32 palette, flat bright lighting: ")

def flood_fill_alpha(im, tol=32):
    im = im.convert("RGBA"); w, h = im.size; px = im.load(); bg = px[0,0]
    stack = [(0,0)]; seen = set()
    while stack:
        x, y = stack.pop()
        if (x,y) in seen or x<0 or y<0 or x>=w or y>=h: continue
        c = px[x,y]
        if abs(c[0]-bg[0])>tol or abs(c[1]-bg[1])>tol or abs(c[2]-bg[2])>tol: continue
        seen.add((x,y)); px[x,y] = (c[0],c[1],c[2],0)
        stack += [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
    return im

for name, view in VIEWS.items():
    out = os.path.join(OUT, f"{name}.png")
    if name == "down":
        im = Image.open(ANCHOR).convert("RGBA")
    else:
        anchor_big = os.path.join(RAW, "anchor_512.png")
        Image.open(ANCHOR).convert("RGBA").resize((512,512), Image.NEAREST).save(anchor_big)
        src = os.path.join(RAW, f"{name}_raw.png")
        print(f"[4dir] 生成 {name} ...")
        n, dt = gen_image(HEAD + view + ". Transparent background, full body, no text, no watermark.",
                          src, ref=anchor_big, size="1024x1024", quality="high")
        print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
        im = Image.open(src).convert("RGB")
        # 32px 量化
        tmp = os.path.join(RAW, f"{name}_32.png")
        subprocess.run([sys.executable, PIX, "--input", src, "--output", tmp, "--size", "32", "--palette", "db32"],
                       check=True, capture_output=True)
        im = Image.open(tmp)
    im = flood_fill_alpha(im)
    bbox = im.getbbox()
    canvas = Image.new("RGBA", (32,32), (0,0,0,0))
    if bbox:
        crop = im.crop(bbox)
        canvas.paste(crop, ((32-crop.width)//2, (32-crop.height)//2), crop)
    canvas.save(out)
    print(f"  {name}.png OK")
print("[4dir] done ->", OUT)