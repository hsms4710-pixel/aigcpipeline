# t10：场景 B 立绘完整测试（主立绘→表情→转面）

状态：done（v9：画风参考加强(明日方舟风格锚点+风格迁移prompt) + 主立绘/半身/4表情/三视图全部产出；转面已实现） ｜ 依赖：t1 ✅ ｜ 预估：1-2 天（已完成）

## 目标
跑通高清立绘资产全套：主立绘 → 表情差分 → 转面/多视图。

## 产出（assets/demo/char_ailin_splash_v9/portrait/）
- full.png 主立绘（--style-ref 阿米娅立绘 + 明日方舟风格锚点）
- bust.png 半身基底
- exp_happy/sad/angry/neutral.png（独立透明 PNG，人脸层合成，body 100% 一致；带质量自检+自动重试）
- exp_sheet.png（2×2 审阅）
- turn_side.png / turn_back.png（逐视图编辑自 full）
- turnaround_sheet.png（front|side|back 3 视图审阅）

## 画风方案（v9 迭代）
- v7/v8：--style-ref 但 prompt 偏"别复制参考角色"，且风格描述笼统 → 用户反馈"画风没遵循"
- v9：① persona.style.anchor 改为显式「Arknights(明日方舟) 官方画风、柔和笔触赛璐璐、细线稿、渐变、暖灰调」；② build_style_prompt 改为"仔细研究参考图的线稿/上色/渲染技法，用完全一致的画风画新角色"；③ bust/表情 prompt 也带风格锚点

## 转面方案（v9 新增）
- 不用整图 3 视图 sheet（模型不可靠），改为逐视图 images.edit(full) → side/back，再合成审阅图

## 验收
- [x] 表情与主立绘一致（合成保证 body 100%，4 张独立表情）
- [x] 转面/多视图（front/side/back 产出）
- [x] 多轮前后对比（v6 拼图 → v7 合成 → v8 画风参考 → v9 画风锚点+三视图）
- [ ] 画风是否最终落地：待用户目检 v9
