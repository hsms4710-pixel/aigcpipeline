# P3 Spec：AI NPC Agent 服务（引擎无关）

> 状态：**规划中（暂不开发，Part 2）** ｜ 对应 ROADMAP Part 2 ｜ 选型基线见 TECH-STACK.md

## 1. 目标
引擎无关的 NPC Agent 服务：Memory-RAG（角色记忆/关系/世界观）+ 多轮对话 + 白名单动作。先做"无游戏也能对话"沙盒，再被 P4 引擎接入。

## 2. 契约（先行定义）
- 协议：HTTP / WebSocket / MCP（至少先通 HTTP）
- 请求：`{session_id, player_message, game_state?, context?}`
- 响应：`{reply, emotions?, actions?: [白名单动作], memory_delta?}`
- 游戏事件 → Agent 感知；Agent 决策 → 白名单动作执行（安全可审计）
- 记忆分层：短期（对话内）/ 长期（跨会话，向量+SQLite）

## 3. 工业实践与开源借鉴
### 工业/商业参考（架构基准）
- **NVIDIA ACE**：米哈游/网易/腾讯/育碧/Convai/Inworld 采用（Riva ASR + Audio2Face + LLM）
- **Inworld**：接入《Mecha Break》《Second Me》；性格/知识/场景上下文（Ubisoft NEO NPCs）
- **Convai**：四层架构（Runtime/Room/Agent/Module）+ 白名单能力
- **网易《逆水寒》AI NPC**（2023 落地）、**腾讯《元梦之星》AI 伴玩**：国内大厂落地验证
- 结论：商业架构 = 性格 + 记忆 + 场景上下文 + 行为白名单，我们的 P3 按此设计

### 开源（主流优先）
- **记忆框架（工业主流）**：Letta（MemGPT 分层记忆）/ Mem0 / Zep（时间知识图谱）/ Cognee → 记忆选型库
- **AI-NPC**（EchoSingh）：RPG NPC 系统，personality/memory/quest → 结构参照
- **ai-character-engine**（Luciferjimmy）：本地全离线、人格一致性+关系演化 → 一致性设计参照
- **MindFox**：离线 NPC 记忆中间件（SQLite 轻量）→ 本地轻量方案
- **Gemma4NPC-it**：NPC 对话 + 游戏状态 JSON（quest flag/交易/情绪）→ 动作/状态输出参照
- **协议参照**：Narra（TypeScript server，引擎只是 HTTP 客户端）、OpenGameAgent（agent kernel + 游戏感知原语）
- 可复用内部资产：multica 的 NPCSimulateGameAgent、Memory-RAG 经验

## 4. MVP 范围（沙盒）
- LLM 后端抽象：本地（Ollama/CosyVoice 无关）或 API（key 可配）
- 记忆跨会话一致（记住玩家名字/关键事件）
- 输出 JSON 化动作意图，白名单校验（先用模拟白名单）
- Web 聊天沙盒页

## 5. 验收（gate）
- [ ] 沙盒可对话，多轮稳定不串角色
- [ ] 跨会话记忆：新会话能回忆起旧会话关键事实
- [ ] 至少一种协议（HTTP）打通
- [ ] 白名单动作校验：非白名单动作被拒绝并记录
