# t3：形象生成子模块 CLI

状态：todo ｜ 依赖：t1（选型）、t2（schema） ｜ 预估：2-3 天

## 目标
可复用的形象生成 CLI：人设卡 → 立绘 + 表情差分 → 资产落盘 + metadata。

## 产出
- `tools/gen-portrait.py`（或同目录脚本）：输入 persona.json + 参考图 → 输出 portrait/ 目录
- 集成：LoRA（参考图方案）或 prompt 方案（由 t1 结论定）

## 验收
- [ ] CLI 从空目录生成完整 portrait 目录（full.png + expressions/*.png + sheet.png）
- [ ] metadata.json 记录模型/参数/seed/耗时/显存
- [ ] 表情差分 4 张身份一致（人工确认）
- [ ] ruff/black 通过
