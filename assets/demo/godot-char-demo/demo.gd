extends Node2D

## 艾琳 · 可玩 demo（定稿资产：chibi_v4 + v10 立绘/表情）
## 操作：WASD/方向键移动（向下=正面 向上=背面 左右=翻转） 空格=攻击 H=受伤 1-4=立绘表情

const EXPRESSIONS := {
	"happy": preload("res://assets/exp_happy.png"),
	"sad": preload("res://assets/exp_sad.png"),
	"angry": preload("res://assets/exp_angry.png"),
	"neutral": preload("res://assets/exp_neutral.png"),
}
const CHIBI := {
	"front": preload("res://assets/chibi_full.png"),
	"side": preload("res://assets/chibi_side.png"),
	"back": preload("res://assets/chibi_back.png"),
	"walk": preload("res://assets/chibi_walk.png"),
	"attack": preload("res://assets/chibi_attack.png"),
	"hurt": preload("res://assets/chibi_hurt.png"),
}

const SPEED := 340.0
const ACTION_DUR := 0.28
## 小人统一显示高度（front_b 角色主体 782px × 原 0.7 缩放 ≈ 547px）
const CHIBI_TARGET_H := 547.0

@onready var portrait: Sprite2D = $Portrait
@onready var chibi: Sprite2D = $Chibi
@onready var hint: Label = $Hint
@onready var info: Label = $Info

var _facing := Vector2.DOWN
var _action := ""
var _action_t := 0.0

func _fit_height(sprite: Sprite2D, target_h: float) -> void:
	## 按角色主体（非透明 bbox）统一高度，避免切帧时大小跳变
	if sprite.texture == null:
		return
	var rect: Rect2i = sprite.texture.get_image().get_used_rect()
	if rect.size.y <= 0:
		return
	var s := target_h / float(rect.size.y)
	sprite.scale = Vector2(s, s)

func _ready() -> void:
	portrait.texture = EXPRESSIONS["neutral"]
	chibi.texture = CHIBI["front"]
	_fit_height(chibi, CHIBI_TARGET_H)
	hint.text = "WASD/方向键=移动（向下正面 / 向上背面 / 左右翻转）  空格=攻击  H=受伤  1-4=立绘表情"
	_update_info()

func _process(delta: float) -> void:
	if _action_t > 0.0:
		_action_t -= delta
		if _action_t <= 0.0:
			_action = ""
	var dir := Vector2.ZERO
	if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W):
		dir.y -= 1.0
	if Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S):
		dir.y += 1.0
	dir = dir.normalized()
	var moving := _action == "" and dir.length() > 0.001
	if moving:
		position += dir * SPEED * delta
		position.x = clampf(position.x, 70.0, 1530.0)
		position.y = clampf(position.y, 90.0, 800.0)
		if absf(dir.x) >= absf(dir.y):
			_facing = Vector2.RIGHT if dir.x > 0.0 else Vector2.LEFT
		else:
			_facing = Vector2.DOWN if dir.y > 0.0 else Vector2.UP
	_update_chibi(dir, moving)
	_last_moving = moving
	_update_info()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1: portrait.texture = EXPRESSIONS["happy"]
			KEY_2: portrait.texture = EXPRESSIONS["sad"]
			KEY_3: portrait.texture = EXPRESSIONS["angry"]
			KEY_4: portrait.texture = EXPRESSIONS["neutral"]
			KEY_SPACE: _trigger("attack")
			KEY_H: _trigger("hurt")

func _trigger(act: String) -> void:
	if _action != "":
		return
	_action = act
	_action_t = ACTION_DUR

func _update_chibi(dir: Vector2, moving: bool) -> void:
	var tex: Texture2D = CHIBI["front"]
	var flip := false
	if _action == "attack":
		tex = CHIBI["attack"]
	elif _action == "hurt":
		tex = CHIBI["hurt"]
	elif moving:
		tex = CHIBI["walk"]
		flip = dir.x < 0.0
	else:
		match _facing:
			Vector2.UP:
				tex = CHIBI["back"]
			Vector2.LEFT, Vector2.RIGHT:
				tex = CHIBI["side"]
				flip = _facing == Vector2.LEFT
			_:
				tex = CHIBI["front"]
				flip = _facing == Vector2.LEFT
	chibi.texture = tex
	chibi.flip_h = flip
	_fit_height(chibi, CHIBI_TARGET_H)

func _update_info() -> void:
	var dirname := "下"
	match _facing:
		Vector2.UP: dirname = "上"
		Vector2.LEFT: dirname = "左"
		Vector2.RIGHT: dirname = "右"
	info.text = "位置=(%d, %d)  朝向=%s  状态=%s" % [int(position.x), int(position.y), dirname, (_action if _action != "" else ("移动" if _last_moving else "待机"))]

var _last_moving := false





