# -*- coding: utf-8 -*-
"""graph.py — 完整 pipeline LangGraph StateGraph（A1 + S0-S5 + A6，第一优先任务）

```
START -> a1_plan
              │（S0 入口路由：persona → s0_gen_portrait；否则 demand → a2_skill→a2_prompt→a2_generate→a3_gate）
              ▼
   S0 生图 ──► S1 拆层 ──► S2 绑骨 ──► S3 动画 ──► S4 打包 ──► S5 引擎 ──► A6 归档 ──► END
               │          │          │          │          │
   a3_gate 条件：PASS/SKIP→S1；FAIL&未达上限→a2_prompt 重试；FAIL&达上限→A6
   每 stage 条件：FAIL→A6（严格）；否则进下一启用 stage（SKIP/STUB/WARN 如实记录并前进）
```

- skill 按 LangGraph 三级渐进披露在 a2_skill 加载一次，重试复用
- 无 langgraph 时 build_pipeline_graph() 返回 None，run_pipeline() 降级顺序执行
"""
from __future__ import annotations

import os, sys, time
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "tools")
PLG = os.path.join(REPO, "pipeline", "langgraph")
for _p in (TOOLS, PLG):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from state import PipelineState  # noqa: E402
from nodes import (  # noqa: E402
    STAGE_ORDER, node_a1_plan, node_a2_generate, node_a2_prompt, node_a2_skill,
    node_a3_gate, node_a6_archive, node_s0_gen_portrait, node_s1_decompose,
    node_s2_rig, node_s3_animate, node_s4_package, node_s5_engine, _stage_status,
)

ALL_STAGES = ["a1", "s0", "s1", "s2", "s3", "s4", "s5", "a6"]


def _enabled(state: dict, stage: str) -> bool:
    return stage in (state.get("stages") or ALL_STAGES)


def _next_enabled(state: dict, after: str) -> str:
    order = (state.get("stages") or ALL_STAGES)
    if after in order:
        i = order.index(after)
        return order[i + 1] if i + 1 < len(order) else "a6"
    return "a6"


def _route_s0_entry(state: PipelineState) -> str:
    """a1 后 S0 入口：persona → 人物卡生图；否则 demand 路径。"""
    if _enabled(state, "s0"):
        if state.get("persona"):
            return "s0_gen_portrait"
        return "a2_skill"
    return _next_enabled(state, "s0")


def _route_gate(state: PipelineState) -> str:
    gate = state.get("gate_result")
    if gate in ("PASS", "SKIP"):
        return _next_enabled(state, "s0")
    if gate == "FAIL" and int(state.get("attempts", 0)) < int(state.get("max_tries", 3)):
        return "a2_prompt"
    return "a6"


def _stage_router(stage: str):
    """生成单 stage 条件路由：FAIL→a6；否则进下一启用 stage。"""
    def _route(state: PipelineState) -> str:
        if not _enabled(state, stage):
            return _next_enabled(state, stage)
        if _stage_status(state, stage) == "FAIL":
            return "a6"
        return _next_enabled(state, stage)
    return _route


def _route_s0_persona(state: PipelineState) -> str:
    if not _enabled(state, "s0"):
        return _next_enabled(state, "s0")
    if _stage_status(state, "s0") == "FAIL":
        return "a6"
    return _next_enabled(state, "s0")


def _route_final(state: PipelineState) -> str:
    return "a6" if _enabled(state, "s5") else _next_enabled(state, "s5")


def build_pipeline_graph():
    """构建完整 pipeline StateGraph；langgraph 缺失返回 None。"""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as e:
        print(f"[pipeline] langgraph 不可用，降级为顺序函数调用: {e}", file=sys.stderr)
        return None

    g = StateGraph(PipelineState)
    g.add_node("a1_plan", node_a1_plan)
    g.add_edge(START, "a1_plan")
    # S0 demand 路径
    g.add_node("a2_skill", node_a2_skill)
    g.add_node("a2_prompt", node_a2_prompt)
    g.add_node("a2_generate", node_a2_generate)
    g.add_node("a3_gate", node_a3_gate)
    # S0 人物卡路径
    g.add_node("s0_gen_portrait", node_s0_gen_portrait)
    # S1-S5
    g.add_node("s1_decompose", node_s1_decompose)
    g.add_node("s2_rig", node_s2_rig)
    g.add_node("s3_animate", node_s3_animate)
    g.add_node("s4_package", node_s4_package)
    g.add_node("s5_engine", node_s5_engine)
    g.add_node("a6_archive", node_a6_archive)

    # A1 -> S0 入口路由（persona→人物卡生图；否则 demand 路径）
    g.add_conditional_edges("a1_plan", _route_s0_entry,
                            {"s0_gen_portrait": "s0_gen_portrait", "a2_skill": "a2_skill",
                             "a6": "a6_archive"})
    # S0 demand：skill -> prompt -> generate -> gate
    g.add_edge("a2_skill", "a2_prompt")
    g.add_edge("a2_prompt", "a2_generate")
    g.add_edge("a2_generate", "a3_gate")
    g.add_conditional_edges("a3_gate", _route_gate,
                            {"a2_prompt": "a2_prompt", "s1": "s1_decompose", "a6": "a6_archive"})
    # S0 人物卡：-> S1
    g.add_conditional_edges("s0_gen_portrait", _route_s0_persona,
                            {"s1": "s1_decompose", "a6": "a6_archive"})
    # S1-S5 线性 + FAIL 拦截
    g.add_conditional_edges("s1_decompose", _stage_router("s1"),
                            {"s2": "s2_rig", "a6": "a6_archive"})
    g.add_conditional_edges("s2_rig", _stage_router("s2"),
                            {"s3": "s3_animate", "a6": "a6_archive"})
    g.add_conditional_edges("s3_animate", _stage_router("s3"),
                            {"s4": "s4_package", "a6": "a6_archive"})
    g.add_conditional_edges("s4_package", _stage_router("s4"),
                            {"s5": "s5_engine", "a6": "a6_archive"})
    g.add_conditional_edges("s5_engine", _stage_router("s5"),
                            {"a6": "a6_archive"})
    g.add_edge("a6_archive", END)
    return g.compile()


def run_pipeline(job: dict, dry_run: bool = False, no_vision: bool = False,
                 skip_generate: bool = False, gate_strict: bool = False,
                 max_tries: int = 3, threshold: float = 7.0) -> dict:
    """运行完整 pipeline。返回最终 state。

    dry_run: 只校验契约+构造命令（不执行外部工具），验证整图可编译/可路由
    stages: job 里可传（默认 a1,s0,s1,s2,s3,s4,s5,a6）
    """
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
    """无 langgraph 降级：顺序执行全部启用节点（不重试）。"""
    for node in ("a1_plan", "s0_gen_portrait", "a2_skill", "a2_prompt", "a2_generate",
                 "a3_gate", "s1_decompose", "s2_rig", "s3_animate", "s4_package",
                 "s5_engine", "a6_archive"):
        if not _enabled(state, _stage_of(node)):
            continue
        fn = globals().get(f"node_{node}")
        if fn:
            state.update(fn(state))
    state["final_status"] = state.get("final_status") or "SKIP"
    return state


def _stage_of(node: str) -> str:
    m = {"s0_gen_portrait": "s0", "a2_skill": "s0", "a2_prompt": "s0", "a2_generate": "s0",
         "a3_gate": "s0", "s1_decompose": "s1", "s2_rig": "s2", "s3_animate": "s3",
         "s4_package": "s4", "s5_engine": "s5", "a1_plan": "a1", "a6_archive": "a6"}
    return m.get(node, node)


