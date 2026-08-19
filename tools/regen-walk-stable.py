# -*- coding: utf-8 -*-
"""regen-walk-stable.py — 重生成侧视 walk 帧（强一致性：只有腿/臂运动，头发/披风/衣摆静止）"""
import os, sys, time, json
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from image_backend import gen_image
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, "env", ".env"), override=True)

CHAR = ("Same chibi character as the reference image: young female elf ranger, slender build, "
        "silver-white long hair, emerald green eyes, green leather armor with silver trim, composite bow, "
        "about 2.5 heads tall, big head small body")
STYLE = "hard-edged pixel-art game sprite style: clean crisp blocky pixels, limited color palette with dithering, flat cel shading, sprite-sheet ready, retro game look"
SIDE = ("character in STRICT SIDE PROFILE facing RIGHT (90-degree profile, one eye visible, "
        "bow held in front, legs in profile). Side view platformer sprite, running right.")
STABLE = ("CRITICAL consistency rule: ONLY the legs and arms move between frames for the walk cycle. "
          "Hair, cloak, skirt hem, bow, face, and torso must remain EXACTLY IDENTICAL across all frames — "
          "no hair sway, no cloth ripple, no outline flicker. Body bob minimal and smooth. "
          "Feet planted on the same ground line, no floating, no vertical jump between frames.")
TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible. AR 1:1")
FRAMING = ("Consistent framing and scale: character centered horizontally, BOTH FEET clearly visible "
           "and planted on the same ground line at the bottom, same character size across all frames, "
           "no zoom, no cropping, no floating.")

WALKS = {
    "walk_1": "walk cycle frame 1/4 side view: front foot planted, rear foot lifting",
    "walk_2": "walk cycle frame 2/4 side view: stride passing, legs crossing",
    "walk_3": "walk cycle frame 3/4 side view: rear leg pushing, front leg swinging forward",
    "walk_4": "walk cycle frame 4/4 side view: front foot landing, body balanced",
}
hero = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2", "hero_pixel_final.png")
outdir = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2", "frames_pixel_side")
meta = {"regen_walk": time.strftime("%Y-%m-%dT%H:%M:%S"), "frames": {}}
for name, desc in WALKS.items():
    out = os.path.join(outdir, f"{name}.png")
    prompt = (CHAR + ". " + STYLE + ". " + SIDE + ". " + desc + ". " + STABLE + ". " + FRAMING + ". "
              "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
              "body proportions, art style, line weight. Same character in every frame. " + TRANSPARENT)
    print(f"[{name}] regenerating...", flush=True)
    ok = False
    for i in range(4):
        try:
            n, dt = gen_image(prompt, out, ref=hero, model="gpt-image-2", size="1024x1024",
                              transparent=True, quality="high")
            print(f"  ok {n} bytes in {dt}s", flush=True)
            meta["frames"][name] = {"ok": True, "sec": round(dt, 1)}
            ok = True
            break
        except Exception as e:
            print(f"  attempt {i+1} fail: {type(e).__name__}: {str(e)[:130]}", flush=True)
            time.sleep(10)
    if not ok:
        meta["frames"][name] = {"ok": False}
    with open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
print("DONE")
