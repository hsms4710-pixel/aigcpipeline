extends SceneTree
func _init():
    print("START")
    var tex = load("res://frames/walk_00.png")
    print("LOADED=", tex)
    if tex == null:
        quit(1)
    print("SIZE=", tex.get_size())
    print("MINI_OK")
    quit(0)