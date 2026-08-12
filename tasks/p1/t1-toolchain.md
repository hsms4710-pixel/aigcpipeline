# t1：生图工具链验证（按资产场景测试）

状态：done（场景 A/B 全部验证通过：t9 像素三视图+行为帧、t10 立绘+表情+转面；多轮调整 v6→v9；成本/耗时记录于各 metadata） ｜ 依赖：runtime venv + key ✅ ｜ 预估：2-3 天（已完成）

## 验证结论（2026-08-13 最终）
### 场景 A：2D 像素角色 ✅
- A1 front 锚点 + A2 三视图 + A3 行为帧(idle/walk/attack/hurt) + A4 精灵表 —— 用户确认 char_ailin_v2（t9 done）
### 场景 B：高清立绘 ✅
- B1 主立绘 + B2 表情差分（逐表情人脸层合成，身体 100% 一致）+ B3 转面/多视图（side/back）—— v9 done（t10）
- 表情质量自检：脸区均差/肤色占比阈值 + 自动重试（修复 neutral 失真，见 v8 fix）
### 通用
- 一致性手段：风格锚点 + 参考图锚点（images.edit）+ 人脸层合成
- 多轮调整：v6(2x2拼图) → v7(逐表情合成) → v8(画风参考) → v9(画风锚点+三视图)，每次前后对比记录
- 画风问题：--style-ref 未真正锁死（images.edit 非严格风格迁移）→ 调研结论见 spec/style-research.md，工业解法=本地 ComfyUI+风格LoRA/IP-Adapter

## 产出
- assets/demo/pixel/（场景 A）、assets/demo/char_ailin_splash_v7/v8/v9/（场景 B）、assets/demo/style_compare/（多画风对比）
- tools/gen-portrait.py / gen_prompt.py / gen-style-compare.py / fetch_fgo_servant.py / fetch_prts_operator.py
- 模板：contracts/prompt-templates/pixel.json / splash.json

## 验收（全部 ✅）
- [x] 场景 A：三视图身份一致、4 行为帧风格统一、透明背景/像素干净
- [x] 场景 B：表情/转面与主立绘一致（v9）
- [x] gen-prompt.py 可跑通（persona+场景+视图 → 提示词）
- [x] 多轮调整流程验证（v6→v9 前后对比）
- [x] 报告含耗时/成本/一致性结论（metadata.json + audit 记录）
