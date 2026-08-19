extends Node2D
## S5 引擎 demo：用 SpinePlayer 播放 pipeline 产出的骨骼动画
## 按键：1=idle 2=walk 3=attack 4=hurt 0=暂停/继续

@onready var player = $Spine  # SpinePlayer (spine_player.gd)
@onready var label: Label = $Label

var clip_names: Array = []

func _ready():
    var ok = player.setup("res://skeleton.lite.json", "res://images")
    if not ok:
        label.text = "SpinePlayer 初始化失败"
        return
    clip_names = player.get_clips()
    # 去掉编辑器内部 clip（Parameters）
    clip_names = clip_names.filter(func(c): return not c.begins_with("Parameters"))
    if clip_names.is_empty():
        clip_names = player.get_clips()
    # 角色画布 1280x1280，缩放到视口并居中
    player.scale = Vector2(0.55, 0.55)
    player.position = Vector2(240, 60)
    var prefer = ["walk", "idle", "attack", "hurt"]
    for p in prefer:
        if p in clip_names:
            player.play(p, true)
            break
    update_label()

func _unhandled_input(event):
    if event is InputEventKey and event.pressed:
        var idx = -1
        if event.keycode == KEY_1: idx = 0
        elif event.keycode == KEY_2: idx = 1
        elif event.keycode == KEY_3: idx = 2
        elif event.keycode == KEY_4: idx = 3
        elif event.keycode == KEY_0:
            player._paused = not player._paused
            return
        if idx >= 0 and idx < clip_names.size():
            player.play(clip_names[idx], true)
            update_label()

func update_label():
    var parts = []
    for i in range(clip_names.size()):
        var mark = "→" if clip_names[i] == player._clip_name else " "
        parts.push_back("%s%s=%d" % [mark, clip_names[i], i + 1])
    label.text = "SpinePlayer | 动画: %s | %s | 按键切换" % [player._clip_name, "  ".join(parts)]
