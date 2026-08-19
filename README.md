# 角色 AIGC → AI NPC → 引擎接入（多引擎）→ 评测

> 研究课题 + 工程仓库 ｜ 一句话目标：把「角色形象/语音 AIGC 生成 → AI NPC（记忆/行为/对话）→ 引擎接入（新建游戏或接入现有游戏）→ 评测」做成一条**可观察、可归因、可复用**的工作流，并沉淀为可开源产品。
> 当前重心（2026-08-19）：**以 Agent Workflow 为中心的 AIGC 资产流水线**（视觉提示词 → 生图 → Vision Gate 视觉验收 → 引擎），落地在宝可梦 NDS BW 风俯视 demo。

## 当前状态（2026-08-19）
- ✅ **A2 资产生成标准入口**：`tools/a2-pipeline.py`（视觉提示词设计师 → 生图 → Vision Gate → FAIL 自动修订重试 → manifest），瓦片集实测 PASS 7.0
- ✅ **Godot MCP 实装**：godot-assistant（25 工具）注册进 Codex；`tools/godot-shot.py` 截游戏内画面 → 喂 Vision Gate（游戏内验收）
- ✅ **W2.1 地图打磨**：A2 生成 12 格瓦片集 + 域扭曲大块草地/有机湖/沙滩/主干道桥/村庄/成林树丛；地图全景 gate 6、游戏内 5（未达 7，继续）
- ✅ 2D 画风定稿（v10 立绘 + chibi_v4 小人）；2D 横板 demo（godot-game-base）可玩；俯视 demo（godot-pokemon-demo）可玩
- ⏳ 2D 骨骼 A 路线（Spine）阻塞：See-Through LayerDiff3D 模型下载（需 hf-mirror）
- ⏸️ 3D 线 / 过场（P2）/ 评测（P5）后置

## 五层结构
| 层 | 内容 | 位置 |
|---|---|---|
| 研究 | 课题拆解 / 全链路调研（网易 DreamMaker 对照）/ 研究问题 | `研究计划.md`、`链路总览.md`、`生图.md`、`spec/` |
| 规范 | 每环节 spec + 风格资产契约 + Agent Workflow | `spec/`、`contracts/` |
| Harness | skills / memory / rules / audit | `harness/`、`rules/`、`audit/` |
| 执行 | AIGC 工具脚本 + 工作台 | `tools/`（见 tools/README.md）、`pipeline/` |
| 产物 | 角色资产 / demo 工程 / A2 流水线输出 | `assets/`（见 assets/demo/ASSET-INDEX.md） |

## Agent Workflow 中心（spec/agent-workflow.md）
```
自然语言需求 → ORCHESTRATOR 拆解 → 分派执行 agent（带 harness）
  A1 需求/规划 → A2 资产生成（prompt_vision → 生图 → 切帧）
             → A3 质量门禁（程序化 QA + Vision Gate 视觉验收）
             → A4 引擎集成（Godot）/ A5 Spine 骨骼 / A6 归档反馈
```
- **A2 标准入口**：`python tools/a2-pipeline.py --demand "..." --style pokemon-nds-bw --type character --name xxx`
- **Vision Gate**：`python tools/vision_gate.py <img> --type map --baseline <风格基准> --out gate.json`
- **游戏内验收**：`python tools/godot-shot.py --scene res://main.tscn --out shot.png` → 再跑 Vision Gate

## 可运行 demo
| demo | 内容 | 启动 |
|---|---|---|
| **godot-pokemon-demo** | 宝可梦 NDS BW 俯视：4向x4帧 walk + W2.1 地图（村庄/湖/桥/森林） | `assets/demo/godot-pokemon-demo/start-pokemon.cmd` |
| **godot-game-base** | 2D 横板：SunnyLand 地图 + 艾琳侧视（像素/HD-2D 切换）+ 战斗 | `assets/demo/godot-game-base/start-game.cmd` |
| 工作台 | 人设卡编辑器 + 阶段状态机 | `tools/workbench/`（见 spec/workbench-v2.md） |

## 目录地图（权威索引：PROJECT-INDEX.md）
```
rules/        # 规则层：课题原则 + 仓库规则
spec/         # 规范层：每 part/环节 spec + 调研（agent-workflow / aigc-tools / style-assets 等）
contracts/    # 资产契约：style-assets.json / persona-schema.json / prompt-templates
harness/      # AI 执行层：mode/inform/constrain/verify/memory + skills
tasks/        # 任务拆解与进度（主表：tasks/pipeline/tasks.md）
audit/        # 审计：清单 + 日志
reference/    # 调研引用（风格标杆库 / aigc-km / 素材站 / 资产源）
assets/       # 工作产物（角色资产、demo 工程、A2 输出，见 ASSET-INDEX.md）
tools/        # 本地工具脚本（见 tools/README.md）
pipeline/     # 工作台运行时（artifacts 不入库）
env/          # 隔离运行环境 + key（不入库）；**环境重建指南见 env/README.md**（工具 clone/安装/模型下载）
_archive/     # 本地归档（不入库）
PROJECT-INDEX.md  # 唯一入口索引（文档/进度/代码/产物全索引）
```

## 怎么进入开发
1. 读 `PROJECT-INDEX.md`（总索引）→ `spec/agent-workflow.md`（当前工作流）→ `tasks/pipeline/tasks.md`（主进度表）
2. 新资产需求走 A2 入口（`tools/a2-pipeline.py`），产出必须过 Vision Gate
3. 遵守 `harness/`（constrain 红线 + verify 门禁），经验沉淀到 `harness/memory/`

## 原则速览
- **引擎无关、资产中立**：P1 只产出标准资产（PNG/WAV/glTF/JSON），任何引擎可导入
- **复用优于自研**：每环节先列开源/论文/产品借鉴清单（godot-assistant / ai-pixel-art / FrameRonin / Spine 等）
- **视觉验收是流水线一部分**：Vision Gate（gpt-5.5）是正式门禁环节，不靠肉眼判断
- **一个 part 一个 part 来**：做透一个再进下一个；评测（P5）后置
