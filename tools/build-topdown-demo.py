"""build-topdown-demo.py — H2：Godot 俯视角 8 向移动 demo 工程生成
- 8 向移动（WASD，斜向归一化）+ 8 向站姿精灵切换 + 程序化 walk bob
- 程序化俯视地图（草地 + 障碍 + 树，Y-sort 遮挡）
- 复制 char_ailin_chibi_8dir 精灵
输出: assets/demo/godot-topdown-demo/
"""
import os, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(REPO, "assets", "demo", "godot-topdown-demo")
SRC8 = os.path.join(REPO, "assets", "demo", "char_ailin_chibi_8dir")
ORDER = ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    if os.path.exists(DEMO):
        shutil.rmtree(DEMO)
    os.makedirs(DEMO)
    # 复制 8 向精灵
    os.makedirs(os.path.join(DEMO, "assets", "char_8dir"), exist_ok=True)
    for name in ORDER:
        shutil.copy2(os.path.join(SRC8, f"{name}.png"), os.path.join(DEMO, "assets", "char_8dir", f"{name}.png"))
    # project.godot
    w(os.path.join(DEMO, "project.godot"), """\
config_version=5

[application]
config/name="Ailin Topdown 8-Dir Demo"
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
""")
    # player.gd
    w(os.path.join(DEMO, "player.gd"), """\
extends CharacterBody2D
## 8 向移动 + 8 向站姿精灵切换 + 程序化 walk bob

const SPEED := 220.0
const SPRINT := 380.0
const ACCEL := 2200.0
const FRICTION := 2000.0
const BOBS := {"down": 1, "down_left": 2, "left": 3, "up_left": 4, "up": 5, "up_right": 6, "right": 7, "down_right": 8}

var _dir := ""
var _spr: Sprite2D
var _t := 0.0
var _moving := false

func setup(char_dir: String) -> void:
	_spr = Sprite2D.new()
	_spr.name = "Sprite"
	_spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_spr.scale = Vector2(0.35, 0.35)
	_spr.centered = false
	# 精灵底边对齐到脚（角色身高约 512px 源，缩放后 ~179px）
	_spr.position = Vector2(-89.6, -179.0)
	add_child(_spr)
	_apply_dir("down")
	# 影子
	var shadow := Polygon2D.new()
	shadow.polygon = PackedVector2Array([Vector2(-14, -2), Vector2(14, -2), Vector2(18, 3), Vector2(-18, 3)])
	shadow.color = Color(0, 0, 0, 0.25)
	shadow.z_index = -10
	add_child(shadow)

func _apply_dir(d: String) -> void:
	if d == _dir:
		return
	_dir = d
	_spr.texture = load("res://assets/char_8dir/%s.png" % d)

func _physics_process(delta: float) -> void:
	var vx := Input.get_axis("ui_left", "ui_right")
	var vy := Input.get_axis("ui_up", "ui_down")
	var inp := Vector2(vx, vy)
	var sprint := Input.is_key_pressed(KEY_SHIFT)
	var speed := SPRINT if sprint else SPEED
	_moving = inp.length() > 0.1
	if _moving:
		velocity = velocity.move_toward(inp.normalized() * speed, ACCEL * delta)
		var ang := atan2(inp.x, -inp.y)  # 0=下, +90°=右, -90°=左, 180°=上
		var deg := rad_to_deg(ang)
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
	# walk bob：上下微动 + 轻微缩放（程序化，站姿图模拟行走）
	_t += delta * (14.0 if _moving else 0.0)
	if _moving:
		_spr.position.y = -179.0 + sin(_t * 2.0) * 3.0
		_spr.scale = Vector2(0.35 + sin(_t * 4.0) * 0.02, 0.35 - sin(_t * 4.0) * 0.02)
	else:
		_spr.position.y = -179.0
		_spr.scale = Vector2(0.35, 0.35)
	move_and_slide()
""")
    # start cmd
    w(os.path.join(DEMO, "start-topdown.cmd"), """\
@echo off
cd /d "%~dp0"
set GODOT=C:\\Users\\26046\\Documents\\lovegaming\\Godot_v4.7.1-stable_win64.exe\\Godot_v4.7.1-stable_win64.exe
"%GODOT%" --path .
""")
    print("godot-topdown-demo created:", DEMO)

if __name__ == "__main__":
    main()