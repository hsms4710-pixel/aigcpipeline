# t1：生图工具链验证（按资产场景测试）

状态：in_progress（基础生图链路 ✅，GPT-SoVITS 零样本 ✅；按场景测试进行中）
依赖：runtime venv + key（已就绪）｜ 预估：2-3 天
选型基线：spec/TECH-STACK.md ｜ 提示词模板：spec/p1/contracts/prompt-templates.md

## 目标
验证生图链路，**按资产场景测试**（不是生成一张图就算完成）：
- 场景 A：2D 像素游戏角色（三视图 + 行为帧 + 精灵表）
- 场景 B：高清立绘角色（主立绘 + 表情差分 + 转面）
每场景：锚点机制保一致 → 三次生成规则 → 多轮调整 → 沉淀 prompt 模板。

## 前置（已就绪）
1. runtime venv（浅路径）+ 中转站 key（GPT Image）
2. 基础生图链路已验证（gpt-image-1/2，见 knowledge/toolchain-2026-08.md）
3. 提示词模板文档（contracts/prompt-templates.md）

## 验证内容（按场景）
### 场景 A：2D 像素角色
- A1 生成 **front 锚点图**（像素风，32×32 或 64×64 档）
- A2 带锚点生成 **三视图**（front/side/back）
- A3 带锚点生成 **行为帧**（idle/walk/attack/hurt）
- A4 拼 **精灵表**（统一画布/网格）→ 透明背景、像素干净
### 场景 B：高清立绘
- B1 生成**主立绘**（full-body）
- B2 带锚点生成**表情差分**（happy/sad/angry/neutral）
- B3 带锚点生成**转面/多视图**（three-quarter/side/back）
### 通用
- 一致性手段：风格锚点 + 参考图锚点（GPT Image 多参考图）+ 三次生成规则
- **多轮调整**：至少一次"生成 → 反馈 → 追加描述/换锚点 → 重生成"，记录前后对比
- 每项记录：prompt / 模型 / 耗时 / 成本 / 是否达标

## 产出
- 测试图集：assets/demo/pixel/（场景 A）、assets/demo/splash/（场景 B）
- `tools/gen-prompt.py`：persona + 资产场景 + 视图 → 提示词（读 prompt-templates）
- 模板文件：contracts/prompt-templates/pixel.md、splash.md
- 验证报告（knowledge/prompt-engineering.md）：锚点机制有效性、一致性结论、调整经验

## 验收
- [ ] 场景 A：三视图身份一致、4 行为帧风格统一、透明背景/像素干净
- [ ] 场景 B：表情/转面与主立绘一致
- [ ] gen-prompt.py 可跑通（persona+场景+视图 → 提示词）
- [ ] 多轮调整流程验证（1 次"生成→反馈→重生成"前后对比）
- [ ] 报告含耗时/成本/一致性结论

## 借鉴
- ai-game-spritesheets（GPT Image 2 锚点 + 方向表 + idle/attack 精灵表）
- 大厂立绘流程（线稿→配色→立绘→三视图→游戏内效果）
- 像素精灵工作流（基础角色→三视图→行为帧）；三次生成规则
