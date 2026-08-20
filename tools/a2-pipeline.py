# -*- coding: utf-8 -*-
"""a2-pipeline.py — A2 资产生成标准入口（一条命令闭环）
视觉提示词设计师(prompt_vision) → 生图(image_backend) → Vision Gate(vision_gate)
→ FAIL 则带门禁问题修订提示词重试 → 产物 + manifest 归档

用法:
  python tools/a2-pipeline.py --demand "宝可梦风艾琳4向行走角色" --style pokemon-nds-bw \
      --type character --name ailin_walk_v3 \
      [--ref 参考图] [--baseline 画风基准图] \
      [--size 512x512] [--transparent] [--max-tries 3] [--threshold 7.0] \
      [--split 4 4] [--frame-size 64] [--out-dir assets/demo/a2/ailin_walk_v3]

资产类型: character / sprite / tileset / animation / map / scene
"""
import argparse, importlib.util, json, os, subprocess, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def load_dotenv():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(REPO, "env", ".env"), override=True)
    except Exception as e:
        print(f"[a2] dotenv warn: {e}", file=sys.stderr)

def vision_prompt(demand, style, atype, refs, current_prompt, out_json):
    """调用 prompt_vision 得到视觉模型生成的提示词 JSON（子进程隔离）"""
    cmd = [sys.executable, os.path.join(TOOLS, "prompt_vision.py"),
           "--demand", demand, "--style", style, "--type", atype,
           "--out", out_json, "--max-size", "768"]
    for r in refs:
        cmd += ["--ref", r]
    if current_prompt:
        cmd += ["--current-prompt", current_prompt]
    print(f"[a2] prompt_vision -> {out_json}")
    r = subprocess.run(cmd)
    if r.returncode != 0 or not os.path.exists(out_json):
        raise RuntimeError("prompt_vision 失败")
    with open(out_json, "r", encoding="utf-8") as f:
        return json.load(f)

def generate(prompt, out, size, transparent, refs):
    from image_backend import gen_image
    n, dt = gen_image(prompt, out, size=size, transparent=transparent, quality="high")
    print(f"[a2] 生图 {n/1024:.0f}KB {dt:.1f}s -> {out}")
    return out

def run_gate(imgs, atype, name, threshold, baseline, out_json, extra=""):
    cmd = [sys.executable, os.path.join(TOOLS, "vision_gate.py")] + imgs + [
        "--type", atype, "--name", name, "--threshold", str(threshold),
        "--out", out_json, "--max-size", "768"]
    for b in baseline:
        cmd += ["--baseline", b]
    if extra:
        cmd += ["--extra", extra]
    r = subprocess.run(cmd)
    if not os.path.exists(out_json):
        return None, "no-gate-json"
    with open(out_json, "r", encoding="utf-8") as f:
        report = json.load(f)
    return report, ("PASS" if r.returncode == 0 else "FAIL")

def split_sheet(src, cols, rows, frame_size, out_dir, prefix):
    """精灵表切帧（如 4向x4帧 walk sheet）"""
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(src)
    w, h = im.size
    cw, ch = w // cols, h // rows
    frames = []
    for r in range(rows):
        for c in range(cols):
            cell = im.crop((c*cw, r*ch, (c+1)*cw, (r+1)*ch))
            if frame_size:
                cell = cell.resize((frame_size, frame_size), Image.NEAREST)
            out = os.path.join(out_dir, f"{prefix}_{r}_{c}.png")
            cell.save(out)
            frames.append(out)
    return frames

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demand", required=True)
    ap.add_argument("--style", default="pokemon-nds-bw")
    ap.add_argument("--type", default="character", choices=["character","sprite","tileset","animation","map","scene"])
    ap.add_argument("--name", default="a2_asset")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--baseline", nargs="*", default=[])
    ap.add_argument("--size", default="1024x1024", help="GPT-Image2-Skill: 16px倍数,>=655k px(1024x1024)/1024x1536/1536x1024")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--max-tries", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=7.0)
    ap.add_argument("--split", nargs=2, type=int, default=None, metavar=("COLS","ROWS"))
    ap.add_argument("--frame-size", type=int, default=0)
    ap.add_argument("--gate-extra", default="")
    ap.add_argument("--skip-generate", action="store_true", help="只跑提示词+门禁（调试用）")
    a = ap.parse_args()
    load_dotenv()
    out_dir = a.out_dir or os.path.join(REPO, "assets", "demo", "a2", a.name)
    os.makedirs(out_dir, exist_ok=True)
    raw = os.path.join(out_dir, "raw.png")
    prompt_json = os.path.join(out_dir, "prompt.json")
    gate_json = os.path.join(out_dir, "gate.json")
    manifest_json = os.path.join(out_dir, "manifest.json")

    prompt_doc = None
    last_prompt = ""
    history = []
    t0 = time.time()
    for attempt in range(1, a.max_tries + 1):
        print(f"\n===== A2 第 {attempt}/{a.max_tries} 轮 =====")
        demand = a.demand
        if attempt > 1 and history:
            issues = history[-1].get("issues", [])
            demand = a.demand + " 上一轮验收问题（请针对性修订提示词修复）: " + ("; ".join(issues) if issues else "整体质量不达标")
        prompt_doc = vision_prompt(demand, a.style, a.type, a.ref, last_prompt, prompt_json)
        last_prompt = prompt_doc.get("prompt", "")
        print(f"[a2] 视觉提示词({len(last_prompt)}字): {last_prompt[:120]}...")
        if a.skip_generate:
            print("[a2] --skip-generate: 跳过生图")
            break
        if not last_prompt:
            print("[a2] 提示词为空，中止"); sys.exit(2)
        generate(last_prompt, raw, a.size, a.transparent, a.ref)
        # 门禁对象：raw（若 split 则对 sheet 门禁）
        gate_imgs = [raw]
        if a.split:
            frames = split_sheet(raw, a.split[0], a.split[1], a.frame_size or None,
                                 os.path.join(out_dir, "frames"), a.name)
            print(f"[a2] 切帧 {len(frames)} 张 -> frames/")
        report, result = run_gate(gate_imgs, a.type, a.name, a.threshold, a.baseline, gate_json, a.gate_extra)
        if report is None:
            print(f"[a2] 门禁无输出：{result}"); sys.exit(2)
        history.append(report)
        print(f"[a2] 第 {attempt} 轮 gate_result={report.get('gate_result')} overall={report.get('overall')}")
        if report.get("gate_result") == "PASS":
            print("[a2] PASS，进入归档")
            break
        if attempt < a.max_tries:
            print(f"[a2] FAIL，带问题修订提示词重试...")
    # 归档 manifest
    final = history[-1] if history else {}
    manifest = {
        "schema": "asset.manifest.v1",
        "type": a.type,
        "name": a.name,
        "style": a.style,
        "artifacts": [raw] + ([os.path.join(out_dir, "frames")] if a.split else []),
        "meta": {
            "demand": a.demand,
            "prompt": last_prompt,
            "prompt_json": prompt_json,
            "params": {"size": a.size, "transparent": a.transparent, "split": a.split},
            "model": "gpt-image-2",
            "attempts": len(history),
            "duration_s": round(time.time() - t0, 1),
            "cost_est_cny": round(0.15 * len(history), 2),
        },
        "qa": {"vision": final},
        "confirmed": False,
    }
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n[a2] manifest -> {manifest_json}")
    print(f"[a2] 最终: gate_result={final.get('gate_result')} overall={final.get('overall')}")
    sys.exit(0 if final.get("gate_result") == "PASS" else 1)

if __name__ == "__main__":
    main()
