# -*- coding: utf-8 -*-
"""gen-transparent-variants.py — 透明背景版本（hd2d / pixel_hard 小人 + splash_v9 立绘，quality 对照）
依据 spec/style-research.md §7 锚点定稿：立绘=splash_v9，小人=chibi_v4。
文章参考（yingtu.ai gpt-image-2 质量）：quality=high 作最终资产对照，transparent 出透明底。
用法:
  python gen-transparent-variants.py [--only chibi_hd2d,chibi_pixel,splash_high,splash_default]
  --no-quality 时跳过 quality=high（全部默认档）
"""
import os, sys, time, json, argparse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from image_backend import gen_image
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, "env", ".env"), override=True)

DEMO = os.path.join(BASE, "assets", "demo")
OUT = os.path.join(DEMO, "style_batch", "transparent_v1")
SPLASH_ANCHOR = os.path.join(DEMO, "char_ailin_splash_v9", "portrait", "full.png")
CHIBI_ANCHOR = os.path.join(DEMO, "char_ailin_chibi_v4", "portrait", "front_b.png")

# ---- 角色描述（与 persona_chibi.json / splash_v9 一致）----
CHAR = ("young female elf ranger, slender build, silver-white long hair, emerald green eyes, "
        "green leather armor with silver trim, composite bow")

STYLE_SPLASH_V9 = ("Arknights official art style: thin dark-brown elegant lineart, thick-painting with cel-shading hybrid, "
                   "low-saturation cool-dark palette (silver-white / deep green / dark brown / dark gold-gray), "
                   "single main light source with fine highlights, slender stylized 2D anime proportions, "
                   "dark fantasy elegant ranger vibe, refined fabric and armor rendering")

STYLE_HD2D = ("HD-2D game style (Octopath Traveler / Triangle Strategy aesthetic): pixel-art character with modern "
              "3D lighting, painterly rich gradients, soft depth-of-field, crisp readable silhouette")

STYLE_PIXEL_HARD = ("hard-edged pixel art (16/24-bit game sprite): limited color palette with dithering, "
                    "crisp clean pixel edges, no anti-aliasing blur, flat cel shading, sprite-sheet ready")

TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): NO background scenery, "
               "NO floor, NO ground shadow, NO backdrop, NO vignette, NO scene elements, NO watermark, NO text. "
               "Only the character visible.")

def build(prompt, out, ref, quality=None):
    kw = dict(prompt=prompt, out=out, ref=ref, model="gpt-image-2", size="1024x1024",
              transparent=True)
    if quality is not None:
        kw["quality"] = quality
    return gen_image(**kw)

def run(label, fn, retries=3, degrade_quality=None):
    last = None
    for i in range(retries):
        try:
            n, dt = fn()
            print(f"[{label}] OK bytes={n} time={dt:.1f}s")
            return True, {"ok": True, "sec": round(dt, 1), "size": n}
        except Exception as e:
            last = e
            msg = str(e)[:300]
            print(f"[{label}] attempt {i+1} failed: {type(e).__name__}: {msg}")
            if degrade_quality is not None and ("quality" in msg.lower() or "invalid" in msg.lower() or "parameter" in msg.lower()):
                print(f"[{label}] quality 参数不被支持 -> 降级为默认质量重试")
                return run(label, degrade_quality, retries=retries, degrade_quality=None)
            time.sleep(8)
    return False, {"ok": False, "err": str(last)[:300]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="comma list: chibi_hd2d,chibi_pixel,splash_high,splash_default")
    ap.add_argument("--no-quality", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    meta = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "jobs": {}}

    jobs = []
    if a.only:
        sel = [x.strip() for x in a.only.split(",")]
    else:
        sel = ["chibi_hd2d", "chibi_pixel", "splash_high", "splash_default"]

    # 小人 hd2d（A-pose，透明，轮廓干净）
    if "chibi_hd2d" in sel:
        jobs.append(("chibi_hd2d", os.path.join(OUT, "chibi_hd2d_t.png"), CHIBI_ANCHOR,
                     (None if a.no_quality else "high"), (
            "Same character as the reference image (" + CHAR + "), chibi proportions about 2.5 heads tall, "
            "big head small body, large expressive eyes. " + STYLE_HD2D + ". "
            "Standing neutral A-pose facing viewer, arms slightly away from the body, full body visible, "
            "clean readable silhouette. " + TRANSPARENT + " AR 1:1")))
    # 小人 pixel_hard（透明，可拆层）
    if "chibi_pixel" in sel:
        jobs.append(("chibi_pixel", os.path.join(OUT, "chibi_pixel_hard_t.png"), CHIBI_ANCHOR,
                     (None if a.no_quality else "high"), (
            "Same character as the reference image (" + CHAR + "), chibi proportions about 2.5 heads tall, "
            "big head small body. " + STYLE_PIXEL_HARD + ". "
            "Standing neutral A-pose facing viewer, arms slightly away from the body, full body visible, "
            "flat clean silhouette, easy to cut into separate body parts. " + TRANSPARENT + " AR 1:1")))
    # 立绘 splash_v9：quality=high（文章建议的最终质量对照）
    if "splash_high" in sel:
        jobs.append(("splash_high", os.path.join(OUT, "splash_v9_high_t.png"), SPLASH_ANCHOR,
                     (None if a.no_quality else "high"), (
            "Same character as the reference image (" + CHAR + "), full-body elegant standing pose, "
            "facing viewer, slender stylized proportions. " + STYLE_SPLASH_V9 + ". "
            "Isolated character cutout. " + TRANSPARENT + " AR 3:4")))
    # 立绘 splash_v9：默认档（quality 对照：high vs 默认）
    if "splash_default" in sel:
        jobs.append(("splash_default", os.path.join(OUT, "splash_v9_default_t.png"), SPLASH_ANCHOR, None, (
            "Same character as the reference image (" + CHAR + "), full-body elegant standing pose, "
            "facing viewer, slender stylized proportions. " + STYLE_SPLASH_V9 + ". "
            "Isolated character cutout. " + TRANSPARENT + " AR 3:4")))

    for label, out, ref, quality, prompt in jobs:
        print(f"\n[{label}] generating -> {os.path.basename(out)} (quality={quality or 'default'})")
        ok, info = run(label, lambda out=out, ref=ref, quality=quality, prompt=prompt: build(prompt, out, ref, quality),
                       degrade_quality=(lambda: lambda out=out, ref=ref, prompt=prompt: build(prompt, out, ref, None))() if quality else None)
        meta["jobs"][label] = {**info, "prompt": prompt, "quality": quality or "default"}
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("\nDONE ->", OUT)
    return 0

if __name__ == "__main__":
    sys.exit(main())
