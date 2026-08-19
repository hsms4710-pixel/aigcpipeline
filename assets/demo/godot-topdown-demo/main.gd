extends Node2D
## 俯视角 8 向移动 demo（艾琳 8 向精灵 + Y-sort 遮挡）
## 操作：WASD/方向键移动（8 向），Shift 疾跑

const TS := 64
const MAP_W := 60
const MAP_H := 40
const CHAR_DIR := "res://assets/char_8dir/"

var player: CharacterBody2D
var _cam: Camera2D

func _ready() -> void:
	_build_ground()
	_build_obstacles()
	_spawn_player()
	_build_ui()

func _build_ground() -> void:
	# 草地地面（程序化多边形，带随机草色块）
	var ground := Polygon2D.new()
	ground.name = "Ground"
	ground.polygon = PackedVector2Array([
		Vector2(0, 0), Vector2(MAP_W * TS, 0), Vector2(MAP_W * TS, MAP_H * TS), Vector2(0, MAP_H * TS)
	])
	ground.color = Color(0.36, 0.55, 0.30)
	add_child(ground)
	# 深浅草色块（打破单调）
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 260:
		var x := rng.randf_range(0, MAP_W * TS)
		var y := rng.randf_range(0, MAP_H * TS)
		var s := rng.randf_range(20, 90)
		var patch := Polygon2D.new()
		patch.polygon = PackedVector2Array([
			Vector2(x, y), Vector2(x + s, y), Vector2(x + s, y + s * 0.7), Vector2(x, y + s * 0.7)
		])
		patch.color = Color(0.31, 0.50, 0.26, 0.5) if rng.randf() > 0.5 else Color(0.42, 0.60, 0.33, 0.5)
		add_child(patch)

func _build_obstacles() -> void:
	# 树（Y-sort 遮挡验证）+ 石头障碍
	var trees := [
		Vector2(10, 8), Vector2(16, 5), Vector2(24, 12), Vector2(38, 7), Vector2(45, 15),
		Vector2(8, 20), Vector2(30, 22), Vector2(52, 25), Vector2(14, 32), Vector2(42, 33),
	]
	for t in trees:
		add_child(_make_tree(t * TS))
	# 石头（碰撞）
	var rocks := [Vector2(20, 15), Vector2(34, 20), Vector2(48, 12), Vector2(26, 30)]
	for r in rocks:
		add_child(_make_rock(r * TS))

func _make_tree(pos: Vector2) -> Node2D:
	var node := Node2D.new()
	node.position = pos
	node.y_sort_enabled = true
	var trunk := Polygon2D.new()
	trunk.polygon = PackedVector2Array([Vector2(-6, 0), Vector2(6, 0), Vector2(4, -18), Vector2(-4, -18)])
	trunk.color = Color(0.45, 0.28, 0.15)
	node.add_child(trunk)
	var crown := Polygon2D.new()
	crown.polygon = PackedVector2Array([Vector2(-24, -18), Vector2(24, -18), Vector2(16, -52), Vector2(-16, -52)])
	crown.color = Color(0.18, 0.42, 0.20)
	node.add_child(crown)
	return node

func _make_rock(pos: Vector2) -> Node2D:
	var body := StaticBody2D.new()
	body.position = pos
	var cs := CollisionShape2D.new()
	var sh := RectangleShape2D.new()
	sh.size = Vector2(40, 28)
	cs.shape = sh
	cs.position = Vector2(0, -6)
	body.add_child(cs)
	var poly := Polygon2D.new()
	poly.polygon = PackedVector2Array([Vector2(-20, 0), Vector2(20, 0), Vector2(14, -22), Vector2(-14, -22)])
	poly.color = Color(0.42, 0.42, 0.46)
	body.add_child(poly)
	return body

func _spawn_player() -> void:
	var p := CharacterBody2D.new()
	p.name = "Player"
	p.set_script(load("res://player.gd"))
	p.collision_layer = 1
	p.collision_mask = 1
	var cs := CollisionShape2D.new()
	var sh := CapsuleShape2D.new()
	sh.radius = 12
	sh.height = 22
	cs.shape = sh
	cs.position = Vector2(0, -8)
	p.add_child(cs)
	p.position = Vector2(12 * TS, 12 * TS)
	add_child(p)
	p.call("setup", CHAR_DIR)
	player = p
	_cam = Camera2D.new()
	_cam.position_smoothing_enabled = true
	_cam.position_smoothing_speed = 8.0
	_cam.limit_left = 0
	_cam.limit_top = 0
	_cam.limit_right = MAP_W * TS
	_cam.limit_bottom = MAP_H * TS
	p.add_child(_cam)
	_cam.make_current()

func _build_ui() -> void:
	var ui := CanvasLayer.new()
	ui.name = "UI"
	add_child(ui)
	var l := Label.new()
	l.text = "WASD/方向键=8向移动  Shift=疾跑"
	l.position = Vector2(16, 16)
	l.add_theme_font_size_override("font_size", 18)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	l.add_theme_constant_override("outline_size", 4)
	ui.add_child(l)
