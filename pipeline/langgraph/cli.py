# -*- coding: utf-8 -*-
"""cli.py — 全 pipeline LangGraph CLI（A1-A6 一条命令）

用法:
  # 完整跑（A1 规划 -> A2 生图 -> A3 门禁 -> A4 引擎 -> A5 骨骼 -> A6 归档）
  python -m pipeline.langgraph.cli --demand "宝可梦风艾琳 4 向角色" --style pokemon-nds-bw \
      --type character --name ailin_v11 --size 1024x1024 --threshold 7.0

  # 离线冒烟：只验证 LangGraph 图 + A1 + skill 三级加载（不调 API 不生图）
  python -m pipeline.langgraph.cli --demand "宝可梦风艾琳 4 向角色" --type character --dry-run

  # 只跑到提示词设计
  python -m pipeline.langgraph.cli --demand "..." --type character --skip-generate

  # 只跑部分阶段
  python -m pipeline.langgraph.cli --demand "..." --type map --stages a1,a2,a3,a6
"""
from __future__ import annotations

import argparse, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from pipeline.langgraph.graph import ALL_STAGES, run_pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="AIGC 资产流水线（LangGraph A1-A6）")
    ap.add_argument("--demand", required=True, help="自然语言需求")
    ap.add_argument("--style", default="", help="风格（缺省由 A1 从 demand 推断 / 默认 pokemon-nds-bw）")
    ap.add_argument("--type", default="", choices=["", "character", "sprite", "tileset", "map", "animation", "scene"])
    ap.add_argument("--name", default="")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--baseline", nargs="*", default=[])
    ap.add_argument("--size", default="")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--stages", default=",".join(ALL_STAGES), help=f"启用阶段，逗号分隔，默认 {','.join(ALL_STAGES)}")
    ap.add_argument("--skill", default="gpt-image")
    ap.add_argument("--skill-root", action="append", default=[])
    ap.add_argument("--max-tries", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=7.0)
    ap.add_argument("--dry-run", action="store_true", help="只验证图 + A1 + skill 三级加载（不调 API）")
    ap.add_argument("--no-vision", action="store_true", help="A2 提示词离线组装（不调视觉 API）")
    ap.add_argument("--skip-generate", action="store_true", help="只跑到 A2 提示词设计")
    ap.add_argument("--skip-skeletal", action="store_true", help="跳过 A5 骨骼")
    a = ap.parse_args()

    job = {
        "demand": a.demand,
        "style": a.style or "pokemon-nds-bw",
        "atype": a.type,
        "name": a.name,
        "refs": a.ref,
        "baseline": a.baseline,
        "size": a.size or "1024x1024",
        "transparent": a.transparent,
        "out_dir": a.out_dir,
        "skill_name": a.skill,
        "skills_roots": a.skill_root or None,
        "stages": [s.strip() for s in a.stages.split(",") if s.strip()],
    }
    state = run_pipeline(job, dry_run=a.dry_run, no_vision=a.no_vision,
                         skip_generate=a.skip_generate, skip_skeletal=a.skip_skeletal,
                         max_tries=a.max_tries, threshold=a.threshold)
    print("\n=== pipeline 结果 ===")
    print(f"final_status={state.get('final_status')} gate_result={state.get('gate_result')} "
          f"attempts={state.get('attempts')}")
    print(f"plan      : {json.dumps(state.get('plan', {}), ensure_ascii=False)}")
    if state.get("skill_ctx"):
        sc = state["skill_ctx"]
        print(f"skill     : activated={sc.get('skill')} loaded={sc.get('skill_loaded')} "
              f"resources={sorted(sc.get('resources', {}).keys())}")
    if state.get("manifest"):
        print(f"manifest  : {os.path.join(state['out_dir'], 'manifest.json')}")
    print(f"out_dir   : {state.get('out_dir')}")
    return 0 if state.get("final_status") in ("PASS", "SKIP", "DRY") else 1


if __name__ == "__main__":
    sys.exit(main())
