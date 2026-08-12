# decision-2026-08-13-表情方案
- 结论：表情差分 = 逐表情 images.edit(mask=人脸区) + **人脸层合成回基底**（羽毛边）
- 原因：中转站 gpt-image-2 的 images.edit 即使带 mask 也整体重绘（body 像素一致率 1.5%），必须合成保证连贯（合成后 100%）
- 附：表情质量自检（脸区肤色占比 + 平均差异）阈值驱动自动重试（最多 3 次）

# decision-2026-08-13-画风路线
- 结论：云 API 的 images.edit 不是严格风格迁移 → 画风锁死走**本地 ComfyUI + 风格 LoRA / IP-Adapter**（工业主流）
- 云 API 轨道：风格母版图 + 固定风格 prompt 模板 + 负向约束，只作快速概念
- 多画风候选：hd2d / anime2d / pixel / gacha2d（assets/demo/style_compare/，待用户选定）
