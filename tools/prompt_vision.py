"""prompt_vision.py — 视觉模型提示词设计师 agent（Vision Prompt Designer）
让 gpt-5.5 视觉模型（而非人工）根据需求 + 风格基底 + 参考图，生成/优化生图提示词。
闭环：vision 生成 prompt -> 生图 -> vision gate 验收 -> 不合格 -> 本工具修订 prompt 重生成

用法:
  python tools/prompt_vision.py --demand "宝可梦风艾琳 4 向角色" --style pokemon-nds-bw \
      --type character [--ref 参考图] [--current-prompt "现有prompt"] [--out prompt.json]
"""
import argparse, base64, io, json, os, sys, time
import urllib.request
from PIL import Image

API = "https://api.sisct2.xyz/v1/chat/completions"
DEFAULT_KEY = ""  # 从 VISION_KEY 环境变量（env/.env）读取，勿硬编码

def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "env", ".env"), override=True)
    except Exception:
        pass

def img_to_dataurl(path, max_size=768):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    scale = max_size / max(w, h)
    if scale < 1.0:
        im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=88)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"

def load_style(name):
    """从 style-assets.json 读取风格基底/场景模板"""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(repo, "contracts", "style-assets.json")
    if not os.path.exists(cfg_path):
        return {}, ""
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    st = cfg.get("styles", {}).get(name, cfg)
    block = st.get("style_block", "")
    scenes = st.get("scene_templates", {})
    return {"style_block": block, "scenes": scenes}, block

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demand", required=True, help="资产需求（如：宝可梦风艾琳 4 向角色）")
    ap.add_argument("--style", default="pokemon-nds-bw")
    ap.add_argument("--type", default="character", choices=["character", "sprite", "tileset", "animation", "map", "scene"])
    ap.add_argument("--ref", nargs="*", default=[], help="参考图（当前资产/风格图，vision 分析差距）")
    ap.add_argument("--current-prompt", default="", help="现有 prompt（vision 修订优化）")
    ap.add_argument("--out", default=None, help="输出 prompt JSON 路径")
    ap.add_argument("--max-size", type=int, default=768)
    a = ap.parse_args()
    _load_env()
    key = os.environ.get("VISION_KEY", DEFAULT_KEY)

    style_info, style_block = load_style(a.style)
    scenes = style_info.get("scenes", {})
    # 场景模板参考（type 对应场景）
    scene_key = {"character": "character", "sprite": "character", "tileset": "route",
                 "animation": "character", "map": "route", "scene": "town"}.get(a.type, "town")
    scene_tpl = scenes.get(scene_key, "")

    sys_prompt = (
        "You are a senior game art director AND a master prompt engineer for AI image generation. "
        "Your job: produce a HIGH-QUALITY, detailed image-generation prompt for game assets. "
        "Use precise style anchors (era/game references), clear composition, palette, pixel specs, "
        "lighting, outline, and scene context. Avoid vague words. "
        "If reference images are provided, ANALYZE what is wrong/weak in them and how to fix in the prompt. "
        "Output STRICT JSON only: "
        '{"prompt": "<the full generation prompt, English>", "rationale": "<why this prompt fixes issues, Chinese>", '
        '"params": {"size": "...", "palette": "...", "transparent_bg": true, "notes": "..."}}'
    )
    user_content = []
    user_content.append({"type": "text", "text": (
        f"需求: {a.demand}\n"
        f"风格基底: {style_block}\n"
        f"场景参考模板: {scene_tpl[:800]}\n"
        + (f"现有 prompt（请修订优化）: {a.current_prompt}\n" if a.current_prompt else "")
        + (f"参考图 {len(a.ref)} 张，请分析其质量问题并给出修复方向。\n" if a.ref else "")
    )})
    for r in a.ref:
        try:
            url = img_to_dataurl(r, a.max_size)
            user_content.append({"type": "image_url", "image_url": {"url": url}})
        except Exception as e:
            print(f"ref skip {r}: {e}", file=sys.stderr)

    body = {"model": "gpt-5.5", "messages": [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content}
    ], "max_tokens": 1800, "response_format": {"type": "json_object"}}
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                j = json.loads(r.read().decode("utf-8"))
            content = j["choices"][0]["message"]["content"]
            break
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, e.read().decode("utf-8")[:200], file=sys.stderr); sys.exit(1)
        except Exception as e:
            last = e; print(f"  retry {attempt+1}: {e}", file=sys.stderr); time.sleep(4*(attempt+1))
    else:
        raise RuntimeError(f"vision failed: {last}")
    try:
        result = json.loads(content)
    except Exception:
        result = {"prompt": content, "rationale": "raw", "params": {}}
    result["style"] = a.style
    result["type"] = a.type
    result["demand"] = a.demand
    print("=== 视觉模型生成的提示词 ===")
    print(result.get("prompt", ""))
    print("\n=== 理由 ===")
    print(result.get("rationale", ""))
    if result.get("params"):
        print("\n=== 参数 ===")
        print(json.dumps(result.get("params"), ensure_ascii=False))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[saved] {a.out}")

if __name__ == "__main__":
    main()