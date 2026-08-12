# t3：形象生成子模块（云生图 API 驱动）

状态：代码框架完成（gen_prompt + gen-portrait dry-run ✅；真实生成待中转站恢复）｜ 依赖：t2 ✅ ｜ 预估：2-3 天

## 目标
可复用的形象生成模块：persona.json → 提示词（gen-prompt）→ 云生图 API（GPT Image，锚点可带参考图）→ 立绘/表情 → 资产包落盘 + metadata。
> 选型已更新：生图后端 = 云 API（GPT Image 2 / Nano Banana Pro），本地 ComfyUI 仅可选离线后端（不再默认 ComfyUI workflow）。

## 产出
- `tools/gen-prompt.py`（t8 前置核心）：persona + 场景 + 视图 → 分层提示词（读 persona-schema + prompt-templates 设计）
- `tools/gen-portrait.py`：主 CLI——persona.json → prompt → 云 API → 落盘 portrait/（full + expressions）+ metadata.json + 资产包校验
- 后端抽象：`IMAGE_BACKEND=openai`（中转站）；生图函数支持文生图（images.generate）与**参考图锚点**（responses API，等中转站恢复即用）

## 验收
- [ ] gen-prompt.py：persona（示例艾琳）→ 像素三视图/立绘表情 prompt 各 1 条，风格锚点自动带
- [ ] gen-portrait.py：代码可运行至调用前（中转站 503 时给出清晰错误 + 重试提示）；恢复后生成 full.png + 表情 + metadata
- [ ] 落盘符合 asset-package-spec；validate-asset-package 通过
- [ ] ruff/black 通过
