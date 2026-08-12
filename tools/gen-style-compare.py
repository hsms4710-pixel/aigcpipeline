#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-style-compare.py — 同一角色多画风对比生成（调研用）
用法: python gen-style-compare.py <persona.json> --out <dir> [--styles hd2d,anime2d,pixel]
产出每个画风一张半身立绘 + 对比拼图 compare_sheet.png
"""
import os, sys, json, time, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STYLES = {
    "hd2d": "HD-2D style (Octopath Traveler / Triangle Strategy aesthetic), pixel-art characters with modern 3D lighting, depth-of-field, painterly rendering, rich gradients, 2D game splash",
    "anime2d": "high-quality 2D anime game art, Arknights (明日方舟) official style, soft painterly cel-shading, elegant thin lineart, subtle gradients, muted warm palette, detailed rendering",
    "pixel": "detailed pixel art portrait, 16-bit RPG style, limited color palette with dithering, clean crisp pixel edges, retro game dialogue portrait, expressive character design",
    "gacha2d": "high-quality 2D gacha game art style (Genshin Impact / Arknights level), polished cel-shading with rim light, refined lineart, vibrant saturated palette, premium splash art",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--out", required=True)
    ap.add_argument("--styles", default="hd2d,anime2d,pixel,gacha2d")
    a = ap.parse_args()
    with open(a.persona, encoding="utf-8-sig") as f:
        persona = json.load(f)
    outdir = os.path.abspath(a.out)
    os.makedirs(outdir, exist_ok=True)
    v = persona.get("visual", {})
    parts = [v.get("subject", persona.get("name", ""))]
    for k in ("outfit", "equipment", "detail"):
        if v.get(k):
            parts.append(v[k])
    desc = ", ".join(p for p in parts if p)
    meta = {"character": persona.get("name"), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "styles": {}}
    from image_backend import gen_image
    from dotenv import load_dotenv
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(repo, "env", ".env"), override=True)
    from PIL import Image as _PIL
    for key in a.styles.split(","):
        key = key.strip()
        if key not in STYLES:
            print("未知风格:", key); continue
        prompt = (f"{desc}, {STYLES[key]}, head-and-shoulders chest-up portrait closeup, facing viewer, "
                  f"transparent background, no text, no watermark")
        out = os.path.join(outdir, f"{key}.png")
        print(f"[{key}] 生成中…")
        try:
            n, dt = gen_image(prompt, out, model="gpt-image-2", size="1024x1024",
                              backend="openai", transparent=True)
            meta["styles"][key] = {"prompt": prompt, "size_bytes": n, "elapsed_s": round(dt, 1)}
            print(f"  ok {key}.png ({n}B, {dt:.1f}s)")
        except Exception as e:
            print(f"  ERR {key}: {e}")
    files = [os.path.join(outdir, f"{k}.png") for k in a.styles.split(",") if os.path.exists(os.path.join(outdir, f"{k}.png"))]
    if files:
        ims = [_PIL.open(f).convert("RGBA") for f in files]
        w = max(i.width for i in ims); h = max(i.height for i in ims)
        cols = len(ims)
        sheet = _PIL.new("RGBA", (w * cols, h), (255, 255, 255, 255))
        for idx, im in enumerate(ims):
            sheet.paste(im, (idx * w, 0))
        sheet.save(os.path.join(outdir, "compare_sheet.png"))
        print("对比拼图: compare_sheet.png", sheet.size)
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return 0

if __name__ == "__main__":
    sys.exit(main())
