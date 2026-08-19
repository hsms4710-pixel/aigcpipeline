# -*- coding: utf-8 -*-
"""port-tiny-rpg-map.py — 把 Tiny RPG Forest 官方地图移植为 Godot 工程资产
- tileset.png 4x 放大(最近邻) → 64px 瓦片图集 atlas.png + atlas.json
- map.json (Tiled) → forest.map.json {w,h,base[],overlay[],collide[],base_flip[],overlay_flip[]}
- 对象(树/岩石/灌木) 从 objects.png 按 atlas-props.json 或 sliced 提取 → assets/props/
"""
import json, io, os, shutil
from PIL import Image

BASE = r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路"
SRC = os.path.join(BASE, "env", "assets", "tiny-rpg-forest", "tiny-RPG-forest-files")
DEMO = os.path.join(SRC, "Demo", "assets")
GAME = os.path.join(BASE, "assets", "demo", "godot-game-base")
OUT_TILES = os.path.join(GAME, "assets", "tiles")
OUT_MAPS = os.path.join(GAME, "assets", "maps")
OUT_PROPS = os.path.join(GAME, "assets", "props")
os.makedirs(OUT_TILES, exist_ok=True)
os.makedirs(OUT_MAPS, exist_ok=True)
os.makedirs(OUT_PROPS, exist_ok=True)

# ---- 1) 图集：tileset.png 4x ----
ts_img = Image.open(os.path.join(DEMO, "environment", "tileset.png")).convert("RGBA")
T16 = 16
COLS = ts_img.width // T16
ROWS = ts_img.height // T16
TS = 64
atlas = ts_img.resize((ts_img.width * 4, ts_img.height * 4), Image.NEAREST)
atlas.save(os.path.join(OUT_TILES, "atlas.png"))
with io.open(os.path.join(OUT_TILES, "atlas.json"), "w", encoding="utf-8") as f:
    json.dump({"tile_size": TS, "src_ts": T16, "cols": COLS, "rows": ROWS, "tiles": None}, f, ensure_ascii=False)
print("atlas:", atlas.size, "grid:", COLS, "x", ROWS)

# ---- 2) 地图 ----
with io.open(os.path.join(DEMO, "maps", "map.json"), encoding="utf-8") as f:
    m = json.load(f)
W, H = m["width"], m["height"]
TILESET_GID = 9  # tileset firstgid
H_FLIP = 1 << 31
V_FLIP = 1 << 30
D_FLIP = 1 << 29

def read_layer(name):
    for l in m["layers"]:
        if l.get("name") == name and l.get("type") == "tilelayer":
            return l["data"]
    return None

base_data = read_layer("Tile Layer")
overlay_data = read_layer("Tile Layer 2")
coll_data = read_layer("Collisions Layer")

def conv(data):
    idx = [0] * (W * H)
    flips = [0] * (W * H)
    if not data:
        return idx, flips
    for i, gid in enumerate(data):
        if not gid:
            continue
        hf = bool(gid & H_FLIP); vf = bool(gid & V_FLIP); df = bool(gid & D_FLIP)
        raw = gid & ~(H_FLIP | V_FLIP | D_FLIP)
        if raw >= TILESET_GID:
            idx[i] = raw - TILESET_GID + 1  # 1-based (0=空)
            if hf: flips[i] |= 1
            if vf: flips[i] |= 2
    return idx, flips

base, base_flip = conv(base_data)
overlay, overlay_flip = conv(overlay_data)
collide = [1 if g else 0 for g in (coll_data or [])]

map_out = {
    "w": W, "h": H, "tile_size": TS, "atlas_cols": COLS,
    "base": base, "base_flip": base_flip,
    "overlay": overlay, "overlay_flip": overlay_flip,
    "collide": collide,
}
with io.open(os.path.join(OUT_MAPS, "forest.map.json"), "w", encoding="utf-8") as f:
    json.dump(map_out, f, ensure_ascii=False, separators=(",", ":"))
print("map:", W, "x", H, "base cells:", sum(1 for v in base if v), "overlay:", sum(1 for v in overlay if v), "collide:", sum(collide))

# ---- 3) 道具：sliced-objects 复制到游戏 ----
so = os.path.join(SRC, "PNG", "environment", "sliced-objects")
for f in os.listdir(so):
    if f.endswith(".png"):
        shutil.copy2(os.path.join(so, f), os.path.join(OUT_PROPS, f))
print("props copied:", len([f for f in os.listdir(OUT_PROPS) if f.endswith('.png')]))
print("DONE")
