# -*- coding: utf-8 -*-
"""gen-chibi-v4.py：chibi 一致性（Hero Reference 策略）。
- 风格参考：方舟 Q 版小人帧（阿米娅-报童，512→放大 1024）
- hero：front 生成 2 张候选（front_a/front_b），其余 6 视图从指定 hero 编辑派生（同角色只换姿势/视角）
用法：
  python gen-chibi-v4.py --only hero                 # 生成 front_a/front_b 候选
  python gen-chibi-v4.py --only poses --hero front_b # 从 front_b 派生 side/back/idle/walk/attack/hurt
"""
import os, sys, time, json
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from gen_prompt import build_style_prompt, build_chibi_pose_edit_prompt
from image_backend import gen_image, prep_style_refs
from PIL import Image


def upscale_to(src, dst, target=1024):
    im = Image.open(src).convert("RGB")
    if im.width < target:
        h = int(im.height * target / im.width)
        im = im.resize((target, h), Image.LANCZOS)
        im.save(dst, "PNG")
        return dst
    return src


def run(label, fn, retries=4):
    last = None
    for i in range(retries):
        try:
            n, dt = fn()
            print(f"[{label}] OK bytes={n} time={dt:.1f}s")
            return True
        except Exception as e:
            last = e
            print(f"[{label}] attempt {i+1} failed: {type(e).__name__}: {str(e)[:120]}")
            time.sleep(10)
    print(f"[{label}] FAILED: {type(last).__name__}: {str(last)[:200]}")
    return False


def make_sheet(portrait, out_name="chibi_v4_review_sheet.png"):
    files = [os.path.join(portrait, f) for f in
             ["front_a.png", "front_b.png", "side.png", "back.png",
              "idle.png", "walk.png", "attack.png", "hurt.png"]]
    ims = [Image.open(p).convert("RGBA") for p in files if os.path.exists(p)]
    if not ims:
        return None
    cell = 360
    cells = []
    for im in ims:
        w, h = im.size
        s = cell / h
        cells.append(im.resize((max(1, int(w * s)), cell), Image.LANCZOS))
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, rows * cell), (245, 245, 245))
    for i, im in enumerate(cells):
        x = (i % cols) * cell + (cell - im.width) // 2
        y = (i // cols) * cell
        canvas.paste(im, (x, y), im)
    sheet = os.path.join(portrait, out_name)
    canvas.save(sheet)
    return sheet


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default=os.path.join(BASE, "assets", "demo", "char_ailin_chibi_v4"))
    ap.add_argument("--only", choices=["hero", "poses"], default=None)
    ap.add_argument("--hero", choices=["front_a", "front_b"], default="front_a")
    ap.add_argument("--force", action="store_true", help="重跑时删除已存在的图")
    a = ap.parse_args()

    with open(os.path.join(BASE, "assets", "demo", "persona_chibi.json"), encoding="utf-8-sig") as f:
        persona = json.load(f)

    portrait = os.path.join(a.out_dir, "portrait")
    os.makedirs(portrait, exist_ok=True)

    # 1) 风格参考：阿米娅 Q 版小人帧（放大到 1024）
    ref_dir = os.path.join(BASE, "assets", "reference", "arknights", "阿米娅", "小人", "阿米娅-报童-小人帧")
    cache = os.path.join(BASE, "assets", "demo", "style_attempts", "_refs")
    os.makedirs(cache, exist_ok=True)
    f0 = upscale_to(os.path.join(ref_dir, "阿米娅-报童-正面-Attack-x1_f0.png"), os.path.join(cache, "chibi_f0_1024.png"))
    f2 = upscale_to(os.path.join(ref_dir, "阿米娅-报童-正面-Attack-x1_f2.png"), os.path.join(cache, "chibi_f2_1024.png"))
    style_refs = prep_style_refs([f0, f2])

    model, size = "gpt-image-2", "1024x1024"
    hero_prompt = build_style_prompt(persona, "front view, chibi full body, standing facing viewer, big head small body proportions, idle stance, centered")

    # 2) hero front 候选
    if a.only in (None, "hero"):
        for cand in ("front_a", "front_b"):
            out = os.path.join(portrait, f"{cand}.png")
            if os.path.exists(out) and not a.force:
                print(f"[hero] skip {cand} (exists)")
                continue
            if os.path.exists(out) and a.force:
                os.remove(out)
            ok = run(f"hero {cand}", lambda out=out: gen_image(
                hero_prompt, out, style_ref=style_refs, model=model, size=size, transparent=True))
            if not ok:
                print(f"[hero] {cand} 失败，继续")
        print("[hero] done: front_a / front_b")

    # 3) 其余 6 视图从指定 hero 编辑派生
    if a.only in (None, "poses"):
        hero = os.path.join(portrait, f"{a.hero}.png")
        if not os.path.exists(hero):
            print(f"[poses] 缺少 {a.hero}.png，先跑 --only hero")
            return 1
        views = [("side", "side view, full body, profile facing left"),
                 ("back", "back view, full body, seen from behind"),
                 ("idle", "idle pose, standing, single animation frame"),
                 ("walk", "walk cycle pose, mid-step, single animation frame"),
                 ("attack", "attacking pose, drawing the bow, single animation frame"),
                 ("hurt", "hurt pose, leaning back, single animation frame")]
        for name, view in views:
            out = os.path.join(portrait, f"{name}.png")
            if os.path.exists(out) and not a.force:
                print(f"[poses] skip {name} (exists)")
                continue
            if os.path.exists(out) and a.force:
                os.remove(out)
            prompt = build_chibi_pose_edit_prompt(persona, view)
            ok = run(f"pose {name}", lambda out=out, prompt=prompt: gen_image(
                prompt, out, ref=hero, model=model, size=size, transparent=True))
            if not ok:
                print(f"[poses] {name} 失败，继续")
        print("[poses] done")

    # 4) 审阅拼图
    sheet = make_sheet(portrait)
    print("[sheet]", sheet)
    print("done:", a.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
