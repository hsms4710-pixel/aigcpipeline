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
- 管线在**隔离环境**执行（env/README.md：Docker Compose / WSL2 / 云机三选一），本机只做浏览器入口 + git
- 本机 8GB 显存 → 隔离机按需选型（SDXL 8GB 够；FLUX/PuLID/3D 需 24GB+ 或云 API）

## Part 1 —— P1 角色形象+语音生成工作台 MVP（⏳ 下一个）
- 目标：本地 Web 工作台：人设卡/参考图/参考音 → 立绘（分层，Live2D/3D blendshape 预留）+ 语音 → 资产包下载
- 生图后端：**云 API 首选 GPT Image 2 + Nano Banana**；本地 ComfyUI 为可选离线后端
- 借鉴：CharForge / Flux Kontext（形象一致性）、GPT-SoVITS / CosyVoice / F5-TTS（语音）、handcrafted-persona-engine / AITuberKit（虚拟人栈）、3dModelGenerator（job 状态机）
- **gate**：P1 验收全部通过（见 `spec/p1-character-voice/spec.md` + `tasks/p1/`）；Godot 最小工程能导入立绘+播放语音；P1 审计记录入 `audit/audit-log.md`

## Part 2 —— P3 AI NPC Agent 服务（规划中）
- 目标：引擎无关 Agent 服务（Memory-RAG + 对话 + 白名单动作），先做"无游戏也能对话"沙盒
- 借鉴：AI-NPC / ai-character-engine / MindFox / Letta / Mem0 / Zep / Gemma4NPC-it；协议参考 Narra
- **gate**：沙盒可对话、记忆跨会话一致、HTTP/WS/MCP 三种协议至少通一种

## Part 3 —— P4 引擎接入（规划中）
- 目标 A：Godot 场景（交互/寻路/任务）接入 P3 Agent，可玩单 NPC demo
- 目标 B（POC）：接入现有游戏（星露谷类 SMAPI/开源游戏），白名单安全动作
- 借鉴：noko / godot-AI-Dialog / OpenGameAgent（Godot）、StardewLivingNPCs / ValleyTalk / SentientValley（Mod）、Thrall / Sigrid（BepInEx）、Convai Modding
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


