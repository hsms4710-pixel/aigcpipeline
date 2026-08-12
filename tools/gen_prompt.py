#!/usr/bin/env python3
"""gen-prompt.py：persona.json + 场景 + 视图 → 分层提示词（读 persona-schema v0 + prompt-templates 设计）
用法：python gen-prompt.py <persona.json> --scene pixel|splash --view <视图> [--exp happy]
"""
import json, argparse, os, sys

VIEW_TEMPLATES = {
    "pixel": {
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
    "splash": {
        "portrait": "full-body splash art, standing pose, facing viewer",
        "expressions": "same character, {exp} expression, head-and-shoulders closeup",
        "turnaround": "same character, three-quarter / side / back views, same outfit and colors",
        "action": "same character, dynamic action pose, full body",
    },
}
STYLE_ANCHORS = {
    "pixel": "pixel art, 16-bit style, limited color palette, hard edges, no anti-aliasing, "
             "grid-aligned pixels, sprite-sheet ready, transparent background",
    "splash": "high-quality game splash art, anime style, clean lineart, detailed rendering, vibrant colors",
}
OUTPUT_CONSTRAINT = "same character, consistent design, no text, no watermark"


def build_prompt(persona, scene, view, exp="neutral"):
    style = persona.get("style", {})
    style_type = scene if scene in STYLE_ANCHORS else style.get("type", "splash")  # scene 优先
    # 主体段
    v = persona.get("visual", {})
    parts = []
    subject = v.get("subject", persona.get("name", ""))
    parts.append(subject)
    for key, label in (("outfit", None), ("equipment", None), ("detail", None)):
        if v.get(key):
            parts.append(v[key])
    body = ", ".join(p for p in parts if p)
    # 风格锚点
    anchor = style.get("anchor") or STYLE_ANCHORS.get(style_type, STYLE_ANCHORS["splash"])
    if style.get("palette"):
        anchor += f", palette: {style['palette']}"
    if style.get("resolution"):
        anchor += f", resolution {style['resolution']}"
    # 视图
    vt = VIEW_TEMPLATES.get(style_type, VIEW_TEMPLATES["splash"]).get(view, view)
    vt = vt.replace("{exp}", exp)
    prompt = f"{body}, {anchor}, {vt}, {OUTPUT_CONSTRAINT}"
    return prompt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona", help="persona.json 路径")
    ap.add_argument("--scene", choices=["pixel", "splash"], required=True)
    ap.add_argument("--view", required=True, help="front/side/back/three_view/idle/walk/attack/hurt/sprite_sheet/directional/portrait/expressions/turnaround/action")
    ap.add_argument("--exp", default="neutral")
    a = ap.parse_args()
    with open(a.persona, encoding="utf-8-sig") as f:
        persona = json.load(f)
    print(build_prompt(persona, a.scene, a.view, a.exp))


if __name__ == "__main__":
    sys.exit(main())
