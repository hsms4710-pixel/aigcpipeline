# -*- coding: utf-8 -*-
"""gen-side-frames.py — 生成艾琳侧面帧（横板专用）：idle/walk/attack/hurt side view
锚点：hero matte（保持身份一致）；风格：pixel_hard
"""
import os, sys, time, json, argparse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from image_backend import gen_image
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, "env", ".env"), override=True)

ap = argparse.ArgumentParser()
ap.add_argument("--style", default="pixel_hard", choices=["pixel_hard", "hd2d"])
a = ap.parse_args()
STYLE = ("hard-edged pixel-art game sprite style: clean crisp blocky pixels, limited color palette with dithering, flat cel shading, sprite-sheet ready, retro game look"
         if a.style == "pixel_hard" else
         "HD-2D game style (Octopath Traveler aesthetic): pixel-art character with modern 3D lighting, painterly rich gradients, crisp readable silhouette, clean thin lineart")
HERO = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2",
                    "hero_pixel_final.png" if a.style == "pixel_hard" else "hero_hd2d_final.png")
OUTDIR = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2",
                      "frames_pixel_side" if a.style == "pixel_hard" else "frames_hd2d_side")
TAG = a.style

CHAR = ("Same chibi character as the reference image: young female elf ranger, slender build, "
        "silver-white long hair, emerald green eyes, green leather armor with silver trim, composite bow, "
        "about 2.5 heads tall, big head small body")
SIDE = ("character in STRICT SIDE PROFILE facing RIGHT (90-degree profile, one eye visible, "
        "bow held in front, legs in profile). Side view platformer sprite, running right.")
TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible. AR 1:1")
FRAMING = ("Consistent framing and scale: character centered horizontally, BOTH FEET clearly visible "
           "and planted on the same ground line at the bottom, same character size across all frames, "
           "no zoom, no cropping, no floating.")

FRAMES = {
    "idle_1": "idle pose standing side profile, gentle breathing, calm face",
    "idle_2": "idle pose standing side profile, slight sway, calm face",
    "walk_1": "walk cycle frame 1/4 side view: front foot planted, rear foot lifting",
    "walk_2": "walk cycle frame 2/4 side view: stride passing, body lowest point",
    "walk_3": "walk cycle frame 3/4 side view: rear leg pushing, front leg swinging forward",
    "walk_4": "walk cycle frame 4/4 side view: front foot landing, body balanced",
    "attack_1": "attack frame 1/3 side view: drawing the bow, arrow nocked, arms pulling back",
    "attack_2": "attack frame 2/3 side view: fully drawn, aiming right",
    "attack_3": "attack frame 3/3 side view: arrow released, bow snapping forward, follow-through",
    "hurt_1": "hurt frame side view: hit impact, leaning back, surprised face",
}

hero = HERO
outdir = OUTDIR
os.makedirs(outdir, exist_ok=True)
meta = {"style": TAG, "view": "side", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "frames": {}}
for name, desc in FRAMES.items():
    out = os.path.join(outdir, f"{name}.png")
    prompt = (CHAR + ". " + STYLE + ". " + SIDE + ". " + desc + ". " + FRAMING + ". "
              "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
              "body proportions, art style, line weight. Same character in every frame. " + TRANSPARENT)
    print(f"[{name}] generating...", flush=True)
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
        print(f"  [{name}] FAILED", flush=True)
    # 每帧后增量保存 meta（防超时丢进度）
    with open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
print("DONE")
