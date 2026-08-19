extends SceneTree
## 验证 H2 俯视 demo：8 向精灵可加载 + 玩家 sprite 有 texture + 方向切换
func _init() -> void:
	var dirs := ["down", "down_left", "left", "up_left", "up", "up_right", "right", "down_right"]
	var ok := true
	for d in dirs:
		var t = load("res://assets/char_8dir/%s.png" % d)
		if t == null:
			print("FAIL load:", d)
			ok = false
		else:
			print("OK load:", d, t.get_width(), "x", t.get_height())
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	var p = scene.get_node_or_null("Player")
	if p == null:
		print("H2-CHECK FAIL: no Player")
		quit()
		return
	var spr = p.get_node_or_null("Sprite")
	if spr == null or spr.texture == null:
		print("H2-CHECK FAIL: sprite/texture null")
		quit()
		return
	# 切换全部 8 向验证 _apply_dir
	for d in dirs:
		p.call("_apply_dir", d)
		if spr.texture == null or not (spr.texture.resource_path.contains(d)):
			print("H2-CHECK FAIL: dir switch", d, spr.texture.resource_path if spr.texture else "null")
			ok = false
	print("H2-CHECK", "PASS" if ok else "FAIL", "player_pos=", p.position)
	quit()