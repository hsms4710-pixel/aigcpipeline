# -*- coding: utf-8 -*-
# spine_player.gd — 自包含迷你 Spine 4.0 运行时（Godot 4.x）
#
# 用途：S5 引擎节点。解析 pipeline 产出的 skeleton.json（StretchyStudio/Spine 4.0 导出）
#       + 全画布部件图（每张图 = 1280x1280，部件画在画布原位置），播放骨骼动画。
#
# 能力：
#   - 骨层级解析（rest 姿态）
#   - mesh/region 附件（全画布图 + 部件 bbox）
#   - 动画关键帧：rotate / translate / scale，含 Spine cubic-bezier 曲线 [x1,y1,x2,y2]
#   - 循环/单次播放、变速、运行时切 clip
#
# 修复层 RIG_REPAIR（重要）：
#   StretchyStudio 的 Spine 导出存在已知问题（spec/2d-animation-quality.md §2）：
#   - "Warp" 骨骼（HairBackWarp/FaceWarp/MouthWarp…）不在 bones 数组 → 这些部件不会跟随
#     动画骨骼；根级骨骼（leftArm/rightArm/head/torso）与 DWPose 子树坐标空间不一致。
#   因此本播放器使用「驱动骨 → 部件」映射 + 从部件 bbox 推导枢轴（DRIVER_PARTS/PIVOT），
#   把动画骨骼的旋转/缩放/位移值应用到对应部件上，得到可看的动作。
#   等 M0-2（标准骨架模板）修复了导出后，可移除修复层走纯 Spine 语义。
#
# 用法（由 tools/export-godot.py 生成的工程 main.gd 调用）：
#   var player = $Spine
#   player.setup("res://skeleton.json", "res://images")
#   player.play("walk")
class_name SpinePlayer
extends Node2D

# ── 驱动骨 → 部件映射（修复层；不在此映射内的部件按 rest 姿态渲染）──
const DRIVER_PARTS := {
    "torso":    ["topwear", "objects"],
    "head":     ["back_hair", "front_hair", "headwear", "face", "mouth", "nose",
                 "eyebrow-l", "eyebrow-r", "eyewhite-l", "eyewhite-r",
                 "eyelash-l", "eyelash-r", "irides-l", "irides-r", "ears-l", "ears-r"],
    "leftLeg":  ["legwear-l", "footwear-l"],
    "rightLeg": ["legwear-r", "footwear-r"],
    "leftArm":  ["handwear-l"],
    "rightArm": ["handwear-r"],
}
## 枢轴推导基准（canvas 坐标）：bbox 的哪个位置作为旋转支点
const PIVOT_MODE := {
    "torso": "bottom_center",   # 绕下半身中心（呼吸/转体）
    "head": "bottom_center",    # 绕颈部
    "leftLeg": "top_center",    # 绕髋
    "rightLeg": "top_center",
    "leftArm": "top_center",    # 绕肩
    "rightArm": "top_center",
    # M0-6/M0-9：肘/膝/脚枢轴 = 关节处（部件 bbox 顶部）
    "leftElbow": "top_center",
    "rightElbow": "top_center",
    "leftKnee": "top_center",
    "rightKnee": "top_center",
    "leftFootTarget": "top_center",
    "rightFootTarget": "top_center",
}

var _bones: Dictionary = {}       # name -> {parent, x, y, rotation, scaleX, scaleY, world_pos, world_rot}
var _slots: Array = []            # [{name, bone}]
var _attachments: Dictionary = {} # slot_name -> {attach_name -> {x, y, bbox}}
var _clips: Dictionary = {}       # clip -> {bones: {name: {rotate:[], translate:[], scale:[]}}}
var _pivot_overrides: Dictionary = {}  # driver -> [x,y]（M0-11 真实关节枢轴，来自拆分工具）
var _textures: Dictionary = {}    # slot_name -> Texture2D
var _img_dir: String = ''
var _drivers: Dictionary = {}     # driver bone -> {rot_deg, scale, translate, parts: [], pivot: Vector2}

var _clip_name: String = ""
var _time: float = 0.0
var _loop: bool = true
var _speed: float = 1.0
var _playing: bool = false
var _clip_duration: float = 0.0
var _paused: bool = false

signal clip_changed(clip_name)
signal animation_finished(clip_name)

func get_clips() -> Array:
    return _clips.keys()

func get_clip_duration() -> float:
    return _clip_duration

func setup(sk_json_path: String, img_dir: String) -> bool:
    """解析 skeleton.json + 加载部件图。返回是否成功。"""
    _img_dir = img_dir
    if not FileAccess.file_exists(sk_json_path):
        push_error("SpinePlayer: skeleton.json 不存在: " + sk_json_path)
        return false
    var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(sk_json_path))
    if data.is_empty():
        push_error("SpinePlayer: skeleton.json 解析失败")
        return false
    _parse_bones(data.get("bones", []))
    _parse_slots(data.get("slots", []))
    _parse_skins(data.get("skins", []))
    _parse_animations(data.get("animations", {}))
    _pivot_overrides = data.get("_pivots", {})
    _load_textures()
    _build_drivers()
    return true

# ── 解析 ──────────────────────────────────────────────────────────────────
func _parse_bones(bones: Array) -> void:
    _bones = {}
    for b in bones:
        _bones[b["name"]] = {
            "parent": b.get("parent", ""),
            "x": float(b.get("x", 0.0)), "y": float(b.get("y", 0.0)),
            "rotation": float(b.get("rotation", 0.0)),
            "scaleX": float(b.get("scaleX", 1.0)), "scaleY": float(b.get("scaleY", 1.0)),
        }

func _parse_slots(slots: Array) -> void:
    _slots = []
    for s in slots:
        _slots.append({"name": s["name"], "bone": s.get("bone", "")})

func _parse_skins(skins: Array) -> void:
    _attachments = {}
    if skins.is_empty():
        return
    var skin: Dictionary = skins[0]
    for slot_name in skin.get("attachments", {}):
        var atts: Dictionary = skin["attachments"][slot_name]
        _attachments[slot_name] = {}
        for att_name in atts:
            var a: Dictionary = atts[att_name]
            var entry := {"x": float(a.get("x", 0.0)), "y": float(a.get("y", 0.0))}
            # 部件 bbox：优先用 lite 格式（bbox 数组），否则从 mesh 顶点推导（顶点即画布坐标）
            if a.has("bbox"):
                var bb: Array = a["bbox"]
                entry["bbox"] = Rect2(float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3]))
            else:
                var verts = a.get("vertices", [])
                if verts is Array and not verts.is_empty():
                    var mnx := INF; var mxx := -INF; var mny := INF; var mxy := -INF
                    for v in verts:
                        var vx: float; var vy: float
                        if v is Dictionary:
                            vx = float(v.get("x", 0.0)); vy = float(v.get("y", 0.0))
                        else:
                            vx = float(v); vy = float(v)
                        mnx = minf(mnx, vx); mxx = maxf(mxx, vx)
                        mny = minf(mny, vy); mxy = maxf(mxy, vy)
                    entry["bbox"] = Rect2(mnx, mny, mxx - mnx, mxy - mny)
            _attachments[slot_name][att_name] = entry

func _parse_animations(animations: Dictionary) -> void:
    _clips = {}
    for clip_name in animations:
        var a: Dictionary = animations[clip_name]
        var clip := {"bones": {}, "duration": 0.0}
        if a.has("bones"):
            for bname in a["bones"]:
                clip["bones"][bname] = a["bones"][bname]
        _clips[clip_name] = clip
        # 时长 = 各骨关键帧最大 time
        var dur := 0.0
        for bname in clip["bones"]:
            var tracks: Dictionary = clip["bones"][bname]
            for prop in tracks:
                for kf in tracks[prop]:
                    dur = maxf(dur, float(kf.get("time", 0.0)))
        clip["duration"] = dur

func _load_textures() -> void:
    _textures = {}
    for s in _slots:
        var p: String = _img_dir + "/" + str(s["name"]) + ".png"
        if FileAccess.file_exists(p):
            var img := Image.new()
            if img.load(p) == OK:
                _textures[s["name"]] = ImageTexture.create_from_image(img)
            else:
                push_warning("SpinePlayer: 图片加载失败 " + p)

func _build_drivers() -> void:
    _drivers = {}
    # M0-1 膝盖弯曲：若存在 <part>-shin 拆分部件，用拆分映射（shin+foot 跟 knee，thigh 跟 leg）
    var driver_parts: Dictionary = {}
    for k in DRIVER_PARTS:
        driver_parts[k] = DRIVER_PARTS[k]
    if _attachments.has("legwear-l-shin"):
        driver_parts["leftLeg"] = ["legwear-l"]
        driver_parts["leftKnee"] = ["legwear-l-shin"]
        driver_parts["leftFootTarget"] = ["footwear-l"]
    if _attachments.has("legwear-r-shin"):
        driver_parts["rightLeg"] = ["legwear-r"]
        driver_parts["rightKnee"] = ["legwear-r-shin"]
        driver_parts["rightFootTarget"] = ["footwear-r"]
    # M0-6 手臂弯曲：若存在 <part>-forearm 拆分部件，upper 跟 arm、forearm 跟 elbow
    if _attachments.has("handwear-l-forearm"):
        driver_parts["leftArm"] = ["handwear-l"]
        driver_parts["leftElbow"] = ["handwear-l-forearm"]
    if _attachments.has("handwear-r-forearm"):
        driver_parts["rightArm"] = ["handwear-r"]
        driver_parts["rightElbow"] = ["handwear-r-forearm"]
    for driver in driver_parts:
        var parts: Array = driver_parts[driver]
        var bbox := Rect2()
        var first := true
        for part in parts:
            var atts: Dictionary = _attachments.get(part, {})
            if atts.is_empty():
                continue
            var entry: Dictionary = atts.values()[0]
            if entry.has("bbox"):
                if first:
                    bbox = entry["bbox"]; first = false
                else:
                    bbox = bbox.merge(entry["bbox"])
        if first:
            continue  # 找不到部件 bbox → 不驱动
        var pivot := _derive_pivot(bbox, PIVOT_MODE.get(driver, "center"))
        var pov: Variant = _pivot_overrides.get(driver)
        if pov is Array and pov.size() == 2:
            pivot = Vector2(float(pov[0]), float(pov[1]))
        var bone_info: Dictionary = _bones.get(driver, {})
        var parent_name: String = bone_info.get("parent", "")
        _drivers[driver] = {"parts": parts, "pivot": pivot, "parent": parent_name}

func _derive_pivot(bbox: Rect2, mode: String) -> Vector2:
    match mode:
        "top_center":
            return Vector2(bbox.position.x + bbox.size.x * 0.5, bbox.position.y)
        "bottom_center":
            return Vector2(bbox.position.x + bbox.size.x * 0.5, bbox.position.y + bbox.size.y)
        "center":
            return bbox.get_center()
    return bbox.get_center()

# ── 播放控制 ──────────────────────────────────────────────────────────────
func play(clip_name: String, loop := true) -> void:
    if not _clips.has(clip_name):
        push_warning("SpinePlayer: clip 不存在 " + clip_name)
        return
    _clip_name = clip_name
    _loop = loop
    _time = 0.0
    _playing = true
    _paused = false
    _clip_duration = _clips[clip_name]["duration"]
    clip_changed.emit(clip_name)
    queue_redraw()

func stop() -> void:
    _playing = false
    _time = 0.0
    queue_redraw()

func set_time(t: float) -> void:
    _time = t
    queue_redraw()

func _process(delta: float) -> void:
    if not _playing or _paused or _clip_duration <= 0.0:
        return
    _time += delta * _speed
    if _time >= _clip_duration:
        if _loop:
            _time = fmod(_time, _clip_duration)
        else:
            _time = _clip_duration
            _playing = false
            animation_finished.emit(_clip_name)
    queue_redraw()

# ── 动画采样（Spine cubic-bezier）────────────────────────────────────────
func _kf_value(kf: Dictionary) -> Variant:
    """关键帧值：rotate→value；translate/scale→{x,y}"""
    if kf.has("value"):
        return kf["value"]
    if kf.has("x"):
        return {"x": kf["x"], "y": kf["y"]}
    return null

func _sample_track(track: Array, t: float) -> Variant:
    """track: [{time, value…, curve?}] 按时间采样，返回插值后的值"""
    if track.is_empty():
        return null
    if t <= float(track[0]["time"]):
        return _kf_value(track[0])
    var last: Dictionary = track[track.size() - 1]
    if t >= float(last["time"]):
        return _kf_value(last)
    for i in range(track.size() - 1):
        var a: Dictionary = track[i]
        var b: Dictionary = track[i + 1]
        var ta := float(a["time"])
        var tb := float(b["time"])
        if t >= ta and t <= tb:
            var span := tb - ta
            var u := 0.0 if span <= 0.0 else (t - ta) / span
            var eu := u
            var curve: Variant = a.get("curve", null)
            if curve is String and curve == "stepped":
                eu = 0.0
            elif curve is Array and curve.size() == 4:
                eu = _bezier_ease(u, float(curve[0]), float(curve[1]), float(curve[2]), float(curve[3]))
            return _lerp_kf(a, b, eu)
    return _kf_value(track[0])

func _lerp_kf(a: Dictionary, b: Dictionary, eu: float) -> Variant:
    var va: Variant = _kf_value(a)
    var vb: Variant = _kf_value(b)
    if va is Dictionary and vb is Dictionary:
        return {"x": lerpf(float(va["x"]), float(vb["x"]), eu),
                "y": lerpf(float(va["y"]), float(vb["y"]), eu)}
    return lerpf(float(va), float(vb), eu)
func _bezier_ease(u: float, x1: float, y1: float, x2: float, y2: float) -> float:
    # 数值求解 bezier: x(t)=u → y(t)。控制点 P0=(0,0), P1=(x1,y1), P2=(x2,y2), P3=(1,1)
    if u <= 0.0: return 0.0
    if u >= 1.0: return 1.0
    var lo := 0.0; var hi := 1.0
    for _i in range(16):
        var mid := (lo + hi) * 0.5
        var x := _bezier_x(mid, x1, x2)
        if x < u: lo = mid
        else: hi = mid
    var tt := (lo + hi) * 0.5
    return _bezier_y(tt, y1, y2)

func _bezier_x(t: float, x1: float, x2: float) -> float:
    var omt := 1.0 - t
    return 3.0 * omt * omt * t * x1 + 3.0 * omt * t * t * x2 + t * t * t

func _bezier_y(t: float, y1: float, y2: float) -> float:
    var omt := 1.0 - t
    return 3.0 * omt * omt * t * y1 + 3.0 * omt * t * t * y2 + t * t * t

func _sample_bone(clip: Dictionary, bone_name: String) -> Dictionary:
    var out := {"rot": 0.0, "scale": Vector2.ONE, "translate": Vector2.ZERO}
    var tracks: Dictionary = clip.get("bones", {}).get(bone_name, {})
    if tracks.has("rotate"):
        var v = _sample_track(tracks["rotate"], _time)
        if v != null: out["rot"] = float(v)
    if tracks.has("scale"):
        var v = _sample_track(tracks["scale"], _time)
        if v is Dictionary: out["scale"] = Vector2(float(v["x"]), float(v["y"]))
    if tracks.has("translate"):
        var v = _sample_track(tracks["translate"], _time)
        if v is Dictionary: out["translate"] = Vector2(float(v["x"]), float(v["y"]))
    return out

# ── 渲染 ──────────────────────────────────────────────────────────────────
func _bone_depth(driver: String) -> int:
    var depth := 0
    var cur := driver
    while _drivers.has(cur):
        var p: String = _drivers[cur].get("parent", "")
        if p == "" or not _drivers.has(p):
            break
        cur = p
        depth += 1
        if depth > 32:
            break
    return depth

func _compute_world(anim: Dictionary) -> Dictionary:
    ## FK：按骨骼层级从根到叶累积世界变换（arm→elbow、leg→knee→footTarget）
    var world := {}
    var order: Array = _drivers.keys()
    order.sort_custom(func(a, b): return _bone_depth(a) < _bone_depth(b))
    for driver in order:
        var d: Dictionary = _drivers[driver]
        var a: Dictionary = anim.get(driver, {"rot": 0.0, "scale": Vector2.ONE, "translate": Vector2.ZERO})
        var rest: Vector2 = d["pivot"]
        var parent: String = d.get("parent", "")
        var rot := float(a["rot"])
        var scale: Vector2 = a["scale"]
        var translate: Vector2 = a["translate"]
        var joint: Vector2
        if parent == "" or not world.has(parent):
            joint = rest + translate
        else:
            var pw: Dictionary = world[parent]
            var pw_joint: Vector2 = pw["joint"]
            var pw_rest: Vector2 = pw["rest"]
            var pw_rot := float(pw["rot"])
            var pw_scale: Vector2 = pw["scale"]
            var offset: Vector2 = rest - pw_rest
            var rotd := deg_to_rad(pw_rot)
            var rotated: Vector2 = Vector2(
                offset.x * cos(rotd) - offset.y * sin(rotd),
                offset.x * sin(rotd) + offset.y * cos(rotd)) * pw_scale
            joint = pw_joint + rotated + translate
            rot = pw_rot + rot
            scale = pw_scale * scale
        world[driver] = {"joint": joint, "rot": rot, "scale": scale, "rest": rest}
    return world

func debug_world_pose(clip_name: String, t: float, driver: String) -> Dictionary:
    ## 调试/验证：返回某 clip 某时刻某驱动骨的世界关节位置/旋转（FK 是否生效）
    if not _clips.has(clip_name) or not _drivers.has(driver):
        return {}
    _clip_name = clip_name
    _time = t
    var clip: Dictionary = _clips.get(_clip_name, {})
    var anim := {}
    for drv in _drivers:
        anim[drv] = _sample_bone(clip, drv) if not clip.is_empty() else {"rot": 0.0, "scale": Vector2.ONE, "translate": Vector2.ZERO}
    var world: Dictionary = _compute_world(anim)
    return world.get(driver, {})

func _draw() -> void:
    var clip: Dictionary = _clips.get(_clip_name, {})
    # 预采样驱动骨
    var anim := {}
    for driver in _drivers:
        anim[driver] = _sample_bone(clip, driver) if not clip.is_empty() else {"rot": 0.0, "scale": Vector2.ONE, "translate": Vector2.ZERO}
    # M0-6/M0-9 FK：沿骨骼层级累积世界变换（arm→elbow、leg→knee→footTarget），子部件跟随父骨
    var world: Dictionary = _compute_world(anim)
    var driver_of := {}  # part -> driver
    for driver in _drivers:
        for part in _drivers[driver]["parts"]:
            driver_of[part] = driver
    for s in _slots:
        var tex: Texture2D = _textures.get(s["name"])
        if tex == null:
            continue
        var driver: String = driver_of.get(s["name"], "")
        if driver == "" or not _drivers.has(driver):
            draw_texture(tex, Vector2.ZERO)  # rest 姿态（部件已在画布原位）
            continue
        var w: Dictionary = world[driver]
        var rest: Vector2 = w["rest"]
        var joint: Vector2 = w["joint"]
        var rot := deg_to_rad(float(w["rot"]))
        var scale: Vector2 = w["scale"]
        # final = joint + R(world)*S(world)*(v - rest)
        draw_set_transform(joint, rot, scale)
        draw_texture(tex, -rest)
        draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
