# -*- coding: utf-8 -*-
"""regen-walk4-v2.py — 重生成 walk_4，改用 hero matte 锚点保持身份一致"""
import os, sys, time
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from image_backend import gen_image
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, "env", ".env"), override=True)

CHAR = ("Same chibi character as the reference image: young female elf ranger, slender build, "
        "silver-white long hair, emerald green eyes, green leather armor with silver trim, composite bow, "
        "about 2.5 heads tall, big head small body")
STYLE = {
    "hd2d": "HD-2D game style (Octopath Traveler aesthetic): pixel-art character with modern 3D lighting, painterly rich gradients, crisp readable silhouette, clean thin lineart",
    "pixel_hard": "hard-edged pixel-art game sprite style: clean crisp blocky pixels, limited color palette with dithering, flat cel shading, sprite-sheet ready, retro game look",
}
TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible. AR 1:1")
FRAMING = ("Consistent framing and scale: character centered horizontally, full body including BOTH FEET "
           "clearly visible and planted on the same ground line at the bottom, same character size across "
           "all frames, no zoom, no cropping, no floating.")
DESC = ("walk cycle frame 4/6 PASSING: legs crossing mid-stride in a compact pose, both feet remaining "
        "near the ground line with one sole still touching, body bob minimal, same height as the idle pose")

hero = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2", "hero_hd2d_final.png")
for style in ["hd2d", "pixel_hard"]:
    outdir = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2",
                          "frames_hd2d_v2" if style == "hd2d" else "frames_pixel_hard")
    out = os.path.join(outdir, "walk_4.png")
    prompt = (CHAR + ". " + STYLE[style] + ". " + DESC + ". " + FRAMING + ". "
              "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
              "body proportions, art style, line weight. Same character in every frame. " + TRANSPARENT)
    print(f"[{style}] walk_4 (hero anchor) generating...", flush=True)
    for i in range(3):
        try:
            n, dt = gen_image(prompt, out, ref=hero, model="gpt-image-2", size="1024x1024",
                              transparent=True, quality="high")
            print(f"  ok {n} bytes in {dt}s", flush=True)
            break
        except Exception as e:
            print(f"  attempt {i+1} fail: {type(e).__name__}: {str(e)[:150]}", flush=True)
            time.sleep(10)
print("DONE")
