# LangGraph 重构全 pipeline（spec/langgraph-pipeline.md）— P0 第一优先

> 日期：2026-08-21 ｜ 触发：用户「整理当前整个项目的文档和文件；把用 langgraph 重构整个 pipeline 作为第一重要任务」
> 状态：**P0（第一优先）**，实现落地于 `pipeline/langgraph/`，任务跟踪 `tasks/pipeline/tasks.md`（L0-L6）
> 上位文档：`spec/agent-workflow.md`（A1-A6 编排视图）、`spec/industrial-pipeline-v2.md`（S0-S5 蓝图，本文件将其编排层 LangGraph 化）

---

## 0. 一句话结论

项目主体是 **agent 驱动的 AIGC pipeline**。把目前「脚本 + FastAPI workbench（S0-S5）+ 人工串联」的编排，
重构为 **一个 LangGraph StateGraph 驱动的全链路**：A1 需求规划 → A2 资产生成（skill 三级渐进披露加载）→
A3 质量门禁（Vision Gate）→ A4 引擎集成（Godot）→ A5 骨骼动画（Spine/rig）→ A6 归档反馈，
节点间只认资产契约（plan/manifest），门禁 FAIL 自动回退 A2 修订重试，全程可观察、可审计、可断点续跑。

**核心转变**：编排不再写在脚本/FastAPI 里，而是显式的 LangGraph 图（StateGraph + 条件边 + 子图），
每个环节 = 节点 + harness（skill/tool/MCP），harness 可独立替换；skill 按 LangGraph 三级渐进披露运行时加载。

---

## 1. 架构（全 pipeline StateGraph）

```
START ──► A1 a1_plan ──► A2 a2_skill ──► a2_prompt ──► a2_generate ──► A3 a3_gate
                需求规划    skill 三级     视觉提示词     生图            质量门禁
                plan.json  加载(一次)     (gpt-5.5)     image_backend    Vision Gate
                                        ▲   │                              │
                                        │   └── FAIL & 未达上限(重试) ──────┤
                                        │                                  ▼
                                        │            PASS/SKIP ──► A4 a4_engine ──► A5 a5_skeletal(可选) ──► A6 a6_archive ──► END
                                        │            FAIL & 达上限 ────────────────┘  Godot 工程            Spine/rig            manifest+lessons+audit
```

**路由（条件边）**：
| 条件 | 去向 |
|---|---|
| a3_gate = PASS / SKIP | A4 引擎（未启用则跳 A5/A6） |
| a3_gate = FAIL 且 attempts < max_tries | A2 prompt（带上一轮 issues 修订重试；skill_ctx 复用不重复读盘） |
| a3_gate = FAIL 且 attempts ≥ max_tries | A6 归档（如实 FAIL） |
| a4 后 | A5（仅角色类且启用）→ A6 |

---

## 2. 状态设计（pipeline/langgraph/state.py）

`PipelineState`（TypedDict，节点间唯一契约通道）：
- **输入**：demand / style / atype / name / refs / baseline / size / transparent / max_tries / threshold / out_dir / skill_name / skills_roots / stages
- **A1**：plan（asset.plan.v1）
- **A2**：skill_ctx（Level1/2/3 三级上下文）、prompt_doc、last_prompt、image_path
- **A3**：attempts、gate_report、gate_result（PASS/FAIL/SKIP）、issues
- **A4**：engine_out（status/project_dir/log）
- **A5**：skeletal_out（status/rig_inputs/log）
- **A6**：manifest（asset.manifest.v2）、final_status、log

**诚实原则**：真实能力缺失时 status=STUB/SKIP/FAIL 并给原因，绝不假装 PASS（可观察、可审计）。

---

## 3. 节点与 harness 映射

| 节点 | 职责 | harness（skill/tool/MCP） | 状态 |
|---|---|---|---|
| A1 a1_plan | demand → 资产契约 plan.json（规则解析；`--llm-plan` 可由视觉模型增强） | contracts/style-assets.json | ✅ 已实现 |
| A2 a2_skill | **LangGraph 三级渐进披露加载 skill**（元数据→SKILL.md→按类型自动选 references） | skills_library/ + tools/skill_loader.py | ✅ 已实现 |
| A2 a2_prompt | 视觉模型提示词设计师（用 skill 上下文生成/修订 prompt） | tools/prompt_vision.py + gpt-image skill | ✅ 已实现 |
| A2 a2_generate | 统一生图后端（openai 中转站/gemini/fal，TLS 补丁） | tools/image_backend.py | ✅ 已实现 |
| A3 a3_gate | 程序化 QA + Vision Gate 视觉验收（结构化多维评分） | tools/vision_gate.run_gate() | ✅ 已实现 |
| A4 a4_engine | 按 atype 派发 Godot builder（map→build-pokemon-map-v2；character→build-godot-anim-demo） | tools/build-*.py + godot-assistant MCP | ✅ 已实现（map/character 自动，其余 STUB 契约） |
| A5 a5_skeletal | 角色类 rig 校验/修复（validate-rig/fix-rig；无输入如实 SKIP） | tools/rig-automation/ + spine | ✅ 已实现（骨架） |
| A6 a6_archive | manifest v2 + lessons 回填 + audit 日志 | harness/memory/pipeline/ + audit/ | ✅ 已实现 |

---

## 4. Skill 加载（LangGraph 三级渐进披露，A2 核心）

- 注册表：`skills_library/gpt-image/`（SKILL.md frontmatter + references + scripts，vendor 同步见 skills_library/README.md）
- 加载器：`tools/skill_loader.py`（discover / select / load / resource，多根 last-one-wins，路径安全）
- 在 a2_skill 节点**加载一次**，门禁重试时 `design_prompt(skill_ctx=...)` 复用，不重复读盘
- 按资产类型自动选 references：gallery.md 路由索引 + 1 类别 gallery（character→character-design、map→gaming、pixel→pixel-art…）+ craft.md（遵循 SKILL.md 最小切片策略）

---

## 5. 与现有 S0-S5 workbench 的关系 / 迁移

- 现有 `tools/workbench/`（FastAPI + React，S0-S5：生图→拆层→绑骨→动画→打包→引擎）保留为**前端观察/控制台**；
  **执行编排以 LangGraph 图为准**（L6 把 workbench 后端改为调用本图，前端不变）
- 两套阶段对应：S0≈A2、S1≈A5 前置（拆层）、S2≈A5、S3≈A5 动画、S4≈A4 打包、S5≈A4 引擎；
  本图以 A1-A6 为统一视图，S 细节作为子任务/子图挂载（L4）

---

## 6. 任务拆解（L0-L6，跟踪见 tasks/pipeline/tasks.md）

| 任务 | 内容 | 状态 |
|---|---|---|
| L0 | 立项：本文档 + 任务表 + LangGraph 依赖（runtime/.venv） | ✅ |
| L1 | pipeline/langgraph 包：state / nodes / graph / cli（A1-A6 全节点接线既有工具） | ✅ |
| L2 | skill 三级渐进披露接入 A2（skills_library + skill_loader + design_prompt(skill_ctx)） | ✅ |
| L3 | 门禁闭环：a3_gate 条件路由 + FAIL 带 issues 自动回退 A2 修订重试 + 离线冒烟验证 | ✅ |
| L4 | 子图化：A5 骨骼（See-Through 拆层 → StretchyStudio 绑骨 → Spine 动画）做成子图挂载 | 📋 |
| L5 | 可观察性：job 记录/断点续跑/成本核算（复用 workbench SQLite 或独立 job.json）+ 前端接线 | 📋 |
| L6 | workbench 后端改调 LangGraph 图（前端 10 Tab 不变），S0-S5 阶段映射为 A 节点子视图 | 📋 |

---

## 7. 用法（CLI）

```bash
# 完整跑（A1→A2→A3→A4→A5→A6）
python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --style pokemon-nds-bw \
    --type character --name ailin_v11 --size 1024x1024 --threshold 7.0

# 离线冒烟：验证图 + A1 + skill 三级加载（不调 API 不生图）
python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --type character --dry-run

# 只到提示词设计 / 只跑部分阶段
python pipeline/langgraph/cli.py --demand "..." --type character --skip-generate
python pipeline/langgraph/cli.py --demand "..." --type map --stages a1,a2,a3,a6
```

---

## 8. 验证与 gate

- **L1-L3 gate**：`python -m py_compile pipeline/langgraph/*.py` 全过；`--dry-run` 图编译 + skill 三级加载 OK；
  全图离线跑（`--no-vision --skip-generate`）A1→A6 产物齐全（plan/prompt/manifest v2）
- **完整门禁**：中转站恢复后 `--threshold 7.0` 真实跑（视觉提示词→生图→Vision Gate→重试）
- **后续**：A5/A6 子图与 workbench 接线（L4-L6）各自过 gate 后推进
