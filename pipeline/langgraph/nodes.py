# -*- coding: utf-8 -*-
"""nodes.py — 全 pipeline LangGraph 节点（A1-A6）

每个节点 = agent/harness 执行单元，只通过 state 传契约：
  A1 需求规划    -> plan（资产契约）
  A2 资产生成    -> skill_context(Level1/2/3) -> design_prompt(视觉模型) -> generate(image_backend)
  A3 质量门禁    -> vision_gate 结构化报告（PASS/FAIL/SKIP）
  A4 引擎集成    -> 按 atype 派发既有 builder（map->pokemon map；character->godot anim demo）
  A5 骨骼动画    -> 角色类：rig-automation 校验/修复（无输入则如实 SKIP）
  A6 归档反馈    -> manifest + lessons 回填 + audit 日志

设计原则（延续项目 harness 文化）：
- 编排 agent 不做具体资产活，只拆解/分派/验收；节点不写死创作参数
- 每节点产物 = artifact + manifest 段；门禁 FAIL 自动回退 A2 修订重试
- 真实能力缺失时不假装 PASS：status=STUB/SKIP/FAIL 并给原因（可观察、可审计）
"""
from __future__ import annotations

import json, os, re, subprocess, sys, time
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "tools")
for _p in (TOOLS, os.path.join(REPO, "pipeline", "langgraph")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from skill_loader import DEFAULT_ROOTS, build_skill_context  # noqa: E402
from state import PipelineState  # noqa: E402


def _log(state: PipelineState, msg: str) -> None:
    state.setdefault("log", []).append(msg)
    print(f"[pipeline] {msg}")


def _dump(state: PipelineState, rel: str, obj: Any) -> str:
    os.makedirs(state["out_dir"], exist_ok=True)
    p = os.path.join(state["out_dir"], rel)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return p


# ---------------------------------------------------------------------------
# A1 需求规划
# ---------------------------------------------------------------------------
_TYPE_KEYWORDS = [
    ("map", ["地图", "map", "俯视", "村庄", "城镇", "野外", "overworld", "场景地图"]),
    ("scene", ["场景", "scene", "town", "室内", "酒馆"]),
    ("tileset", ["瓦片", "tileset", "图块", "无缝"]),
    ("animation", ["动画", "animation", "walk", "idle", "攻击动画", "帧动画"]),
    ("character", ["角色", "character", "小人", "立绘", "人物", "chibi", "sprite character"]),
]
_TYPE_ALIAS = {"sprite": "character"}


def node_a1_plan(state: PipelineState) -> dict:
    """A1 需求规划：demand -> plan 资产契约（规则解析，--llm-plan 时可由视觉模型增强）。

    输出 plan.json：{type, style, name, params, sub_tasks, notes}
    """
    demand = state.get("demand", "")
    atype = state.get("atype", "")
    if not atype:
        dl = demand.lower()
        for t, kws in _TYPE_KEYWORDS:
            if any(k in demand or k in dl for k in kws):
                atype = t
                break
        atype = atype or "sprite"
    atype = _TYPE_ALIAS.get(atype, atype)
    style = state.get("style", "pokemon-nds-bw")
    name = state.get("name") or _auto_name(demand, atype)
    transparent = state.get("transparent", atype in ("character", "sprite"))
    size = state.get("size", "1024x1024")
    sub_tasks = _sub_tasks(atype)
    plan = {
        "schema": "asset.plan.v1",
        "type": atype,
        "style": style,
        "name": name,
        "params": {"size": size, "transparent": transparent,
                   "split": _split_for(atype), "frame_size": 64 if atype in ("character", "animation") else 0},
        "sub_tasks": sub_tasks,
        "notes": "A1 规则解析生成；LLM 增强见 --llm-plan",
    }
    state["plan"] = plan
    state["atype"] = atype
    state["style"] = style
    state["name"] = name
    state["size"] = size
    state["transparent"] = transparent
    p = _dump(state, "plan.json", plan)
    _log(state, f"A1 规划 -> type={atype} style={style} name={name} ({p})")
    return {"plan": plan, "atype": atype, "style": style, "name": name, "size": size, "transparent": transparent}


def _auto_name(demand: str, atype: str) -> str:
    m = re.search(r"(艾琳|ailin|阿米娅|amiya|[\u4e00-\u9fff]{2,4})", demand)
    who = (m.group(1) if m else "char").lower()
    return f"{who}_{atype}_{int(time.time()) % 100000}"


def _sub_tasks(atype: str) -> list:
    base = {
        "character": ["A2-1 立绘/表情生成", "A2-2 三视图/转面（按需）", "A3 视觉门禁", "A4 帧动画/Godot 工程", "A5 骨骼（可选）"],
        "map": ["A2-1 瓦片集生成", "A2-2 地图拼接", "A3 视觉门禁", "A4 Godot TileMap 工程"],
        "tileset": ["A2-1 瓦片集生成", "A3 无缝/风格门禁", "A4 瓦片入库"],
        "animation": ["A2-1 关键帧生成", "A3 帧间一致性门禁", "A4 Godot AnimatedSprite2D"],
        "scene": ["A2-1 场景图生成", "A3 视觉门禁", "A4 Godot 场景骨架"],
        "sprite": ["A2-1 精灵生成", "A3 视觉门禁", "A4 入库/引擎接入"],
    }
    return base.get(atype, base["sprite"])


def _split_for(atype: str):
    if atype in ("character", "animation"):
        return [4, 4]  # 4向 x 4帧 walk sheet（A2 切帧用）
    return None


# ---------------------------------------------------------------------------
# A2 资产生成（LangGraph skill 三级渐进披露 + 视觉提示词 + 生图）
# ---------------------------------------------------------------------------
def node_a2_skill(state: PipelineState) -> dict:
    """A2-0：LangGraph 方式加载 skill 三级上下文（Level1 元数据 + Level2 SKILL.md + Level3 按需资源）。"""
    task = f"{state.get('style', '')} {state.get('atype', '')} {state.get('demand', '')}"
    ctx = build_skill_context(state.get("skill_name") or "gpt-image", task=task,
                              skills_roots=state.get("skills_roots") or DEFAULT_ROOTS)
    state["skill_ctx"] = ctx
    _log(state, f"A2 skill_context -> activated={ctx['skill']} skill_loaded={ctx['skill_loaded']} "
                f"resources={sorted(ctx['resources'].keys())}")
    return {"skill_ctx": ctx}


def node_a2_prompt(state: PipelineState) -> dict:
    """A2-1：视觉模型提示词设计师（复用 graph 已加载的 skill_ctx，重试不重复读盘）。"""
    from prompt_vision import design_prompt
    no_vision = bool(state.get("dry_run") or state.get("no_vision"))
    prompt_doc = design_prompt(
        state["demand"], state["style"], state["atype"],
        refs=state.get("refs", []),
        current_prompt=state.get("last_prompt", ""),
        skill_name=state.get("skill_name") or "gpt-image",
        skills_roots=state.get("skills_roots") or DEFAULT_ROOTS,
        max_resource_chars=state.get("max_resource_chars", 8000),
        out_json=os.path.join(state["out_dir"], "prompt.json"),
        no_vision=no_vision,
        skill_ctx=state.get("skill_ctx"),
    )
    state["prompt_doc"] = prompt_doc
    state["last_prompt"] = prompt_doc.get("prompt", "")
    _log(state, f"A2 design_prompt -> {len(state['last_prompt'])} chars (no_vision={no_vision})")
    return {"prompt_doc": prompt_doc, "last_prompt": state["last_prompt"]}


def node_a2_generate(state: PipelineState) -> dict:
    """A2-2：生图（image_backend 统一后端；skip 时如实标记）。"""
    if state.get("dry_run") or state.get("skip_generate") or not state.get("last_prompt"):
        state["image_path"] = ""
        _log(state, "A2 generate -> SKIP（dry-run/skip-generate）")
        return {"image_path": ""}
    from image_backend import gen_image
    raw = os.path.join(state["out_dir"], "raw.png")
    n, dt = gen_image(state["last_prompt"], raw, size=state["size"],
                      transparent=state.get("transparent", False), quality="high")
    state["image_path"] = raw
    _log(state, f"A2 generate -> {n/1024:.0f}KB {dt:.1f}s ({raw})")
    return {"image_path": raw}


# ---------------------------------------------------------------------------
# A3 质量门禁（程序化 QA + Vision Gate 视觉验收）
# ---------------------------------------------------------------------------
def node_a3_gate(state: PipelineState) -> dict:
    if state.get("dry_run") or state.get("skip_generate") or not state.get("image_path"):
        state["gate_result"] = "SKIP"
        _log(state, "A3 gate -> SKIP（无图可验）")
        return {"gate_result": "SKIP", "attempts": int(state.get("attempts", 0)) + 1, "issues": []}
    from vision_gate import run_gate  # 复用正式门禁
    gate_json = os.path.join(state["out_dir"], "gate.json")
    report, result = run_gate(
        [state["image_path"]], state["atype"], state["name"],
        state.get("threshold", 7.0), state.get("baseline", []), gate_json,
        max_size=768,
    )
    attempts = int(state.get("attempts", 0)) + 1
    issues = report.get("issues", []) if isinstance(report, dict) else []
    state["gate_report"] = report
    state["gate_result"] = result
    state["attempts"] = attempts
    state["issues"] = list(issues)
    _log(state, f"A3 gate -> {result} overall={report.get('overall')} issues={len(issues)} (attempt {attempts})")
    return {"gate_report": report, "gate_result": result, "attempts": attempts, "issues": list(issues)}


# ---------------------------------------------------------------------------
# A4 引擎集成（Godot）
# ---------------------------------------------------------------------------
def node_a4_engine(state: PipelineState) -> dict:
    """按资产类型派发既有 Godot builder；失败/缺输入如实记录（不假装 PASS）。"""
    atype = state.get("atype", "sprite")
    out_dir = state["out_dir"]
    engine_out = {"status": "STUB", "engine": "godot", "project_dir": "", "log": []}
    try:
        if atype == "map":
            engine_out = _engine_map(state, out_dir)
        elif atype in ("character", "sprite", "animation"):
            engine_out = _engine_character(state, out_dir)
        else:
            engine_out = {"status": "STUB", "engine": "godot",
                          "project_dir": "", "log": [f"atype={atype} 暂无自动 builder，按契约接入"]}
    except Exception as e:
        engine_out = {"status": "FAIL", "engine": "godot", "project_dir": "",
                      "log": [f"A4 exception: {type(e).__name__}: {e}"]}
    state["engine_out"] = engine_out
    _dump(state, "engine.json", engine_out)
    _log(state, f"A4 engine -> {engine_out['status']} {engine_out.get('project_dir', '')}")
    return {"engine_out": engine_out}


def _engine_map(state: PipelineState, out_dir: str) -> dict:
    py = sys.executable
    map_json = os.path.join(out_dir, "map_v2.json")
    r = subprocess.run([py, os.path.join(TOOLS, "build-pokemon-map-v2.py"),
                        "--out", map_json], capture_output=True, text=True, timeout=300)
    if r.returncode == 0 and os.path.exists(map_json):
        return {"status": "PASS", "engine": "godot", "project_dir": map_json,
                "log": [f"map json -> {map_json}", r.stdout.strip()[-200:]]}
    return {"status": "FAIL", "engine": "godot", "project_dir": "",
            "log": [r.stdout.strip()[-300:], r.stderr.strip()[-300:]]}


def _engine_character(state: PipelineState, out_dir: str) -> dict:
    frames_dir = os.path.join(out_dir, "frames")
    # 有切帧结果则生成 Godot AnimatedSprite2D 工程
    if os.path.isdir(frames_dir) and any(f.endswith(".png") for f in os.listdir(frames_dir)):
        out_proj = os.path.join(out_dir, "godot-anim")
        py = sys.executable
        r = subprocess.run([py, os.path.join(TOOLS, "build-godot-anim-demo.py"),
                            "--frames", frames_dir, "--out", out_proj, "--name", state["name"]],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            return {"status": "PASS", "engine": "godot", "project_dir": out_proj,
                    "log": [f"godot anim demo -> {out_proj}", r.stdout.strip()[-200:]]}
        return {"status": "FAIL", "engine": "godot", "project_dir": "",
                "log": [r.stdout.strip()[-300:], r.stderr.strip()[-300:]]}
    # 单图：记录 asset 入库契约（Godot 接入由下游/人工确认）
    return {"status": "STUB", "engine": "godot", "project_dir": "",
            "log": ["无切帧结果；A4 契约：单图资产需 frames/ 后走 build-godot-anim-demo 或人工接入"]}


# ---------------------------------------------------------------------------
# A5 骨骼动画（Spine / rig-automation）
# ---------------------------------------------------------------------------
def node_a5_skeletal(state: PipelineState) -> dict:
    if state.get("skip_skeletal"):
        state["skeletal_out"] = {"status": "SKIP", "log": ["--skip-skeletal"]}
        return {"skeletal_out": state["skeletal_out"]}
    atype = state.get("atype", "sprite")
    out_dir = state["out_dir"]
    # 输入探测：分层 PSD / spine zip / .stretch
    candidates = [f for f in os.listdir(out_dir) if f.endswith((".psd", ".zip", ".stretch"))] if os.path.isdir(out_dir) else []
    if atype not in ("character", "sprite") or not candidates:
        state["skeletal_out"] = {"status": "SKIP", "atype": atype,
                                 "log": ["A5 仅角色类且有 rig 输入（psd/zip/.stretch）时执行；当前无输入，如实跳过"]}
        return {"skeletal_out": state["skeletal_out"]}
    # 校验门禁（validate-rig 在 tools/；无输入文件时以存在性为主）
    try:
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "validate-rig.py"), out_dir],
                           capture_output=True, text=True, timeout=120)
        ok = r.returncode == 0
        state["skeletal_out"] = {"status": "PASS" if ok else "FAIL", "rig_inputs": candidates,
                                 "log": [r.stdout.strip()[-300:], r.stderr.strip()[-300:]]}
    except Exception as e:
        state["skeletal_out"] = {"status": "FAIL", "rig_inputs": candidates,
                                 "log": [f"A5 exception: {type(e).__name__}: {e}"]}
    _log(state, f"A5 skeletal -> {state['skeletal_out']['status']}")
    return {"skeletal_out": state["skeletal_out"]}


# ---------------------------------------------------------------------------
# A6 归档反馈（manifest + lessons 回填 + audit）
# ---------------------------------------------------------------------------
def node_a6_archive(state: PipelineState) -> dict:
    gate_result = state.get("gate_result", "SKIP")
    final_status = "PASS" if gate_result == "PASS" else ("FAIL" if gate_result == "FAIL" else gate_result)
    manifest = {
        "schema": "asset.manifest.v2",
        "orchestrator": "langgraph-pipeline",
        "type": state.get("atype"),
        "name": state.get("name"),
        "style": state.get("style"),
        "plan": state.get("plan", {}),
        "artifacts": [p for p in [state.get("image_path", ""), state.get("engine_out", {}).get("project_dir", "")] if p],
        "meta": {
            "demand": state.get("demand", ""),
            "prompt": state.get("last_prompt", ""),
            "params": {"size": state.get("size"), "transparent": state.get("transparent", False)},
            "model": "gpt-image-2",
            "attempts": state.get("attempts", 0),
            "duration_s": round(time.time() - state.get("_t0", time.time()), 1),
        },
        "qa": {"vision": state.get("gate_report", {})},
        "engine": state.get("engine_out", {}),
        "skeletal": state.get("skeletal_out", {}),
        "skill": state.get("skill_ctx", {}).get("skill"),
        "confirmed": False,
    }
    state["manifest"] = manifest
    mpath = _dump(state, "manifest.json", manifest)
    _feedback(state)
    _audit(state, mpath)
    state["final_status"] = final_status
    _log(state, f"A6 archive -> {mpath} | final_status={final_status}")
    return {"manifest": manifest, "final_status": final_status}


def _feedback(state: PipelineState) -> None:
    """门禁 FAIL 的 issues 自动沉淀到 harness/memory/pipeline/lessons-learned.md（反馈闭环）。"""
    issues = state.get("issues") or []
    if state.get("gate_result") != "FAIL" or not issues:
        return
    path = os.path.join(REPO, "harness", "memory", "pipeline", "lessons-learned.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M')} | {state.get('name')} | langgraph-pipeline\n")
        for it in issues:
            f.write(f"- {it}\n")


def _audit(state: PipelineState, manifest_path: str) -> None:
    audit_dir = os.path.join(REPO, "audit")
    os.makedirs(audit_dir, exist_ok=True)
    with open(os.path.join(audit_dir, "langgraph-runs.md"), "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} | {state.get('name')} | "
                f"type={state.get('atype')} | gate={state.get('gate_result')} | "
                f"attempts={state.get('attempts')} | manifest={manifest_path}\n")
