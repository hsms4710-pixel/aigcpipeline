# 角色 AIGC → AI NPC → 引擎接入（多引擎）→ 评测

> 研究课题 + 工程仓库 ｜ 一句话目标：把「角色形象/语音 AIGC 生成 → AI NPC（记忆/行为/对话）→ 引擎接入（新建游戏或接入现有游戏）→ 评测」做成一条**可观察、可归因、可复用**的工作流，并沉淀为可开源产品。

## 当前状态（2026-08-12）
- ✅ Part 0 地基：仓库 / rule / spec / harness / task 拆解 / 审计机制（本仓库）
- ⏳ **下一步：Part 1 —— P1 角色形象+语音生成工作台 MVP**
- ⏸️ 评测（P5）**后置**：等 P1-P4 跑通后再规划实现，当前只保留目标占位（见 `spec/p5-eval/`）

## 五个 Part
| Part | 内容 | 状态 |
|---|---|---|
| P1 | 角色形象（立绘+表情差分/3D glTF）+ 语音（克隆 TTS） | **先行（MVP）** |
| P2 | 过场动画 AIGC（依赖 P1 资产） | 暂缓 |
| P3 | AI NPC Agent（记忆/行为/对话，引擎无关 HTTP/WS/MCP） | 规划中 |
| P4 | 引擎接入（Godot 新建场景 / 接入现有游戏 Mod） | 规划中 |
| P5 | 评测（内容×行为×集成 + 跨层归因） | **后置，暂不实现** |

## 目录地图
```
rules/        # 规则层：课题原则 + 仓库规则
spec/         # 规范层：每个 part 一份 spec（含开源借鉴清单）
harness/      # AI 执行规则层：mode/inform/constrain/verify/memory/metrics + skills
tasks/        # 任务拆解：backlog + 每 part 可执行任务（含验收）
audit/        # 审计：清单 + 日志
reference/    # 调研引用（开源/论文/产品，按 part 分组）
assets/       # 工作产物（角色资产、样本、实验输出）
tools/        # 本地工具脚本（校验、导入、编排）
工作流设计.md  # 管线衔接 / 多引擎 / 工作台形态（调研文档）
研究计划.md    # 研究问题 / 架构 / 评测设计 / 节奏（调研文档）
```

## 怎么进入开发（流程）
1. 读 `ROADMAP.md` 确认当前 Part
2. 读该 Part 的 `spec/<part>/spec.md`（范围 + 借鉴清单 + 契约）
3. 看 `tasks/<part>/` 的任务拆解，逐条执行（每条含验收标准）
4. 执行时遵守 `harness/`（尤其 `constrain.md` 红线 + `verify.md` 门禁）
5. Part 完成后跑 `audit/AUDIT.md` 清单，结果记入 `audit/audit-log.md`
6. 经验沉淀到 `harness/memory/`（knowledge/errors/decisions）

## 原则速览
- **引擎无关、资产中立**：P1 只产出标准资产（PNG/WAV/glTF/JSON），任何引擎可导入
- **复用优于自研**：每 part 都先列开源/论文/产品借鉴清单，再决定自研范围
- **一个 part 一个 part 来**：不并行铺开，做透一个再进下一个；评测后置
- **每层产物可见**：工作台形态，阶段状态机 + 预览/下载/单步重试
