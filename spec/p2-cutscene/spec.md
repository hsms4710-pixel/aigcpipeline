# P2 Spec：过场动画 AIGC

> 状态：**暂缓（Part 4）** ｜ 依赖 P1 资产 ｜ 选型基线见 TECH-STACK.md

## 1. 目标
用 P1 资产生成程序化过场：脚本/剧情 → 分镜 → 表情/运镜/配音 → 可播放过场。

## 2. 范围
- MVP：程序化过场（对话脚本 + 表情/口型 + 简易运镜 + P1 语音）
- 进阶：Director Agent 编排（参考 Cutscene Agent / studiomi300）

## 3. 借鉴清单（工业主流优先）
- **叙事/对话脚本（shipped games 验证）**：
  - **Ink**（Inkle）：Disco Elysium / 80 Days / Heaven's Vault 使用；knots/diverts/weave，适合 10 万+ 词的大规模分支 → 首选语言
  - **Yarn Spinner**：Night in the Woods / A Short Hike / Dredge 使用；适合中小叙事 → Godot 友好备选
  - Dialogic（Godot 社区插件）：快速实现参考，非工业主流
- **Director Agent 编排**：
  - **Cutscene Agent**（论文 2604.25318）：MCP 工具包 + director 多智能体编排 3D 过场 + CutsceneBench 分层评测基准 → 最强参照
  - **studiomi300**：Director Agent + 6 镜头分镜 + 配乐/配音 → 30s 全自动管线

## 4. 验收（gate）
- [ ] 脚本（Ink/Yarn 格式）→ 可播放过场 demo（含表情/语音/运镜）
