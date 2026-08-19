# -*- coding: utf-8 -*-
"""build-pokemon-map-v2.py — W2.1 地图打磨 v2.1（新 8 瓦片统一 atlas）
瓦片: 0-2 草地(浅/中/深) 3-4 水面(深/浅) 5 沙滩 6 土路 7 石板路
布局: 值噪声大块草地 + 有机湖形 + 沙滩环 + 1 格宽弯曲主干道(跨湖桥) + 密林群落/林缘 + 村庄清地 + 花草点缀
输出: assets/demo/pokemon_map/map_v2.json（与 main.gd map.json 同格式）
"""
import argparse, json, math, os, random

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "assets", "demo", "pokemon_map")

# 12-cell atlas (4x3): 0-5 草地(含旋转变体打散条纹), 6-7 水, 8 沙, 9 土, 10 石板路
GRASS0, GRASS0R, GRASS1, GRASS1R, GRASS2, GRASS2R = 0, 1, 2, 3, 4, 5
WATER0, WATER1, SAND, DIRT, PATH = 6, 7, 8, 9, 10

def value_noise(w, h, scale, seed):
    rng = random.Random(seed)
    gw, gh = max(2, w // scale + 1), max(2, h // scale + 1)
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = [[0.0]*w for _ in range(h)]
    for y in range(h):
        fy = y / scale; y0 = min(int(fy), gh-2); ty = fy - y0
        for x in range(w):
            fx = x / scale; x0 = min(int(fx), gw-2); tx = fx - x0
            v00, v10 = g[y0][x0], g[y0][x0+1]
            v01, v11 = g[y0+1][x0], g[y0+1][x0+1]
            a = v00 + (v10-v00)*tx; b = v01 + (v11-v01)*tx
            out[y][x] = a + (b-a)*ty
    return out

def organic_blob(w, h, cx, cy, r, seed):
    """随机游走生成有机湖形点集"""
    rng = random.Random(seed)
    pts = set()
    x, y = cx, cy
    pts.add((x, y))
    steps = int(math.pi * r * r * 1.4)
    for _ in range(steps):
        d = random.choice([(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)])
        nx, ny = x+d[0], y+d[1]
        # 与中心距离约束，形成圆润但不规则的形状
        if math.hypot(nx-cx, ny-cy) <= r * (0.75 + 0.5*rng.random()):
            x, y = nx, ny
            pts.add((x, y))
    return pts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=60)
    ap.add_argument("--h", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260819)
    ap.add_argument("--out", default=os.path.join(SRC, "map_v2.json"))
    a = ap.parse_args()
    w, h = a.w, a.h
    rng = random.Random(a.seed)
    grid = [[GRASS0]*w for _ in range(h)]

    # 1) 草地大块（双 octave 值噪声 -> 大色块）+ 细噪声旋转变体打散条纹
    # 域扭曲：坐标加噪声偏移，打破任何方向条带
    def domain_noise(w, h, scale, seed, warp):
        base = value_noise(w, h, scale, seed)
        wx = value_noise(w, h, scale*2, seed+50)
        wy = value_noise(w, h, scale*2, seed+51)
        out = [[0.0]*w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                sx = x + (wx[y][x]-0.5)*warp*scale
                sy = y + (wy[y][x]-0.5)*warp*scale
                if sx < 0: sx = 0
                elif sx >= w-1: sx = w-1.001
                if sy < 0: sy = 0
                elif sy >= h-1: sy = h-1.001
                x0 = int(sx); y0 = int(sy); tx = sx-x0; ty = sy-y0
                a = base[y0][x0] + (base[y0][min(x0+1,w-1)]-base[y0][x0])*tx
                b = base[min(y0+1,h-1)][x0] + (base[min(y0+1,h-1)][min(x0+1,w-1)]-base[min(y0+1,h-1)][x0])*tx
                out[y][x] = a + (b-a)*ty
        return out
    n1 = domain_noise(w, h, 10, a.seed, 0.6)
    n2 = domain_noise(w, h, 5, a.seed+1, 0.5)
    nf = value_noise(w, h, 2, a.seed+3)
    for y in range(h):
        for x in range(w):
            v = n1[y][x]*0.6 + n2[y][x]*0.4
            flip = 1 if nf[y][x] > 0.5 else 0
            if v > 0.66:
                grid[y][x] = GRASS2 + flip
            elif v > 0.44:
                grid[y][x] = GRASS1 + flip
            else:
                grid[y][x] = GRASS0 + flip

    # 2) 湖泊：有机游走湖形 x2
    is_water = [[False]*w for _ in range(h)]
    for i, (cx, cy, r) in enumerate([(int(w*0.24), int(h*0.68), 7), (int(w*0.80), int(h*0.24), 5)]):
        for (x, y) in organic_blob(w, h, cx, cy, r, a.seed + 10*i):
            if 0 <= x < w and 0 <= y < h:
                is_water[y][x] = True
    wn = value_noise(w, h, 3, a.seed+9)
    for y in range(h):
        for x in range(w):
            if is_water[y][x]:
                grid[y][x] = WATER0 if wn[y][x] > 0.5 else WATER1

    # 3) 沙滩环（1-2 格，随机变宽）+ 浅滩 WATER1 环
    for y in range(h):
        for x in range(w):
            if grid[y][x] in (WATER0, WATER1):
                continue
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] in (WATER0, WATER1):
                    grid[y][x] = SAND
                    break
    # 浅滩：水格邻沙 -> WATER1；再一圈沙
    for y in range(h):
        for x in range(w):
            if grid[y][x] in (WATER0,):
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == SAND:
                        grid[y][x] = WATER1
                        break
    # 平滑：孤立水像素（<2 个水邻）移除
    def water_neighbors(x, y):
        n = 0
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] in (WATER0, WATER1):
                n += 1
        return n
    for y in range(h):
        for x in range(w):
            if grid[y][x] in (WATER0, WATER1) and water_neighbors(x, y) < 2:
                grid[y][x] = GRASS1

    # 4) 主干道：西村 -> 中桥 -> 东侧 + 北分支到草地广场（第二个桥/地标）
    def polyline(pts):
        cells = []
        for i in range(len(pts)-1):
            x0, y0 = pts[i]; x1, y1 = pts[i+1]
            n = max(abs(x1-x0), abs(y1-y0)) + 1
            for k in range(n+1):
                tt = k/n
                cells.append((int(round(x0+(x1-x0)*tt)), int(round(y0+(y1-y0)*tt))))
        return cells
    road_main = polyline([(0, int(h*0.52)), (int(w*0.16), int(h*0.44)), (int(w*0.40), int(h*0.54)),
                          (int(w*0.62), int(h*0.44)), (int(w*0.80), int(h*0.34)), (w-1, int(h*0.30))])
    road_fork = polyline([(int(w*0.38), int(h*0.54)), (int(w*0.42), int(h*0.42)),
                          (int(w*0.48), int(h*0.36)), (int(w*0.55), int(h*0.32))])
    road = road_main + road_fork
    for (x, y) in road:
        if not (0 <= x < w and 0 <= y < h):
            continue
        if grid[y][x] in (GRASS0, GRASS0R, GRASS1, GRASS1R, GRASS2, GRASS2R, SAND):
            grid[y][x] = PATH
        elif grid[y][x] in (WATER0, WATER1):
            grid[y][x] = PATH  # 桥
    # 桥两端衔接 + 道路两侧 1 格 dirt 收边
    for (x, y) in road:
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h:
                if grid[ny][nx] in (WATER0, WATER1):
                    grid[ny][nx] = PATH
                elif grid[ny][nx] in (GRASS0, GRASS0R, GRASS1, GRASS1R, GRASS2, GRASS2R, SAND) and rng.random() < 0.5:
                    grid[ny][nx] = DIRT

    # 5) 森林群落：核心实块（2x2 成林）+ 林缘稀疏，边界 1 格林带
    nf = value_noise(w, h, 6, a.seed+7)
    trees = set()
    def forest_ok(x, y):
        return grid[y][x] in (GRASS0, GRASS0R, GRASS1, GRASS1R, GRASS2, GRASS2R)
    # 核心区 -> 实心 2x2
    for y in range(2, h-2):
        for x in range(2, w-2):
            if nf[y][x] > 0.84 and forest_ok(x, y):
                for dx in (0, 1):
                    for dy in (0, 1):
                        nx, ny = x+dx, y+dy
                        if 1 <= nx < w-1 and 1 <= ny < h-1 and forest_ok(nx, ny):
                            trees.add((nx, ny))
    # 林缘稀疏
    for y in range(2, h-2):
        for x in range(2, w-2):
            v = nf[y][x]
            if 0.74 < v <= 0.84 and forest_ok(x, y) and rng.random() < 0.4:
                trees.add((x, y))
    # 边界林带（1 格）
    for x in range(w):
        for y in (0, h-1):
            if forest_ok(x, y):
                trees.add((x, y))
    for y in range(h):
        for x in (0, w-1):
            if forest_ok(x, y):
                trees.add((x, y))
    # 移除孤立单株（<2 个树邻）
    def tree_neighbors(tx, ty):
        n = 0
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            if (tx+dx, ty+dy) in trees:
                n += 1
        return n
    trees = {(x, y) for (x, y) in trees if tree_neighbors(x, y) >= 1}
    trees = [[x, y] for (x, y) in trees]

    # 6) 村庄清地 + 6 houses + 花圃广场
    vx, vy = int(w*0.15), int(h*0.46)
    houses = []
    house_spots = [(vx-2, vy-2), (vx+1, vy-2), (vx-2, vy+1), (vx+2, vy+1),
                   (vx, vy+2), (vx+3, vy-1)]
    for hx, hy in house_spots:
        if 1 <= hx < w-1 and 1 <= hy < h-1:
            houses.append([hx, hy])
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    nx, ny = hx+dx, hy+dy
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] in (GRASS0, GRASS0R, GRASS1, GRASS1R, GRASS2, GRASS2R, SAND):
                        grid[ny][nx] = GRASS0
    # 花圃：村庄广场 + 草地广场（北分支终点）
    flowers = []
    plaza = [(vx, vy), (vx+1, vy), (vx, vy+1), (int(w*0.5), int(h*0.30)), (int(w*0.52), int(h*0.31))]
    for (px_, py_) in plaza:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = px_+dx, py_+dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] in (GRASS0, GRASS1):
                    flowers.append([nx, ny])
    for y in range(h):
        for x in range(w):
            if grid[y][x] in (GRASS0, GRASS1) and rng.random() < 0.012:
                flowers.append([x, y])

    spawn = {"x": vx+1, "y": vy+2}
    meta = {
        "w": w, "h": h, "tile": 32, "grid": grid, "trees": trees,
        "flowers": flowers, "houses": houses, "spawn": spawn,
        "version": "v2.1", "seed": a.seed,
        "generated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    from collections import Counter
    cnt = Counter(v for row in grid for v in row)
    print(f"[map-v2.1] -> {a.out}")
    print(f"[map-v2.1] tiles: {dict(cnt)}")
    print(f"[map-v2.1] trees={len(trees)} flowers={len(flowers)} houses={len(houses)} spawn={spawn}")

if __name__ == "__main__":
    main()
