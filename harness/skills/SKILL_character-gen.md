# SKILL：角色形象生成（P1）

## 触发
P1 立绘/表情/分层生成、角色一致性（InstantID/PuLID）、风格 LoRA。

## 流程
1. 读人设卡 `persona.json`（校验通过）
2. 在 **ComfyUI** 中组装/复用 workflow：参考图/人设 → **InstantID**（或 PuLID）锁身份 → 风格 LoRA（按需）→ 立绘 + 表情差分
3. 表情差分：同人设 + 表情模板 + 固定 seed（neutral/happy/sad/angry）
4. 分层预留：产出 `portrait/layered/`（头发/脸/身体/服饰分部件，Live2D/Spine 管线需要；MVP 可先人工拆分 + 规范）
5. 落 metadata：ComfyUI workflow 版本/模型/seed/耗时/显存
6. 人工确认身份一致 → 落盘 assets/<character_id>/portrait/

## 参考（工业主流）
- ComfyUI（Ubisoft CHORD / Series Entertainment 生产管线）
- InstantID（首选）/ PuLID（高质量）/ IP-Adapter FaceID（轻量）
- LoRA 训练（角色/风格锁定，按需）
- CharForge 仅研究参考，不默认
