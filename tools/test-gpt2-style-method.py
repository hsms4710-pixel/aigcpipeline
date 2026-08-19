# -*- coding: utf-8 -*-
"""test-gpt2-style-method.py：按 SKILL_gpt-image-2.md 5.3 新方法实测 gpt-image-2 画风迁移。
多参考图分工（风格基准+同风格细节，压到 1152px 再上传）→ 失败自动回退单图。
用法：python tools/test-gpt2-style-method.py [--out xxx.png]
"""
import os, sys, time, traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from image_backend import gen_image

STYLE_SIG = (
    "Arknights official art style (Wei@W style signature): thin clean elegant lineart, "
    "soft painterly cel-shading with gentle gradients, low-saturation muted warm-gray palette "
    "(#B8AD9E #6E6558 #F5F0E8), delicate fabric and armor detail rendering, soft diffuse lighting, "
    "gentle highlight roll-off, subtle film-like finish, semi-realistic proportions, "
    "no heavy outline, no CG plastic skin."
)

CHAR = (
    "a young female elf ranger with a slender build, long silver-white hair, emerald green eyes, "
    "wearing a green leather armor with subtle silver trim, carrying a composite bow on her back"
)

PROMPT_MULTI = (
    "Image 1 is the art-style anchor: learn ONLY its lineart, coloring, shading, painterly texture "
    "and finish quality. Image 2 is an additional same-style detail reference. "
    "Draw a NEW original character in EXACTLY this art style: "
    + CHAR + ". Full-body standing pose, facing the viewer, clean simple background. "
    "Do NOT copy the reference character's face, pose, or outfit. "
    "Match the line weight, coloring/shading technique, level of detail and finish exactly. "
    "Style consistency first; do not invent a new style. " + STYLE_SIG + " "
    "natural skin texture, visible pores, no text, no watermark. AR 3:4"
)

PROMPT_SINGLE = (
    "Study the reference artwork's art style very carefully: its lineart, coloring, shading, "
    "painterly texture and finish. Draw a NEW original character in EXACTLY this art style, "
    "using the same line weight, same coloring/shading technique, same level of detail and same "
    "finish quality as the reference. The new character is: " + CHAR + ". "
    "Full-body standing pose, facing viewer, clean simple background. "
    "Do NOT copy the reference character's face, pose or outfit. " + STYLE_SIG + " "
    "natural skin texture, no text, no watermark. AR 3:4"
)

def prep_refs():
    """把参考图压到 1152px 再上传（减小上传量，降低中转站断连概率）。"""
    from PIL import Image
    ref_dir = os.path.join(BASE, "assets", "reference", "arknights", "阿米娅")
    tmp_dir = os.path.join(BASE, "assets", "demo", "style_attempts", "_refs")
    os.makedirs(tmp_dir, exist_ok=True)
    out = []
    for name, fname, maxw in [("anchor", "阿米娅_2.png", 1152), ("detail", "阿米娅_1.png", 1024)]:
        src = os.path.join(ref_dir, "立绘", fname)
        dst = os.path.join(tmp_dir, f"ref_{name}_{maxw}.png")
        im = Image.open(src).convert("RGB")
        if im.width > maxw:
            h = int(im.height * maxw / im.width)
            im = im.resize((maxw, h), Image.LANCZOS)
        im.save(dst, "PNG")
        out.append(dst)
        print(f"  prep {name}: {im.width}x{im.height} -> {os.path.getsize(dst)//1024}KB")
    return out

def run(label, prompt, refs):
    import time as _t
    last = None
    for attempt in range(4):
        try:
            n, dt = gen_image(prompt, a.out, style_ref=refs, model="gpt-image-2", size="1024x1536")
            print(f"[{label}] attempt {attempt+1} OK bytes={n} time={dt:.1f}s -> {a.out}")
            return True
        except Exception as e:
            last = e
            print(f"[{label}] attempt {attempt+1} failed: {type(e).__name__}: {str(e)[:120]}")
            _t.sleep(10)
    print(f"[{label}] FAILED after retries: {type(last).__name__}: {str(last)[:200]}")
    return False

def main():
    global a
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(BASE, "assets", "demo", "style_attempts", "gpt2_v10_styleSig.png"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    refs = prep_refs()
    if run("multi-ref", PROMPT_MULTI, refs):
        return 0
    if run("single-ref", PROMPT_SINGLE, [refs[0]]):
        return 0
    return 2

if __name__ == "__main__":
    sys.exit(main())
