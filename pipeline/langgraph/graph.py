# -*- coding: utf-8 -*-
"""graph.py — 全 pipeline LangGraph StateGraph（A1-A6，第一优先任务）

```
START -> a1_plan -> a2_skill -> a2_prompt -> a2_generate -> a3_gate
                                                      │
   a3_gate 条件边：PASS/SKIP -> a4_engine -> a5_skeletal(可选) -> a6_archive -> END
                  FAIL & 未达上限 -> a2_prompt（带 issues 修订重试，skill_ctx 复用）
                  FAIL & 达上限 -> a6_archive（如实 FAIL 归档）
```

- skill 按 LangGraph 三级渐进披露在 a2_skill 节点加载一次，重试复用（不重复读盘）
- 每个节点只通过 state 传契约；门禁 FAIL 自动回退 A2 修订（带上一轮 issues）
- 无 langgraph 时 build_pipeline_graph() 返回 None，由 run_pipeline() 降级为顺序函数调用
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
    node_a1_plan, node_a2_generate, node_a2_prompt, node_a2_skill,
    node_a3_gate, node_a4_engine, node_a5_skeletal, node_a6_archive,
)

ALL_STAGES = ["a1", "a2", "a3", "a4", "a5", "a6"]


def _stage_enabled(state: dict, stage: str) -> bool:
    stages = state.get("stages") or ALL_STAGES
    return stage in stages


def _route_gate(state: PipelineState) -> str:
    """a3_gate 条件边：PASS/SKIP→a4；FAIL 未达上限→a2_prompt 重试；FAIL 达上限→a6 归档。"""
    gate = state.get("gate_result")
    if gate in ("PASS", "SKIP"):
        return "a4" if _stage_enabled(state, "a4") else ("a5" if _stage_enabled(state, "a5") else "a6")
    if gate == "FAIL" and int(state.get("attempts", 0)) < int(state.get("max_tries", 3)):
        return "a2_prompt"
    return "a6"


def _route_a4(state: PipelineState) -> str:
    return "a5" if _stage_enabled(state, "a5") else "a6"


def build_pipeline_graph():
    """构建全 pipeline StateGraph；langgraph 缺失返回 None。"""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as e:
        print(f"[pipeline] langgraph 不可用，降级为顺序函数调用: {e}", file=sys.stderr)
        return None

    g = StateGraph(PipelineState)
    g.add_node("a1_plan", node_a1_plan)
    g.add_node("a2_skill", node_a2_skill)
    g.add_node("a2_prompt", node_a2_prompt)
    g.add_node("a2_generate", node_a2_generate)
    g.add_node("a3_gate", node_a3_gate)
    g.add_node("a4_engine", node_a4_engine)
    g.add_node("a5_skeletal", node_a5_skeletal)
    g.add_node("a6_archive", node_a6_archive)

    # 主线：a1 -> a2(skill -> prompt -> generate) -> a3
    g.add_edge(START, "a1_plan")
    g.add_edge("a1_plan", "a2_skill")
    g.add_edge("a2_skill", "a2_prompt")
    g.add_edge("a2_prompt", "a2_generate")
    g.add_edge("a2_generate", "a3_gate")
    # a3 条件边：PASS/SKIP→a4；FAIL 重试/归档
    g.add_conditional_edges("a3_gate", _route_gate,
                            {"a2_prompt": "a2_prompt", "a4": "a4_engine", "a5": "a5_skeletal", "a6": "a6_archive"})
    # a4 -> a5（可选）-> a6
    g.add_conditional_edges("a4_engine", _route_a4, {"a5": "a5_skeletal", "a6": "a6_archive"})
    g.add_edge("a5_skeletal", "a6_archive")
    g.add_edge("a6_archive", END)
    return g.compile()


def run_pipeline(job: dict, dry_run: bool = False, no_vision: bool = False,
                 skip_generate: bool = False, skip_skeletal: bool = False,
                 max_tries: int = 3, threshold: float = 7.0) -> dict:
    """运行全 pipeline。返回最终 state。

    dry_run: 只跑 A1+A2(离线组装 skill 上下文) ，验证图与 skill 加载，不调 API 不生图
    skip_generate: 跑到 A2 prompt 设计为止
    stages: job 里可传（默认全开 a1..a6）
    """
    out_dir = job.get("out_dir") or os.path.join(REPO, "assets", "demo", "pipeline", job.get("name", "job"))
    os.makedirs(out_dir, exist_ok=True)
    initial: PipelineState = {
        **job,
        "out_dir": out_dir,
        "dry_run": dry_run,
        "no_vision": no_vision,
        "skip_generate": skip_generate,
        "skip_skeletal": skip_skeletal,
        "max_tries": max_tries,
        "threshold": threshold,
        "attempts": 0,
        "issues": [],
        "log": [],
        "_t0": time.time(),
    }
    graph = build_pipeline_graph()
    if graph is None:
        # 降级：顺序执行（等价路径，无 langgraph）
        state = dict(initial)
        for node in ("a1_plan", "a2_skill", "a2_prompt", "a2_generate", "a3_gate",
                     "a4_engine", "a5_skeletal", "a6_archive"):
            if node == "a2_prompt" and state.get("gate_result") == "FAIL":
                continue  # 简化降级路径不重试
            fn = globals()[f"node_{node}"]
            state.update(fn(state))
        state["final_status"] = state.get("final_status") or "DRY"
        return state
    if dry_run:
        # 离线冒烟：a1 -> a2_skill -> a2_prompt（no_vision 组装），验证图 + skill 三级加载
        state = dict(initial)
        for node in ("a1_plan", "a2_skill", "a2_prompt"):
            fn = globals()[f"node_{node}"]
            state.update(fn(state))
        state["final_status"] = "DRY"
        return state
    return graph.invoke(initial)

