# -*- coding: utf-8 -*-
"""graph.py — 完整 pipeline LangGraph StateGraph（A1 + 三路线 + A6，第一优先任务）

```
START ──► A1 a1_plan ──► 路线路由（state.route：skeletal / keyframe / 3d）
                             │
   skeletal（骨骼 A）:  S0 生图（persona→s0_gen_portrait ｜ demand→a2_skill→a2_prompt→a2_generate→a3_gate）
                       → S1 拆层 → S2 绑骨 → S3 动画 → S4 打包 → S5 引擎
   keyframe（关键帧 B）: kb1 关键帧生成 → kb2 Godot 帧动画工程
   3d（后续补充 F）:    f1 生成 → f2 Blender → f3 绑骨 → f4 动作 → f5 Godot 3D
   各路线终点 → A6 归档 → END

S0 门禁：PASS/SKIP→S1；FAIL&未达上限→a2_prompt 重试；FAIL&达上限→A6
每 stage 条件：FAIL→A6（严格）；SKIP/STUB/WARN 如实记录并前进下一启用 stage
```

- workflow 与节点实现解耦：本图只编排，节点实现见 pipeline/stage_executors.py（不冲突）
- 无 langgraph 时 build_pipeline_graph() 返回 None，run_pipeline() 降级顺序执行
"""
from __future__ import annotations

import os, sys, time
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "tools")
PLG = os.path.join(REPO, "pipeline", "langgraph")
for _p in (TOOLS, PLG, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from state import PipelineState  # noqa: E402
from nodes import (  # noqa: E402
    node_a1_plan, node_a2_generate, node_a2_prompt, node_a2_skill, node_a3_gate,
    node_a6_archive, node_f1_gen3d, node_f2_blender, node_f3_rig, node_f4_motion,
    node_f5_godot3d, node_kb1_keyframes, node_kb2_godot_anim, node_s0_gen_portrait,
    node_s1_decompose, node_s2_rig, node_s3_animate, node_s4_package, node_s5_engine,
    _stage_status,
)

# 每条路线的 stage 顺序（stage key -> 下一个 stage key）
ROUTE_ORDERS = {
    "skeletal": ["a1", "s0", "s1", "s2", "s3", "s4", "s5", "a6"],
    "keyframe": ["a1", "kb1", "kb2", "a6"],
    "3d": ["a1", "f1", "f2", "f3", "f4", "f5", "a6"],
}
ALL_STAGES = sorted({s for order in ROUTE_ORDERS.values() for s in order})

# stage key -> 下一个 stage key
NEXT_STAGE = {
    "s0": "s1", "s1": "s2", "s2": "s3", "s3": "s4", "s4": "s5", "s5": "a6",
    "kb1": "kb2", "kb2": "a6",
    "f1": "f2", "f2": "f3", "f3": "f4", "f4": "f5", "f5": "a6",
}
# stage key -> 节点名
STAGE_NODE = {
    "s1": "s1_decompose", "s2": "s2_rig", "s3": "s3_animate", "s4": "s4_package", "s5": "s5_engine",
    "kb1": "kb1_keyframes", "kb2": "kb2_godot_anim",
    "f1": "f1_gen3d", "f2": "f2_blender", "f3": "f3_rig", "f4": "f4_motion", "f5": "f5_godot3d",
}


def _route(state: PipelineState) -> str:
    return state.get("route") or "skeletal"


def _enabled(state: dict, stage: str) -> bool:
    return stage in (state.get("stages") or ALL_STAGES)


def _route_from_a1(state: PipelineState) -> str:
    """A1 后按路线选 S0/关键帧/3D 入口节点。"""
    r = _route(state)
    if r == "keyframe":
        return "kb1_keyframes" if _enabled(state, "kb1") else ("kb2_godot_anim" if _enabled(state, "kb2") else "a6_archive")
    if r == "3d":
        for st in ("f1", "f2", "f3", "f4", "f5"):
            if _enabled(state, st):
                return STAGE_NODE[st]
        return "a6_archive"
    # skeletal
    if _enabled(state, "s0"):
        return "s0_gen_portrait" if state.get("persona") else "a2_skill"
    for st in ("s1", "s2", "s3", "s4", "s5"):
        if _enabled(state, st):
            return STAGE_NODE[st]
    return "a6_archive"


def _route_gate(state: PipelineState) -> str:
    gate = state.get("gate_result")
    if gate in ("PASS", "SKIP"):
        return STAGE_NODE.get("s1", "a6_archive") if _enabled(state, "s1") else _next_node(state, "s1")
    if gate == "FAIL" and int(state.get("attempts", 0)) < int(state.get("max_tries", 3)):
        return "a2_prompt"
    return "a6_archive"


def _route_s0_persona(state: PipelineState) -> str:
    if _stage_status(state, "s0") == "FAIL":
        return "a6_archive"
    return STAGE_NODE.get("s1", "a6_archive") if _enabled(state, "s1") else _next_node(state, "s1")


def _next_node(state: PipelineState, stage: str) -> str:
    nxt = NEXT_STAGE.get(stage, "a6")
    if nxt == "a6":
        return "a6_archive"
    if _enabled(state, nxt):
        return STAGE_NODE.get(nxt, "a6_archive")
    return _next_node(state, nxt)


def _stage_router(stage: str):
    """单 stage 条件路由：FAIL→a6；否则进下一启用 stage。"""
    def _route(state: PipelineState) -> str:
        if not _enabled(state, stage):
            return _next_node(state, stage)
        if _stage_status(state, stage) == "FAIL":
            return "a6_archive"
        return _next_node(state, stage)
    return _route


def build_pipeline_graph():
    """构建完整 pipeline StateGraph；langgraph 缺失返回 None。"""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as e:
        print(f"[pipeline] langgraph 不可用，降级为顺序函数调用: {e}", file=sys.stderr)
        return None

    g = StateGraph(PipelineState)
    g.add_node("a1_plan", node_a1_plan)
    # S0（骨骼路线 demand/persona）
    g.add_node("a2_skill", node_a2_skill)
    g.add_node("a2_prompt", node_a2_prompt)
    g.add_node("a2_generate", node_a2_generate)
    g.add_node("a3_gate", node_a3_gate)
    g.add_node("s0_gen_portrait", node_s0_gen_portrait)
    # 骨骼 S1-S5
    g.add_node("s1_decompose", node_s1_decompose)
    g.add_node("s2_rig", node_s2_rig)
    g.add_node("s3_animate", node_s3_animate)
    g.add_node("s4_package", node_s4_package)
    g.add_node("s5_engine", node_s5_engine)
    # 关键帧 B
    g.add_node("kb1_keyframes", node_kb1_keyframes)
    g.add_node("kb2_godot_anim", node_kb2_godot_anim)
    # 3D F（后续补充）
    g.add_node("f1_gen3d", node_f1_gen3d)
    g.add_node("f2_blender", node_f2_blender)
    g.add_node("f3_rig", node_f3_rig)
    g.add_node("f4_motion", node_f4_motion)
    g.add_node("f5_godot3d", node_f5_godot3d)
    g.add_node("a6_archive", node_a6_archive)

    g.add_edge(START, "a1_plan")
    g.add_conditional_edges("a1_plan", _route_from_a1,
                            {n: n for n in ("a2_skill", "s0_gen_portrait", "kb1_keyframes",
                                            "kb2_godot_anim", "f1_gen3d", "f2_blender",
                                            "f3_rig", "f4_motion", "f5_godot3d",
                                            "s1_decompose", "s2_rig", "s3_animate",
                                            "s4_package", "s5_engine", "a6_archive")})
    # 骨骼：S0 demand 链
    g.add_edge("a2_skill", "a2_prompt")
    g.add_edge("a2_prompt", "a2_generate")
    g.add_edge("a2_generate", "a3_gate")
    g.add_conditional_edges("a3_gate", _route_gate,
                            {"a2_prompt": "a2_prompt", "s1_decompose": "s1_decompose",
                             "a6_archive": "a6_archive"})
    g.add_conditional_edges("s0_gen_portrait", _route_s0_persona,
                            {"s1_decompose": "s1_decompose", "a6_archive": "a6_archive"})
    # 各路线线性链（FAIL→a6）
    for stage in ("s1", "s2", "s3", "s4", "s5", "kb1", "kb2", "f1", "f2", "f3", "f4", "f5"):
        nxt = _next_node({"stages": ALL_STAGES}, stage)  # 全启用时的下一节点
        g.add_conditional_edges(STAGE_NODE[stage], _stage_router(stage),
                                {nxt: nxt, "a6_archive": "a6_archive"})
    g.add_edge("a6_archive", END)
    return g.compile()


def run_pipeline(job: dict, dry_run: bool = False, no_vision: bool = False,
                 skip_generate: bool = False, gate_strict: bool = False,
                 max_tries: int = 3, threshold: float = 7.0) -> dict:
    """运行完整 pipeline（按 route 走对应路线）。返回最终 state。"""
    out_dir = job.get("out_dir") or os.path.join(REPO, "assets", "demo", "pipeline", job.get("name", "job"))
    os.makedirs(out_dir, exist_ok=True)
    initial: PipelineState = {
        **job,
        "out_dir": out_dir,
        "dry_run": dry_run,
        "no_vision": no_vision,
        "skip_generate": skip_generate,
        "gate_strict": gate_strict,
        "max_tries": max_tries,
        "threshold": threshold,
        "attempts": 0,
        "issues": [],
        "stage_outputs": {},
        "stage_logs": {},
        "log": [],
        "_t0": time.time(),
    }
    graph = build_pipeline_graph()
    if graph is None:
        return _run_sequential(initial)
    return graph.invoke(initial)


def _run_sequential(state: dict) -> dict:
    """无 langgraph 降级：按路线顺序执行全部启用节点（不重试）。"""
    r = _route(state)
    order = ROUTE_ORDERS.get(r, ROUTE_ORDERS["skeletal"])
    for stage in order:
        if stage == "a1":
            state.update(node_a1_plan(state))
        elif stage == "a6":
            state.update(node_a6_archive(state))
        elif stage == "s0":
            if state.get("persona"):
                state.update(node_s0_gen_portrait(state))
            else:
                state.update(node_a2_skill(state))
                state.update(node_a2_prompt(state))
                state.update(node_a2_generate(state))
                state.update(node_a3_gate(state))
        elif stage in STAGE_NODE:
            fn = globals()[f"node_{STAGE_NODE[stage]}"]
            state.update(fn(state))
    state["final_status"] = state.get("final_status") or "SKIP"
    return state
