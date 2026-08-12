#!/usr/bin/env python3
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
            "expressions": "same character, {exp} expression, head-and-shoulders closeup",
            "turnaround": "same character, three-quarter / side / back views, same outfit and colors",
            "action": "same character, dynamic action pose, full body",
        },
        "output_constraint": "same character, consistent design, no text, no watermark",
    },
}

def _load_templates(tpl_dir=None):
    """从模板目录加载 {pixel,splash}.json；无则用内置默认。返回 {scene: {...}}"""
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
    if style.get("resolution"):
        anchor += f", resolution {style['resolution']}"
    vt = t.get("views", {}).get(view, view).replace("{exp}", exp)
    constraint = t.get("output_constraint", "")
    return f"{body}, {anchor}, {vt}, {constraint}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--scene", choices=["pixel", "splash"], required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--exp", default="neutral")
    ap.add_argument("--templates", default=None, help="模板目录（pixel.json/splash.json）")
    a = ap.parse_args()
    tpls = _load_templates(a.templates)
    with open(a.persona, encoding="utf-8-sig") as f:
        persona = json.load(f)
    print(build_prompt(persona, a.scene, a.view, a.exp, tpls))

if __name__ == "__main__":
    sys.exit(main())
