# LangGraph 重构完整 pipeline（spec/langgraph-pipeline.md）— P0 第一优先

> 日期：2026-08-21 ｜ 触发：用户「整理当前整个项目的文档和文件；把用 langgraph 重构整个 pipeline 作为第一重要任务」
> 更新：2026-08-21 v2 —— **完整链路全部 LangGraph 化**：S0 生图→S1 拆层→S2 绑骨→S3 动画→S4 打包→S5 引擎 全部接线真实工具（不再是生图+占位）
> 状态：**P0（第一优先）**，实现落地于 `pipeline/langgraph/`，任务跟踪 `tasks/pipeline/tasks.md`（L0-L6）
> 上位文档：`spec/agent-workflow.md`（A1-A6 编排视图）、`spec/industrial-pipeline-v2.md`（S0-S5 蓝图，本文件将其编排层 LangGraph 化）

---

## 0. 一句话结论

项目主体是 **agent 驱动的 AIGC pipeline**。把目前「脚本 + FastAPI workbench（S0-S5）+ 人工串联」的编排，
**完整重构为 LangGraph StateGraph**：`A1 需求规划 → S0 生图 → S1 拆层 → S2 绑骨 → S3 动画 → S4 打包 → S5 引擎 → A6 归档反馈`。
每个 stage = 一个（或一组）LangGraph 节点，**真实调用既有底层工具**（gen-portrait / prompt_vision+image_backend /
See-through / StretchyStudio rig-psd / LLM 动画导演 stretchy-agent / package-assets / export-godot / validate-*），
节点间只认资产契约（plan / stage_outputs / manifest），门禁 FAIL 自动沉淀经验并回退重试，全程可观察、可审计。

**核心转变**：编排不再写在 FastAPI/脚本里，而是显式的 LangGraph 图（StateGraph + 条件边）；
skill 按 LangGraph 三级渐进披露运行时加载；workbench 前端保留为观察/控制台（L6 接线）。

---

## 1. 架构（完整 pipeline StateGraph）

```
START ──► A1 a1_plan ──► ┌ S0 生图 ──────────────┐
                           │ persona → s0_gen_portrait │
                           │ demand → a2_skill → a2_prompt → a2_generate → a3_gate │
                           └──────────────────────────┘
                                   │ a3_gate：PASS/SKIP→S1；FAIL&未达上限→a2_prompt 重试；FAIL&达上限→A6
                                   ▼
S1 s1_decompose ──► S2 s2_rig ──► S3 s3_animate ──► S4 s4_package ──► S5 s5_engine ──► A6 a6_archive ──► END
See-through      StretchyStudio   LLM 动画导演       package-assets     export-godot      manifest+lessons
blockswap→PSD    DWPose+fix-rig   +fix-rig+usage     图集+校验          Godot SpinePlayer  +audit
+validate-layered  +validate-rig   +validate-anim
```

**每 stage 条件边**：FAIL→A6（gate_strict 严格模式即停；否则记录）；SKIP/STUB/WARN 如实记录并前进下一启用 stage。
**S0 门禁重试**：a3_gate FAIL & attempts<max_tries → a2_prompt（带上一轮 issues 修订；skill_ctx 复用）。

---

## 2. 状态设计（pipeline/langgraph/state.py）

`PipelineState`（TypedDict，节点间唯一契约通道）：
- **输入**：demand/style/atype/name/refs/baseline/size/…；persona/scene/view/exp/backend/model/style_ref（人物卡驱动）；
  s1_src/s2_psd/s2_joints/s3_input/s3_task/s4_input/s5_input/godot_exe（单 stage 独立跑覆盖）
- **A1**：plan（asset.plan.v1）
- **S0**：skill_ctx（三级）、prompt_doc、last_prompt、image_path、attempts、gate_report、gate_result、issues
- **各 stage 契约**：`stage_outputs[<stage>] = {status, out, gate, reason}`
  - s0.out = {image_path, images?}；s1.out = {layered_dir, psd}；s2.out = {rig_zip}
  - s3.out = {anim_zip, gif, usage, cost}；s4.out = {package_dir}；s5.out = {godot_dir, project}
- **A6**：manifest（asset.manifest.v2，含 stages 各状态/gate/reason + artifacts + meta）、final_status、log

**诚实原则**：工具/服务缺失（See-through 未装、StretchyStudio 未起、输入缺失）时 status=STUB/SKIP/FAIL 并给原因，绝不假装 PASS。

---

## 3. 节点与真实工具接线

| 节点 | 职责 | 底层工具（真实接线） | 门禁 | 状态 |
|---|---|---|---|---|
| A1 a1_plan | demand→plan 资产契约 | contracts/style-assets.json | — | ✅ |
| S0 s0_gen_portrait | 人物卡→立绘/表情/小人 | tools/gen-portrait.py（persona→--scene splash/chibi/pixel） | — | ✅ |
| S0 a2_skill | **LangGraph 三级渐进披露加载 skill** | skills_library/ + tools/skill_loader.py | — | ✅ |
| S0 a2_prompt | 视觉提示词设计师（用 skill 上下文） | tools/prompt_vision.design_prompt（skill_ctx 复用） | — | ✅ |
| S0 a2_generate | 统一生图后端 | tools/image_backend.gen_image（openai/gemini/fal + TLS 补丁） | — | ✅ |
| S0 a3_gate | 视觉验收门禁 | tools/vision_gate.run_gate()（结构化多维评分，threshold 7.0） | PASS/FAIL/SKIP | ✅ |
| S1 s1_decompose | 立绘→Live2D 规范分层 PSD | env/runtime/tools/see-through inference_psd_blockswap.py（HF offline env） | validate-layered.py（WARN 非致命） | ✅ |
| S2 s2_rig | 分层 PSD→DWPose 自动绑骨→.stretch+Spine | tools/rig-automation/rig-psd.cjs + fix-rig.py | validate-rig.py（FAIL→lessons；strict 即停） | ✅ |
| S3 s3_animate | LLM 动画导演（idle/walk/attack/hurt+表情） | tools/rig-automation/stretchy-agent.cjs（AGENT_MODEL=deepseek，--rules 注入经验）+ fix-rig.py + usage 成本核算 | validate-anim.py（FAIL→lessons；strict 即停） | ✅ |
| S4 s4_package | Spine→atlas 图集+manifest | tools/package-assets.py（--atlas-size） | validate-asset-package.py | ✅ |
| S5 s5_engine | 资产包→Godot 可玩工程（SpinePlayer） | tools/export-godot.py（--godot 可执行路径） | 工程生成 | ✅ |
| A6 a6_archive | manifest v2 + lessons 回填 + audit | harness/memory/pipeline/lessons-learned.md + audit/langgraph-runs.md | — | ✅ |

**反馈闭环**：S1/S2/S3 门禁 FAIL → `_append_lesson()` 自动沉淀 harness/memory/pipeline/lessons-learned.md（同签名去重）→ S3 动画 `--rules` 注入规避规则。

---

## 4. Skill 加载（LangGraph 三级渐进披露）

- 注册表：`skills_library/gpt-image/`（SKILL.md frontmatter + references + scripts）
- 加载器：`tools/skill_loader.py`（discover/select/load/resource，多根 last-one-wins，路径安全）
- a2_skill 节点**加载一次**，门禁重试 `design_prompt(skill_ctx=...)` 复用；按资产类型自动选 references（character→character-design、map→gaming、pixel→pixel-art… + craft.md）

---

## 5. 与现有 workbench 的关系 / 迁移

- `tools/workbench/`（FastAPI + React，S0-S5 + 一键流水线 + 断点续跑）保留为**前端观察/控制台**；
  **执行编排以 LangGraph 图为准**（L6：workbench 后端 run_stage 改为调用本图节点；前端 10 Tab 不变）
- 命令构造逐字对齐 app.py（见 nodes.py 各 stage），产物/门禁/经验库路径一致，可无缝切换

---

## 6. 任务拆解（L0-L6，跟踪见 tasks/pipeline/tasks.md）

| 任务 | 内容 | 状态 |
|---|---|---|
| L0 | 立项：spec + 任务表 + langgraph 依赖 | ✅ |
| L1 | pipeline/langgraph 包：state/nodes/graph/cli | ✅ |
| L2 | skill 三级渐进披露接入 S0（skills_library + skill_loader + design_prompt(skill_ctx)） | ✅ |
| L3 | S0 门禁闭环：a3_gate 条件路由 + FAIL 带 issues 回退重试 | ✅ |
| L3.5 | **完整 S0-S5 接线**：拆层/绑骨/动画/打包/引擎 全节点接真实工具 + 各 stage 门禁 + 反馈闭环 | ✅（离线验证：整图编译+契约+命令构造通过） |
| L4 | 真实跑通：See-through/StretchyStudio/deepseek 服务就绪后全链实测（含 GPU/端口/模型依赖） | 📋 |
| L5 | 可观察性：job 记录/断点续跑/成本核算 + 前端接线 | 📋 |
| L6 | workbench 后端改调 LangGraph 图（前端 10 Tab 不变） | 📋 |

---

## 7. 用法（CLI）

```bash
# 人物卡驱动的完整链路（S0 gen-portrait → S1 拆层 → S2 绑骨 → S3 动画 → S4 打包 → S5 引擎 → A6 归档）
python pipeline/langgraph/cli.py --persona assets/demo/persona.json --scene splash \
    --name ailin_v11 --out-dir pipeline/artifacts/job_xxx

# 需求驱动的生图链路（LangGraph skill 三级渐进披露 + 视觉提示词 + 生图 + Vision Gate）
python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --type character --name ailin_v11

# 离线冒烟：整图编译 + 契约校验 + 命令构造（不执行外部工具）
python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --type character --dry-run

# 单 stage / 部分 stage（从已有产物继续）
python pipeline/langgraph/cli.py --demand "..." --stages s4,s5 --s4-input <zip> --out-dir <dir>
```

---

## 8. 验证与 gate

- **L1-L3.5 gate**：`py_compile` 全过；`--dry-run` 整图编译 + 路由 + skill 三级加载 OK；manifest v2 含全部 stages 状态
- **L4 gate（真实跑）**：See-through（GPU）→ StretchyStudio（5173/5174）→ deepseek 动画 → package → godot，各 stage 门禁如实记录；中转站恢复后 S0 Vision Gate threshold 7.0
- **后续**：L5/L6 可观察性与 workbench 接线各自过 gate 后推进
