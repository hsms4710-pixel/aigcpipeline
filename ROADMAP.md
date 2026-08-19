# ROADMAP：实现路线（一个 part 一个 part）

> 总原则：**顺序推进，做透一个再进下一个**；评测（P5）后置，不在前期实现。
> 范围边界与分 Part 验证：见 链路总览.md（权威视图）。
> 每个 Part 完成后必须过 gate（完成标准）+ 审计，才能进入下一个 Part。

## 依赖关系
```
P1 资产 ──► P2 过场（用 P1 资产）
  │
  └──────► P4 引擎接入（用 P1 资产）
P3 Agent（引擎无关，可先沙盒）──► P4
P2 / P3 / P4 ──► P5 评测（后置）
```

## Part 0 —— 地基（✅ 本次完成）
- 仓库骨架、rule、spec 占位、harness、task 拆解、审计机制
- **gate**：README 目录地图与实际一致；每个 part 有 spec 占位；P1 有可执行任务拆解

## DCC 加工层（P6，横切）
- AIGC 资产进引擎前需 DCC 加工（清理/UV/绑定/表情 morph/导出）→ Agent 通过 **DCC-MCP** 控制 Blender 等自动完成
- 复用：dcc-mcp-creator（intern-learn 664011）+ layout-forge dccBridge 经验；见 spec/p6
- 进入时机：P1 3D 扩展（S1）→ P4（S3/S5）→ P2（S4）

## 主线（当前重点）：生成一个可交互 NPC
> 用户决策 2026-08-12：**过场动画（P2）后置**，先考虑怎么把 NPC 生成出来。
> 主链：**P1 形象+语音 → P3 Agent → P4 引擎接入（NPC 实体化+引擎内动画）** → 打通后再启动 P2 过场 / P5 评测。
## 执行环境（全 Part 通用）
- 管线在**本地隔离文件夹**执行（env/runtime/，uv venv 3.11，见 env/README.md），不污染系统
- 生图走云 API（GPT + Nano Banana），本地只跑工作台 + TTS + 音频 → 本机 8GB 够 P1；3D/PuLID 后置（需云机/API）

## Part 1 —— P1 角色形象 + V1 语音管线（✅ 已交付 2026-08-13；t4 语音暂缓）
- **P1 形象**：工作台：人设卡/参考图 → 立绘（分层，Live2D/3D blendshape 预留）→ 资产包
  - 生图后端：**云 API 首选 GPT Image 2 + Nano Banana**；本地 ComfyUI 为可选离线后端
  - 借鉴：ComfyUI 生产管线 / InstantID / GPT Image 2 / Nano Banana；handcrafted-persona-engine（UI）、3dModelGenerator（job 状态机）
  - **gate**：验收全过（见 `spec/p1-character-voice/spec.md` + `tasks/p1/`）；Godot 最小工程能导入立绘；P1 审计
- **V1 语音管线**（独立实践，见 `spec/voice/spec.md`）：
  - 路线 A 零样本克隆（CosyVoice 2，3-10s）｜ 路线 B **声音集训练定制 TTS**（GPT-SoVITS 微调 / CosyVoice2 / Spark-TTS / Qwen3-TTS，5-10min+ 声音集）｜ 增强 RVC 音色转换
  - 数据工具：zh-tts-mini-corpus + 自研清洗（人声分离/切分/标注）；版权仅用自有/授权声音集
  - **gate**：三条验证（零样本/微调/RVC）全过 + 版权声明

## Part 2 —— P3 AI NPC Agent 服务（规划中）
- 目标：引擎无关 Agent 服务（Memory-RAG + 对话 + 白名单动作），先做"无游戏也能对话"沙盒
- 借鉴：AI-NPC / ai-character-engine / MindFox / Letta / Mem0 / Zep / Gemma4NPC-it；协议参考 Narra
- **gate**：沙盒可对话、记忆跨会话一致、HTTP/WS/MCP 三种协议至少通一种

## Part 3 —— P4 引擎接入（⏳ M0 已完成：Godot 角色展示链路，见 tasks/p1/t11）
- 目标 A：Godot 场景（交互/寻路/任务）接入 P3 Agent，可玩单 NPC demo
- 目标 B（POC）：接入现有游戏（星露谷类 SMAPI/开源游戏），白名单安全动作
- 借鉴：noko / godot-AI-Dialog / OpenGameAgent（Godot）、StardewLivingNPCs / ValleyTalk / SentientValley（Mod）、Thrall / Sigrid（BepInEx）、Convai Modding
- **M0（✅ 2026-08-13）**：Godot 角色展示（立绘+表情切换+小人，t11）
- **gate**：Godot 单 NPC demo 可玩；Mod POC 不破坏原游戏（回归检查）

## Part 4 —— P2 过场 AIGC（⏸️ 后置，NPC 主链打通后再启动；方案见 spec/p2-cutscene）
- 范式：A AIGC 视频过场（播片）/ B 引擎内程序化过场（实机）/ C 混合 → MVP 走 B 为主 + A 做展示
- 管线：Ink 剧本 → Director Agent 拆镜头 → GPT Image 2（角色/关键帧）+ Nano Banana Pro（场景/分镜）→ 动画化（B: Godot 时间轴 / A: Veo/Kling/Wan 图生视频）→ TTS 配音
- **gate**：M2-1→M2-3（引擎内过场 demo）+ M2-4（AIGC 视频 POC）

## Part 5 —— P5 评测（⏸️ 后置，暂不实现）
- 目标：内容×行为×集成 三维评分卡 + 跨层归因 + 元评测（详见 `研究计划.md` §4）
- **前置依赖**：P1-P4 至少各有一个稳定 demo 可被评测；评测方法论先行（人工锚点→VLM judge）
- **明确不做**：在 P1-P4 跑通之前，不实现评测功能、不建评测平台

## 阶段流转（每个 Part 内部）
```
spec（范围+借鉴+契约）→ tasks 拆解 → harness/skill 就位 → 开发（逐 task）→ verify → audit → 归档
```





## 双管线推进（2026-08-13 起，详见 spec/dev-roadmap-2d3d.md + tasks/pipeline/tasks.md）
> 依据：生图.md（网易 DreamMaker 调研）+ pipeline-unified-2d3d.md（双管线统一分析，网易内部=缺口）
> 原则：**2D 线优先**（外部工具齐，差异化在 2D 骨骼）；3D 线后置（可选）

| 阶段 | 名称 | 主线 | 验收一句话 |
|---|---|---|---|
| P1-A | 画风定稿+生图基线 | 定主画风→三件套同画风 | 立绘/表情/小人同画风，用户确认 |
| P1-B | 2D 拆层 | 立绘→可动部件（Live2D 规范 PSD） | ≥8 可动层，可导入 Spine/Live2D |
| P1-C | 2D 骨骼 | Spine/Live2D + 自动绑骨 | 可摆姿势+表情参数 |
| P1-D | 2D 动画 | 基础动画+AI 补帧 | 动作循环+表情切换 |
| P1-E | 打包/引擎 | 图集+Godot 导入 | demo 分层显示/动画播放 |
| P2-3D | 3D 线（后置） | 3D生成→修正→绑骨→动作→引擎 | 3D 角色进 Godot 可动 |

**每阶段 gate**：任务全过 + 产出物 + 验收清单 + audit 记录（沿用项目 verify/audit 文化）
**横切**：画风 LoRA（如选 ComfyUI 路线）、工作台 v2 前端（后续）、memory 沉淀

---

## 2D 骨骼动画重规划（2026-08-14）
> **权威文档：`spec/pipeline-remaster-2d-skeletal.md`**（含「2D 骨骼怎么做」调研 + 烂因实测 + 全任务重规划）
> 路线：**P1 动画质量修复（M0 walk→M1 全动画）→ P2 流水线硬化（rig/anim gate + S5 spine 播放器）→ P3 引擎闭环 → P4 反馈/成本/开源**
> 关键：不能把烂动画流水线化；M0/M1 未过前不批量重跑 S3。

---

## 近期重点（2026-08-19：Agent Workflow + AIGC 资产流水线）
> 权威文档：`spec/agent-workflow.md`（A1-A6 编排）、`spec/aigc-tools-integration.md`（工具集成）、`spec/style-assets.md`（风格资产契约）
> 主进度表：`tasks/pipeline/tasks.md`

| 项 | 内容 | 状态 |
|---|---|---|
| W0 工具层 | skills 6 + frame-ronin MCP + **godot-assistant MCP** + aigc-toolkit + vision_gate | ✅ |
| A2 标准入口 | tools/a2-pipeline.py（视觉提示词→生图→Vision Gate→重试→manifest） | ✅ 瓦片集 PASS 7.0 |
| W2 宝可梦俯视地图全链 | 瓦片→地图→Godot demo（4向x4帧 walk + 村庄/湖/桥/森林） | ✅ 闭环 |
| W2.1 地图打磨 | 全景 gate 6 / 游戏内 5（画风7/可玩7/统一7） | ⏳ 未达 7，待办：过渡瓦片/路标地标/统一描边 |
| W3 角色/动画全链 | 8向精灵→行动画→Spine（A 路线） | 📋（阻塞：See-Through 模型下载） |
| W5 评测/反馈闭环 | agent eval 平台接自家 agent | 📋 |
