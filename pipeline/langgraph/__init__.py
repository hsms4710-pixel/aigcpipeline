# -*- coding: utf-8 -*-
"""pipeline.langgraph — 用 LangGraph 重构的 AIGC 资产流水线（P0）。

- state.py : A1-A6 统一状态
- nodes.py : A1 规划 / A2 资产生成(skill 三级加载+视觉提示词+生图) / A3 门禁 / A4 引擎 / A5 骨骼 / A6 归档
- graph.py : 全 pipeline StateGraph（门禁 FAIL 自动回退 A2 修订重试）
- cli.py   : python -m pipeline.langgraph.cli

设计文档：spec/langgraph-pipeline.md ｜ 任务跟踪：tasks/pipeline/tasks.md（L0-L6）
"""
from pipeline.langgraph.graph import build_pipeline_graph, run_pipeline
from pipeline.langgraph.state import PipelineState

__all__ = ["build_pipeline_graph", "run_pipeline", "PipelineState"]
