# P3 任务草稿（Part 2 启动时再细化）
> 状态：草稿 ｜ 依赖：无（可独立于 P1）

- t21 Agent 协议契约：HTTP 请求/响应 + 事件 + 白名单动作定义（contracts/agent-protocol.md）
- t22 角色注入：人设卡 → system prompt（文风/性格/世界观）
- t23 对话沙盒：本地 LLM 或 API，多轮对话不串角色
- t24 跨会话记忆：SQLite + 向量，新会话能回忆旧事实
- t25 白名单动作：JSON 输出 + 校验 + 拒绝记录
