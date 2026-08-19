extends Node2D

## 艾琳 · HD-2D 对齐版可玩 demo（transparent_v2：matte 对齐 hero + 姿势派生 + 无弓 A-pose）
## 操作：WASD/方向键=移动（向下=正面 向上=背面 左右=翻转） 空格=攻击 H=受伤 N=无弓A-pose 1=正面

const CHIBI := {
	"front": preload("res://assets/chibi_full.png"),
	"side": preload("res://assets/chibi_side.png"),
	"back": preload("res://assets/chibi_back.png"),
	"walk": preload("res://assets/chibi_walk.png"),
	"attack": preload("res://assets/chibi_attack.png"),
	"hurt": preload("res://assets/chibi_hurt.png"),
	"idle": preload("res://assets/chibi_idle.png"),
	"nobow": preload("res://assets/chibi_nobow.png"),
}

const SPEED := 340.0
const ACTION_DUR := 0.28
## 角色显示高度（各帧大小差异用非透明 bbox 归一）
const CHIBI_TARGET_H := 560.0

@onready var chibi: Sprite2D = $Chibi
@onready var hint: Label = $Hint
@onready var info: Label = $Info

var _facing := Vector2.DOWN
var _action := ""
var _action_t := 0.0

func _fit_height(sprite: Sprite2D, target_h: float) -> void:
	if sprite.texture == null:
		return
	var rect: Rect2i = sprite.texture.get_image().get_used_rect()
	if rect.size.y <= 0:
		return
	var s := target_h / float(rect.size.y)
	sprite.scale = Vector2(s, s)

func _show(k: String) -> void:
	chibi.texture = CHIBI[k]
	_fit_height(chibi, CHIBI_TARGET_H)

func _ready() -> void:
	_show("front")
	hint.text = "WASD/方向键=移动（下=正面 上=背面 左右=翻转） 空格=攻击 H=受伤 N=无弓A-pose 1=正面"

func _set_action(name: String, dur: float = ACTION_DUR) -> void:
	_action = name
	_action_t = dur
	_show(name)

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
	if Input.is_key_pressed(KEY_SPACE):
		_set_action("attack")
	if Input.is_key_pressed(KEY_H):
		_set_action("hurt")
	if Input.is_key_pressed(KEY_N):
		_show("nobow")
	if Input.is_key_pressed(KEY_1):
		_show("front")

	if dir != Vector2.ZERO:
		_facing = dir.normalized()
		if _action == "":
			if _facing.x < -0.5:
				chibi.flip_h = true
				_show("walk")
			elif _facing.x > 0.5:
				chibi.flip_h = false
				_show("walk")
			elif _facing.y > 0.5:
				_show("front")
			elif _facing.y < -0.5:
				_show("back")
		position += dir * SPEED * delta
	else:
		if _action == "":
			_show("front")
	_update_info()

func _update_info() -> void:
	var f := ""
	if _facing.x < -0.5: f = "左"
	elif _facing.x > 0.5: f = "右"
	elif _facing.y < -0.5: f = "背"
	else: f = "正"
	var st := "空闲" if _action == "" else _action
	info.text = "位置(%d,%d) 朝向:%s 状态:%s" % [int(position.x), int(position.y), f, st]
