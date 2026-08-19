extends CharacterBody2D
## 宝可梦式 4 向 x 4 帧 walk 动画角色（视觉模型提示词生成，NDS BW 风）

var _const_dir := "res://assets/char_walk"
const SPEED := 160.0
const SPRINT := 260.0
const ACCEL := 1800.0
const FRICTION := 1800.0

var _dir := ""
var _spr: Sprite2D
var _t := 0.0
var _moving := false
var _frame := 0

func setup(char_dir: String) -> void:
	_const_dir = char_dir
	_spr = Sprite2D.new()
	_spr.name = "Sprite"
	_spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_spr.centered = false
	add_child(_spr)
	_apply_dir("down", 0)
	# 64px 精灵，底边对齐到脚（角色身高 64px = 2 瓦片，宝可梦比例）
	_spr.position = Vector2(-_spr.texture.get_width() / 2.0, -64.0)
	var shadow := Polygon2D.new()
	shadow.polygon = PackedVector2Array([Vector2(-10, -2), Vector2(10, -2), Vector2(12, 3), Vector2(-12, 3)])
	shadow.color = Color(0, 0, 0, 0.25)
	shadow.z_index = -10
	add_child(shadow)

func _apply_dir(d: String, f: int) -> void:
	if d == _dir and f == _frame:
		return
	_dir = d
	_frame = f
	_spr.texture = load("%s/%s_%d.png" % [_const_dir, d, f])

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
		if deg >= -45.0 and deg < 45.0: d = "down"
		elif deg >= 45.0 and deg < 135.0: d = "right"
		elif deg >= 135.0 or deg < -135.0: d = "up"
		else: d = "left"
		_t += delta * 8.0
		_apply_dir(d, int(_t) % 4)
		_spr.position.y = -64.0 + sin(_t * 2.0) * 1.5
	else:
		velocity = velocity.move_toward(Vector2.ZERO, FRICTION * delta)
		_apply_dir(_dir, 0)
		_spr.position.y = -64.0
		_spr.scale = Vector2.ONE
	move_and_slide()