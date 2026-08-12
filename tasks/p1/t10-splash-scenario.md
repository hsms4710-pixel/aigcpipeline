# t10：场景 B 立绘完整测试（主立绘→表情→转面）

状态：done（v8：主立绘 + 半身基底 + 4 张独立表情，**明日方舟阿米娅立绘作 --style-ref 画风迁移**；转面后置） ｜ 依赖：t1 ✅ ｜ 预估：1-2 天（已完成）

## 目标
跑通高清立绘资产全套：主立绘 → 表情差分 → 转面/多视图。

## 产出
- assets/demo/char_ailin_splash_v8/：主立绘(full.png) + 半身基底(bust.png) + 表情差分×4（独立透明 PNG）+ 2×2 审阅拼图(exp_sheet.png) + metadata.json
  - v8 使用 `assets/reference/arknights/阿米娅/立绘/阿米娅_1.png`（唯@W）作为 --style-ref 画风迁移
- v7（无风格参考）保留对照：assets/demo/char_ailin_splash_v7/
- 记录：prompt / 锚点 / 耗时 / 成本 → metadata.json

## 表情方案（v8 迭代，对齐工业做法）
- ❌ v6（废弃）：一张 2×2 拼图 → 切分。模型不按网格画，产出"一张大图被切 4 份"。
- ✅ v7/v8（当前）：**逐表情生成 + 人脸层合成**（VNCCS Emotion Studio / Live2D 表情切换同思路）
  1. `full.png`：主立绘（style-ref 画风迁移 / 或纯 prompt）
  2. `bust.png`：半身头像基底（images.edit 从 full 保持角色）
  3. 每个表情：`images.edit(bust, mask=人脸区)` → **抠人脸区合成回 bust 基底**（羽毛边）→ 身体/发型/服装像素级一致，只替换表情
- 关键发现：中转站 gpt-image-2 的 images.edit 即使带 mask 也会整体重绘（body 一致率仅 1.5%），必须"人脸层合成回基底"（合成后 100%）。

## 验收
- [x] 表情与主立绘一致（合成保证身体 100% 一致，4 张独立表情）
- [x] 构图可用（透明背景、立绘完整性）
- [x] 多轮前后对比（v6 拼图 → v7 合成 → v8 画风迁移）
- [x] 画风参考落地：--style-ref 阿米娅立绘（用户反馈 v7"表情对、画风参考没到位" → v8 补上）
- [ ] 转面/多视图（后置）
