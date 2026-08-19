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
