# -*- coding: utf-8 -*-
"""build-kenney-atlas.py — 把 Kenney 俯视角瓦片打包成游戏图集 + 生成 ASCII 地图"""
import json, os, random
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 兼容: 脚本位于 tools/ 下，ROOT = 角色AIGC... 根目录
KENNEY = os.path.join(ROOT, "env", "assets", "kenney", "extracted", "PNG", "Tiles")
GAME = os.path.join(ROOT, "assets", "demo", "godot-game-base")
OUT_TILES = os.path.join(GAME, "assets", "tiles")
OUT_MAPS = os.path.join(GAME, "assets", "maps")
os.makedirs(OUT_TILES, exist_ok=True)
os.makedirs(OUT_MAPS, exist_ok=True)

TILES = {
    "grass_1": "tile_01", "grass_2": "tile_02", "grass_3": "tile_03", "grass_4": "tile_04",
    "grass_flower": "tile_102",
    "sand_1": "tile_05", "sand_2": "tile_06", "sand_light": "tile_100",
    "water": "tile_19", "water_shore": "tile_07",
    "wall": "tile_163", "wall_plain": "tile_169",
    "tree_a": "tile_134", "tree_b": "tile_158",
    "rock": "tile_187",
    "crate": "tile_123",
    "health": "tile_290",
}

TS = 64
COLS = 8
names = list(TILES.keys())
rows = (len(names) + COLS - 1) // COLS
atlas = Image.new("RGBA", (COLS * TS, rows * TS), (0, 0, 0, 0))
index = {}
for i, name in enumerate(names):
    c, r = i % COLS, i // COLS
    src = os.path.join(KENNEY, TILES[name] + ".png")
    im = Image.open(src).convert("RGBA")
    assert im.size == (TS, TS), f"{name} size {im.size}"
    atlas.paste(im, (c * TS, r * TS))
    index[name] = {"col": c, "row": r}
atlas.save(os.path.join(OUT_TILES, "atlas.png"))
with open(os.path.join(OUT_TILES, "atlas.json"), "w", encoding="utf-8") as f:
    json.dump({"tile_size": TS, "cols": COLS, "rows": rows, "tiles": index}, f, ensure_ascii=False, indent=1)

W, H = 64, 48
legend = {
    "#": "wall", "G": "grass_1", "S": "sand_1", "W": "water", "D": "water",
    "T": "tree_a", "R": "rock", "C": "crate", "F": "grass_flower",
}
grid = [["G"] * W for _ in range(H)]

def rect(c, r, w, h, ch):
    for y in range(r, r + h):
        for x in range(c, c + w):
            if 0 <= x < W and 0 <= y < H:
                grid[y][x] = ch

rect(0, 0, W, 1, "#"); rect(0, H - 1, W, 1, "#")
rect(0, 0, 1, H, "#"); rect(W - 1, 0, 1, H, "#")
rect(6, 5, 9, 7, "D")
rect(5, 4, 11, 9, "W")
rect(44, 20, 8, 6, "D")
rect(43, 19, 10, 8, "W")
for x in range(12, 52): grid[28][x] = "S"
for y in range(8, 40): grid[y][30] = "S"
rect(12, 14, 6, 4, "S"); rect(46, 30, 5, 4, "S")

random.seed(7)
def can_place(x, y):
    return 2 <= x < W - 2 and 2 <= y < H - 2 and grid[y][x] == "G"
for _ in range(46):
    x, y = random.randrange(3, W - 3), random.randrange(3, H - 3)
    if can_place(x, y):
        grid[y][x] = random.choice(["T", "T", "T", "R", "R", "C", "F", "F"])
for _ in range(30):
    x, y = random.randrange(2, W - 2), random.randrange(2, H - 2)
    if can_place(x, y):
        grid[y][x] = "F"
for y in range(22, 26):
    for x in range(30, 34):
        if grid[y][x] in "TRC": grid[y][x] = "G"

map_path = os.path.join(OUT_MAPS, "town.map.txt")
with open(map_path, "w", encoding="utf-8") as f:
    f.write("# Ailin Town 64x48 tiles (64px) legend: #wall G grass S sand W/D water T tree R rock C crate F flower\n")
    for row in grid:
        f.write("".join(row) + "\n")
print("atlas:", atlas.size, "tiles:", len(names))
print("map:", map_path)

preview = Image.new("RGBA", (W * TS, H * TS), (0, 0, 0, 0))
for y in range(H):
    for x in range(W):
        name = legend.get(grid[y][x], "grass_1")
        if name == "grass_1" and random.random() < 0.25:
            name = random.choice(["grass_2", "grass_3", "grass_4"])
        ci = names.index(name)
        c, r = ci % COLS, ci // COLS
        preview.paste(atlas.crop((c * TS, r * TS, c * TS + TS, r * TS + TS)), (x * TS, y * TS))
preview.convert("RGB").save(os.path.join(OUT_MAPS, "town-preview.png"))
print("preview saved")
