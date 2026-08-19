extends CharacterBody2D

## 艾琳横板玩家：奔跑 + 跳跃 + 近战攻击（J 键）
## 攻击判定：Area2D 只检测敌人层(2) + 攻击窗口轮询，排除自身，修复"按攻击自己掉血"

const RUN_SPEED := 340.0
const ACCEL := 2600.0
const FRICTION := 2400.0
const GRAVITY := 2200.0
const JUMP_VEL := -880.0
const MAX_FALL := 1400.0
const ATTACK_DAMAGE := 25
const ATTACK_COOLDOWN := 0.4
const ATTACK_WINDOW := 0.2
const INVINCIBLE := 1.0
const FLASH_RATE := 0.06

var max_hp := 100.0
var hp := 100.0
var _facing := 1.0
var _attack_t := 0.0
var _attack_cd := 0.0
var _inv_t := 0.0
var _flash_t := 0.0
var _dead := false
var _anim: AnimatedSprite2D
var _attack_area: Area2D
var _hit: Array = []
var _style_dir := "res://assets/ailin_pixel_side/"
var _was_on_floor := false
var _land_t := 0.0
var _breath_base_y := 0.0

func setup_animations(dir: String) -> void:
	_anim = AnimatedSprite2D.new()
	_anim.name = "Anim"
	_anim.sprite_frames = _load_frames(dir)
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.scale = Vector2.ONE
	_fit_feet()
	add_child(_anim)
	# 落地阴影（图像润色：锚定脚底）
	var shadow := Polygon2D.new()
	shadow.name = "Shadow"
	shadow.polygon = PackedVector2Array([
		Vector2(-22, -2), Vector2(22, -2), Vector2(30, 4), Vector2(-30, 4)
	])
	shadow.color = Color(0, 0, 0, 0.28)
	shadow.z_index = -1
	add_child(shadow)
	_anim.play("idle")
	# 攻击判定区：只检测敌人层(collision_layer=2)
	_attack_area = Area2D.new()
	_attack_area.name = "AttackArea"
	_attack_area.collision_mask = 2
	var cs := CollisionShape2D.new()
	var sh := RectangleShape2D.new()
	sh.size = Vector2(70, 70)
	cs.shape = sh
	_attack_area.add_child(cs)
	_attack_area.monitoring = false
	add_child(_attack_area)
	_attack_area.body_entered.connect(_on_attack_body_entered)

func _fit_feet() -> void:
	var tex: Texture2D = _anim.sprite_frames.get_frame_texture("idle", 0)
	if tex == null:
		return
	_breath_base_y = -tex.get_height() / 2.0
	_anim.offset = Vector2(0, _breath_base_y)

func _load_frames(dir: String) -> SpriteFrames:
	var sf := SpriteFrames.new()
	var groups := {"idle": [], "walk": [], "attack": [], "hurt": []}
	var files := DirAccess.get_files_at(dir)
	for f in files:
		if not f.ends_with(".png"):
			continue
		var action: String = f.get_slice("_", 0)
		if groups.has(action):
			groups[action].append(dir + f)
	for action in groups:
		if groups[action].is_empty():
			continue
		sf.add_animation(action)
		for fp in groups[action]:
			sf.add_frame(action, load(fp))
		var fps := 8
		if action == "walk":
			fps = 6
		elif action == "idle":
			fps = 4
		elif action == "attack":
			fps = 12
		elif action == "hurt":
			fps = 8
		sf.set_animation_speed(action, fps)
		sf.set_animation_loop(action, action == "idle" or action == "walk")
	return sf

func switch_style(dir: String) -> void:
	if _style_dir == dir or _anim == null:
		return
	_style_dir = dir
	_anim.sprite_frames = _load_frames(dir)
	_fit_feet()
	var cur := _anim.animation
	if cur != "" and _anim.sprite_frames.has_animation(cur):
		_anim.play(cur)
	else:
		_anim.play("idle")

func _physics_process(delta: float) -> void:
	if _dead:
		velocity.x = 0
		move_and_slide()
		return
	_attack_cd = maxf(_attack_cd - delta, 0)
	_attack_t = maxf(_attack_t - delta, 0)
	_inv_t = maxf(_inv_t - delta, 0)
	if _attack_t == 0.0:
		_attack_area.monitoring = false
	var dir := 0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		dir -= 1
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		dir += 1
	if dir != 0:
		_facing = float(dir)
		velocity.x = move_toward(velocity.x, dir * RUN_SPEED, ACCEL * delta)
	else:
		velocity.x = move_toward(velocity.x, 0, FRICTION * delta)
	velocity.y = minf(velocity.y + GRAVITY * delta, MAX_FALL)
	if (Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)) and is_on_floor():
		velocity.y = JUMP_VEL
	if Input.is_key_pressed(KEY_J) and _attack_cd == 0.0:
		_do_attack()
	move_and_slide()
	# 落地缓冲（squash）
	if is_on_floor() and not _was_on_floor:
		_land_t = 0.16
	_was_on_floor = is_on_floor()
	_land_t = maxf(_land_t - delta, 0)
	# 动画
	_anim.flip_h = _facing < 0
	if _attack_t > 0:
		if _anim.animation != "attack":
			_anim.play("attack")
	elif _inv_t > 0:
		pass  # hurt 动画保持
	elif not is_on_floor():
		if _anim.animation != "walk":
			_anim.play("walk")
	elif absf(velocity.x) > 20.0:
		if _anim.animation != "walk":
			_anim.play("walk")
	else:
		if _anim.animation != "idle":
			_anim.play("idle")
	# 静止呼吸（idle 单帧 + 平滑缩放，避免 AI 帧间抖动）
	if _land_t > 0.0:
		var k := _land_t / 0.16
		_anim.scale = Vector2(1.0 + 0.10 * k, 1.0 - 0.12 * k)
	elif is_on_floor() and _attack_t <= 0.0 and _inv_t <= 0.0:
		var breath := 1.0 + 0.012 * sin(Time.get_ticks_msec() / 900.0)
		_anim.scale = Vector2(1.0, breath)
		_anim.offset.y = _breath_base_y + 1.5 * sin(Time.get_ticks_msec() / 900.0 + 0.6)
	else:
		_anim.scale = Vector2.ONE
		_anim.offset.y = _breath_base_y
	# 攻击窗口轮询重叠（修复贴身不中 + 自伤：mask=2 只检测敌人）
	if _attack_t > 0 and _attack_area.monitoring:
		for body in _attack_area.get_overlapping_bodies():
			_try_hit(body)
	# 受伤闪烁
	if _inv_t > 0:
		_flash_t -= delta
		if _flash_t <= 0:
			_flash_t = FLASH_RATE
			_anim.visible = not _anim.visible
	else:
		_anim.visible = true

func _do_attack() -> void:
	_attack_cd = ATTACK_COOLDOWN
	_attack_t = ATTACK_WINDOW
	_anim.play("attack")
	_anim.flip_h = _facing < 0
	_attack_area.monitoring = true
	_attack_area.position = Vector2(_facing * 52, -30)
	_hit.clear()
	_spawn_arrow()

func _spawn_arrow() -> void:
	var parent := get_parent()
	if parent == null:
		return
	var arrow := Area2D.new()
	arrow.set_script(load("res://arrow.gd"))
	parent.add_child(arrow)
	var hand := global_position + Vector2(_facing * 34, -35)
	arrow.call("setup", _facing, hand, self)

func _on_attack_body_entered(body: Node2D) -> void:
	_try_hit(body)

func _try_hit(body: Node2D) -> void:
	if body == null or body == self:
		return
	if not body.has_method("take_damage") or _hit.has(body):
		return
	_hit.append(body)
	body.take_damage(ATTACK_DAMAGE)

func take_damage(n: float) -> void:
	if _inv_t > 0 or _dead:
		return
	hp -= n
	_inv_t = INVINCIBLE
	_anim.play("hurt")
	if hp <= 0:
		hp = 0
		_dead = true
		velocity = Vector2.ZERO
		_anim.play("hurt")
		get_tree().create_timer(0.6).timeout.connect(func():
			var game = get_tree().get_first_node_in_group("game")
			if game != null:
				game.call("_on_player_died"))
