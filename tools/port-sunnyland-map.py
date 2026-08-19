# -*- coding: utf-8 -*-
"""port-sunnyland-map.py — 移植 SunnyLand Forest 官方横板地图到 Godot
- tileset.png 4x 放大(最近邻) → 64px 瓦片图集 atlas.png + atlas.json
- map.json → sunny.map.json {w,h,base[],collide[],objs[]}
- 背景层/道具/敌人帧复制到游戏资产
"""
import json, io, os, shutil
from PIL import Image

BASE = r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路"
SRC = os.path.join(BASE, "env", "assets", "sunny-land-forest", "Sunny-land-forest-files")
DEMO = os.path.join(SRC, "demo", "assets")
GAME = os.path.join(BASE, "assets", "demo", "godot-game-base")
OUT_TILES = os.path.join(GAME, "assets", "tiles")
OUT_MAPS = os.path.join(GAME, "assets", "maps")
OUT_BG = os.path.join(GAME, "assets", "bg")
OUT_ENEMY = os.path.join(GAME, "assets", "slug")
os.makedirs(OUT_TILES, exist_ok=True); os.makedirs(OUT_MAPS, exist_ok=True)
os.makedirs(OUT_BG, exist_ok=True); os.makedirs(OUT_ENEMY, exist_ok=True)

# ---- 1) 图集 ----
ts = Image.open(os.path.join(SRC, "PNG", "environment", "layers", "tileset.png")).convert("RGBA")
COLS = ts.width // 16; ROWS = ts.height // 16
TS = 64
atlas = ts.resize((ts.width * 4, ts.height * 4), Image.NEAREST)
atlas.save(os.path.join(OUT_TILES, "atlas.png"))
with io.open(os.path.join(OUT_TILES, "atlas.json"), "w", encoding="utf-8") as f:
    json.dump({"tile_size": TS, "src_ts": 16, "cols": COLS, "rows": ROWS}, f)
print("atlas:", atlas.size, "grid", COLS, "x", ROWS)

# ---- 2) 地图 ----
with io.open(os.path.join(DEMO, "maps", "map.json"), encoding="utf-8") as f:
    m = json.load(f)
W, H = m["width"], m["height"]
TILESET_GID = 9
H_FLIP, V_FLIP, D_FLIP = 1<<31, 1<<30, 1<<29
def read_layer(name):
    for l in m["layers"]:
        if l.get("name") == name and l.get("type") == "tilelayer":
            return l["data"]
    return None
main = read_layer("Main Layer")
coll = read_layer("Collisions Layer")
def conv(data):
    idx = [0]*(W*H)
    if not data: return idx
    for i, gid in enumerate(data):
        if not gid: continue
        raw = gid & ~(H_FLIP|V_FLIP|D_FLIP)
        if raw >= TILESET_GID:
            idx[i] = raw - TILESET_GID + 1
    return idx
base = conv(main)
collide = [1 if g else 0 for g in (coll or [])]
map_out = {"w": W, "h": H, "tile_size": TS, "atlas_cols": COLS, "base": base, "collide": collide}
with io.open(os.path.join(OUT_MAPS, "sunny.map.json"), "w", encoding="utf-8") as f:
    json.dump(map_out, f, ensure_ascii=False, separators=(",", ":"))
print("map:", W, "x", H, "base:", sum(1 for v in base if v), "collide:", sum(collide))

# ---- 3) 背景层 ----
for name in ["background", "middleground"]:
    shutil.copy2(os.path.join(SRC, "PNG", "environment", "layers", name + ".png"), os.path.join(OUT_BG, name + ".png"))
print("bg copied")

# ---- 4) 敌人 slug ----
sd = os.path.join(SRC, "PNG", "sprites", "enemies", "slug")
i = 1
for f in sorted(os.listdir(sd)):
    if f.endswith(".png"):
        shutil.copy2(os.path.join(sd, f), os.path.join(OUT_ENEMY, f"slug_{i}.png"))
        i += 1
print("slug frames:", i-1)
print("DONE")
