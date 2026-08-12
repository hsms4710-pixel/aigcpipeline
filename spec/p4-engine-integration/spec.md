# P4 Spec：引擎接入（Godot 新建场景 / 接入现有游戏）

> 状态：**规划中（暂不开发，Part 3）** ｜ 对应 ROADMAP Part 3

## 1. 目标
两种模式，都吃 P1 资产包 + P3 Agent 服务：
- **模式 A（从 0 建）**：Godot 场景：NPC 实体（动画/寻路/交互）+ 对话 UI + 白名单动作执行
- **模式 B（接入现有游戏）**：Mod/注入给现有游戏加 AI NPC（白名单安全动作 + 回归检查，不破坏原游戏）

## 2. 契约
- NPC 实体 = P1 资产（立绘/图集/语音）+ P3 Agent 连接配置
- 事件总线：游戏事件（靠近/对话/任务）→ Agent；Agent 动作 → 白名单执行器
- 白名单动作示例：say / emote / face_player / move_to(范围) / give_item(白名单) / set_quest_flag

## 3. 开源/论文/产品借鉴清单（已调研）
### Godot
- **noko**（Godot 插件，Ollama API 交互，动态对话/智能 NPC）→ 最直接参照
- **godot-AI-Dialog**（免费 AI 对话生成，RPG 动态任务）→ 对话 UI 参照
- **OpenGameAgent**：Godot 4.7 .NET + Unity 6，agent kernel + 游戏感知原语 → 双引擎架构参照
- **openagentic-sdk-gdscript**：Godot 4.x Agent SDK（含 2D/VR demo）
- **Player2 AI NPC for Godot**（asset lib）：AI NPC 插件
### 接入现有游戏（Mod）
- **StardewLivingNPCs**（星露谷 SMAPI）：AI NPC + 白名单安全动作 + SVE 进度感知层 + **离线回归检查** → 模式 B 的最佳参照
- **ValleyTalk / stardew-llm-dialog / SentientValley**（星露谷对话 Mod：本地 LM Studio/OpenAI）
- **Thrall / Sigrid**（Valheim，BepInEx + HarmonyX 注入 Unity）→ BepInEx 注入技术参照
- **Convai Modding 框架**：可注入已发布 UE 游戏（商业）→ 模式 B 商业参照
### 中间件/商业
- **Oxyde**（AI Agent SDK for Game NPC，Unity/WASM 绑定，Unreal/Godot 开发中）
- **Inworld / Charisma / ego AI / NVIDIA ACE**：商业平台形态参照

## 4. MVP 范围（模式 A 先行）
- Godot 最小工程：导入 P1 资产包 → NPC 角色可显示、可播放语音、可对话（接 P3）
- 简单交互：靠近触发对话、选项/自由输入、表情变化
- 模式 B 作为后续 POC：选一个 Mod 友好的开源游戏（如星露谷类）

## 5. 验收（gate）
- [ ] Godot 单 NPC demo：显示立绘 + 播放语音 + 多轮对话
- [ ] 白名单动作执行正确，越权动作被拒
- [ ] （POC）接入现有游戏不破坏原任务/存档（回归检查）
