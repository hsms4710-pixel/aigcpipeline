"""gen-8dir-chibi.py — H1：以 chibi_v4 front_b 为锚点，gpt-image-2 生成 3/4 视角补全 8 向
输出: assets/demo/char_ailin_chibi_8dir/<dir>.png（front_left/front_right/back_left/back_right）
用法: python tools/gen-8dir-chibi.py [--dirs front_left front_right ...]
"""
import os, sys, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from image_backend import gen_image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHOR = os.path.join(REPO, "assets", "demo", "char_ailin_chibi_v4", "portrait", "front_b.png")
OUT_DIR = os.path.join(REPO, "assets", "demo", "char_ailin_chibi_8dir")

VIEWS = {
    "front_left":  "same character rotated to face the lower-left corner (3/4 front-left view), head turned slightly left, feet still planted on the same ground line",
    "front_right": "same character rotated to face the lower-right corner (3/4 front-right view), head turned slightly right, feet still planted on the same ground line",
    "back_left":   "same character seen from behind-left (3/4 back-left view), showing back of head and cape/hair, feet planted on the same ground line",
    "back_right":  "same character seen from behind-right (3/4 back-right view), showing back of head and cape/hair, feet planted on the same ground line",
}
PROMPT_HEAD = (
    "Keep the EXACT same pixel-art chibi character from the reference image: identical face, hair color/style, outfit, "
    "color palette, proportions and art style. ONLY change the viewing angle: "
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["front_left", "front_right"])
    ap.add_argument("--size", default="512x512")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    for d in args.dirs:
        if d not in VIEWS:
            print("skip unknown dir:", d); continue
        out = os.path.join(OUT_DIR, f"{d}.png")
        prompt = PROMPT_HEAD + VIEWS[d] + (". Transparent background, full body visible, no ground shadow, no text.")
        print(f"[H1] 生成 {d} ...")
        try:
            n, dt = gen_image(prompt, out, ref=ANCHOR, size=args.size, transparent=True, quality="high")
            print(f"  -> {d} {n/1024:.0f}KB {dt:.1f}s")
        except Exception as e:
            print(f"  FAIL {d}: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()