extends SceneTree
func _init():
    print("FRAME_TEST_START")
    var frames = SpriteFrames.new()
    frames.add_animation("walk")
    var names = ["walk_00.png","walk_01.png","walk_02.png","walk_03.png"]
    for i in range(names.size()):
        var img = Image.load_from_file("res://frames/" + names[i])
        if img == null:
            print("LOAD_FAIL ", names[i]); quit(1); return
        var tex = ImageTexture.create_from_image(img)
        frames.add_frame("walk", tex, 1.0 / 6.0)
    print("FRAME_COUNT=", frames.get_frame_count("walk"))
    print("FRAME_SIZE=", frames.get_frame_texture("walk", 0).get_size())
    print("FRAME_ANIM_OK")
    quit(0)