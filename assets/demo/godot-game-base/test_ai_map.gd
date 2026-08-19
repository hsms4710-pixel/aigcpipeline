extends SceneTree
## 验证 AI 地图加载：打印 TS / 地面瓦片数 / 玩家位置，然后退出
func _init() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	var world: Node = scene.get_node_or_null("World")
	var ground: Node = null
	if world != null:
		ground = world.get_node_or_null("Ground")
	var cells := 0
	if ground != null and ground.has_method("get_used_cells"):
		cells = ground.get_used_cells().size()
	var p: Node = scene.get_node_or_null("World/Player")
	var ppos := "none"
	if p != null:
		ppos = str(p.position)
	print("AI-MAP-CHECK TS=", scene.get("TS"), " ground_cells=", cells, " player=", ppos)
	if cells > 0 and p != null:
		print("AI-MAP-CHECK PASS")
	else:
		print("AI-MAP-CHECK FAIL")
	quit()