# -*- coding: utf-8 -*-
"""gen-chibi-final.py — 对齐 v9_v4_variants 的透明 hero + 全套姿势 + 无弓 A-pose
用法:
  python gen-chibi-final.py --only align_hd2d,align_pixel          # 对齐透明 hero
  python gen-chibi-final.py --only poses_hd2d,poses_pixel         # 全套姿势（基于已对齐 hero）
  python gen-chibi-final.py --only nobow_hd2d,nobow_pixel         # 无弓 A-pose
  --force 重跑（覆盖已存在）
"""
import os, sys, time, json, argparse
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from image_backend import gen_image
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, "env", ".env"), override=True)

DEMO = os.path.join(BASE, "assets", "demo")
VARIANTS = os.path.join(DEMO, "style_batch", "v9_v4_variants")
OUT = os.path.join(DEMO, "style_batch", "transparent_v2")
os.makedirs(OUT, exist_ok=True)

CHAR = ("young female elf ranger, slender build, silver-white long hair, emerald green eyes, "
        "green leather armor with silver trim, composite bow")

TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible.")

def _prep_ref(path, cache_dir=None):
    """参考图压成 1024px JPEG q88（中转站上传体积限制，越小越不容易断连）。"""
    from PIL import Image
    if cache_dir is None:
        cache_dir = os.path.join(OUT, "_refs")
    os.makedirs(cache_dir, exist_ok=True)
    im = Image.open(path).convert("RGB")
    if im.width > 1024:
        h = int(im.height * 1024 / im.width)
        im = im.resize((1024, h), Image.LANCZOS)
    dst = os.path.join(cache_dir, os.path.splitext(os.path.basename(path))[0] + "_1024q88.jpg")
    im.save(dst, "JPEG", quality=88)
    return dst

def gen(prompt, out, ref, quality="high", retries=3):
    last = None
    for i in range(retries):
        try:
            n, dt = gen_image(prompt, out, ref=ref, model="gpt-image-2", size="1024x1024",
                              transparent=True, quality=quality)
            return True, {"ok": True, "sec": round(dt,1), "size": n}
        except Exception as e:
            last = e
            print(f"  attempt {i+1} fail: {type(e).__name__}: {str(e)[:150]}")
            time.sleep(8)
    return False, {"ok": False, "err": str(last)[:200]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sel = [x.strip() for x in a.only.split(",")] if a.only else ["align_hd2d","align_pixel","poses_hd2d","poses_pixel","nobow_hd2d","nobow_pixel"]
    meta = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "jobs": {}}

    styles = {
        "hd2d": ("chibi_hd2d.png", "HD-2D game style (Octopath Traveler aesthetic): pixel-art character with modern 3D lighting, painterly rich gradients, crisp readable silhouette"),
        "pixel": ("chibi_pixel_hard.png", "pixel-art influenced chibi style, clean crisp outline, limited palette with dithering, sprite-sheet ready"),
    }
    for key, (src_fn, style_desc) in styles.items():
        src = os.path.join(VARIANTS, src_fn)
        hero_out = os.path.join(OUT, f"hero_{key}_final.png")

        if f"align_{key}" in sel:
            print(f"\n[align_{key}] -> {os.path.basename(hero_out)}")
            if os.path.exists(hero_out) and not a.force:
                print("  skip (exists)")
            else:
                prompt = ("Reproduce this EXACT same character in EXACTLY the same pose, same outfit, same colors, "
                          "same hair, same proportions, same art style (" + style_desc + "), same level of detail. "
                          "Do not change the character, pose, expression, or composition at all. "
                          "Only change the BACKGROUND: remove the current scene and output ONLY the character "
                          "isolated on a FULLY TRANSPARENT background (alpha transparency), no scene, no floor, "
                          "no shadow, no backdrop, no text, no watermark.")
                ok, info = gen(prompt, hero_out, _prep_ref(src))
                meta["jobs"][f"align_{key}"] = {**info, "prompt": prompt, "ref": src_fn}

        if f"poses_{key}" in sel:
            if not os.path.exists(hero_out):
                print(f"[poses_{key}] 缺 hero {hero_out}，先跑 align_{key}"); continue
            views = [("side","side view, full body, profile facing left, same character design"),
                     ("back","back view, full body, seen from behind, same character design"),
                     ("idle","idle pose, standing, single animation frame"),
                     ("walk","walk cycle pose, mid-step, single animation frame"),
                     ("attack","attacking pose, drawing the bow, single animation frame"),
                     ("hurt","hurt pose, leaning back, single animation frame")]
            for name, view in views:
                out = os.path.join(OUT, f"{key}_pose_{name}.png")
                if os.path.exists(out) and not a.force:
                    print(f"[poses_{key}] skip {name} (exists)"); continue
                prompt = ("Same chibi character as the reference image (" + CHAR + ") — same face, same silver-white long hair, "
                          "same emerald green eyes, same green leather armor with silver trim, same composite bow, "
                          "same proportions (about 2.5 heads tall), same art style (" + style_desc + "). "
                          "Change ONLY the view/pose to: " + view + ". "
                          "Preserve exactly: identity, hairstyle and hair color, outfit and colors, body proportions, art style. "
                          "Do not replace the character with a generalized or different design. " + TRANSPARENT + " AR 1:1")
                print(f"[poses_{key}] {name}")
                ok, info = gen(prompt, out, hero_out)
                meta["jobs"][f"pose_{key}_{name}"] = {**info, "prompt": prompt}

        if f"nobow_{key}" in sel:
            out = os.path.join(OUT, f"hero_{key}_nobow_apose.png")
            if os.path.exists(out) and not a.force:
                print(f"[nobow_{key}] skip (exists)"); continue
            prompt = ("Same chibi character as the reference image — same face, same silver-white long hair, "
                      "same emerald green eyes, same green leather armor with silver trim, same proportions "
                      "(about 2.5 heads tall), same art style (" + style_desc + "). "
                      "REMOVE the composite bow and quiver: empty hands, palms slightly open, "
                      "arms relaxed and slightly away from the body in a neutral A-pose, "
                      "standing facing viewer, full body visible, clean readable silhouette. "
                      "Preserve identity, hair, outfit and colors. " + TRANSPARENT + " AR 1:1")
            print(f"[nobow_{key}] -> {os.path.basename(out)}")
            ok, info = gen(prompt, out, hero_out)
            meta["jobs"][f"nobow_{key}"] = {**info, "prompt": prompt}

    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("\nDONE ->", OUT)
    return 0

if __name__ == "__main__":
    sys.exit(main())
