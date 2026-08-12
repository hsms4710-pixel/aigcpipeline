# t5：工作台 Web（MVP 核心）

状态：todo ｜ 依赖：t2/t3/t4 ｜ 预估：3-4 天

## 目标
本地 Web 工作台：上传人设/参考图/参考音 → Job 队列 → 阶段状态机（concept→portrait→voice→package）→ 每阶段预览/下载/单步重试 → 资产包下载。

## 产出
- `tools/workbench/`：FastAPI 后端 + 前端页
- Job 存储（SQLite），状态可查询、可重试单阶段

## 验收
- [ ] 浏览器完整走通：上传 → 看到概念图 → 选图 → 听语音 → 下载资产包
- [ ] 单阶段失败可重试，不重跑整条链路
- [ ] 资产包通过 validate-asset-package
- [ ] ruff/black 通过

## 借鉴
- 3dModelGenerator（job 轮询）、handcrafted-persona-engine（角色卡交互）
