# SKILL：工作台 Web / 编排（P1）

## 触发
工作台开发、Job 队列、阶段状态机、ComfyUI 集成、预览/重试。

## 流程
1. 按 `spec/p1-character-voice/` 契约实现后端（FastAPI）：
   - 提交 Job（人设卡+参考文件）→ 队列（**接口抽象**：MVP SQLite+状态机，生产可换 Celery/Temporal）
   - 阶段状态机：concept → portrait → voice → package
   - **形象阶段调用 ComfyUI**：人设卡 → 生成 workflow JSON → 提交 ComfyUI → 轮询结果
   - 每阶段产物可预览/下载；失败可单步重试（不整条重跑）
2. 前端：上传 → 阶段卡片（预览图/语音播放器）→ 确认/重试 → 下载资产包
3. 资产包结构按契约，`tools/validate-asset-package.ps1` 校验

## 参考
- ComfyUI API（/prompt 提交 + 轮询）→ 工业主流执行引擎
- 3dModelGenerator（job 轮询）、studiomi300（streaming 阶段输出）
