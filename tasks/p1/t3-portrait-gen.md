# t3：形象生成子模块（ComfyUI workflow 驱动）

状态：todo ｜ 依赖：t1（选型）、t2（schema） ｜ 预估：2-3 天

## 目标
可复用的形象生成模块：人设卡 → ComfyUI workflow JSON → 提交/轮询 → 立绘 + 表情差分 → 落盘 + metadata。

## 产出
- `tools/gen-portrait/`：
  - workflow 模板（InstantID 锁定身份 + 表情差分 + 分层预留）
  - 提交器：人设卡 → workflow JSON → ComfyUI API（/prompt）→ 轮询结果
  - 落盘：portrait/full.png + expressions/* + sheet.png + layered/（预留）
- metadata：workflow 版本/模型/seed/耗时/显存

## 验收
- [ ] CLI 从人设卡生成完整 portrait 目录（full + expressions + sheet）
- [ ] 表情差分 4 张身份一致（人工确认）
- [ ] metadata 记录引擎/模型/seed/耗时/显存
- [ ] ruff/black 通过
