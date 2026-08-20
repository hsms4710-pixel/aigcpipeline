# -*- coding: utf-8 -*-
"""state.py — 完整 pipeline LangGraph 状态（A1 规划 + S0-S5 全链 + A6 归档）

完整链路（与 tools/workbench S0-S5 一一对应，全部 LangGraph 化）：
  A1 需求规划 → S0 生图(gen-portrait 或 demand+skill 路径) → S1 拆层(See-through)
  → S2 绑骨(StretchyStudio DWPose + fix-rig) → S3 动画(LLM 动画导演 + fix-rig)
  → S4 打包(package-assets atlas) → S5 引擎(export-godot SpinePlayer) → A6 归档反馈

每 stage 输出写进 stage_outputs[<stage>]；门禁结果写 gate 段；节点只认 state 契约。
"""
from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    # ---------- 输入（job） ----------
    demand: str            # 自然语言需求（demand 驱动路径）
    style: str
    atype: str             # character/sprite/tileset/map/animation/scene
    name: str
    route: str             # 路线：skeletal(骨骼A) / keyframe(关键帧B) / 3d(3D F，后续补充)
    refs: list
    baseline: list
    size: str
    transparent: bool
    max_tries: int         # S0 视觉门禁重试上限
    threshold: float       # S0 Vision Gate 阈值
    out_dir: str           # job 产物根目录
    skill_name: str
    skills_roots: list
    stages: list           # 启用的阶段，如 ["a1","s0","s1","s2","s3","s4","s5","a6"]
    dry_run: bool          # 只校验契约+命令构造，不执行工具（离线验证）
    no_vision: bool        # S0 demand 路径提示词离线组装
    skip_generate: bool    # S0 只到提示词设计
    gate_strict: bool      # S2/S3 门禁严格模式（FAIL 即停）
    max_resource_chars: int
    # ---------- S0 人物卡驱动（gen-portrait） ----------
    persona: str           # persona.json 路径（有则走 gen-portrait，否则 demand 路径）
    scene: str             # splash/chibi/pixel
    view: str
    exp: str
    backend: str           # openai/gemini/fal
    model: str             # 生图模型
    style_ref: str         # 风格参考（逗号分隔）
    # ---------- 各阶段显式输入覆盖（支持单 stage 独立跑） ----------
    s1_src: str
    s2_psd: str
    s2_joints: str
    s3_input: str
    s3_task: str
    s3_max_steps: int
    s4_input: str
    s5_input: str
    godot_exe: str
    atlas_size: int
    # ---------- B 关键帧路线输入 ----------
    kb_hero: str           # matte 锚点图（gen-frame-cycle --hero）
    kb_style: str          # hd2d / pixel / ...
    kb_only: str           # 只生成部分动作（逗号分隔，可空）
    kb_force: bool
    kb_frames: str         # 关键帧目录（kb2 显式输入，可空）
    target_h: int
    fps: str
    # ---------- A1 需求规划 ----------
    plan: dict
    # ---------- S0 demand 路径（LangGraph skill 三级渐进披露） ----------
    skill_ctx: dict
    prompt_doc: dict
    last_prompt: str
    image_path: str
    attempts: int
    gate_report: dict
    gate_result: str       # PASS / FAIL / SKIP
    issues: list
    # ---------- 各 stage 输出（契约） ----------
    stage_outputs: dict    # {"s0": {...}, "s1": {...}, "s2": {...}, ...}
    stage_logs: dict       # {stage: 日志尾部}
    # ---------- A6 归档反馈 ----------
    manifest: dict
    final_status: str      # PASS / FAIL / SKIP / DRY
    log: list
    _t0: float
