"""vision_gate.py — 流水线正式视觉验收门禁（Vision Gate）
将视觉模型验收固化为流水线标准环节：按资产类型跑 gpt-5.5 挑刺式验收，
输出结构化评分报告（JSON），与阈值比较得出 PASS/FAIL，可写入资产 manifest。

用法:
  python tools/vision_gate.py <img...> --type map --name overworld_map --threshold 7.0 \
      [--ref <锚点图>] [--extra "附加要求"] [--out <gate.json>] [--manifest <manifest.json>]

资产类型模板: sprite / tileset / map / animation / spine / character
"""
import argparse, base64, io, json, os, sys, time
import urllib.request
from PIL import Image

API = "https://api.sisct2.xyz/v1/chat/completions"
KEY_ENV = "VISION_KEY"
DEFAULT_KEY = ""  # 从 VISION_KEY 环境变量（env/.env）读取，勿硬编码

TEMPLATES = {
    "sprite": (
        "以挑剔的游戏美术师标准验收这张【精灵/角色】资产："
        "1) 角色识别/身份一致性（若提供锚点图则与锚点对比）；2) 像素规格（真像素硬边/无模糊/调色板受限）；"
        "3) 透明背景干净度（无白边/杂边残留）；4) 动作/姿态可读性；5) 画风统一性。"
    ),
    "tileset": (
        "以挑剔的游戏美术师标准验收这张【瓦片集/无缝纹理】资产："
        "1) 瓦片风格统一（同画风/同调色板/同光照）；2) 平铺无缝性（左右/上下边缘是否匹配、重复是否突兀）；"
        "3) 语义可区分（各瓦片类型是否明确）；4) 像素规格（真像素/无模糊/噪点是否过度）；5) 整体可用性。"
    ),
    "map": (
        "以挑剔的游戏美术师标准验收这张【2D 地图】全景："
        "1) 布局自然度（地形/道路/水域/树丛是否像设计过的世界而非测试图）；2) 瓦片平铺/重复感；"
        "3) 物件与地表风格统一性（树/建筑/角色与瓦片像素规格与调色板是否一致）；4) 可玩性结构（主路径/边界/地标）；"
        "5) 整体作为游戏地图的观感。"
    ),
    "animation": (
        "以挑剔的动画师标准验收这组【动画帧】："
        "1) 帧间一致性（身份/比例/轮廓稳定）；2) 动作连贯性（无跳变/无断裂/无穿模）；"
        "3) 循环闭合（若为循环动画）；4) 节奏与幅度合理性；5) 与角色锚点的一致性。"
    ),
    "spine": (
        "以挑剔的 Spine/骨骼动画师标准验收这张【骨骼/绑骨】产物："
        "1) 骨骼层级与枢轴落点（是否在真实关节）；2) 部件/网格完整性（无缺漏/无撕裂）；"
        "3) 蒙皮权重合理性（弯曲处是否平滑）；4) 动作可读性；5) 与源资产一致性。"
    ),
    "character": (
        "以挑剔的游戏美术师标准验收这组【角色多方向】资产："
        "1) 多方向身份一致性（脸/发/服装/配色）；2) 各方向视角正确性（下/左下/左/左上/上/右上/右/右下）；"
        "3) 透明背景干净度；4) 画风统一性；5) 作为 8 向行走精灵的可用性。"
    ),
}

def img_to_dataurl(path, max_size):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    scale = max_size / max(w, h)
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=88)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}", im.size

def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "env", ".env"), override=True)
    except Exception:
        pass

def build_prompt(atype, extra, ref_present, baseline_present=False):
    base = TEMPLATES.get(atype, TEMPLATES["sprite"])
    p = (
        base +
        " 请给出结构化评审：输出 JSON（不要其他文字）："
        '{"scores": {"维度1名称": 0-10, ...}, "overall": 0-10, "verdict": "PASS"或"FAIL", '
        '"issues": ["问题1", ...], "improvements": ["建议1", ...], "summary": "一句话结论"}。'
        " 维度按上述 5 点各给 1 项分数，overall 为整体分。verdict 由你判断（>=7 为 PASS）。"
    )
    if baseline_present:
        p += " 另附【画风基准图】。请新增维度【画风一致性】：产物与基准图是否共享同一像素规格/调色板/光照/边缘处理，是否同一套美术资产。该维度计入 scores 并在整体判断中占重要权重。"
    if extra:
        p += " 附加要求：" + extra
    return p

def call_vision(imgs, prompt, model, max_size, api, key):
    content = [{"type": "text", "text": prompt}]
    for p in imgs:
        url, size = img_to_dataurl(p, max_size)
        print(f"  img {os.path.basename(p)} -> {size}", file=sys.stderr)
        content.append({"type": "image_url", "image_url": {"url": url}})
    body = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 1600,
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request(api, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                j = json.loads(r.read().decode("utf-8"))
            return j["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, e.read().decode("utf-8")[:200], file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            last = e
            print(f"  retry {attempt+1}: {e}", file=sys.stderr)
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"vision call failed: {last}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imgs", nargs="+")
    ap.add_argument("--type", default="sprite", choices=list(TEMPLATES.keys()))
    ap.add_argument("--name", default="asset")
    ap.add_argument("--threshold", type=float, default=7.0)
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--max-size", type=int, default=768)
    ap.add_argument("--ref", nargs="*", default=[], help="锚点/参考图（对比一致性）")
    ap.add_argument("--baseline", nargs="*", default=[], help="style baseline refs")
    ap.add_argument("--extra", default="")
    ap.add_argument("--out", default=None, help="gate 报告 JSON 路径")
    ap.add_argument("--manifest", default=None, help="写入资产 manifest（追加 qa.vision 段）")
    ap.add_argument("--api", default=API)
    ap.add_argument("--key", default=None)
    a = ap.parse_args()
    key = a.key or os.environ.get(KEY_ENV) or DEFAULT_KEY
    prompt = build_prompt(a.type, a.extra, bool(a.ref), baseline_present=bool(a.baseline))
    all_imgs = list(a.baseline) + list(a.ref) + list(a.imgs)
    content = call_vision(all_imgs, prompt, a.model, a.max_size, a.api, key)
    # 解析 JSON（模型可能输出 ```json 包裹）
    txt = content.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.startswith("json"):
            txt = txt[4:]
    try:
        report = json.loads(txt)
    except Exception:
        report = {"raw": content, "overall": None, "verdict": "PARSE_FAIL", "issues": ["响应非 JSON"]}
    overall = report.get("overall")
    gate_ok = overall is not None and overall >= a.threshold
    report["name"] = a.name
    report["type"] = a.type
    report["threshold"] = a.threshold
    report["baseline"] = a.baseline
    report["gate_result"] = "PASS" if gate_ok else ("FAIL" if overall is not None else "PARSE_FAIL")
    # 输出
    print(f"\n[VISION-GATE] {a.name} ({a.type}) overall={overall} threshold={a.threshold} -> {report['gate_result']}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[VISION-GATE] report -> {a.out}")
    if a.manifest and os.path.exists(a.manifest):
        with open(a.manifest, "r", encoding="utf-8") as f:
            m = json.load(f)
        m.setdefault("qa", {})["vision"] = report
        with open(a.manifest, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=2)
        print(f"[VISION-GATE] manifest updated -> {a.manifest}")
    sys.exit(0 if gate_ok else 1)

if __name__ == "__main__":
    main()