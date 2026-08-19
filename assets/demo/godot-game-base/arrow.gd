extends Area2D

## 箭矢投射物：沿朝向直线飞行，命中敌人造成伤害，命中地面/超时消失

const SPEED := 720.0
const DAMAGE := 25
const LIFE := 1.4
const ARROW_TEX := preload("res://assets/arrow.png")

var _vel := Vector2.ZERO
var _life := LIFE
var _player: Node2D

func setup(dir_x: float, from: Vector2, player: Node2D) -> void:
	_player = player
	global_position = from
	_vel = Vector2(dir_x * SPEED, 0)
	rotation = PI / 2.0 if dir_x > 0 else -PI / 2.0
	collision_mask = 3  # 敌人(2) + 地面(1)
	var cs := CollisionShape2D.new()
	var sh := CapsuleShape2D.new()
	sh.radius = 4
	sh.height = 16
	cs.shape = sh
	add_child(cs)
	var spr := Sprite2D.new()
	spr.texture = ARROW_TEX
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.scale = Vector2(4.0, 4.0)
	add_child(spr)
	# 发光（尾部光点，增强可见性）
	var glow := Polygon2D.new()
	glow.polygon = PackedVector2Array([
		Vector2(-14, -6), Vector2(6, -6), Vector2(12, 0), Vector2(6, 6), Vector2(-14, 6)
	])
	glow.color = Color(1.0, 0.85, 0.4, 0.55)
	glow.position = Vector2(-6, 0)
	add_child(glow)
	body_entered.connect(_on_body)

func _physics_process(delta: float) -> void:
	global_position += _vel * delta
	_life -= delta
	if _life <= 0:
		queue_free()

func _on_body(body: Node2D) -> void:
	if body == _player:
		return
	if body.has_method("take_damage"):
		body.take_damage(DAMAGE)
	queue_free()
