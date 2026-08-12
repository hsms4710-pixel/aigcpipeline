# Key 接入规范（env/key-access.md）

> 原则：**不自己写接入**。LLM/生图 key 接入参照 OpenClaw config.toml 的 `[model_providers.XXX]` 格式（也兼容 hermes/piagent 等 agent 框架的 provider 配置思路）；MCP 用 OpenClaw 的现成集成（`openclaw mcp` 命令 / `mcp.servers` 配置），复用 dcc-mcp 等已有 adapter。

## 1. LLM / 生图（中转站，OpenAI 兼容）
- 配置：`env/config.toml`（OpenClaw 格式，已填用户 key，**不入库**）
  - `[model_providers.OpenAI]`：base_url = https://api.sisct2.xyz/v1，wire_api = "responses"，requires_openai_auth = true
  - model = gpt-5.5（LLM/审阅）
- 生图：走同一中转站（OpenAI 兼容 /v1）；**模型名/参数按中转站文档确认**（gpt-image-1/2 或该站模型名）；工作台通过 `env/.env` 读 key（GPT_API_KEY/GPT_BASE_URL）
- 不要自己写 OpenAI 客户端逻辑：用现有 SDK（openai-python）按 base_url 指向中转站即可

## 2. 3D（Tripo 试用 key，额度有限）
- `env/.env` → TRIPO_API_KEY=tcli_...；调用走 Tripo 官方 API（SDK 现成），不自己实现协议

## 3. MCP（不要自写客户端）
- 用 OpenClaw 集成：`openclaw mcp add <name> -- <command>` 或 config `mcp.servers`（stdio/SSE/Streamable HTTP）
- 复用已有 adapter：dcc-mcp（Blender 等 DCC）、OpenClaw 自带/社区 MCP servers
- 我们的工作台如需 MCP 能力：通过 OpenClaw 暴露（OpenClaw 作为 MCP 客户端注册表），不在工作台里自研 MCP 客户端

## 4. 敏感信息
- `env/config.toml`、`env/.env` 含真实 key，已在 .gitignore，**禁止提交**
- 审计时检查：`git ls-files | grep -i "config.toml\|.env"` 应为空
