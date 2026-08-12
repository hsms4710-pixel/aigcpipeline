#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-portrait.py：persona.json → 提示词 → 云生图 API → 立绘/表情 → 资产包落盘 + metadata
用法：
  python gen-portrait.py <persona.json> --out <character_id_dir> [--dry-run] [--ref <锚点图>] [--style-ref <画风参考图>] [--force]
后端：IMAGE_BACKEND=openai（中转站；文生图 images.generate / 参考图锚点 images.edit）

表情差分方案（对齐工业做法：VNCCS Emotion Studio / Live2D 表情切换 / 二次元游戏立绘表情层）：
  主立绘(full.png) → 半身头像(bust.png) → 逐表情「人脸区域编辑」→ **人脸区域抠出合成回 bust 基底**
  → 身体/发型/服装 100% 一致（同构图），只替换面部表情 → 4 张独立透明 PNG + 2x2 审阅拼图
  说明：中转站 gpt-image-2 的 images.edit 即使带 mask 也会整体重绘，因此必须做"人脸层合成"保证连贯性。
"""
import os, sys, json, time, argparse, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_prompt import build_prompt, build_style_prompt, build_exp_edit_prompt
from image_backend import face_mask


def load_client():
    from dotenv import load_dotenv
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(repo, "env", ".env"), override=True)
    return None


def gen_image(client, prompt, out, ref=None, model="gpt-image-2", size="1024x1024", backend="openai",
              transparent=False, mask=None, seed=None, style_ref=None):
    from image_backend import gen_image as _gen
    return _gen(prompt, out, ref=ref, backend=backend, model=model, size=size, client=client,
                transparent=transparent, mask=mask, seed=seed, style_ref=style_ref)


def face_bbox(w, h, cy=0.40, rx=0.20, ry=0.24, margin=0.06):
    """人脸编辑区域包围盒（与 face_mask 同一椭圆参数，外加边距）"""
    cx = w * 0.5
    x0 = int(cx - w * rx - w * margin); x1 = int(cx + w * rx + w * margin)
    y0 = int(h * cy - h * ry - h * margin); y1 = int(h * cy + h * ry + h * margin)
    return max(0, x0), max(0, y0), min(w, x1), min(h, y1)


def composite_face(base, face_img, box, out):
    """把表情图的人脸区域合成回基底（羽毛边融合），保证身体/发型/服装完全一致。"""
    from PIL import Image, ImageFilter
    base = Image.open(base).convert("RGBA")
    face = Image.open(face_img).convert("RGBA")
    x0, y0, x1, y1 = box
    crop = face.crop((x0, y0, x1, y1))
    # 羽毛遮罩：边缘 alpha 渐变，避免接缝
    w = crop.width; h = crop.height
    feather = int(min(w, h) * 0.12)
    mask = Image.new("L", (w, h), 255)
    px = mask.load()
    for yy in range(h):
        for xx in range(w):
            d = min(xx, w - 1 - xx, yy, h - 1 - yy)
            px[xx, yy] = 255 if d >= feather else int(255 * d / max(1, feather))
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    base.paste(crop, (x0, y0), mask)
    base.save(out)
    return out


def make_exp_sheet(exp_dir, out_sheet, emos=("happy", "sad", "angry", "neutral")):
    from PIL import Image as _PIL
    files = [os.path.join(exp_dir, f"exp_{e}.png") for e in emos]
    if not all(os.path.exists(f) for f in files):
        return None
    ims = [_PIL.open(f).convert("RGBA") for f in files]
    w = max(i.width for i in ims); h = max(i.height for i in ims)
    canvas = _PIL.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    for idx, im in enumerate(ims):
        canvas.paste(im, ((idx % 2) * w, (idx // 2) * h))
    canvas.save(out_sheet)
    return out_sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ref", default=None)
    ap.add_argument("--model", default="gpt-image-2")
    ap.add_argument("--backend", choices=["openai", "gemini", "fal"], default="openai")
    ap.add_argument("--scene", choices=["pixel", "splash"], default=None)
    ap.add_argument("--no-ref", action="store_true")
    ap.add_argument("--style-ref", default=None)
    ap.add_argument("--force", action="store_true", help="强制重新生成已存在的 full/bust")
    a = ap.parse_args()

    with open(a.persona, encoding="utf-8-sig") as f:
        persona = json.load(f)
    char_id = persona.get("name", "character")
    outdir = os.path.join(a.out)
    portrait_dir = os.path.join(outdir, "portrait")
    raw_dir = os.path.join(portrait_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    style_type = a.scene or persona.get("style", {}).get("type", "splash")
    asset_types = persona.get("assets", {}).get(style_type, [])
    if style_type == "pixel":
        tasks = [("full", "front"), ("side", "side"), ("back", "back")]
        if "actions" in asset_types:
            for act in ("idle", "walk", "attack", "hurt"):
                tasks.append((act, act))
    else:
        tasks = [("full", "portrait")]
        if "expressions" in asset_types:
            tasks.append(("bust", "bust"))
        if "turnaround" in asset_types:
            tasks.append(("turnaround", "turnaround"))

    print(f"角色: {char_id} | style: {style_type} | 任务: {[t[0] for t in tasks]}")
    if a.dry_run:
        for name, view in tasks:
            p = build_prompt(persona, style_type, view, exp="neutral")
            print(f"\n--- {name} ({view}) ---\n{p}\n")
        print("DRY-RUN: 未调用 API")
        return 0

    client = load_client()
    ref = a.ref
    style_ref = a.style_ref
    size = "1536x1024" if style_type == "splash" else "1024x1024"
    assets_meta = []
    transparent = style_type == "splash"

    for name, view in tasks:
        outfile = os.path.join(portrait_dir, f"{name}.png")
        if os.path.exists(outfile) and not a.force:
            print(f"[{name}] 跳过（已存在，--force 重新生成）")
            if ref is None:
                ref = outfile
            continue
        if style_ref is not None and name == "full":
            prompt = build_style_prompt(persona)
        else:
            prompt = build_prompt(persona, style_type, view, exp="neutral")
        print(f"[{name}] 生成中…")
        n, dt = gen_image(client, prompt, outfile, ref=ref, model=a.model, backend=a.backend,
                          transparent=transparent, mask=None, seed=None, style_ref=style_ref)
        if name == "bust":
            ref = outfile
            print(f"  ok bust.png ({n}B, {dt:.1f}s) [表情基底]")
            assets_meta.append({"type": f"{style_type}/bust", "file": "portrait/bust.png",
                                "engine": a.model, "prompt": prompt, "size_bytes": n, "elapsed_s": round(dt, 1)})
            continue
        assets_meta.append({"type": f"{style_type}/{name}", "file": f"portrait/{name}.png",
                            "engine": a.model, "prompt": prompt, "size_bytes": n, "elapsed_s": round(dt, 1)})
        print(f"  ok {name}.png ({n}B, {dt:.1f}s)")
        if ref is None and not a.no_ref:
            ref = outfile

    # 表情差分：逐表情人脸编辑 → 人脸层合成回基底（保证身体 100% 一致）
    if style_type == "splash" and "expressions" in asset_types:
        bust = os.path.join(portrait_dir, "bust.png")
        if os.path.exists(bust):
            maskf = os.path.join(portrait_dir, "_face_mask.png")
            face_mask(bust, maskf)
            from PIL import Image as _PIL
            bw, bh = _PIL.open(bust).size
            box = face_bbox(bw, bh)
            print(f"[expressions] 逐表情人脸区域编辑 + 人脸层合成回 bust 基底（box={box}）…")
            for emo in ("happy", "sad", "angry", "neutral"):
                final = os.path.join(portrait_dir, f"exp_{emo}.png")
                raw = os.path.join(raw_dir, f"raw_exp_{emo}.png")
                prompt = build_exp_edit_prompt(persona, emo)
                if os.path.exists(final) and not a.force:
                    print(f"  skip exp_{emo}.png（已存在，--force 重新生成）")
                    assets_meta.append({"type": f"{style_type}/exp_{emo}", "file": f"portrait/exp_{emo}.png",
                                        "engine": a.model, "prompt": prompt, "source": "face-mask-edit+composite"})
                    continue
                print(f"[exp_{emo}] 生成中…")
                try:
                    n, dt = gen_image(client, prompt, raw, ref=bust, model=a.model, backend=a.backend,
                                      transparent=True, mask=maskf)
                    composite_face(bust, raw, box, final)
                    assets_meta.append({"type": f"{style_type}/exp_{emo}", "file": f"portrait/exp_{emo}.png",
                                        "engine": a.model, "prompt": prompt, "source": "face-mask-edit+composite",
                                        "raw_file": f"portrait/raw/raw_exp_{emo}.png",
                                        "size_bytes": n, "elapsed_s": round(dt, 1)})
                    print(f"  ok exp_{emo}.png (raw {n}B, {dt:.1f}s) -> 人脸层合成")
                except Exception as e:
                    print(f"  ERR exp_{emo}: {e}")
            sheet = make_exp_sheet(portrait_dir, os.path.join(portrait_dir, "exp_sheet.png"))
            print("  2x2 审阅拼图:", sheet or "（缺图，未生成）")
        else:
            print("[expressions] 跳过：缺 bust.png 基底")

    meta = {"character_id": char_id, "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "assets": assets_meta}
    with open(os.path.join(outdir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    import shutil
    shutil.copy(a.persona, os.path.join(outdir, "persona.json"))
    print("资产包已写入:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

