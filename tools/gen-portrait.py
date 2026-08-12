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
    from openai import OpenAI
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(repo, "env", ".env"), override=True)
    return OpenAI(api_key=os.environ.get("GPT_API_KEY", ""), base_url=os.environ.get("GPT_BASE_URL", ""))


def download(url, out):
    import requests
    img = requests.get(url, timeout=180).content
    with open(out, "wb") as f:
        f.write(img)
    return len(img)


def gen_image(client, prompt, out, ref=None, model="gpt-image-1", size="1024x1024"):
    """文生图（无参考）或 responses 参考图锚点。返回 (bytes 大小, 用时秒)。"""
    t0 = time.time()
    if ref is None:
        resp = client.images.generate(model=model, prompt=prompt, n=1, size=size)
        url = resp.data[0].url
        n = download(url, out)
    else:
        with open(ref, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        resp = client.responses.create(model=model, input=[
            {"type": "image", "image_url": "data:image/png;base64," + b64},
            {"type": "text", "text": prompt},
        ])
        saved = False
        for it in resp.output:
            for part in (getattr(it, "content", None) or []):
                if getattr(part, "type", "") == "image":
                    url = getattr(part, "image_url", "")
                    if isinstance(url, str) and url.startswith("data:"):
                        data = base64.b64decode(url.split(",", 1)[1])
                        with open(out, "wb") as f:
                            f.write(data)
                        n = len(data); saved = True
        if not saved:
            raise RuntimeError("responses 输出中未找到图片（可能中转站不支持或格式不同）")
    return n, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--out", required=True, help="角色资产目录")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不调用 API")
    ap.add_argument("--ref", default=None, help="锚点图（参考图）")
    ap.add_argument("--model", default="gpt-image-1")
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
        n, dt = gen_image(client, prompt, outfile, ref=ref, model=a.model)
        assets_meta.append({"type": f"{style_type}/{name}", "file": f"portrait/{name}.png",
                            "engine": a.model, "prompt": prompt, "size_bytes": n, "elapsed_s": round(dt, 1)})
        print(f"  ok {name}.png ({n}B, {dt:.1f}s)")
        if ref is None:
            ref = outfile  # 之后的任务带锚点
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
