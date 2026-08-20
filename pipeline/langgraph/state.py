# -*- coding: utf-8 -*-
"""state.py — 全 pipeline LangGraph 共享状态（A1-A6 统一状态机）

把 A1 需求规划 / A2 资产生成 / A3 质量门禁 / A4 引擎集成 / A5 骨骼动画 / A6 归档反馈
放进同一个 StateGraph，所有环节只通过 state 传契约（manifest/plan/gate），
与 spec/langgraph-pipeline.md 的状态设计一一对应。
"""
from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    # ---------- 输入（job） ----------
    demand: str            # 自然语言需求
    style: str             # 风格（style-assets.json 中的 key，如 pokemon-nds-bw）
    atype: str             # 资产类型：character/sprite/tileset/map/animation/scene
    name: str              # 资产名
    refs: list             # 参考图
    baseline: list         # 画风基准图
    size: str              # 生图尺寸（gpt-image-2：16px 倍数，>=655k px）
    transparent: bool      # 透明底
    max_tries: int         # 门禁重试上限
    threshold: float       # Vision Gate 阈值
    out_dir: str           # 产物目录
    skill_name: str        # 激活 skill（默认 gpt-image）
    skills_roots: list     # skill 根（默认 skills_library/）
    stages: list           # 启用的阶段列表，如 ["a1","a2","a3","a4","a5","a6"]
    dry_run: bool          # 离线冒烟：不调 API 不生图
    no_vision: bool        # design_prompt 不调视觉 API（离线组装）
    skip_generate: bool    # 只到 prompt 设计
    skip_skeletal: bool    # 跳过 A5 骨骼
    # ---------- A1 需求规划 ----------
    plan: dict             # {type, style, name, params, sub_tasks, notes}
    # ---------- A2 资产生成 ----------
    skill_ctx: dict        # LangGraph 三级 skill 上下文（Level1/2/3）
    prompt_doc: dict       # 视觉模型生成的提示词 JSON
    last_prompt: str
    image_path: str
    # ---------- A3 质量门禁 ----------
    attempts: int
    gate_report: dict      # vision_gate 结构化报告
    gate_result: str       # PASS / FAIL / SKIP
    issues: list
    # ---------- A4 引擎集成 ----------
    engine_out: dict       # {status, project_dir, engine, log}
    # ---------- A5 骨骼动画 ----------
    skeletal_out: dict     # {status, rig, clips, log}
    # ---------- A6 归档反馈 ----------
    manifest: dict
    final_status: str      # PASS / FAIL / SKIP / DRY
    log: list              # 运行日志（可观察性）
