# SKILL：角色形象生成（P1）

## 触发
P1 立绘/分层生成、角色一致性（InstantID/PuLID）、2D/3D 表情方案。

## 流程
1. 读人设卡 `persona.json`（校验通过）
2. 在 **ComfyUI** 中组装/复用 workflow：参考图/人设 → **InstantID**（或 PuLID）锁身份 → 风格 LoRA（按需）→ 立绘
3. **分层输出**（主产物）：`portrait/layered/`（头发/脸/身体/服饰分部件）→ 供 Live2D/Umamo 绑定
4. **表情（不靠 AIGC 生成表情图）**：
   - 2D：分层 → Live2D Cubism/Umamo 绑定 → 参数化表情/口型（引擎内驱动）
   - 3D：模型带 Blend Shapes/Morph Target → 引擎内调权重
   - `expressions/` 图集仅作无绑定的快速可玩占位
5. 落 metadata：ComfyUI workflow 版本/模型/seed/耗时/显存
6. 人工确认身份一致 → 落盘 assets/<character_id>/portrait/

## 参考（工业主流）
- ComfyUI（Ubisoft CHORD / Series Entertainment 生产管线）
- InstantID（首选）/ PuLID（高质量）/ IP-Adapter FaceID（轻量）
- Live2D Cubism（免费版商用门槛<1000万日元）+ Umamo（开源 rigging）
- 3D 表情：引擎原生 Blend Shapes / Morph Targets
