"""gen-pokemon-4dir.py — 宝可梦风 64px 角色 4 向（down 用样本锚点，left/up/right 以锚点生成）"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "assets", "demo", "pokemon_map", "pokemon_style")
ANCHOR = os.path.join(BASE, "ailin_pokemon.png")
OUT = os.path.join(BASE, "char_4dir")
RAW = os.path.join(BASE, "_raw4")
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
HEAD = ("Keep the EXACT same GBA Pokemon-style chibi elf archer (big head, silver-white high ponytail, elf ears, "
        "dark green tunic, bow, bold outline, bright flat colors, aap64 palette): ")
VIEWS = {
    "left": "PROFILE view facing LEFT, body and head turned left, bow visible, full body",
    "up":   "seen FROM BEHIND, back of head with ponytail, full body",
    "right":"PROFILE view facing RIGHT, body and head turned right, bow visible, full body",
}
def flood_fill_alpha(im, tol=32):
    im = im.convert("RGBA"); w,h = im.size; px = im.load(); bg = px[0,0]
    stack=[(0,0)]; seen=set()
    while stack:
        x,y=stack.pop()
        if (x,y) in seen or x<0 or y<0 or x>=w or y>=h: continue
        c=px[x,y]
        if abs(c[0]-bg[0])>tol or abs(c[1]-bg[1])>tol or abs(c[2]-bg[2])>tol: continue
        seen.add((x,y)); px[x,y]=(c[0],c[1],c[2],0)
        stack += [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
    return im
for name, view in VIEWS.items():
    anchor_big = os.path.join(RAW, "anchor_512.png")
    Image.open(ANCHOR).convert("RGBA").resize((512,512), Image.NEAREST).save(anchor_big)
    src = os.path.join(RAW, f"{name}_raw.png")
    print(f"[pk4dir] 生成 {name} ...")
    n, dt = gen_image(HEAD + view + ". Transparent background, full body, no text.",
                      src, ref=anchor_big, size="1024x1024", quality="high")
    print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
    im = Image.open(src).convert("RGB")
    # 64px aap64 量化
    tmp = os.path.join(RAW, f"{name}_64.png")
    subprocess.run([sys.executable, os.path.join(REPO,"tools","vendor","ai-pixel-art","scripts","pixelize.py"),
                    "--input", src, "--output", tmp, "--size", "64", "--palette", "aap64"], check=True, capture_output=True)
    im = Image.open(tmp)
    im = flood_fill_alpha(im)
    bbox = im.getbbox()
    canvas = Image.new("RGBA",(64,64),(0,0,0,0))
    if bbox:
        crop = im.crop(bbox)
        canvas.paste(crop, ((64-crop.width)//2, (64-crop.height)//2), crop)
    canvas.save(os.path.join(OUT, f"{name}.png"))
    print(f"  {name}.png OK")
# down = 锚点（居中）
im = Image.open(ANCHOR).convert("RGBA")
bbox = im.getbbox()
canvas = Image.new("RGBA",(64,64),(0,0,0,0))
if bbox:
    crop = im.crop(bbox)
    canvas.paste(crop, ((64-crop.width)//2, (64-crop.height)//2), crop)
canvas.save(os.path.join(OUT, "down.png"))
print("  down.png OK (anchor)")
print("[pk4dir] done ->", OUT)