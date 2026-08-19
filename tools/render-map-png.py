# -*- coding: utf-8 -*-
"""render-map-png.py — 把 pokemon map.json 渲染成 PNG（Vision Gate 用，不依赖 Godot）
瓦片源: pokemon_map/tiles/overworld.png(0-5) + decor.png(6-8) + tiles_v3/transition.png(9-12)
sprite: tree.png / flower_bush.png / house*.png（若有）
用法: python tools/render-map-png.py --map <map.json> --out <png> [--scale 1]
"""
import argparse, json, os
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "assets", "demo", "pokemon_map")
DEFAULT_TILES = os.path.join(REPO, "assets", "demo", "a2", "overworld_v2", "overworld_v6_atlas.png")
DEFAULT_TREE = os.path.join(SRC, "tree.png")
DEFAULT_FLOWER = os.path.join(SRC, "closed_loop", "flower_bush.png")
DEFAULT_HOUSE = os.path.join(SRC, "house.png")

def load_atlas(path, cols, rows, ts=32):
    im = Image.open(path).convert("RGBA")
    return [im.crop(((i%cols)*ts, (i//cols)*ts, (i%cols+1)*ts, (i//cols+1)*ts)) for i in range(cols*rows)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=1)
    a = ap.parse_args()
    d = json.load(open(a.map, "r", encoding="utf-8"))
    w, h, ts = d["w"], d["h"], d.get("tile", 32)
    grid = d["grid"]
    tiles = load_atlas(DEFAULT_TILES, 4, 3, ts)
    tree = Image.open(DEFAULT_TREE).convert("RGBA")
    flower = Image.open(DEFAULT_FLOWER).convert("RGBA")
    house_im = Image.open(DEFAULT_HOUSE).convert("RGBA") if os.path.exists(DEFAULT_HOUSE) else None
    canvas = Image.new("RGBA", (w*ts, h*ts), (0,0,0,0))
    for y in range(h):
        for x in range(w):
            v = int(grid[y][x])
            tile = tiles[v] if 0 <= v < len(tiles) else tiles[0]
            canvas.paste(tile, (x*ts, y*ts), tile)
    def paste_sprite(sp, x, y, scale=1):
        tw, th = sp.size
        if scale != 1:
            sp = sp.resize((int(tw*scale), int(th*scale)), Image.NEAREST)
        canvas.paste(sp, (int(x*ts + (ts - sp.size[0])/2), int(y*ts + ts - sp.size[1])), sp)
    for t in d.get("trees", []):
        paste_sprite(tree, t[0], t[1])
    for f in d.get("flowers", []):
        paste_sprite(flower, f[0], f[1])
    for hp in d.get("houses", []):
        if house_im is not None:
            paste_sprite(house_im, hp[0], hp[1], scale=max(1, int(64/ts)))
    if a.scale != 1:
        canvas = canvas.resize((canvas.width*a.scale, canvas.height*a.scale), Image.NEAREST)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    canvas.convert("RGB").save(a.out)
    print(f"[render-map] {w}x{h} tiles -> {a.out} ({canvas.size[0]}x{canvas.size[1]})")

if __name__ == "__main__":
    main()
