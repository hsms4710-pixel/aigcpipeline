extends SceneTree
## 自检：godot --headless --path <proj> --script test_spine.gd
func _init():
    var player = Node2D.new()
    player.set_script(load("res://spine_player.gd"))
    var ok = player.setup("res://skeleton.lite.json", "res://images")
    print("SETUP_OK=", ok)
    if not ok:
        quit(1); return
    var clips = player.get_clips()
    print("CLIPS=", clips)
    for c in clips:
        player.play(c, true)
        var dur = player.get_clip_duration()
        var s0 = player._sample_bone(player._clips[c], "leftLeg")
        print("CLIP=", c, " DUR=", dur, " leftLeg.rot@0=", s0.rot)
    print("PARSE_OK")
    quit(0)
