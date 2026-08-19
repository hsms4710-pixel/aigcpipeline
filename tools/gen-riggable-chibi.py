# -*- coding: utf-8 -*-
"""gen-riggable-chibi.py — 生成「可骨骼绑定」的 A-pose 像素小人（无遮挡、四肢清晰分离）
用法: python gen-riggable-chibi.py --out <png> [--prompt "..."] [--model gpt-image-2] [--size 1024x1024]
"""
import os, sys, time, argparse, json
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base, 'tools'))
os.chdir(base)

DEFAULT_PROMPT = (
    "2D pixel art game sprite, cute chibi elf archer girl, about 2 to 3 heads tall, "
    "big head with large expressive eyes, short silver-white hair, simple green tunic and brown pants, "
    "front view, standing in symmetric A-pose (both arms slightly raised outward from the body, "
    "straight arms, palms facing forward, arms clearly separated from the torso with visible gaps at shoulders), "
    "NO cape, NO weapons, NO bow, NO quiver, NO accessories covering the body, "
    "clean simple readable silhouette, arms and legs fully visible and clearly separated "
    "at shoulders, elbows, knees and ankles, "
    "simple cel pixel shading, limited color palette, hard pixel edges, grid-aligned, sprite-sheet ready, "
    "full body, single character centered, transparent background, no text, no watermark"
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(base, "assets", "demo", "chibi_apose.png"))
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--model", default="gpt-image-2")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--meta", default=None)
    a = ap.parse_args()
    from dotenv import load_dotenv
    load_dotenv(os.path.join(base, "env", ".env"), override=True)
    from image_backend import gen_image
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    t0 = time.time()
    gen_image(a.prompt, a.out, model=a.model, size=a.size)
    dt = round(time.time() - t0, 1)
    print("OK out=", a.out, "size=", os.path.getsize(a.out), "sec=", dt)
    if a.meta:
        json.dump({"prompt": a.prompt, "model": a.model, "size": a.size, "seconds": dt,
                   "generated": time.strftime("%Y-%m-%d %H:%M:%S")},
                  open(a.meta, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()