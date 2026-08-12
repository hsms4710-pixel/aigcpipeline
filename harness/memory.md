# harness/memory.md —— 经验沉淀规则

## 目录
- `harness/memory/daily/`：每日工作流水（短期原料）
- `harness/memory/errors/`：踩坑记录（现象/原因/修复）
- `harness/memory/knowledge/`：可复用知识（命令、流程、参数、模型选型结论）
- `harness/memory/decisions/`：设计决策（为什么这么做、放弃了什么方案）

## 规则
- 每个 part 结束：至少 1 条 decision + 1 条 knowledge
- 踩坑 3 次以上同类问题 → 提升到 knowledge 或 constrain
- 选型结论（如 TTS 对比实测）→ knowledge（含日期与条件，避免过时）
- memory 也是"代码知识库与代码同时维护"的一部分：改 spec 时同步改 memory 索引
