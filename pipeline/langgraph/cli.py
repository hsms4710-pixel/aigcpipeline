# -*- coding: utf-8 -*-
"""cli.py — 完整 pipeline LangGraph CLI（A1 + S0-S5 + A6 一条命令）

用法:
  # 人物卡驱动的完整链路（S0 gen-portrait -> S1 拆层 -> S2 绑骨 -> S3 动画 -> S4 打包 -> S5 引擎 -> A6 归档）
  python pipeline/langgraph/cli.py --persona assets/persona/ailin.json --scene splash \
      --name ailin_v11 --out-dir pipeline/artifacts/job_xxx

  # 需求驱动的生图链路（LangGraph skill 三级渐进披露 + 视觉提示词 + 生图 + Vision Gate）
  python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --type character --name ailin_v11

  # 离线冒烟：整图编译 + 契约校验 + 命令构造（不执行外部工具）
  python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --type character --dry-run

  # 单 stage / 部分 stage（从已有产物继续）
  python pipeline/langgraph/cli.py --demand "..." --type character --stages s4,s5 --s4-input <zip> --out-dir <dir>
"""
from __future__ import annotations

import argparse, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from pipeline.langgraph.graph import ALL_STAGES, run_pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="AIGC 完整流水线（LangGraph A1+S0-S5+A6）")
    # 需求驱动
    ap.add_argument("--demand", default="", help="自然语言需求（demand 路径）")
    ap.add_argument("--style", default="")
    ap.add_argument("--type", default="", choices=["", "character", "sprite", "tileset", "map", "animation", "scene"])
    # 人物卡驱动（S0 gen-portrait）
    ap.add_argument("--persona", default="", help="persona.json 路径（有则走 gen-portrait）")
    ap.add_argument("--scene", default="splash", choices=["splash", "chibi", "pixel"])
    ap.add_argument("--view", default="")
    ap.add_argument("--exp", default="")
    ap.add_argument("--backend", default="openai", choices=["openai", "gemini", "fal"])
    ap.add_argument("--model", default="")
    ap.add_argument("--style-ref", default="")
    # 通用
    ap.add_argument("--name", default="")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--baseline", nargs="*", default=[])
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--stages", default=",".join(ALL_STAGES), help=f"启用阶段，逗号分隔，默认 {','.join(ALL_STAGES)}")
    ap.add_argument("--skill", default="gpt-image")
    ap.add_argument("--skill-root", action="append", default=[])
    ap.add_argument("--max-tries", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=7.0)
    ap.add_argument("--gate-strict", action="store_true", help="S2/S3 门禁严格模式（FAIL 即停）")
    ap.add_argument("--s1-src", default="")
    ap.add_argument("--s2-psd", default="")
    ap.add_argument("--s2-joints", default="")
    ap.add_argument("--s3-input", default="")
    ap.add_argument("--s3-task", default="")
    ap.add_argument("--s3-max-steps", type=int, default=16)
    ap.add_argument("--s4-input", default="")
    ap.add_argument("--s5-input", default="")
    ap.add_argument("--godot-exe", default="")
    ap.add_argument("--dry-run", action="store_true", help="只校验契约+构造命令（不执行外部工具）")
    ap.add_argument("--no-vision", action="store_true", help="S0 提示词离线组装（不调视觉 API）")
    ap.add_argument("--skip-generate", action="store_true", help="S0 只到提示词设计")
    a = ap.parse_args()

    job = {
        "demand": a.demand,
        "style": a.style or "pokemon-nds-bw",
        "atype": a.type,
        "name": a.name,
        "persona": a.persona,
        "scene": a.scene,
        "view": a.view,
        "exp": a.exp,
        "backend": a.backend,
        "model": a.model,
        "style_ref": a.style_ref,
        "refs": a.ref,
        "baseline": a.baseline,
        "size": a.size,
        "transparent": a.transparent,
        "out_dir": a.out_dir,
        "skill_name": a.skill,
        "skills_roots": a.skill_root or None,
        "stages": [s.strip() for s in a.stages.split(",") if s.strip()],
        "s1_src": a.s1_src,
        "s2_psd": a.s2_psd,
        "s2_joints": a.s2_joints,
        "s3_input": a.s3_input,
        "s3_task": a.s3_task,
        "s3_max_steps": a.s3_max_steps,
        "s4_input": a.s4_input,
        "s5_input": a.s5_input,
        "godot_exe": a.godot_exe,
    }
    state = run_pipeline(job, dry_run=a.dry_run, no_vision=a.no_vision,
                         skip_generate=a.skip_generate, gate_strict=a.gate_strict,
                         max_tries=a.max_tries, threshold=a.threshold)
    print("\n=== pipeline 结果 ===")
    print(f"final_status={state.get('final_status')} gate_result={state.get('gate_result')} attempts={state.get('attempts')}")
    stages = state.get("stage_outputs") or {}
    for s, e in stages.items():
        g = e.get("gate", {})
        print(f"  {s}: {e.get('status')}" + (f" | gate={g.get('result')}({g.get('script','')})" if g else "") +
              (f" | {e.get('reason')}" if e.get("reason") else ""))
    if state.get("skill_ctx"):
        sc = state["skill_ctx"]
        print(f"skill: activated={sc.get('skill')} loaded={sc.get('skill_loaded')} "
              f"resources={sorted(sc.get('resources', {}).keys())}")
    print(f"out_dir: {state.get('out_dir')}")
    return 0 if state.get("final_status") in ("PASS", "WARN", "SKIP", "DRY") else 1


if __name__ == "__main__":
    sys.exit(main())
