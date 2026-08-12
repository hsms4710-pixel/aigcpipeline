# SKILL：NPC Agent 服务（P3，Part 2 使用）

## 触发
P3 Agent 沙盒开发、记忆、对话、白名单动作。

## 流程
1. 读 `spec/p3-npc-agent/contracts/agent-protocol.md`（Part 2 建立）
2. 角色注入：读人设卡 → system prompt 构建（文风/性格/世界观）
3. 记忆：短期（对话内）+ 长期（SQLite/向量，跨会话）
4. 输出：reply + emotions + actions（白名单校验，越权拒绝并记录）
5. 协议：HTTP 先通，再 WS/MCP

## 参考
- AI-NPC / ai-character-engine / MindFox / Letta / Mem0 / Zep
- Gemma4NPC-it（动作/状态 JSON 输出）
- 内部可复用：NPCSimulateGameAgent、Memory-RAG 经验
