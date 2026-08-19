extends Node2D
## 宝可梦式俯视地图 demo v2（W2.1 打磨版）
## 12 格统一 atlas：0-5 草地(旋转变体) 6-7 水 8 沙 9 土 10 石板路
## 操作：WASD/方向键 4 向移动（4向x4帧 walk 动画） Shift=疾跑  R=重开

const TS := 32
const MAP_JSON := "res://assets/map.json"

var _map: Dictionary
var player: CharacterBody2D
var _cam: Camera2D

func _ready() -> void:
	_map = JSON.parse_string(FileAccess.get_file_as_string(MAP_JSON))
	_build_map()
	_spawn_trees()
	_spawn_houses()
	_spawn_flowers()
	_spawn_player()
	_build_ui()

func _build_map() -> void:
	var atlas := load("res://assets/tiles/overworld.png")
	var ground := TileMapLayer.new()
	ground.name = "Ground"
	ground.tile_set = _build_tileset(atlas)
	add_child(ground)
	var grid: Array = _map["grid"]
	for y in grid.size():
		var row: Array = grid[y]
		for x in row.size():
			var v := int(row[x])
			ground.set_cell(Vector2i(x, y), 0, Vector2i(v % 4, int(v / 4)))

func _build_tileset(atlas: Texture2D) -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TS, TS)
	var src := TileSetAtlasSource.new()
	src.texture = atlas
	src.texture_region_size = Vector2i(TS, TS)
	for i in 12:
		src.create_tile(Vector2i(i % 4, int(i / 4)))
	ts.add_source(src, 0)
	return ts

func _is_water(x: int, y: int) -> bool:
	var grid: Array = _map["grid"]
	if y < 0 or y >= grid.size() or x < 0 or x >= grid[y].size():
		return false
	var v := int(grid[y][x])
	return v == 6 or v == 7

func _spawn_sprite(path: String, cells: Array, collide: bool) -> void:
	for c in cells:
		var tx: int = c[0]; var ty: int = c[1]
		var s := Sprite2D.new()
		s.texture = load(path)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		s.y_sort_enabled = true
		s.position = Vector2(tx * TS + TS / 2, ty * TS + TS)
		add_child(s)
		if collide:
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

func _spawn_trees() -> void:
	if _map.has("trees"):
		_spawn_sprite("res://assets/tree.png", _map["trees"], true)

func _spawn_houses() -> void:
	if _map.has("houses"):
		_spawn_sprite("res://assets/house.png", _map["houses"], true)

func _spawn_flowers() -> void:
	if _map.has("flowers"):
		for f in _map["flowers"]:
			var fx: int = f[0]; var fy: int = f[1]
			var s := Sprite2D.new()
			s.texture = load("res://assets/flower_bush.png")
			s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			s.y_sort_enabled = true
			s.position = Vector2(fx * TS + TS / 2, fy * TS + TS)
			add_child(s)

func _spawn_player() -> void:
	var p := CharacterBody2D.new()
	p.name = "Player"
	p.set_script(load("res://player.gd"))
	p.collision_layer = 1
	p.collision_mask = 1
	var cs := CollisionShape2D.new()
	var sh := CapsuleShape2D.new()
	sh.radius = 12
	sh.height = 34
	cs.shape = sh
	cs.position = Vector2(0, -20)
	p.add_child(cs)
	var sp: Dictionary = _map.get("spawn", {"x": 8, "y": 8})
	p.position = Vector2(int(sp["x"]) * TS + TS / 2, int(sp["y"]) * TS + TS / 2)
	add_child(p)
	p.call("setup", "res://assets/char_walk")
	player = p
	_cam = Camera2D.new()
	_cam.position_smoothing_enabled = true
	_cam.position_smoothing_speed = 8.0
	_cam.zoom = Vector2(2.5, 2.5)
	_cam.anchor_mode = Camera2D.ANCHOR_MODE_DRAG_CENTER
	_cam.limit_left = 0
	_cam.limit_top = 0
	_cam.limit_right = int(_map["w"]) * TS
	_cam.limit_bottom = int(_map["h"]) * TS
	p.add_child(_cam)
	_cam.make_current()

func _physics_process(delta: float) -> void:
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
	l.text = "WASD=4向移动  Shift=疾跑  水域/树/房屋不可通行"
	l.position = Vector2(16, 16)
	l.add_theme_font_size_override("font_size", 18)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("outline_size", 4)
	ui.add_child(l)
