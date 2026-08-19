# -*- coding: utf-8 -*-
"""gen_prompt.py：persona.json + 场景 + 视图 → 分层提示词
模板从 contracts/prompt-templates/{pixel,splash}.json 读取（可 --templates 覆盖），缺失时回退内置默认。
用法：python gen_prompt.py <persona.json> --scene pixel|splash --view <视图> [--exp happy] [--templates <目录>]
"""
import json, argparse, os, sys

_DEFAULT = {
    "pixel": {
        "style_anchor": "pixel art, 16-bit style, limited color palette, hard edges, no anti-aliasing, "
                        "grid-aligned pixels, sprite-sheet ready, transparent background",
        "views": {
            "front": "front view, idle, standing facing viewer, full body",
            "side": "side view, full body, profile facing left, same character design as front view",
            "back": "back view, full body, seen from behind, same character design",
            "three_view": "character sheet, front / side / back three views, same character, consistent design",
            "idle": "animation frame, idle pose, single frame, consistent with reference",
            "walk": "animation frame, walk cycle pose, single frame, consistent with reference",
            "attack": "animation frame, attacking pose, single frame, consistent with reference",
            "hurt": "animation frame, hurt pose, single frame, consistent with reference",
            "sprite_sheet": "sprite sheet, evenly spaced grid of animation frames, same character",
            "directional": "directional sprite sheet, 4 directions (down/up/left/right), same character",
        },
        "output_constraint": "same character, consistent design, no text, no watermark",
    },
    "chibi": {
        "style_anchor": "chibi anime style, cute small character with big head and small body (about 2-3 heads tall), clean lineart, soft cel coloring, cute expressive face, transparent background",
        "views": {
            "front": "front view, chibi full body, standing facing viewer, big head small body proportions",
            "side": "side view, chibi full body, profile facing left, same character design as front view",
            "back": "back view, chibi full body, seen from behind, same character design",
            "three_view": "character sheet, front / side / back three views, same chibi character, consistent design",
            "idle": "animation frame, idle pose, chibi, single frame, consistent with reference",
            "walk": "animation frame, walk cycle pose, chibi, single frame, consistent with reference",
            "attack": "animation frame, attacking pose, chibi, single frame, consistent with reference",
            "hurt": "animation frame, hurt pose, chibi, single frame, consistent with reference",
            "sprite_sheet": "sprite sheet, evenly spaced grid of animation frames, same chibi character",
            "directional": "directional sprite sheet, 4 directions (down/up/left/right), same chibi character",
        },
        "output_constraint": "same chibi character, consistent design, no text, no watermark",
    },
    "splash": {
        "style_anchor": "high-quality game splash art, anime style, clean lineart, detailed rendering, vibrant colors",
        "views": {
            "portrait": "full-body splash art, standing pose, facing viewer",
            "bust": "head-and-shoulders chest-up portrait closeup, facing viewer, same character design",
            "expressions": "same character, head-and-shoulders closeup, {exp} expression",
            "turnaround": "same character, three-quarter / side / back views, same outfit and colors",
            "side_view": "same character, full body, side view profile facing left, exact same outfit hair colors and design as the front view, consistent design",
            "back_view": "same character, full body, back view seen from behind, exact same outfit hair colors and design as the front view, consistent design",
            "action": "same character, dynamic action pose, full body",
        },
        "output_constraint": "same character, consistent design, no text, no watermark",
    },
}

def _load_templates(tpl_dir=None):
    merged = json.loads(json.dumps(_DEFAULT))
    if tpl_dir and os.path.isdir(tpl_dir):
        for scene in ("pixel", "splash"):
            f = os.path.join(tpl_dir, f"{scene}.json")
            if os.path.exists(f):
                try:
                    with open(f, encoding="utf-8-sig") as fh:
                        data = json.load(fh)
                    merged[scene].update(data)
                except Exception as e:
                    print(f"警告: 模板 {f} 加载失败({e})，使用内置", file=sys.stderr)
    return merged

STYLE_SIGNATURE_ARKNIGHTS = (
    "Arknights official art style (Wei@W style signature): thin clean elegant lineart, "
    "soft painterly cel-shading with gentle gradients, low-saturation muted warm-gray palette "
    "(#B8AD9E #6E6558 #F5F0E8), delicate fabric and armor detail rendering, soft diffuse lighting, "
    "gentle highlight roll-off, subtle film-like finish, semi-realistic proportions, "
    "no heavy outline, no CG plastic skin."
)

STYLE_SIGNATURE_CHIBI_ARKNIGHTS = (
    "Arknights chibi style (2D in-game sprite): cute small character about 2-3 heads tall, "
    "big head, large expressive eyes, small body, clean thin lineart, soft cel shading, "
    "muted warm-gray palette (#B8AD9E #6E6558 #F5F0E8), simple readable silhouette, "
    "game-ready sprite look, no heavy outline, no CG plastic skin."
)
TEMPLATES = _load_templates()

def build_prompt(persona, scene, view, exp="neutral", templates=None):
    tpl = templates or TEMPLATES
    style = persona.get("style", {})
    style_type = scene if scene in tpl else style.get("type", "splash")
    t = tpl.get(style_type, tpl["splash"])
    v = persona.get("visual", {})
    parts = [v.get("subject", persona.get("name", ""))]
    for key in ("outfit", "equipment", "detail"):
        if v.get(key):
            parts.append(v[key])
    body = ", ".join(p for p in parts if p)
    anchor = style.get("anchor") or t.get("style_anchor", "")
    if style.get("palette"):
        anchor += f", palette: {style['palette']}"
    # 分辨率只对像素场景生效（splash 不需要 64x64 这类约束）
    if style_type == "pixel" and style.get("resolution"):
        anchor += f", resolution {style['resolution']}"
    vt = t.get("views", {}).get(view, view).replace("{exp}", exp)
    constraint = t.get("output_constraint", "")
    return f"{body}, {anchor}, {vt}, {constraint}"

EXP_EDIT_PROMPTS = {
    "happy": "warm bright happy smile, eyes slightly closed and cheerful, relaxed brows",
    "sad": "sad expression, downturned mouth, slightly teary eyes, worried brows",
    "angry": "angry expression, furrowed brows, glaring eyes, tightened mouth",
    "neutral": "calm neutral expression, relaxed eyes and mouth, composed face",
}

def build_exp_edit_prompt(persona, emotion="happy"):
    """表情差分专用（人脸区域编辑）：Change only X + 保锁清单（SKILL_gpt-image-2.md 5.2）。
    保持整张图完全不变，只改表情；逐项锁 identity/pose/构图/光线/阴影/背景/服装，避免模型重绘。"""
    e = EXP_EDIT_PROMPTS.get(emotion, EXP_EDIT_PROMPTS["neutral"])
    return (
        "Change only the facial expression to: " + e + ". Preserve exactly: "
        "identity (same face shape, same eyes, same hairstyle and hair color, same skin tone), "
        "pose and body geometry (same posture, same limb positions, same proportions), "
        "camera angle, crop, and framing, lighting direction and shadow placement, "
        "every background element, the outfit, and all colors. "
        "Do not replace the face with a generalized, beautified, or idealized face. "
        "Keep natural skin texture. Keep everything else in the image unchanged. "
        "Anime game portrait expression swap, single face, no text, no watermark"
    )
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--scene", choices=["pixel", "splash"], required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--exp", default="neutral")
    ap.add_argument("--templates", default=None)
    a = ap.parse_args()
    tpls = _load_templates(a.templates)
    with open(a.persona, encoding="utf-8-sig") as f:
        persona = json.load(f)
    print(build_prompt(persona, a.scene, a.view, a.exp, tpls))

if __name__ == "__main__":
    sys.exit(main())


def build_style_prompt(persona, with_composition="full body, standing pose, facing viewer", multi_ref=True, ar=None):
    """新方法（SKILL_gpt-image-2.md 5.3）：风格签名 + 多图分工 + No-Beautify。
    参考图：Image1=风格锚点 / Image2=同风格细节，prompt 内按编号声明分工。
    与无参考的 build_prompt 结构完全不同（聚焦画风迁移）。"""
    v = persona.get("visual", {})
    parts = [v.get("subject", persona.get("name", ""))]
    for k in ("outfit", "equipment", "detail"):
        if v.get(k):
            parts.append(v[k])
    desc = ", ".join(p for p in parts if p)
    style = persona.get("style", {})
    style_type = style.get("type", "splash")
    if style_type == "chibi":
        sig = style.get("signature") or STYLE_SIGNATURE_CHIBI_ARKNIGHTS
    else:
        sig = style.get("signature") or STYLE_SIGNATURE_ARKNIGHTS
    if multi_ref:
        role = ("Image 1 is the art-style anchor: learn ONLY its lineart, coloring, shading, "
                "painterly texture and finish quality. Image 2 is an additional same-style detail "
                "reference; use it only for style details.")
    else:
        role = ("Study the reference artwork's art style very carefully: its lineart, coloring, "
                "shading, painterly texture and finish.")
    return (
        role + " Draw a NEW original character in EXACTLY this art style: " + desc + ". "
        + with_composition + ". Clean simple background. "
        "Do NOT copy the reference character's face, pose, or outfit. "
        "Match the line weight, coloring/shading technique, level of detail and finish exactly. "
        "Style consistency first; do not invent a new style. " + sig + " "
        f"natural skin texture, visible pores, no text, no watermark. " + (ar or ("AR 1:1" if style_type in ("chibi", "pixel") else "AR 3:4"))
    )


def build_chibi_pose_edit_prompt(persona, view, hero_note="the chibi character in the input image"):
    """chibi Hero Reference 编辑：以已验收的 front 为锚点，只换姿势/视角，锁死身份/服装/配色/比例/画风。"""
    return (
        f"Same chibi character as {hero_note} — same face, same hair (long silver-white hair), "
        f"same emerald green eyes, same green leather armor with silver trim, same composite bow, "
        f"same proportions (about 2-3 heads tall), same art style and same colors. "
        f"Change ONLY the view/pose to: {view}. "
        "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
        "body proportions, art style (clean thin lineart, soft cel shading, muted warm-gray palette). "
        "Do not replace the character with a generalized or different design. "
        "Game-ready chibi sprite, single character, no text, no watermark. AR 1:1"
    )

