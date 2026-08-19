extends Node2D

## 艾琳 2D 横板平台游戏（SunnyLand Forest 官方地图移植）
## 操作：A/D 或 ←/→ = 移动  空格/W = 跳跃  J = 攻击  R = 重开

var TS := 64
var atlas_json := "res://assets/tiles/atlas.json"
var atlas_png := "res://assets/tiles/atlas.png"
var map_file := "res://assets/maps/sunny.map.json"
const PLAYER_SCENE := "res://player.gd"
const MONSTER_SCENE := "res://monster.gd"
const AILIN_DIR := "res://assets/ailin/"
const AILIN_PIXEL_DIR := "res://assets/ailin_pixel_side/"
const AILIN_HD2D_SIDE_DIR := "res://assets/ailin_hd2d_side/"
const BG_FAR := preload("res://assets/bg/background.png")
const BG_MID := preload("res://assets/bg/middleground.png")

var MAP_COLS := 160
var MAP_ROWS := 25
var MAP_PX_W := 0
var MAP_PX_H := 0
const MAX_MONSTERS := 4
const MONSTER_RESPAWN := 4.0
const GRAVITY := 2200.0

var player: CharacterBody2D
var monsters: Array = []
var kills := 0
var _respawn_t := 0.0
var _game_over := false

var _atlas_meta: Dictionary
var _map_meta: Dictionary
var _atlas_tex: Texture2D
var _ground: TileMapLayer
var _world: Node2D
var _bg_far: Node2D
var _bg_mid: Node2D
var _cam: Camera2D
var _hp_bar: ColorRect
var _hp_bg: ColorRect
var _kill_label: Label
var _hint: Label
var _over: Label

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for i in args.size():
		var a: String = args[i]
		if a.begins_with("--map="):
			map_file = a.trim_prefix("--map=")
		elif a == "--map" and i + 1 < args.size():
			map_file = args[i + 1]
	add_to_group("game")
	_build_background()
	_build_world()
	_spawn_player()
	for i in MAX_MONSTERS:
		_spawn_monster(_rand_ground_pos())
	_build_ui()
	_update_hp_ui()

func _build_background() -> void:
	# 视差背景：多层手动平铺跟随摄像机
	_bg_far = _make_bg_layer(BG_FAR, 0.15, 40)
	add_child(_bg_far)
	_bg_mid = _make_bg_layer(BG_MID, 0.35, 90)
	add_child(_bg_mid)

func _make_bg_layer(tex: Texture2D, scroll: float, y: float) -> Node2D:
	var node := Node2D.new()
	var w: float = tex.get_width()
	var copies := int(ceil(1600.0 / w)) + 3
	for i in copies:
		var sp := Sprite2D.new()
		sp.texture = tex
		sp.position = Vector2(i * w, y)
		node.add_child(sp)
	node.set_meta("tex_w", w)
	node.set_meta("scroll", scroll)
	return node

func _update_bg() -> void:
	if _cam == null:
		return
	var cx: float = _cam.global_position.x
	for node in [_bg_far, _bg_mid]:
		var w: float = node.get_meta("tex_w")
		var s: float = node.get_meta("scroll")
		var offset := -fmod(cx * s, w)
		node.position.x = offset

func _build_world() -> void:
	_map_meta = JSON.parse_string(FileAccess.get_file_as_string(map_file))
	if _map_meta.has("atlas_json"):
		atlas_json = _map_meta["atlas_json"]
	_atlas_meta = JSON.parse_string(FileAccess.get_file_as_string(atlas_json))
	TS = int(_atlas_meta.get("tile_size", 64))
	MAP_COLS = int(_map_meta.get("w", 160))
	MAP_ROWS = int(_map_meta.get("h", 25))
	MAP_PX_W = MAP_COLS * TS
	MAP_PX_H = MAP_ROWS * TS
	if _map_meta.has("atlas"):
		atlas_png = _map_meta["atlas"]
	_atlas_tex = load(atlas_png)
	_world = Node2D.new()
	_world.name = "World"
	add_child(_world)
	_ground = TileMapLayer.new()
	_ground.name = "Ground"
	_ground.tile_set = _build_tileset()
	_world.add_child(_ground)
	_place_map()
	_build_collisions()

func _build_tileset() -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TS, TS)
	var src := TileSetAtlasSource.new()
	src.texture = _atlas_tex
	src.texture_region_size = Vector2i(TS, TS)
	var cols: int = _atlas_meta["cols"]
	var rows: int = _atlas_meta["rows"]
	for r in rows:
		for c in cols:
			src.create_tile(Vector2i(c, r))
	ts.add_source(src, 0)
	return ts

func _place_map() -> void:
	var cols: int = _atlas_meta["cols"]
	var w: int = _map_meta["w"]
	var h: int = _map_meta["h"]
	var base: Array = _map_meta["base"]
	for i in w * h:
		var b: int = base[i]
		if b <= 0:
			continue
		var idx := b - 1
		var x := i % w
		var y := int(i / w)
		_ground.set_cell(Vector2i(x, y), 0, Vector2i(idx % cols, int(idx / cols)))

func _build_collisions() -> void:
	var w: int = _map_meta["w"]
	var collide: Array = _map_meta["collide"]
	var body := StaticBody2D.new()
	body.name = "Collision"
	_world.add_child(body)
	var y := 0
	while y < MAP_ROWS:
		var x := 0
		while x < MAP_COLS:
			if collide[y * w + x] == 1:
				var x2 := x
				while x2 < MAP_COLS and collide[y * w + x2] == 1:
					x2 += 1
				var cs := CollisionShape2D.new()
				var sh := RectangleShape2D.new()
				sh.size = Vector2((x2 - x) * TS, TS)
				cs.shape = sh
				cs.position = Vector2((x + x2) * TS / 2.0, y * TS + TS / 2.0)
				body.add_child(cs)
				x = x2
			else:
				x += 1
		y += 1

func _find_spawn() -> Vector2:
	var w: int = _map_meta["w"]
	var collide: Array = _map_meta["collide"]
	# 找"站得稳且前方开阔"的平台：本格 solid、上方 air、前方 6 格 air（射箭不被挡）
	for tx in range(6, 60):
		for ty in range(1, MAP_ROWS):
			if collide[ty * w + tx] == 1 and collide[(ty - 1) * w + tx] == 0:
				var ok := true
				for i in range(1, 7):
					if tx + i < MAP_COLS and collide[(ty - 1) * w + tx + i] == 1:
						ok = false
						break
				if ok:
					return Vector2(tx * TS + TS / 2, ty * TS - 40)
	return Vector2(400, 300)

func _spawn_player() -> void:
	var p := CharacterBody2D.new()
	p.name = "Player"
	p.set_script(load(PLAYER_SCENE))
	var cs := CollisionShape2D.new()
	var sh := CapsuleShape2D.new()
	sh.radius = 18
	sh.height = 96
	cs.shape = sh
	cs.position = Vector2(0, -48)
	p.add_child(cs)
	_world.add_child(p)
	p.position = _find_spawn()
	p.call("setup_animations", AILIN_PIXEL_DIR)
	player = p
	_cam = Camera2D.new()
	_cam.name = "Camera"
	_cam.position_smoothing_enabled = true
	_cam.position_smoothing_speed = 6.0
	_cam.limit_left = 0
	_cam.limit_top = 0
	_cam.limit_right = MAP_PX_W
	_cam.limit_bottom = MAP_PX_H
	_cam.offset = Vector2(0, -120)
	p.add_child(_cam)
	_cam.make_current()

func _rand_ground_pos() -> Vector2:
	var w: int = _map_meta["w"]
	var collide: Array = _map_meta["collide"]
	for attempt in 60:
		var tx := randi_range(20, MAP_COLS - 8)
		for ty in range(MAP_ROWS - 2, 0, -1):
			if collide[ty * w + tx] == 1:
				return Vector2(tx * TS + TS / 2, ty * TS - 30)
	return Vector2(600, 400)

func _spawn_monster(pos: Vector2) -> void:
	var m := CharacterBody2D.new()
	m.set_script(load(MONSTER_SCENE))
	m.collision_layer = 2
	m.collision_mask = 1
	var cs := CollisionShape2D.new()
	var sh := CapsuleShape2D.new()
	sh.radius = 12
	sh.height = 26
	cs.shape = sh
	cs.position = Vector2(0, -14)
	m.add_child(cs)
	m.position = pos
	m.call("setup", player)
	_world.add_child(m)
	monsters.append(m)

func _build_ui() -> void:
	var ui := CanvasLayer.new()
	ui.name = "UI"
	add_child(ui)
	_hp_bg = ColorRect.new()
	_hp_bg.color = Color(0.25, 0.05, 0.05, 0.9)
	_hp_bg.size = Vector2(240, 22)
	_hp_bg.position = Vector2(16, 16)
	ui.add_child(_hp_bg)
	_hp_bar = ColorRect.new()
	_hp_bar.color = Color(0.9, 0.2, 0.2)
	_hp_bar.size = Vector2(236, 18)
	_hp_bar.position = Vector2(18, 18)
	ui.add_child(_hp_bar)
	_kill_label = _mk_label("击杀 0", Vector2(16, 44), 20)
	ui.add_child(_kill_label)
	_hint = _mk_label("A/D=移动  空格/W=跳  J=攻击  R=重开  1/2=HD-2D/像素", Vector2(16, 700), 15)
	ui.add_child(_hint)
	_over = _mk_label("", Vector2(640 - 200, 300), 40)
	_over.visible = false
	ui.add_child(_over)

func _mk_label(txt: String, pos: Vector2, size: int) -> Label:
	var l := Label.new()
	l.text = txt
	l.position = pos
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("outline_size", 4)
	return l

func _update_hp_ui() -> void:
	if player == null:
		return
	var hp: float = player.get("hp")
	var max_hp: float = player.get("max_hp")
	var w := 236.0 * clampf(hp / max_hp, 0, 1)
	_hp_bar.size = Vector2(w, 18)

func _on_player_died() -> void:
	_game_over = true
	_over.text = "你阵亡了！ 按 R 重开"
	_over.visible = true

func _on_monster_killed(m) -> void:
	kills += 1
	_kill_label.text = "击杀 %d" % kills
	monsters.erase(m)
	_respawn_t = MONSTER_RESPAWN

func _process(delta: float) -> void:
	_update_bg()
	if player != null and Input.is_key_pressed(KEY_1):
		player.call("switch_style", AILIN_HD2D_SIDE_DIR)
	if player != null and Input.is_key_pressed(KEY_2):
		player.call("switch_style", AILIN_PIXEL_DIR)
	if _game_over:
		if Input.is_key_pressed(KEY_R):
			get_tree().reload_current_scene()
		return
	if _respawn_t > 0:
		_respawn_t -= delta
		if _respawn_t <= 0 and monsters.size() < MAX_MONSTERS:
			_spawn_monster(_rand_ground_pos())
	if player != null:
		_update_hp_ui()
