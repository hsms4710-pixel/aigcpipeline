"""build-pokemon-demo.py — W2/A4：宝可梦式俯视地图 Godot demo 生成
- 32px 无缝瓦片（overworld.png 6 瓦片：草x2/水x2/土/路，ai-pixel-art 生成）
- 64px 像素 8 向角色（char_pixel/，db32）
- 32px 树 sprite（tree.png，y-sort 遮挡 + 碰撞）
- 8 向移动 + 水域/树碰撞 + 网格地图布局
输出: assets/demo/godot-pokemon-demo/
"""
import os, shutil, random

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(REPO, "assets", "demo", "godot-pokemon-demo")
SRC = os.path.join(REPO, "assets", "demo", "pokemon_map")
ORDER = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]

# 瓦片常量（sheet 3x2, 32px）
T_GRASS0, T_GRASS1, T_WATER0, T_WATER1, T_DIRT, T_PATH = 0, 1, 2, 3, 4, 5

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def build_map(w, h):
    """程序化宝可梦式地图：草地为主 + 水域块 + 土路 + 树丛（树作为独立物体）"""
    rng = random.Random(42)
    grid = [[T_GRASS0 if rng.random() > 0.35 else T_GRASS1 for _ in range(w)] for _ in range(h)]
    # 水域：左下角一块湖（圆形）
    cx, cy, r = w * 0.22, h * 0.72, 6
    for y in range(h):
        for x in range(w):
            if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                grid[y][x] = T_WATER0 if (x + y) % 3 else T_WATER1
    # 土路：横穿中部 + 右上小路
    for x in range(w):
        if x < w * 0.6:
            grid[h // 2][x] = T_PATH if x % 2 else T_DIRT
    for x in range(int(w * 0.6), w):
        for y in range(h // 2, h):
            if abs((x - w * 0.8) * 0.7 + (y - h * 0.8)) < 3:
                grid[y][x] = T_PATH
    # 树丛位置（独立 sprite，放在草地上，不占瓦片）
    trees = []
    clusters = [(0.45, 0.25, 5), (0.75, 0.3, 4), (0.5, 0.85, 4)]
    for tx, ty, n in clusters:
        for _ in range(n):
            trees.append((int(tx * w) + rng.randint(-2, 2), int(ty * h) + rng.randint(-2, 2)))
    return grid, trees

def main():
    if os.path.exists(DEMO):
        shutil.rmtree(DEMO)
    os.makedirs(os.path.join(DEMO, "assets", "tiles"))
    os.makedirs(os.path.join(DEMO, "assets", "char"))
    # 复制资产
    shutil.copy2(os.path.join(SRC, "tiles", "overworld.png"), os.path.join(DEMO, "assets", "tiles", "overworld.png"))
    shutil.copy2(os.path.join(SRC, "tree.png"), os.path.join(DEMO, "assets", "tree.png"))
    for d in ORDER:
        shutil.copy2(os.path.join(SRC, "char_pixel", f"{d}.png"), os.path.join(DEMO, "assets", "char", f"{d}.png"))
    # 地图
    W, H = 60, 40
    grid, trees = build_map(W, H)
    w(os.path.join(DEMO, "assets", "map.json"), __import__("json").dumps(
        {"w": W, "h": H, "tile": 32, "grid": grid, "trees": trees}))
    # project.godot
    w(os.path.join(DEMO, "project.godot"), """\
config_version=5

[application]
config/name="Ailin Pokemon-style Demo"
config/features=PackedStringArray("4.7")
run/main_scene="res://main.tscn"

[display]
window/size/viewport_width=1280
window/size/viewport_height=720
""")
    # main.tscn
    w(os.path.join(DEMO, "main.tscn"), """\
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://main.gd" id="1"]

[node name="Main" type="Node2D"]
script = ExtResource("1")
""")
    # main.gd
    w(os.path.join(DEMO, "main.gd"), """\
extends Node2D
## 宝可梦式俯视地图 demo（32px 无缝瓦片 + 64px 像素 8 向角色 + Y-sort 树）
## 操作：WASD/方向键 8 向移动  Shift=疾跑  R=重开

const TS := 32
const MAP_JSON := "res://assets/map.json"
const CHAR_DIR := "res://assets/char/"

var _map: Dictionary
var player: CharacterBody2D
var _cam: Camera2D
var _trees: Array = []

func _ready() -> void:
	_map = JSON.parse_string(FileAccess.get_file_as_string(MAP_JSON))
	_build_map()
	_spawn_trees()
	_spawn_player()
	_build_ui()

func _build_map() -> void:
	var atlas := load("res://assets/tiles/overworld.png")
	var ground := TileMapLayer.new()
	ground.name = "Ground"
	ground.tile_set = _build_tileset(atlas)
	add_child(ground)
	var grid: Array = _map["grid"]
	var w: int = _map["w"]
	for y in grid.size():
		var row: Array = grid[y]
		for x in row.size():
			ground.set_cell(Vector2i(x, y), 0, Vector2i(row[x] % 3, int(row[x] / 3)))

func _build_tileset(atlas: Texture2D) -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TS, TS)
	var src := TileSetAtlasSource.new()
	src.texture = atlas
	src.texture_region_size = Vector2i(TS, TS)
	for i in 6:
		src.create_tile(Vector2i(i % 3, int(i / 3)))
	ts.add_source(src, 0)
	return ts

func _is_water(x: int, y: int) -> bool:
	var grid: Array = _map["grid"]
	if y < 0 or y >= grid.size() or x < 0 or x >= grid[y].size():
		return false
	return int(grid[y][x]) >= 2 and int(grid[y][x]) <= 3

func _spawn_trees() -> void:
	for t in _map["trees"]:
		var tx: int = t[0]; var ty: int = t[1]
		var s := Sprite2D.new()
		s.texture = load("res://assets/tree.png")
		s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		s.y_sort_enabled = true
		s.position = Vector2(tx * TS + TS / 2, ty * TS + TS)
		add_child(s)
		_trees.append(s)
		# 树碰撞（树干位置，32px）
		var body := StaticBody2D.new()
		body.position = s.position
		body.collision_layer = 1
		body.collision_mask = 1
		var cs := CollisionShape2D.new()
		var sh := RectangleShape2D.new()
		sh.size = Vector2(20, 12)
		cs.shape = sh
		cs.position = Vector2(0, -4)
		body.add_child(cs)
		add_child(body)

func _spawn_player() -> void:
	var p := CharacterBody2D.new()
	p.name = "Player"
	p.set_script(load("res://player.gd"))
	p.collision_layer = 1
	p.collision_mask = 1
	var cs := CollisionShape2D.new()
	var sh := CapsuleShape2D.new()
	sh.radius = 8
	sh.height = 14
	cs.shape = sh
	cs.position = Vector2(0, -8)
	p.add_child(cs)
	p.position = Vector2(6 * TS, 8 * TS)
	add_child(p)
	p.call("setup", CHAR_DIR)
	player = p
	_cam = Camera2D.new()
	_cam.position_smoothing_enabled = true
	_cam.position_smoothing_speed = 8.0
	_cam.limit_left = 0
	_cam.limit_top = 0
	_cam.limit_right = int(_map["w"]) * TS
	_cam.limit_bottom = int(_map["h"]) * TS
	p.add_child(_cam)
	_cam.make_current()

func _physics_process(delta: float) -> void:
	# 水域阻挡：玩家在水上则退回（简化：碰撞不可行走，这里检测位置瓦片）
	if player != null:
		var gx := int(player.position.x / TS)
		var gy := int(player.position.y / TS)
		if _is_water(gx, gy):
			player.position = player.position - player.velocity * delta * 2.0

func _build_ui() -> void:
	var ui := CanvasLayer.new()
	ui.name = "UI"
	add_child(ui)
	var l := Label.new()
	l.text = "WASD=8向移动  Shift=疾跑  水域/树不可通行"
	l.position = Vector2(16, 16)
	l.add_theme_font_size_override("font_size", 18)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("outline_size", 4)
	ui.add_child(l)
""")
    # player.gd（8 向移动，64px 像素角色）
    w(os.path.join(DEMO, "player.gd"), """\
extends CharacterBody2D

const SPEED := 160.0
const SPRINT := 260.0
const ACCEL := 1800.0
const FRICTION := 1800.0

var _dir := ""
var _spr: Sprite2D
var _t := 0.0
var _moving := false

func setup(char_dir: String) -> void:
	_spr = Sprite2D.new()
	_spr.name = "Sprite"
	_spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_spr.centered = false
	add_child(_spr)
	_apply_dir("down")
	# 64px 精灵，底边对齐到脚（角色身高 64px）
	_spr.position = Vector2(-_spr.texture.get_width() / 2.0, -64.0)
	var shadow := Polygon2D.new()
	shadow.polygon = PackedVector2Array([Vector2(-10, -2), Vector2(10, -2), Vector2(12, 3), Vector2(-12, 3)])
	shadow.color = Color(0, 0, 0, 0.25)
	shadow.z_index = -10
	add_child(shadow)

func _apply_dir(d: String) -> void:
	if d == _dir:
		return
	_dir = d
	_spr.texture = load("res://assets/char/%s.png" % d)

func _physics_process(delta: float) -> void:
	var vx := Input.get_axis("ui_left", "ui_right")
	var vy := Input.get_axis("ui_up", "ui_down")
	var inp := Vector2(vx, vy)
	var speed := SPRINT if Input.is_key_pressed(KEY_SHIFT) else SPEED
	_moving = inp.length() > 0.1
	if _moving:
		velocity = velocity.move_toward(inp.normalized() * speed, ACCEL * delta)
		var deg := rad_to_deg(atan2(inp.x, -inp.y))
		var d := "down"
		if deg >= -22.5 and deg < 22.5: d = "down"
		elif deg >= 22.5 and deg < 67.5: d = "down_right"
		elif deg >= 67.5 and deg < 112.5: d = "right"
		elif deg >= 112.5 and deg < 157.5: d = "up_right"
		elif deg >= 157.5 or deg < -157.5: d = "up"
		elif deg >= -157.5 and deg < -112.5: d = "up_left"
		elif deg >= -112.5 and deg < -67.5: d = "left"
		elif deg >= -67.5 and deg < -22.5: d = "down_left"
		_apply_dir(d)
	else:
		velocity = velocity.move_toward(Vector2.ZERO, FRICTION * delta)
	_t += delta * (14.0 if _moving else 0.0)
	if _moving:
		_spr.position.y = -64.0 + sin(_t * 2.0) * 2.0
		_spr.scale = Vector2(1.0 + sin(_t * 4.0) * 0.02, 1.0 - sin(_t * 4.0) * 0.02)
	else:
		_spr.position.y = -64.0
		_spr.scale = Vector2.ONE
	move_and_slide()
""")
    w(os.path.join(DEMO, "start-pokemon.cmd"), """\
@echo off
cd /d "%~dp0"
set GODOT=C:\\Users\\26046\\Documents\\lovegaming\\Godot_v4.7.1-stable_win64.exe\\Godot_v4.7.1-stable_win64.exe
"%GODOT%" --path .
""")
    print("godot-pokemon-demo created:", DEMO)

if __name__ == "__main__":
    main()