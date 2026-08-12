# P2 Spec：过场动画 AIGC

> 状态：**暂缓（Part 4）** ｜ 依赖 P1 资产

## 1. 目标
用 P1 资产生成程序化过场：脚本/剧情 → 分镜 → 表情/运镜/配音 → 可播放过场。

## 2. 范围
- MVP：程序化过场（Dialogic / Godot 时间轴 + 表情差分 + 简易运镜 + P1 语音）
- 进阶：Director Agent 编排（参考 Cutscene Agent / studiomi300）

## 3. 借鉴清单
- **Cutscene Agent**（论文 2604.25318）：MCP 工具包 + director 多智能体编排 3D 过场 + **CutsceneBench 分层评测基准** → 最强参照
- **studiomi300**：Director Agent + 6 镜头分镜 + 配乐/配音 → 30s 全自动管线
- **Dialogic / Yarn Spinner / Ink / Naninovel**：游戏对话/过场脚本生态

## 4. 验收（gate）
- [ ] 脚本 → 可播放过场 demo（含表情/语音/运镜）
