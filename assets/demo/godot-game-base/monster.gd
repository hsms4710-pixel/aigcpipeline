extends CharacterBody2D

## 鼻涕虫敌人：地面巡逻 + 撞墙/到边缘转身 + 接触伤害 + 受击/死亡

const SPEED := 70.0
const ATTACK_CD := 0.9
const ATTACK_DAMAGE := 10.0
const MAX_HP := 40.0
const SCALE := 1.5
const EDGE_CHECK := 26.0

var hp := MAX_HP
var _player: Node2D
var _anim: AnimatedSprite2D
var _dir := 1.0
var _attack_t := 0.0
var _hurt_t := 0.0
var _edge_a: RayCast2D
var _edge_b: RayCast2D

func setup(player: Node2D) -> void:
	_player = player
	_anim = AnimatedSprite2D.new()
	var sf := SpriteFrames.new()
	sf.add_animation("walk")
	for i in 4:
		sf.add_frame("walk", load("res://assets/slug/slug_%d.png" % (i + 1)))
	sf.set_animation_speed("walk", 6)
	sf.set_animation_loop("walk", true)
	_anim.sprite_frames = sf
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.scale = Vector2(SCALE, SCALE)
	_anim.offset = Vector2(0, 10)
	add_child(_anim)
	_anim.play("walk")
	# 边缘检测射线（前方脚下）
	_edge_a = RayCast2D.new()
	_edge_a.target_position = Vector2(EDGE_CHECK, 34)
	_edge_a.collision_mask = 1
	add_child(_edge_a)
	_edge_b = RayCast2D.new()
	_edge_b.target_position = Vector2(-EDGE_CHECK, 34)
	_edge_b.collision_mask = 1
	add_child(_edge_b)

func _physics_process(delta: float) -> void:
	_attack_t = maxf(_attack_t - delta, 0)
	_hurt_t = maxf(_hurt_t - delta, 0)
	velocity.x = _dir * SPEED
	move_and_slide()
	if is_on_wall():
		_dir = -_dir
	# 边缘检测：前方脚下悬空则转身
	_edge_a.position = Vector2(0, -8)
	_edge_b.position = Vector2(0, -8)
	var front := _edge_a if _dir > 0 else _edge_b
	front.force_raycast_update()
	if is_on_floor() and not front.is_colliding():
		_dir = -_dir
	_anim.flip_h = _dir < 0
	# 接触伤害
	if _player != null and not _player.get("_dead"):
		var d := global_position.distance_to(_player.global_position)
		if d < 38.0 and _attack_t == 0.0:
			_attack_t = ATTACK_CD
			_player.call("take_damage", ATTACK_DAMAGE)

func take_damage(n: float) -> void:
	hp -= n
	_hurt_t = 0.25
	if hp <= 0:
		var game := get_tree().get_first_node_in_group("game")
		if game != null:
			game.call("_on_monster_killed", self)
		queue_free()
