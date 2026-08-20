# pipeline/langgraph — 全 pipeline LangGraph 重构（P0）

> 项目主体是 agent 驱动的 AIGC pipeline。本包把**完整链路三路线**做成一个 LangGraph StateGraph（workflow 与节点实现解耦，实现见 ../stage_executors.py）：
> `A1 → 路线路由 → 骨骼A: S0-S5 ｜ 关键帧B: kb1-kb2 ｜ 3D F: f1-f5（桩）→ A6 归档`

## 文件
| 文件 | 作用 |
|---|---|
| state.py | A1-A6 统一状态（PipelineState，节点间唯一契约通道） |
| nodes.py | 18 个节点：a1_plan / s0(gen_portrait,a2_skill,a2_prompt,a2_generate,a3_gate) / s1-s5 / kb1-kb2 / f1-f5 / a6_archive；实现全部委托 stage_executors |
| graph.py | 全 pipeline StateGraph + 条件路由（门禁 FAIL 自动回退 A2 修订重试）+ run_pipeline() |
| cli.py | 命令行入口 |

## 用法
```bash
# 完整跑
python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --style pokemon-nds-bw \
    --type character --name ailin_v11 --size 1024x1024 --threshold 7.0
# 离线冒烟（不调 API 不生图）
python pipeline/langgraph/cli.py --demand "..." --type character --dry-run
# 只到提示词 / 部分阶段
python pipeline/langgraph/cli.py --demand "..." --type character --skip-generate
python pipeline/langgraph/cli.py --demand "..." --type map --stages a1,a2,a3,a6
```

## 关键设计
- **skill 运行时加载**：a2_skill 节点用 `skill_loader.build_skill_context()` 加载 gpt-image skill 三级内容
  （元数据→完整 SKILL.md→按资产类型自动选 gallery/craft），门禁重试复用 `skill_ctx` 不重复读盘
- **门禁闭环**：a3_gate 用 `vision_gate.run_gate()`（正式 Vision Gate，结构化多维评分）；FAIL 自动带 issues 回退 A2 修订
- **诚实原则**：真实能力缺失时 status=STUB/SKIP/FAIL 并给原因，不假装 PASS
- **产物**：out_dir/plan.json + prompt.json + gate.json + engine.json + manifest.json（asset.manifest.v2）

详见 `spec/langgraph-pipeline.md`（架构/状态/路由/任务拆解 L0-L6）。


