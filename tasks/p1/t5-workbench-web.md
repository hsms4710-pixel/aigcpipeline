# t5：工作台 Web（MVP 核心）

状态：in_progress（后端+前端+画布已实现并构建；实跑待中转站恢复） ｜ 依赖：t2 ✅ t3 ✅ ｜ 预估：3-4 天

## 目标
本地 Web 工作台：上传人设/参考图/参考音 → Job 队列 → 阶段状态机（concept→portrait→voice→package）→ 每阶段预览/下载/单步重试 → 资产包下载。

## 产出
- `tools/workbench/`：FastAPI 后端 + 前端页
- Job 存储（SQLite，接口抽象可换 Celery/Temporal）；形象阶段调云生图 API（GPT/Nano Banana）

## 验收
- [ ] 浏览器完整走通：上传 → 看到概念图 → 选图 → 听语音 → 下载资产包（待中转站恢复后实跑）
- [ ] 无限画布：人设卡/立绘/语音节点铺开，点击预览，产物自动入画布
- [ ] 单阶段失败可重试，不重跑整条链路
- [ ] 资产包通过 validate-asset-package
- [ ] ruff/black 通过

## 借鉴
- ComfyUI API（工业主流执行引擎）、3dModelGenerator（job 轮询）
