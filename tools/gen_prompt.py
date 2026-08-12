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
    """表情差分专用（人脸区域编辑）：保持整张图完全不变，只改表情。
    参考二次元游戏立绘表情切换（同构图同画风，只换面部表情）。"""
    e = EXP_EDIT_PROMPTS.get(emotion, EXP_EDIT_PROMPTS["neutral"])
    return (f"Keep this exact character, pose, outfit, hair, colors, lighting and composition 100% identical. "
            f"ONLY change her facial expression to: {e}. "
            f"Anime game portrait expression swap, single face, transparent background, no text, no watermark")

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


def build_style_prompt(persona, with_composition="full body, standing pose, facing viewer"):
    """有参考图（风格参考）时的专用 prompt：把参考图的画风（线稿/上色/渲染）迁移到新角色上。
    与无参考的 build_prompt 结构完全不同（聚焦画风迁移，而非拼模板）。"""
    v = persona.get("visual", {})
    parts = [v.get("subject", persona.get("name", ""))]
    for k in ("outfit", "equipment", "detail"):
        if v.get(k):
            parts.append(v[k])
    desc = ", ".join(p for p in parts if p)
    style = persona.get("style", {})
    anchor = style.get("anchor") or ""
    return (f"Study the reference artwork's ART STYLE very carefully: its lineart quality, coloring, "
            f"shading, painterly texture, rendering and finish. Draw a NEW original character in EXACTLY "
            f"this art style, using the same line weight, same coloring/shading technique, same level of detail "
            f"and same overall finish quality as the reference. The new character is: {desc}. {with_composition}. "
            f"Do NOT copy the reference character's face, pose or outfit, but DO match its art style exactly. "
            f"SINGLE standalone full-body illustration of ONE character only - NOT a character sheet, "
            f"NOT multiple views/poses, NOT a concept sheet. {anchor} transparent background, no text, no watermark")


