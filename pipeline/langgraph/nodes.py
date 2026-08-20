# -*- coding: utf-8 -*-
"""nodes.py — 完整 pipeline LangGraph 节点（A1 + 三路线：骨骼 A / 关键帧 B / 3D F + A6）

> **workflow 与节点实现解耦**：本文件只做"节点 = 编排单元"；每个节点的具体实现
> 放在共享实现层 `pipeline/stage_executors.py`（可被 LangGraph 节点、workbench 等复用，不冲突）。
> 图（graph.py）负责流程；本文件负责把 executor 结果映射进 state 契约（stage_outputs）。

路线：
  A 骨骼：S0 生图 -> S1 拆层 -> S2 绑骨 -> S3 动画 -> S4 打包 -> S5 引擎
  B 关键帧：kb1 关键帧生成 -> kb2 Godot 帧动画工程
  F 3D（后续补充）：f1 生成 -> f2 Blender -> f3 绑骨 -> f4 动作 -> f5 Godot 3D
"""
from __future__ import annotations

import json, os, re, sys, time
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "tools")
PLG = os.path.join(REPO, "pipeline", "langgraph")
for _p in (TOOLS, PLG, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from skill_loader import DEFAULT_ROOTS, build_skill_context  # noqa: E402
from state import PipelineState  # noqa: E402
from pipeline import stage_executors as SE  # noqa: E402


def _log(state: PipelineState, msg: str) -> None:
    state.setdefault("log", []).append(msg)
    print(f"[pipeline] {msg}")


def _dump(state: PipelineState, rel: str, obj: Any) -> str:
    os.makedirs(state["out_dir"], exist_ok=True)
    p = os.path.join(state["out_dir"], rel)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return p


def _set_stage(state: PipelineState, stage: str, result: dict) -> dict:
    """把 executor 结果写进 stage_outputs[stage] 契约。"""
    so = dict(state.get("stage_outputs") or {})
    so[stage] = {"status": result.get("status"), "out": result.get("out", {}),
                 "gate": result.get("gate", {}), "reason": result.get("reason", "")}
    state["stage_outputs"] = so
    state.setdefault("stage_logs", {})
    state["stage_logs"][stage] = result.get("log_tail", "")
    _log(state, f"{stage} -> {result.get('status')}" +
         (f" | gate={result.get('gate', {}).get('result')}" if result.get("gate", {}).get("result") else "") +
         (f" | {result.get('reason')}" if result.get("reason") else ""))
    return {"stage_outputs": so, "stage_logs": state["stage_logs"]}


def _cfg(state: PipelineState) -> dict:
    """把 state 转成 executor 需要的 cfg（含 stage_outputs 供上游查找）。"""
    return {**dict(state), "stage_outputs": state.get("stage_outputs") or {}}


def _stage_status(state: PipelineState, stage: str) -> str:
    """读某 stage 的契约状态（graph 路由用）。"""
    return (state.get("stage_outputs") or {}).get(stage, {}).get("status", "SKIP")


# ===========================================================================
# A1 需求规划（含路线判定：skeletal / keyframe / 3d）
# ===========================================================================
_TYPE_KEYWORDS = [
    ("map", ["地图", "map", "俯视", "村庄", "城镇", "野外", "overworld", "场景地图"]),
    ("scene", ["场景", "scene", "town", "室内", "酒馆"]),
    ("tileset", ["瓦片", "tileset", "图块", "无缝"]),
    ("animation", ["动画", "animation", "walk", "idle", "攻击动画", "帧动画"]),
    ("character", ["角色", "character", "小人", "立绘", "人物", "chibi", "sprite character"]),
]
_ROUTE_KEYWORDS = [
    ("keyframe", ["关键帧", "帧动画", "frame", "keyframe", "godot anim", "animsprite", "帧"]),
    ("3d", ["3d", "三维", "模型", "mesh", "gltf", "fbx", "mixamo", "rigify"]),
]


def node_a1_plan(state: PipelineState) -> dict:
    demand = state.get("demand", "")
    atype = state.get("atype", "")
    if not atype:
        dl = demand.lower()
        for t, kws in _TYPE_KEYWORDS:
            if any(k in demand or k in dl for k in kws):
                atype = t
                break
        atype = atype or "sprite"
    if atype == "sprite" and state.get("persona"):
        atype = "character"
    # 路线判定：显式 --route > 需求关键词 > 默认（角色/人物 -> skeletal；其余 -> keyframe）
    route = state.get("route", "")
    if not route:
        dl = demand.lower()
        for r, kws in _ROUTE_KEYWORDS:
            if any(k in demand or k in dl for k in kws):
                route = r
                break
        route = route or ("skeletal" if atype in ("character", "sprite") else "keyframe")
    style = state.get("style", "pokemon-nds-bw")
    name = state.get("name") or _auto_name(demand, atype)
    transparent = state.get("transparent", atype in ("character", "sprite"))
    size = state.get("size", "1024x1024")
    plan = {
        "schema": "asset.plan.v1",
        "type": atype,
        "style": style,
        "name": name,
        "route": route,
        "params": {"size": size, "transparent": transparent,
                   "split": [4, 4] if atype in ("character", "animation") else None,
                   "frame_size": 64 if atype in ("character", "animation") else 0},
        "sub_tasks": _sub_tasks(atype, route),
        "pipeline": {"skeletal": "A1->S0->S1->S2->S3->S4->S5->A6",
                     "keyframe": "A1->kb1->kb2->A6",
                     "3d": "A1->F1->F2->F3->F4->F5->A6"}.get(route),
        "notes": "A1 规则解析生成；route 可被 --route 显式覆盖",
    }
    state["plan"] = plan
    state["atype"] = atype
    state["style"] = style
    state["name"] = name
    state["size"] = size
    state["transparent"] = transparent
    state["route"] = route
    _dump(state, "plan.json", plan)
    _log(state, f"A1 规划 -> type={atype} style={style} name={name} route={route} pipeline={plan['pipeline']}")
    return {"plan": plan, "atype": atype, "style": style, "name": name, "size": size,
            "transparent": transparent, "route": route}


def _auto_name(demand: str, atype: str) -> str:
    m = re.search(r"(艾琳|ailin|阿米娅|amiya|[\u4e00-\u9fff]{2,4})", demand)
    who = (m.group(1) if m else "char").lower()
    return f"{who}_{atype}_{int(time.time()) % 100000}"


def _sub_tasks(atype: str, route: str) -> list:
    if route == "keyframe":
        return ["kb1 关键帧生成（gen-frame-cycle）", "kb2 Godot 帧动画工程（对齐+AnimatedSprite2D）", "A6 归档"]
    if route == "3d":
        return ["F1 3D 生成（Tripo/混元3D/Meshy）", "F2 Blender 修正", "F3 绑骨（Mixamo/RigNet）",
                "F4 动作", "F5 Godot 3D 导入"]
    base = {
        "character": ["S0 立绘/表情/小人", "S1 拆层(PSD)", "S2 绑骨", "S3 动画", "S4 打包", "S5 Godot 引擎"],
        "map": ["S0 瓦片集/地图", "S3 门禁", "S5 Godot TileMap 工程"],
        "tileset": ["S0 瓦片集", "S3 无缝/风格门禁", "S5 瓦片入库"],
        "animation": ["S0 关键帧", "S3 帧间一致性门禁", "S5 Godot AnimatedSprite2D"],
        "scene": ["S0 场景图", "S3 视觉门禁", "S5 Godot 场景骨架"],
        "sprite": ["S0 精灵生成", "S3 视觉门禁", "S5 入库/引擎接入"],
    }
    return base.get(atype, base["sprite"])


# ===========================================================================
# S0 生图（demand 路径：LangGraph skill 三级渐进披露 + 视觉提示词 + 生图 + 门禁）
# ===========================================================================
def node_a2_skill(state: PipelineState) -> dict:
    task = f"{state.get('style', '')} {state.get('atype', '')} {state.get('demand', '')}"
    ctx = build_skill_context(state.get("skill_name") or "gpt-image", task=task,
                              skills_roots=state.get("skills_roots") or DEFAULT_ROOTS)
    state["skill_ctx"] = ctx
    _log(state, f"S0 skill_context -> activated={ctx['skill']} loaded={ctx['skill_loaded']} "
                f"resources={sorted(ctx['resources'].keys())}")
    return {"skill_ctx": ctx}


def node_a2_prompt(state: PipelineState) -> dict:
    from prompt_vision import design_prompt
    no_vision = bool(state.get("dry_run") or state.get("no_vision"))
    eff_demand = state["demand"]
    if state.get("issues"):
        eff_demand += " 上一轮验收问题（请针对性修订提示词修复）: " + "; ".join(str(x) for x in state["issues"][:6])
    prompt_doc = design_prompt(
        eff_demand, state["style"], state["atype"],
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
    _log(state, f"S0 design_prompt -> {len(state['last_prompt'])} chars (no_vision={no_vision})")
    return {"prompt_doc": prompt_doc, "last_prompt": state["last_prompt"]}


def node_a2_generate(state: PipelineState) -> dict:
    if state.get("dry_run") or state.get("skip_generate") or not state.get("last_prompt"):
        state["image_path"] = ""
        _log(state, "S0 generate -> SKIP（dry-run/skip-generate）")
        return {"image_path": ""}
    from image_backend import gen_image
    raw = os.path.join(state["out_dir"], "s0", "raw.png")
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    n, dt = gen_image(state["last_prompt"], raw, size=state["size"],
                      transparent=state.get("transparent", False), quality="high")
    state["image_path"] = raw
    _log(state, f"S0 generate -> {n/1024:.0f}KB {dt:.1f}s ({raw})")
    return {"image_path": raw}


def node_a3_gate(state: PipelineState) -> dict:
    """S0 视觉门禁（Vision Gate）。dry-run/skip 时 SKIP。"""
    if state.get("dry_run") or state.get("skip_generate") or not state.get("image_path"):
        state["gate_result"] = "SKIP"
        upd = _set_stage(state, "s0", {"status": "WARN", "out": {"image_path": state.get("image_path", "")},
                                       "gate": {"script": "vision_gate.py", "result": "SKIP", "report": {}},
                                       "reason": "dry-run/skip-generate：无图可验"})
        return {"gate_result": "SKIP", "attempts": int(state.get("attempts", 0)) + 1, "issues": [], **upd}
    from vision_gate import run_gate
    gate_json = os.path.join(state["out_dir"], "gate.json")
    report, result = run_gate([state["image_path"]], state["atype"], state["name"],
                              state.get("threshold", 7.0), state.get("baseline", []), gate_json, max_size=768)
    attempts = int(state.get("attempts", 0)) + 1
    issues = report.get("issues", []) if isinstance(report, dict) else []
    state["gate_report"] = report
    state["gate_result"] = result
    state["attempts"] = attempts
    state["issues"] = list(issues)
    _log(state, f"S0 gate -> {result} overall={report.get('overall')} issues={len(issues)} (attempt {attempts})")
    s0_status = "PASS" if result == "PASS" else ("WARN" if result == "SKIP" else "FAIL")
    upd = _set_stage(state, "s0", {"status": s0_status, "out": {"image_path": state.get("image_path", "")},
                                   "gate": {"script": "vision_gate.py", "result": result, "report": report}})
    return {"gate_report": report, "gate_result": result, "attempts": attempts, "issues": list(issues), **upd}


def node_s0_gen_portrait(state: PipelineState) -> dict:
    """S0 人物卡驱动生图（实现见 stage_executors.exec_s0_gen_portrait）。"""
    result = SE.exec_s0_gen_portrait(_cfg(state), state["out_dir"], dry_run=bool(state.get("dry_run")))
    if result["status"] == "PASS":
        state["image_path"] = result["out"].get("image_path", "")
    return _set_stage(state, "s0", result)


# ===========================================================================
# A 骨骼路线：S1-S5（实现见 stage_executors）
# ===========================================================================
def node_s1_decompose(state: PipelineState) -> dict:
    return _set_stage(state, "s1", SE.exec_s1_decompose(_cfg(state), state["out_dir"],
                                                        dry_run=bool(state.get("dry_run"))))


def node_s2_rig(state: PipelineState) -> dict:
    return _set_stage(state, "s2", SE.exec_s2_rig(_cfg(state), state["out_dir"],
                                                  dry_run=bool(state.get("dry_run"))))


def node_s3_animate(state: PipelineState) -> dict:
    return _set_stage(state, "s3", SE.exec_s3_animate(_cfg(state), state["out_dir"],
                                                      dry_run=bool(state.get("dry_run"))))


def node_s4_package(state: PipelineState) -> dict:
    return _set_stage(state, "s4", SE.exec_s4_package(_cfg(state), state["out_dir"],
                                                      dry_run=bool(state.get("dry_run"))))


def node_s5_engine(state: PipelineState) -> dict:
    return _set_stage(state, "s5", SE.exec_s5_engine(_cfg(state), state["out_dir"],
                                                     dry_run=bool(state.get("dry_run"))))


# ===========================================================================
# B 关键帧路线
# ===========================================================================
def node_kb1_keyframes(state: PipelineState) -> dict:
    return _set_stage(state, "kb1", SE.exec_kb1_keyframes(_cfg(state), state["out_dir"],
                                                          dry_run=bool(state.get("dry_run"))))


def node_kb2_godot_anim(state: PipelineState) -> dict:
    return _set_stage(state, "kb2", SE.exec_kb2_godot_anim(_cfg(state), state["out_dir"],
                                                           dry_run=bool(state.get("dry_run"))))


# ===========================================================================
# F 3D 路线（后续补充）
# ===========================================================================
def node_f1_gen3d(state: PipelineState) -> dict:
    return _set_stage(state, "f1", SE.exec_f1_gen3d(_cfg(state), state["out_dir"],
                                                    dry_run=bool(state.get("dry_run"))))


def node_f2_blender(state: PipelineState) -> dict:
    return _set_stage(state, "f2", SE.exec_f2_blender(_cfg(state), state["out_dir"],
                                                      dry_run=bool(state.get("dry_run"))))


def node_f3_rig(state: PipelineState) -> dict:
    return _set_stage(state, "f3", SE.exec_f3_rig(_cfg(state), state["out_dir"],
                                                  dry_run=bool(state.get("dry_run"))))


def node_f4_motion(state: PipelineState) -> dict:
    return _set_stage(state, "f4", SE.exec_f4_motion(_cfg(state), state["out_dir"],
                                                     dry_run=bool(state.get("dry_run"))))


def node_f5_godot3d(state: PipelineState) -> dict:
    return _set_stage(state, "f5", SE.exec_f5_godot3d(_cfg(state), state["out_dir"],
                                                      dry_run=bool(state.get("dry_run"))))


# ===========================================================================
# A6 归档反馈
# ===========================================================================
def node_a6_archive(state: PipelineState) -> dict:
    stages = {}
    for s, e in (state.get("stage_outputs") or {}).items():
        stages[s] = {"status": e.get("status"), "gate": e.get("gate", {}), "reason": e.get("reason", "")}
    overall = _overall_status(stages)
    manifest = {
        "schema": "asset.manifest.v2",
        "orchestrator": "langgraph-pipeline",
        "pipeline": state.get("plan", {}).get("pipeline", "A1->S0->S1->S2->S3->S4->S5->A6"),
        "route": state.get("route"),
        "type": state.get("atype"),
        "name": state.get("name"),
        "style": state.get("style"),
        "plan": state.get("plan", {}),
        "stages": stages,
        "artifacts": _artifact_paths(state),
        "meta": {
            "demand": state.get("demand", ""),
            "prompt": state.get("last_prompt", ""),
            "model": state.get("model") or "gpt-image-2",
            "attempts": state.get("attempts", 0),
            "duration_s": round(time.time() - state.get("_t0", time.time()), 1),
        },
        "qa": {"vision": state.get("gate_report", {})},
        "skill": state.get("skill_ctx", {}).get("skill"),
        "confirmed": False,
    }
    state["manifest"] = manifest
    mpath = _dump(state, "manifest.json", manifest)
    _audit(state, mpath)
    state["final_status"] = overall
    _log(state, f"A6 归档 -> {mpath} | route={state.get('route')} final_status={overall}")
    return {"manifest": manifest, "final_status": overall}


def _overall_status(stages: dict) -> str:
    if not stages:
        return "SKIP"
    statuses = [s.get("status", "SKIP") for s in stages.values()]
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS" in statuses:
        return "PASS"
    if "WARN" in statuses:
        return "WARN"
    return "SKIP"


def _artifact_paths(state: PipelineState) -> list:
    paths = []
    for s, e in (state.get("stage_outputs") or {}).items():
        o = e.get("out", {})
        for k in ("image_path", "layered_dir", "rig_zip", "anim_zip", "package_dir",
                  "godot_dir", "gif", "frames_dir", "project"):
            if o.get(k):
                paths.append(o[k])
    if state.get("image_path"):
        paths.append(state["image_path"])
    return paths


def _audit(state: PipelineState, manifest_path: str) -> None:
    audit_dir = os.path.join(REPO, "audit")
    os.makedirs(audit_dir, exist_ok=True)
    with open(os.path.join(audit_dir, "langgraph-runs.md"), "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} | {state.get('name')} | "
                f"route={state.get('route')} type={state.get('atype')} | "
                f"stages={sorted((state.get('stage_outputs') or {}).keys())} | "
                f"final={state.get('final_status')} | manifest={manifest_path}\n")
