# -*- coding: utf-8 -*-
"""gen-frame-cycle.py — 帧动画关键帧生成（B 路线）
核心：所有帧从同一个 matte hero 作为唯一身份锚点重绘，固定角色+风格块，保证帧间一致。
用法:
  python gen-frame-cycle.py --style hd2d --hero <matte.png> --out <dir> [--only idle,walk,attack,hurt]
"""
import os, sys, time, json, argparse
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

FRAMES = {
    "idle":   [("idle_1", "idle pose standing, gentle breathing in, arms relaxed at sides, calm face"),
               ("idle_2", "idle pose standing, breathing neutral, arms relaxed, subtle sway"),
               ("idle_3", "idle pose standing, gentle breathing out, arms relaxed, calm face")],
    "walk":   [("walk_1", "walk cycle frame 1/6 CONTACT: front foot planted on ground, rear foot lifting, slight forward lean"),
               ("walk_2", "walk cycle frame 2/6 DOWN: body lowest point, legs passing each other, arms mid-swing"),
               ("walk_3", "walk cycle frame 3/6 RECOIL: rear leg pushing off, front leg beginning to swing forward"),
               ("walk_4", "walk cycle frame 4/6 PASSING: legs crossing, body at highest point, arms swinging"),
               ("walk_5", "walk cycle frame 5/6 UP: front foot lifting, rear leg straightening, arms at swing extreme"),
               ("walk_6", "walk cycle frame 6/6 LAND: front foot coming down to contact, body balanced")],
    "attack": [("attack_1", "attack frame 1/4: drawing the bow, arrow nocked, arms pulling back, body steady"),
               ("attack_2", "attack frame 2/4: fully drawn, aiming, focused, slight lean forward"),
               ("attack_3", "attack frame 3/4: arrow released, bow snapping forward, follow-through"),
               ("attack_4", "attack frame 4/4: recovery, bow returning to rest, body settling")],
    "hurt":   [("hurt_1", "hurt frame 1/3: hit impact, leaning back, arms flinching, surprised face"),
               ("hurt_2", "hurt frame 2/3: recoiling backward, off balance, guard up"),
               ("hurt_3", "hurt frame 3/3: recovering stance, returning to standing")],
}

TRANSPARENT = ("Isolated character on a FULLY TRANSPARENT background (alpha transparency): "
               "NO background scenery, NO floor, NO ground shadow, NO backdrop, NO vignette, "
               "NO scene elements, NO watermark, NO text. Only the character visible. AR 1:1")

FRAMING = ("Consistent framing and scale: character centered horizontally, full body including BOTH FEET "
           "clearly visible and planted on the same ground line at the bottom, same character size across "
           "all frames, no zoom, no cropping, no floating.")

def gen(prompt, out, ref, retries=3):
    last = None
    for i in range(retries):
        try:
            n, dt = gen_image(prompt, out, ref=ref, model="gpt-image-2", size="1024x1024",
                              transparent=True, quality="high")
            return True, {"ok": True, "sec": round(dt,1), "size": n}
        except Exception as e:
            last = e
            print(f"  attempt {i+1} fail: {type(e).__name__}: {str(e)[:120]}")
            time.sleep(8)
    return False, {"ok": False, "err": str(last)[:200]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True, choices=list(STYLE))
    ap.add_argument("--hero", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sel = set(a.only.split(",")) if a.only else set(FRAMES)
    meta = {"style": a.style, "hero": os.path.basename(a.hero), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "frames": {}}
    for action in sel:
        if action not in FRAMES: continue
        for name, desc in FRAMES[action]:
            out = os.path.join(a.out, f"{name}.png")
            if os.path.exists(out) and not a.force:
                print(f"[{action}] skip {name} (exists)"); continue
            prompt = (CHAR + ". " + STYLE[a.style] + ". " + desc + ". " + FRAMING + ". "
                      "Preserve exactly: identity, hairstyle and hair color, outfit and colors, "
                      "body proportions, art style, line weight. Same character in every frame. "
                      + TRANSPARENT)
            print(f"[{action}] {name} generating...")
            ok, info = gen(prompt, out, a.hero)
            meta["frames"][name] = {**info, "action": action, "desc": desc}
    with open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("DONE ->", a.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
