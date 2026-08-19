# -*- coding: utf-8 -*-
"""regen-walk4-v3.py — 重生成 hd2d walk_4，用 walk_1 锚点（此前候选更好）"""
import os, sys, time
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from image_backend import gen_image
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, "env", ".env"), override=True)

CHAR = ("Same chibi character as the reference image: young female elf ranger, slender build, "
        "silver-white long hair, emerald green eyes, green leather armor with silver trim, composite bow, "
        "about 2.5 heads tall, big head small body")
STYLE = "HD-2D game style (Octopath Traveler aesthetic): pixel-art character with modern 3D lighting, painterly rich gradients, crisp readable silhouette, clean thin lineart"
TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible. AR 1:1")
FRAMING_W4 = ("Consistent framing and scale: character centered horizontally, BOTH FEET near the bottom "
              "ground line just like the contact frames, feet only slightly crossed and barely lifted "
              "(one sole still touching the ground line), body height and bob equal to the other walk "
              "frames (NO jumping, NO floating, NO large vertical shift), no zoom, no cropping, "
              "same character size across all frames.")
desc = ("walk cycle frame 4/6 PASSING: legs crossing mid-stride, one foot planted on the ground line, "
        "the other foot slightly lifted but keeping the body at the same height as the contact frames")

outdir = os.path.join(BASE, "assets", "demo", "style_batch", "transparent_v2", "frames_hd2d_v2")
ref = os.path.join(outdir, "walk_1.png")
out = os.path.join(outdir, "walk_4.png")
prompt = (CHAR + ". " + STYLE + ". " + desc + ". " + FRAMING_W4 + ". "
          "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
          "body proportions, art style, line weight. Same character in every frame. " + TRANSPARENT)
print("[hd2d] walk_4 (walk_1 anchor) generating...", flush=True)
for i in range(3):
    try:
        n, dt = gen_image(prompt, out, ref=ref, model="gpt-image-2", size="1024x1024",
                          transparent=True, quality="high")
        print(f"  ok {n} bytes in {dt}s", flush=True)
        break
    except Exception as e:
        print(f"  attempt {i+1} fail: {type(e).__name__}: {str(e)[:150]}", flush=True)
        time.sleep(10)
print("DONE")
