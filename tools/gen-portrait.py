#!/usr/bin/env python3
"""gen-portrait.py：persona.json → 提示词 → 云生图 API → 立绘/表情 → 资产包落盘 + metadata
用法：
  python gen-portrait.py <persona.json> --out <character_id_dir> [--dry-run] [--ref <锚点图>]
后端：IMAGE_BACKEND=openai（中转站；文生图 images.generate / 参考图锚点 responses）
"""
import os, sys, json, time, base64, argparse, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_prompt import build_prompt


def load_client():
    from dotenv import load_dotenv
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(repo, "env", ".env"), override=True)
    return None  # image_backend 内按 backend 懒加载


def gen_image(client, prompt, out, ref=None, model="gpt-image-2", size="1024x1024", backend="openai"):
    from image_backend import gen_image as _gen
    return _gen(prompt, out, ref=ref, backend=backend, model=model, size=size, client=client)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--out", required=True, help="角色资产目录")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不调用 API")
    ap.add_argument("--ref", default=None, help="锚点图（参考图）")
    ap.add_argument("--model", default="gpt-image-2")
    ap.add_argument("--backend", choices=["openai", "gemini", "fal"], default="openai", help="生图后端")
    ap.add_argument("--no-ref", action="store_true", help="不用参考图锚点（纯 prompt 逐任务生成）")
    ap.add_argument("--scene", choices=["pixel", "splash"], default=None, help="overwrite persona.style.type")
    a = ap.parse_args()

    with open(a.persona, encoding="utf-8-sig") as f:
        persona = json.load(f)
    char_id = persona.get("name", "character")
    outdir = os.path.join(a.out)
    portrait_dir = os.path.join(outdir, "portrait")
    os.makedirs(portrait_dir, exist_ok=True)

    style_type = a.scene or persona.get("style", {}).get("type", "splash")
    asset_types = persona.get("assets", {}).get(style_type, [])
    # 默认任务：立绘 + 表情（splash）或 front 锚点 + 三视图（pixel）
    if style_type == "pixel":
        tasks = [("full", "front"), ("side", "side"), ("back", "back")]
        if "actions" in asset_types:
            for act in ("idle", "walk", "attack", "hurt"):
                tasks.append((act, act))
    else:
        tasks = [("full", "portrait")]
        if "expressions" in asset_types:
            for e in ("happy", "sad", "angry", "neutral"):
                tasks.append((f"exp_{e}", "expressions"))
        if "turnaround" in asset_types:
            tasks.append(("turnaround", "turnaround"))

    print(f"角色: {char_id} | style: {style_type} | 任务: {[t[0] for t in tasks]}")
    if a.dry_run:
        for name, view in tasks:
            p = build_prompt(persona, style_type, view, exp=name.split("_")[-1] if name.startswith("exp_") else "neutral")
            print(f"\n--- {name} ({view}) ---\n{p}\n")
        print("DRY-RUN: 未调用 API")
        return 0

    client = load_client()
    ref = a.ref
    assets_meta = []
    for name, view in tasks:
        exp = name.split("_")[-1] if name.startswith("exp_") else "neutral"
        prompt = build_prompt(persona, style_type, view, exp=exp)
        outfile = os.path.join(portrait_dir, f"{name}.png")
        print(f"[{name}] 生成中...")
        n, dt = gen_image(client, prompt, outfile, ref=ref, model=a.model, backend=a.backend)
        assets_meta.append({"type": f"{style_type}/{name}", "file": f"portrait/{name}.png",
                            "engine": a.model, "prompt": prompt, "size_bytes": n, "elapsed_s": round(dt, 1)})
        print(f"  ok {name}.png ({n}B, {dt:.1f}s)")
        if ref is None and not a.no_ref:
            ref = outfile  # 参考图锚点（images.edit 保持角色）
    meta = {"character_id": char_id, "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "assets": assets_meta}
    with open(os.path.join(outdir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    # 拷贝 persona
    import shutil
    shutil.copy(a.persona, os.path.join(outdir, "persona.json"))
    print("资产包已写入:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
