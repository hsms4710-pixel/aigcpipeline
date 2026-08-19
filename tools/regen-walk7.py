# -*- coding: utf-8 -*-
"""regen-walk7.py — 针对性重生成 walk_7（用 walk_6 锚点，强制高度/脚底/轮廓一致）"""
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
desc = ("walk cycle frame 2/4 side view: legs crossing mid-stride. "
        "CRITICAL: body height, head position, hair shape, cloak and skirt hem must match the reference "
        "walk frame EXACTLY (same silhouette height, same hair arc, same cloak drape) - only the legs change. "
        "Feet planted on the same ground line, body bob minimal, no vertical jump.")
TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible. AR 1:1")
FRAMING = ("Consistent framing and scale: character centered horizontally, BOTH FEET clearly visible "
           "and planted on the same ground line at the bottom, same character size across all frames, "
           "no zoom, no cropping, no floating.")

outdir = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2", "frames_pixel_side")
ref = os.path.join(outdir, "walk_1.png")  # walk_6 的源帧（walk_1 生成时编号）
out = os.path.join(outdir, "walk_2.png")
prompt = (CHAR + ". " + STYLE + ". " + SIDE + ". " + desc + ". " + FRAMING + ". "
          "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
          "body proportions, art style, line weight. Same character in every frame. " + TRANSPARENT)
print("[walk_2=walk_7] regenerating with walk_1 anchor...", flush=True)
for i in range(4):
    try:
        n, dt = gen_image(prompt, out, ref=ref, model="gpt-image-2", size="1024x1024",
                          transparent=True, quality="high")
        print(f"  ok {n} bytes in {dt}s", flush=True)
        break
    except Exception as e:
        print(f"  attempt {i+1} fail: {type(e).__name__}: {str(e)[:130]}", flush=True)
        time.sleep(10)
print("DONE")
