# SKILL：角色形象生成（P1）

## 触发
P1 立绘/表情差分生成、LoRA 一致性训练。

## 流程
1. 读人设卡 `persona.json`（校验通过）
2. 有参考图 → 按 CharForge 流程训角色 LoRA（或先用 prompt 方案验证）；无 → 风格 LoRA + 强 prompt
3. 生成立绘 full.png → 同人设+表情模板+固定 seed 生成表情差分（neutral/happy/sad/angry）
4. 产出 sheet.png 图集 + metadata（模型/参数/seed/耗时/显存）
5. 人工确认身份一致 → 落盘到 assets/<character_id>/portrait/

## 参考
- CharForge（单参考图训 LoRA）
- Flux Kontext / RefControl（身份保持+pose）
- PaCo-FLUX（RL 一致性，进阶）
