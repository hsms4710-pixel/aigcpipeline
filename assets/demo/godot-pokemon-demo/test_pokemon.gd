extends SceneTree
func _init() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var ground = scene.get_node_or_null("Ground")
	var cells := 0
	if ground != null and ground.has_method("get_used_cells"):
		cells = ground.get_used_cells().size()
	var p = scene.get_node_or_null("Player")
	var spr = p.get_node_or_null("Sprite") if p else null
	var spr_tex := "none"
	if spr != null and spr.texture != null:
		spr_tex = spr.texture.resource_path
	var tree_count := 0
	for ch in scene.get_children():
		if ch is Sprite2D and ch.name == "" and ch.texture != null and ch.texture.resource_path.contains("tree"):
			tree_count += 1
	print("POKEMON-CHECK ground_cells=", cells, " player=", (p.position if p else "none"), " spr=", spr_tex, " trees=", tree_count)
	var ok := cells > 100 and p != null and spr_tex.contains("char")
	print("POKEMON-CHECK ", "PASS" if ok else "FAIL")
	quit()