"""build-ai-map.py — G1：用 tiles_hd2d AI 瓦片程序化生成 Godot 横板地图 map.json
输出 assets/maps/ai_forest.map.json（与 main.gd 的 map 格式一致：w/h/base/collide）
atlas 8x8=64 块，瓦片 tile_r_c 在 atlas 的索引 = r*8+c，base 存 index+1
"""
import os, json, argparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "assets", "demo", "godot-game-base", "assets")

def idx(r, c):
    return r * 8 + c + 1  # base 1-based

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=80)
    ap.add_argument("--h", type=int, default=12)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    w, h = args.w, args.h
    out = args.out or os.path.join(BASE, "maps", "ai_forest.map.json")

    base = [0] * (w * h)
    collide = [0] * (w * h)

    def put(x, y, r, c):
        if 0 <= x < w and 0 <= y < h:
            base[y * w + x] = idx(r, c)

    def put_collide(x, y, v=1):
        if 0 <= x < w and 0 <= y < h:
            collide[y * w + x] = v

    # 背景树冠（6_*，不碰撞）：顶部 3 行，循环用 6_0..6_7
    for y in range(0, 3):
        for x in range(w):
            put(x, y, 6, x % 8)
    # 远景层（7_*，不碰撞）：第 3-4 行
    for y in range(3, 5):
        for x in range(w):
            put(x, y, 7, x % 8)
    # 主地面：y=9 草皮顶层（0_*），y=10-11 土层（1_*），碰撞
    ground_top = 9
    for x in range(w):
        put(x, ground_top, 0, x % 8)
        put_collide(x, ground_top)
        for y in range(ground_top + 1, h):
            put(x, y, 1, x % 8)
            put_collide(x, y)
    # 悬空木平台（4_*）：三段，碰撞
    platforms = [(8, 6, 10), (28, 5, 12), (52, 6, 14)]
    for px, py, plen in platforms:
        for i in range(plen):
            x = px + i
            put(x, py, 4, i % 8)
            put_collide(x, py)
    # 苔藓石墙装饰（3_*，碰撞）：两处竖墙
    for y in range(6, ground_top + 1):
        put(20, y, 3, y % 2)
        put_collide(20, y)
        put(64, y, 3, y % 2)
        put_collide(64, y)

    meta = {
        "w": w, "h": h, "tile_size": 128, "src_ts": 128, "cols": 8, "rows": 8,
        "atlas": "res://assets/tiles_hd2d/atlas.png",
        "base": base, "collide": collide,
        "note": "AI 生成瓦片（tiles_hd2d）程序化地图；草皮0_* 土1_* 石3_* 平台4_* 树冠6_* 远景7_*",
        "generated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    print(f"[build-ai-map] -> {out}")
    print(f"[build-ai-map] 尺寸 {w}x{h} 瓦片(128px)，地面y={ground_top}，平台{len(platforms)}段，墙2处")

if __name__ == "__main__":
    main()