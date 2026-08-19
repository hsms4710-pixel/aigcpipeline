extends SceneTree
## FK 数值验证：子部件是否跟随父骨（M0-6 手臂 / M0-9 腿脚）
func _init():
    var player = Node2D.new()
    player.set_script(load("res://spine_player.gd"))
    var ok = player.setup("res://skeleton.lite.json", "res://images")
    print("SETUP_OK=", ok)
    if not ok:
        quit(1); return
    print("DRIVERS=", player._drivers.keys())
    for needed in ["leftElbow", "rightElbow", "leftKnee", "rightKnee", "leftFootTarget", "rightFootTarget"]:
        print("DRIVER_HAS ", needed, "=", player._drivers.has(needed))
    var rest := {}
    for d in ["leftArm", "leftElbow", "rightArm", "rightElbow", "leftLeg", "leftKnee", "leftFootTarget", "rightLeg", "rightKnee", "rightFootTarget"]:
        if player._drivers.has(d):
            rest[d] = player._drivers[d]["pivot"]
    print("REST_PIVOTS=", rest)
    # walk: leftLeg.rot(t0)=-30 -> 膝/脚关节应移动（继承）
    var wk0 = player.debug_world_pose("walk", 0.0, "leftKnee")
    print("WALK t0 leftKnee joint=", wk0.get("joint"), " rot=", wk0.get("rot"))
    var wf0 = player.debug_world_pose("walk", 0.0, "leftFootTarget")
    print("WALK t0 leftFoot joint=", wf0.get("joint"), " rot=", wf0.get("rot"))
    var dk = (wk0.get("joint") - rest["leftKnee"]).length()
    var df = (wf0.get("joint") - rest["leftFootTarget"]).length()
    print("WALK knee-joint delta=", dk, " foot-joint delta=", df)
    # attack: rightArm.rot(t0.4)=+50 -> 肘关节应移动（继承）
    var ae4 = player.debug_world_pose("attack", 0.4, "rightElbow")
    print("ATTACK t0.4 rightElbow joint=", ae4.get("joint"), " rot=", ae4.get("rot"))
    var de = (ae4.get("joint") - rest["rightElbow"]).length()
    print("ATTACK elbow-joint delta=", de)
    var pass1: bool = dk > 5.0 and df > 5.0 and de > 5.0
    print("FK_INHERIT_PASS=", pass1)
    quit(0 if pass1 else 1)