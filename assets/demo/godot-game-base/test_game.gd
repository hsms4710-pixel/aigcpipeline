extends SceneTree

var _main: Node
var _frames := 0
var _phase := 0

func _initialize() -> void:
	_main = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	print("[TEST] main instantiated")

func _arrows() -> int:
	var n := 0
	for ch in _main.get_node("World").get_children():
		var sc = ch.get_script()
		if sc != null and String(sc.resource_path).ends_with("arrow.gd"):
			n += 1
	return n

func _process(delta: float) -> bool:
	_frames += 1
	if _phase == 0 and _frames >= 15:
		assert(_main.player != null, "player missing")
		assert(_main.monsters.size() >= 1, "monsters missing")
		var ground = _main.get("_ground")
		assert(ground != null and ground.get_used_cells().size() > 100, "ground map not built")
		print("[TEST] player+monsters+map OK, monsters=%d cells=%d" % [_main.monsters.size(), ground.get_used_cells().size()])
		for i in range(_main.monsters.size() - 1, 0, -1):
			_main.monsters[i].queue_free()
		_phase = 1
		_frames = 0
	elif _phase == 1 and _frames >= 40:
		var p: Node2D = _main.player
		print("[TEST] player floor=%s y=%.0f" % [p.is_on_floor(), p.global_position.y])
		assert(p.is_on_floor(), "player did not land on ground")
		# 传送怪物到玩家前方，并强制同步物理体
		var m: Node2D = _main.monsters[0]
		m.global_position = p.global_position + Vector2(110, -11)
		PhysicsServer2D.body_set_state(m.get_rid(), PhysicsServer2D.BODY_STATE_TRANSFORM, m.global_transform)
		m.set_physics_process(false)  # 冻结巡逻，避免 move_and_slide 带离
		_main.set_meta("attack_hp0", p.get("hp"))
		_main.set_meta("attack_mhp0", m.get("hp"))
		_phase = 2
		_frames = 0
	elif _phase == 2 and _frames >= 12:
		_main.player.call("_do_attack")
		print("[TEST] attack fired arrows=%d player=(%.0f,%.0f)" % [_arrows(), _main.player.global_position.x, _main.player.global_position.y])
		_phase = 3
		_frames = 0
	elif _phase == 3:
		var m: Node2D = _main.monsters[0]
		var mhp: float = m.get("hp")
		var mhp0: float = _main.get_meta("attack_mhp0")
		if _frames == 15 or _frames == 40:
			print("[TEST] poll f=%d arrows=%d m0hp=%.0f" % [_frames, _arrows(), mhp])
		if mhp < mhp0 or _frames >= 120:
			var p: Node2D = _main.player
			var php: float = p.get("hp")
			var php0: float = _main.get_meta("attack_hp0")
			print("[TEST] monster hp %.0f->%.0f player hp %.0f->%.0f" % [mhp0, mhp, php0, php])
			assert(mhp < mhp0, "attack did not damage monster (melee or arrow)")
			assert(absf(php - php0) < 0.01, "SELF DAMAGE! player hp changed after attack")
			print("[TEST] no self damage OK (arrow hit)")
			m.take_damage(999)
			_phase = 4
			_frames = 0
	elif _phase == 4 and _frames >= 20:
		print("[TEST] kills=%d monsters=%d" % [_main.kills, _main.monsters.size()])
		assert(_main.kills >= 1, "kill not counted")
		print("[TEST] ALL PASS")
		quit(0)
	return false
