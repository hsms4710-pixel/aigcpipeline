# -*- coding: utf-8 -*-
"""agent_a2_node.py — A2 资产生成节点：LangGraph StateGraph 版（skill 按 LangGraph 方式加载）

项目主体是 agent 驱动的 AIGC pipeline。本文件把 A2 资产生成做成真正的 LangGraph 图，
skill（gpt-image）在运行时按 LangGraph 三级渐进披露加载进 agent 上下文：

  skill_context 节点  -> build_skill_context()（Level1 元数据 + Level2 完整 SKILL.md
                         + Level3 按资产类型自动选 references）
  design_prompt 节点  -> 视觉模型（gpt-5.5）用上述 skill 上下文生成/修订生图提示词
  generate      节点  -> image_backend.gen_image 生图
  vision_gate   节点  -> vision_gate.py 视觉验收门禁（A3，正式环节）
  条件边 decide_retry -> PASS→archive；FAIL & 未达最大轮数→带 issues 回 design_prompt 修订重试

用法:
  # 完整跑（视觉提示词 → 生图 → Vision Gate → 自动重试 → manifest）
  python tools/agent_a2_node.py --demand "宝可梦风艾琳4向角色" --style pokemon-nds-bw \
      --type character --name ailin_v11 [--ref ...] [--size 1024x1024]

  # 离线冒烟：只验证 LangGraph 图 + skill 三级加载（不调 API 不生图）
  python tools/agent_a2_node.py --demand "宝可梦风艾琳4向角色" --type character --dry-run

依赖: langgraph（已装到 runtime/.venv）；无 langgraph 时自动降级为直接函数调用。
"""
from __future__ import annotations

import argparse, json, os, subprocess, sys, time
from typing import TypedDict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)

from skill_loader import DEFAULT_ROOTS, build_skill_context  # noqa: E402


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class A2State(TypedDict, total=False):
    # job 输入
    demand: str
    style: str
    atype: str
    name: str
    refs: list
    baseline: list
    size: str
    transparent: bool
    max_tries: int
    threshold: float
    out_dir: str
    skill_name: str
    skills_roots: list
    max_resource_chars: int
    # 运行时
    attempts: int
    skill_ctx: dict
    prompt_doc: dict
    last_prompt: str
    image_path: str
    gate_report: dict
    gate_result: str          # PASS / FAIL
    issues: list
    manifest: dict
    final_status: str


# ---------------------------------------------------------------------------
# 工具（节点内部复用，保持与 a2-pipeline.py 一致的行为）
# ---------------------------------------------------------------------------
def _load_dotenv():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(REPO, "env", ".env"), override=True)
    except Exception:
        pass


def _run_gate(imgs, atype, name, threshold, baseline, out_json, max_size=768):
    cmd = [sys.executable, os.path.join(TOOLS, "vision_gate.py")] + list(imgs) + [
        "--type", atype, "--name", name, "--threshold", str(threshold),
        "--out", out_json, "--max-size", str(max_size)]
    for b in baseline or []:
        cmd += ["--baseline", b]
    subprocess.run(cmd)
    if not os.path.exists(out_json):
        return {}, "NO-GATE"
    with open(out_json, "r", encoding="utf-8") as f:
        report = json.load(f)
    return report, ("PASS" if report.get("gate_result") == "PASS" else "FAIL")


# ---------------------------------------------------------------------------
# 节点
# ---------------------------------------------------------------------------
def node_skill_context(state: A2State) -> dict:
    """LangGraph 三级渐进披露：按任务加载 gpt-image skill 上下文。"""
    task = f"{state.get('style', '')} {state.get('atype', '')} {state.get('demand', '')}"
    ctx = build_skill_context(state.get("skill_name") or "gpt-image", task=task,
                              skills_roots=state.get("skills_roots") or DEFAULT_ROOTS)
    print(f"[a2-node] skill_context: activated={ctx['skill']} "
          f"skill_loaded={ctx['skill_loaded']} resources={sorted(ctx['resources'].keys())}")
    return {"skill_ctx": ctx}


def node_design_prompt(state: A2State) -> dict:
    """视觉模型提示词设计师：用 skill 上下文生成/修订生图 prompt（no_vision 时离线组装）。"""
    from prompt_vision import design_prompt
    no_vision = bool(state.get("no_vision"))
    prompt_doc = design_prompt(
        state["demand"], state["style"], state["atype"],
        refs=state.get("refs", []),
        current_prompt=state.get("last_prompt", ""),
        skill_name=state.get("skill_name") or "gpt-image",
        skills_roots=state.get("skills_roots") or DEFAULT_ROOTS,
        max_resource_chars=state.get("max_resource_chars", 8000),
        out_json=os.path.join(state["out_dir"], "prompt.json"),
        no_vision=no_vision,
    )
    return {"prompt_doc": prompt_doc, "last_prompt": prompt_doc.get("prompt", "")}


def node_generate(state: A2State) -> dict:
    from image_backend import gen_image
    raw = os.path.join(state["out_dir"], "raw.png")
    n, dt = gen_image(state["last_prompt"], raw, size=state["size"],
                      transparent=state.get("transparent", False), quality="high")
    print(f"[a2-node] 生图 {n/1024:.0f}KB {dt:.1f}s -> {raw}")
    return {"image_path": raw}


def node_vision_gate(state: A2State) -> dict:
    report, result = _run_gate([state["image_path"]], state["atype"], state["name"],
                               state["threshold"], state.get("baseline", []),
                               os.path.join(state["out_dir"], "gate.json"))
    attempts = int(state.get("attempts", 0)) + 1
    issues = report.get("issues", []) if isinstance(report, dict) else []
    print(f"[a2-node] 第 {attempts} 轮 gate_result={result} overall={report.get('overall')} issues={len(issues)}")
    return {"gate_report": report, "gate_result": result,
            "attempts": attempts, "issues": list(issues)}


def node_archive(state: A2State) -> dict:
    report = state.get("gate_report") or {}
    final_status = "PASS" if state.get("gate_result") == "PASS" else "FAIL"
    manifest = {
        "schema": "asset.manifest.v1",
        "type": state["atype"],
        "name": state["name"],
        "style": state["style"],
        "artifacts": [state.get("image_path", "")],
        "meta": {
            "demand": state["demand"],
            "prompt": state.get("last_prompt", ""),
            "params": {"size": state["size"], "transparent": state.get("transparent", False)},
            "model": "gpt-image-2",
            "attempts": state.get("attempts", 1),
            "duration_s": round(time.time() - state.get("_t0", time.time()), 1),
            "orchestrator": "langgraph-a2-node",
        },
        "qa": {"vision": report},
        "skill": state.get("skill_ctx", {}).get("skill"),
        "confirmed": False,
    }
    mpath = os.path.join(state["out_dir"], "manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[a2-node] manifest -> {mpath} | final_status={final_status}")
    return {"manifest": manifest, "final_status": final_status}


def route_retry(state: A2State) -> str:
    if state.get("gate_result") == "PASS":
        return "archive"
    if int(state.get("attempts", 0)) >= int(state.get("max_tries", 3)):
        return "archive"
    return "design_prompt"


# ---------------------------------------------------------------------------
# 图构建 / 运行
# ---------------------------------------------------------------------------
def build_graph():
    """构建 LangGraph StateGraph。langgraph 缺失时返回 None（调用方降级）。"""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as e:
        print(f"[a2-node] langgraph 不可用，降级为直接函数调用: {e}", file=sys.stderr)
        return None
    g = StateGraph(A2State)
    g.add_node("skill_context", node_skill_context)
    g.add_node("design_prompt", node_design_prompt)
    g.add_node("generate", node_generate)
    g.add_node("vision_gate", node_vision_gate)
    g.add_node("archive", node_archive)
    g.add_edge(START, "skill_context")
    g.add_edge("skill_context", "design_prompt")
    g.add_edge("design_prompt", "generate")
    g.add_edge("generate", "vision_gate")
    g.add_conditional_edges("vision_gate", route_retry,
                            {"design_prompt": "design_prompt", "archive": "archive"})
    g.add_edge("archive", END)
    return g.compile()


def run_a2(job: dict, dry_run: bool = False, no_vision: bool = False,
           skip_generate: bool = False, max_tries: int = 3, threshold: float = 7.0) -> dict:
    """运行 A2 节点。返回最终 state。

    dry_run=True: 只跑 skill_context + design_prompt(no_vision)，验证 LangGraph 图 + skill 三级加载。
    skip_generate=True: 跑完 design_prompt 即停（生图/门禁由外部做）。
    """
    _load_dotenv()
    out_dir = job.get("out_dir") or os.path.join(REPO, "assets", "demo", "a2", job.get("name", "a2_asset"))
    os.makedirs(out_dir, exist_ok=True)
    initial: A2State = {
        **job,
        "out_dir": out_dir,
        "max_tries": max_tries,
        "threshold": threshold,
        "attempts": 0,
        "issues": [],
        "_t0": time.time(),
    }
    if dry_run:
        initial["no_vision"] = True
    graph = build_graph()
    if graph is None:
        # 降级：直接函数调用（等价路径，无 langgraph）
        state = dict(initial)
        state.update(node_skill_context(state))
        state.update(node_design_prompt(state))
        state["final_status"] = "DRY" if (dry_run or no_vision or skip_generate) else "SKIP"
        return state
    if dry_run or skip_generate:
        # 手工跑子图（skill_context -> design_prompt），不编译全图
        state = dict(initial)
        state.update(node_skill_context(state))
        state.update(node_design_prompt(state))
        state["final_status"] = "DRY" if dry_run else "SKIP"
        return state
    return graph.invoke(initial)


def main():
    ap = argparse.ArgumentParser(description="A2 资产生成节点（LangGraph StateGraph + skill 加载）")
    ap.add_argument("--demand", required=True)
    ap.add_argument("--style", default="pokemon-nds-bw")
    ap.add_argument("--type", default="character", choices=["character", "sprite", "tileset", "animation", "map", "scene"])
    ap.add_argument("--name", default="a2_asset")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--baseline", nargs="*", default=[])
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--max-tries", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=7.0)
    ap.add_argument("--skill", default="gpt-image")
    ap.add_argument("--skill-root", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true", help="只验证图 + skill 三级加载（不调 API）")
    ap.add_argument("--no-vision", action="store_true", help="design_prompt 离线组装（不调视觉 API）")
    ap.add_argument("--skip-generate", action="store_true", help="只跑到 design_prompt")
    a = ap.parse_args()
    job = {
        "demand": a.demand, "style": a.style, "atype": a.type, "name": a.name,
        "refs": a.ref, "baseline": a.baseline, "size": a.size, "transparent": a.transparent,
        "out_dir": a.out_dir, "skill_name": a.skill,
        "skills_roots": a.skill_root or DEFAULT_ROOTS,
    }
    state = run_a2(job, dry_run=a.dry_run, no_vision=a.no_vision,
                   skip_generate=a.skip_generate, max_tries=a.max_tries, threshold=a.threshold)
    print(f"[a2-node] final_status={state.get('final_status')} "
          f"gate_result={state.get('gate_result')} attempts={state.get('attempts')}")
    if a.dry_run and state.get("skill_ctx"):
        print("\n--- skill 三级上下文快照 ---")
        print(f"activated={state['skill_ctx'].get('skill')} "
              f"skill_loaded={state['skill_ctx'].get('skill_loaded')} "
              f"resources={sorted(state['skill_ctx'].get('resources', {}).keys())}")
    sys.exit(0)


if __name__ == "__main__":
    main()

