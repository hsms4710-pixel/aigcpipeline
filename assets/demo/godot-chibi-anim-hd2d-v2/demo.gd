extends Node2D

const ANIMS = {
    "attack": { "frames": [preload("res://assets/attack_0.png"), preload("res://assets/attack_1.png"), preload("res://assets/attack_2.png"), preload("res://assets/attack_3.png")], "fps": 10, "loop": false },
    "hurt": { "frames": [preload("res://assets/hurt_4.png"), preload("res://assets/hurt_5.png"), preload("res://assets/hurt_6.png")], "fps": 10, "loop": false },
    "idle": { "frames": [preload("res://assets/idle_7.png"), preload("res://assets/idle_8.png"), preload("res://assets/idle_9.png")], "fps": 4, "loop": true },
    "walk": { "frames": [preload("res://assets/walk_10.png"), preload("res://assets/walk_11.png"), preload("res://assets/walk_12.png"), preload("res://assets/walk_13.png"), preload("res://assets/walk_14.png"), preload("res://assets/walk_15.png")], "fps": 10, "loop": true },
}

const SPEED = 340.0
const TARGET_H = float(560)

@onready var chibi: AnimatedSprite2D = $Chibi
@onready var hint: Label = $Hint
@onready var info: Label = $Info

var _facing := Vector2.DOWN
var _transition := false

func _fit_all() -> void:
    var frames: Array = ANIMS.idle.frames
    if frames.is_empty(): return
    var rect: Rect2i = frames[0].get_image().get_used_rect()
    var s := TARGET_H / float(max(rect.size.y, 1))
    chibi.scale = Vector2(s, s)

func _play(name: String) -> void:
    if chibi.animation == name and chibi.is_playing(): return
    chibi.animation = name
    chibi.play()
    _transition = not ANIMS.get(name, { "loop": true }).loop

func _ready() -> void:
    chibi.sprite_frames = SpriteFrames.new()
    for k in ANIMS:
        chibi.sprite_frames.add_animation(k)
        for f in ANIMS[k].frames:
            chibi.sprite_frames.add_frame(k, f)
        chibi.sprite_frames.set_animation_speed(k, ANIMS[k].fps)
        chibi.sprite_frames.set_animation_loop(k, ANIMS[k].loop)
    _fit_all()
    _play("idle")
    hint.text = "WASD/方向键=移动(下=idle/上=back/左右=翻转walk)  空格=attack  H=hurt"

func _process(delta: float) -> void:
    var dir := Vector2.ZERO
    if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A): dir.x -= 1.0
    if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D): dir.x += 1.0
    if Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W): dir.y -= 1.0
    if Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S): dir.y += 1.0
    if Input.is_key_pressed(KEY_SPACE): _play("attack")
    if Input.is_key_pressed(KEY_H): _play("hurt")
    if not chibi.is_playing(): _transition = false
    if dir != Vector2.ZERO:
        _facing = dir.normalized()
        if not _transition:
            if _facing.x < -0.5:
                chibi.flip_h = true; _play("walk")
            elif _facing.x > 0.5:
                chibi.flip_h = false; _play("walk")
            elif _facing.y < -0.5:
                _play("back")
            else:
                _play("idle")
        position += dir * SPEED * delta
    else:
        if not _transition:
            chibi.flip_h = false
            _play("idle")
    var st: String = "transition" if _transition else str(chibi.animation)
    info.text = "朝向:" + _facing_desc() + " 动画:" + st + " 位置(" + str(int(position.x)) + "," + str(int(position.y)) + ")"

func _facing_desc() -> String:
    if _facing.x < -0.5: return "左"
    elif _facing.x > 0.5: return "右"
    elif _facing.y < -0.5: return "背"
    return "正"