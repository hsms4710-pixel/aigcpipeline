# harness/inform.md —— 项目地图（AI 先看这里）

## 我是什么
「角色 AIGC → AI NPC → 引擎接入 → 评测」研究课题仓库。当前主线：**Part 1 = P1 形象+语音工作台 MVP**。

## 先读什么
1. `README.md` —— 总览与状态
2. `ROADMAP.md` —— 当前 Part 与 gate
3. `rules/PRINCIPLES.md` —— 8 条原则（必须遵守）
4. `rules/REPO.md` —— 目录/命名/提交/审计规则
5. 当前 part 的 `spec/<part>/spec.md` 与 `tasks/<part>/`

## 模块索引
- 生成管线：P1（形象/语音）→ 见 spec/p1
- Agent：P3 → 见 spec/p3（暂不开发）
- 引擎：P4 → 见 spec/p4（暂不开发）
- 过场：P2 → 见 spec/p2（暂缓）
- 评测：P5 → 见 spec/p5（后置，不实现）
- 调研引用：reference/README.md
- 经验沉淀：harness/memory/（daily/errors/knowledge/decisions）

## 关键契约文件（待创建）
- `spec/p1-character-voice/contracts/persona-schema.json`（人设卡 v0）
- `spec/p1-character-voice/contracts/asset-package-spec.md`（资产包规范）
- `spec/p3-npc-agent/contracts/agent-protocol.md`（Agent 协议，Part 2 建）

