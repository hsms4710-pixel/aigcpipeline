"""gen-ailin-walk-sheet.py — 用视觉模型提示词生成艾琳 4 向 x 4 帧 walk sheet（256x256 → 16 帧 64x64）
"""
import os, sys, json, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "assets", "demo", "pokemon_map", "pokemon_style")
ANCHOR = os.path.join(BASE, "ailin_pokemon.png")
OUT = os.path.join(BASE, "char_4dir_walk")
RAW = os.path.join(BASE, "_raw_walk")
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)

prompt = json.load(io.open(os.path.join(BASE, "ailin_prompt_v2.json"), encoding="utf-8"))["prompt"]

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

src = os.path.join(RAW, "walk_sheet.png")
print("[walk] 生图 256x256（4向x4帧）...")
n, dt = gen_image(prompt, src, size="512x512", quality="high")
print(f"  -> {n/1024:.0f}KB {dt:.1f}s")
im = Image.open(src).convert("RGB")
per = im.size[0] // 4
dirs = ["down", "left", "up", "right"]
for r, d in enumerate(dirs):
    for c in range(4):
        cell = im.crop((c*per, r*per, (c+1)*per, (r+1)*per))
        cell = flood_fill_alpha(cell)
        # 128px -> 64px????????????
        cell = cell.resize((64, 64), Image.NEAREST)
        bbox = cell.getbbox()
        canvas = Image.new("RGBA", (64,64), (0,0,0,0))
        if bbox:
            crop = cell.crop(bbox)
            canvas.paste(crop, ((64-crop.width)//2, (64-crop.height)//2), crop)
        out = os.path.join(OUT, f"{d}_{c}.png")
        canvas.save(out)
        print(f"  {d}_{c}.png")
print("[walk] done ->", OUT)