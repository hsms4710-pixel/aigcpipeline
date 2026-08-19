extends Node2D
## 关键帧帧动画 demo（walk 循环）— 运行时 ImageTexture 加载（无需资源导入）
var sprite: AnimatedSprite2D
var frames: SpriteFrames
var names: Array = ["walk_00.png","walk_01.png","walk_02.png","walk_03.png"]
func _load_tex(path: String) -> Texture2D:
    var img = Image.load_from_file(path)
    if img == null:
        push_error("frame load fail: " + path)
        return null
    return ImageTexture.create_from_image(img)
func _ready():
    sprite = $Sprite
    frames = SpriteFrames.new()
    frames.add_animation("walk")
    frames.set_animation_loop("walk", true)
    frames.set_animation_speed("walk", 6.0)
    for i in range(names.size()):
        var tex = _load_tex("res://frames/" + names[i])
        if tex != null:
            frames.add_frame("walk", tex, 1.0 / 6.0)
    sprite.sprite_frames = frames
    sprite.play("walk")
    sprite.scale = Vector2(3.0, 3.0)
    sprite.position = Vector2(240, 360)