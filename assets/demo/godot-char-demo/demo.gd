extends Node2D

const EXPRESSIONS := {
	"happy": preload("res://assets/exp_happy.png"),
	"sad": preload("res://assets/exp_sad.png"),
	"angry": preload("res://assets/exp_angry.png"),
	"neutral": preload("res://assets/exp_neutral.png"),
}
const CHIBI := {
	"front": preload("res://assets/chibi_full.png"),
	"side": preload("res://assets/chibi_side.png"),
	"back": preload("res://assets/chibi_back.png"),
	"idle": preload("res://assets/chibi_idle.png"),
	"walk": preload("res://assets/chibi_walk.png"),
	"attack": preload("res://assets/chibi_attack.png"),
	"hurt": preload("res://assets/chibi_hurt.png"),
}

@onready var portrait: Sprite2D = $Portrait
@onready var chibi: Sprite2D = $Chibi
@onready var hint: Label = $Hint

func _ready() -> void:
	portrait.texture = EXPRESSIONS["neutral"]
	chibi.texture = CHIBI["front"]
	hint.text = "表情: 1=happy 2=sad 3=angry 4=neutral   小人: Q=正面 W=侧 E=背 A=idle S=walk D=attack F=hurt"

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1: portrait.texture = EXPRESSIONS["happy"]
			KEY_2: portrait.texture = EXPRESSIONS["sad"]
			KEY_3: portrait.texture = EXPRESSIONS["angry"]
			KEY_4: portrait.texture = EXPRESSIONS["neutral"]
			KEY_Q: chibi.texture = CHIBI["front"]
			KEY_W: chibi.texture = CHIBI["side"]
			KEY_E: chibi.texture = CHIBI["back"]
			KEY_A: chibi.texture = CHIBI["idle"]
			KEY_S: chibi.texture = CHIBI["walk"]
			KEY_D: chibi.texture = CHIBI["attack"]
			KEY_F: chibi.texture = CHIBI["hurt"]