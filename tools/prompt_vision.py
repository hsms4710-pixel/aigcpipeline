# -*- coding: utf-8 -*-
"""prompt_vision.py — 视觉模型提示词设计师 agent（Vision Prompt Designer）

让 gpt-5.5 视觉模型（而非人工）根据 需求 + 风格基底 + 参考图 生成/修订生图提示词。

Skill 按 **LangGraph 三级渐进披露**加载（tools/skill_loader.py，项目主体是 agent 驱动的
AIGC pipeline，skill 运行时按需加载而不是静态写死）：
  Level 1 Discovery : 全部 skill 的 name+description 元数据注入 system prompt
  Level 2 Read      : 本任务命中 gpt-image skill → 注入完整 SKILL.md 指令正文
  Level 3 Execute   : 按资产类型自动选 references（gallery.md 路由索引 + 1 个类别 gallery + craft.md）
                      （SKILL.md 的 reference loading policy：最小切片，绝不默认全量加载）

闭环：vision 生成 prompt -> 生图 -> vision gate 验收 -> 不合格 -> 本工具修订 prompt 重生成

用法:
  python tools/prompt_vision.py --demand "宝可梦风艾琳 4 向角色" --style pokemon-nds-bw \
      --type character [--ref 参考图] [--current-prompt "现有prompt"] [--out prompt.json] \
      [--skill gpt-image] [--max-resource-chars 8000]
"""
import argparse, base64, io, json, os, sys, time
import urllib.request
from PIL import Image

API = "https://api.sisct2.xyz/v1/chat/completions"
DEFAULT_KEY = ""  # 从 VISION_KEY 环境变量（env/.env）读取，勿硬编码

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_loader import build_skill_context  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 输出契约：与旧版一致，保证 a2-pipeline / vision_gate 兼容
OUTPUT_CONTRACT = (
    "Output STRICT JSON only: "
    '{"prompt": "<the full generation prompt, English, structured>", "rationale": "<why this prompt fixes issues, Chinese>", '
    '"params": {"size": "1024x1024", "quality": "high", "palette": "...", "transparent_bg": true, "notes": "..."}}'
)

BASE_ROLE = (
    "You are a senior game art director AND a master prompt engineer for AI image generation. "
    "You operate inside an agent-driven AIGC pipeline; the gpt-image skill is loaded via "
    "LangGraph progressive disclosure (Level 1 metadata at startup, Level 2 full SKILL.md when "
    "activated, Level 3 references on demand). Follow the activated skill's operating loop and "
    "reference loading policy exactly: search gallery routing index first, then load the closest "
    "category gallery, then craft.md for prompt repair. Use concrete visual anchors, never empty adjectives."
)


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(REPO, "env", ".env"), override=True)
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
    cfg_path = os.path.join(REPO, "contracts", "style-assets.json")
    if not os.path.exists(cfg_path):
        return {}, ""
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    st = cfg.get("styles", {}).get(name, cfg)
    block = st.get("style_block", "")
    scenes = st.get("scene_templates", {})
    return {"style_block": block, "scenes": scenes}, block


def compose_system_prompt(ctx, atype="", max_resource_chars=8000):
    """把 LangGraph 三级 skill 上下文组装成视觉提示词设计师的 system prompt。

    ctx = build_skill_context() 返回：metadata(Level1) / skill_body(Level2) / resources(Level3)
    """
    parts = [BASE_ROLE]
    meta = (ctx.get("metadata") or "").strip()
    parts.append("## Level 1 — Available skills (metadata only, loaded at startup)\n" + (meta or "(none)"))
    if ctx.get("skill_loaded") and ctx.get("skill_body"):
        parts.append(
            "## Level 2 — Activated skill: %s (full SKILL.md; follow its operating loop & reference loading policy)\n%s"
            % (ctx.get("skill"), ctx["skill_body"][:20000])
        )
    for rel, content in (ctx.get("resources") or {}).items():
        snippet = content[:max_resource_chars]
        parts.append(f"## Level 3 — Skill resource (loaded on demand): {rel}\n{snippet}")
        if len(content) > max_resource_chars:
            parts.append(f"({rel} 共 {len(content)} 字符，以上为前 {max_resource_chars} 字符；如确需更多可按路径继续查阅)")
    parts.append(OUTPUT_CONTRACT)
    return "\n\n".join(parts)


def design_prompt(demand, style, atype, refs=None, current_prompt="", skill_name="gpt-image",
                  skills_roots=None, max_size=768, max_resource_chars=8000,
                  key=None, out_json=None, no_vision=False, verbose=True, skill_ctx=None):
    """核心：LangGraph 方式加载 skill 三级内容 -> 调用视觉模型生成/修订生图提示词。

    返回 dict：{"prompt","rationale","params","style","type","demand",
                "skill": {...三级上下文快照}}；no_vision=True 时只组装不调 API（离线调试）。
    """
    _load_env()
    key = key if key is not None else os.environ.get("VISION_KEY", DEFAULT_KEY)
    style_info, style_block = load_style(style)
    scenes = style_info.get("scenes", {})
    scene_key = {"character": "character", "sprite": "character", "tileset": "route",
                 "animation": "character", "map": "route", "scene": "town"}.get(atype, "town")
    scene_tpl = scenes.get(scene_key, "")

    # ---- LangGraph progressive disclosure：按任务组装三级 skill 上下文 ----
    # 若外部（LangGraph 图）已加载 skill_ctx（如门禁重试时复用），则不再重复读盘
    task = f"{style} {atype} {demand}"
    ctx = skill_ctx if skill_ctx else build_skill_context(skill_name, task=task, skills_roots=skills_roots)
    sys_prompt = compose_system_prompt(ctx, atype, max_resource_chars)

    user_content = [{"type": "text", "text": (
        f"需求: {demand}\n"
        f"风格基底: {style_block}\n"
        f"场景参考模板: {scene_tpl[:800]}\n"
        + (f"现有 prompt（请按 skill 的 craft 规则修订优化）: {current_prompt}\n" if current_prompt else "")
        + (f"参考图 {len(refs or [])} 张，请按 skill 的 reference loading policy 分析其质量问题并给出修复方向。\n" if refs else "")
    )}]
    for r in (refs or []):
        try:
            url = img_to_dataurl(r, max_size)
            user_content.append({"type": "image_url", "image_url": {"url": url}})
        except Exception as e:
            print(f"ref skip {r}: {e}", file=sys.stderr)

    if no_vision:
        result = {"prompt": "", "rationale": "no_vision dry-run", "params": {}}
        if verbose:
            print("=== [no_vision] 已组装 system prompt（skill 三级上下文）===")
            print(sys_prompt[:6000])
        result["skill"] = {
            "metadata": ctx["metadata"],
            "activated": ctx["skill"],
            "skill_loaded": ctx["skill_loaded"],
            "resources_loaded": sorted(ctx["resources"].keys()),
        }
        result["style"], result["type"], result["demand"] = style, atype, demand
        if out_json:
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return result

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
            print("HTTP", e.code, e.read().decode("utf-8")[:200], file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            last = e
            print(f"  retry {attempt+1}: {e}", file=sys.stderr)
            time.sleep(4*(attempt+1))
    else:
        raise RuntimeError(f"vision failed: {last}")
    try:
        result = json.loads(content)
    except Exception:
        result = {"prompt": content, "rationale": "raw", "params": {}}
    result["style"] = style
    result["type"] = atype
    result["demand"] = demand
    result["skill"] = {
        "metadata": ctx["metadata"],
        "activated": ctx["skill"],
        "skill_loaded": ctx["skill_loaded"],
        "resources_loaded": sorted(ctx["resources"].keys()),
    }
    if verbose:
        print("=== 视觉模型生成的提示词 ===")
        print(result.get("prompt", ""))
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def main():
    ap = argparse.ArgumentParser(description="视觉模型提示词设计师（LangGraph skill 加载）")
    ap.add_argument("--demand", required=True, help="资产需求（如：宝可梦风艾琳 4 向角色）")
    ap.add_argument("--style", default="pokemon-nds-bw")
    ap.add_argument("--type", default="character", choices=["character", "sprite", "tileset", "animation", "map", "scene"])
    ap.add_argument("--ref", nargs="*", default=[], help="参考图（当前资产/风格图，vision 分析差距）")
    ap.add_argument("--current-prompt", default="", help="现有 prompt（vision 修订优化）")
    ap.add_argument("--out", default=None, help="输出 prompt JSON 路径")
    ap.add_argument("--max-size", type=int, default=768)
    ap.add_argument("--skill", default="gpt-image", help="激活的 skill 名（默认 gpt-image）")
    ap.add_argument("--skill-root", action="append", default=[], help="额外 skill 根（可多次）")
    ap.add_argument("--max-resource-chars", type=int, default=8000, help="每个 Level3 资源注入上限字符")
    ap.add_argument("--no-vision", action="store_true", help="只组装 skill 上下文不调 API（离线调试）")
    a = ap.parse_args()
    design_prompt(a.demand, a.style, a.type, a.ref, a.current_prompt,
                  skill_name=a.skill, skills_roots=a.skill_root or None,
                  max_size=a.max_size, max_resource_chars=a.max_resource_chars,
                  out_json=a.out, no_vision=a.no_vision)


if __name__ == "__main__":
    main()

