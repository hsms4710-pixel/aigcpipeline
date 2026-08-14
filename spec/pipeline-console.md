# 工业级流水线工作台（spec/pipeline-console.md）—— 实现文档

> 日期：2026-08-14 ｜ 目标：所有已实现流程（生图→拆层→绑骨→动画→打包→引擎）流水线化 + 工业级多 Tab 前端
> 参照：生图.md（SunshineFlow/DreamMaker 工作流编排 + job 状态 + 效果预览）+ 工作流设计.md（阶段产物可观察）
> 状态：✅ 后端 orchestrator + 前端多 Tab 工作台已实现并联调通过（S4/S5 实测 done）

## 1. 架构
```
┌────────────────────────────────────────────────────────────┐
│ 前端（web/，React+Vite，构建到 dist/）多 Tab 工作台          │
│ 总览 / 生图 / 拆层 / 绑骨 / 动画 / 打包 / 引擎 / 资产库 / 设置│
└───────────────┬────────────────────────────────────────────┘
                │ REST (JSON)
┌───────────────▼────────────────────────────────────────────┐
│ 后端 orchestrator（tools/workbench/app.py，FastAPI :8000）  │
│ 阶段注册表(配置schema) → job 队列(线程) → 执行器(调工具/agent)│
│ → 产物归档(pipeline/artifacts/<job>) + 日志 + 门禁 + 成本    │
└───────────────┬────────────────────────────────────────────┘
  S0 生图        S1 拆层       S2 绑骨        S3 动画
  gen-portrait   see-through   rig-psd.cjs    stretchy-agent.cjs
  (python)       (GPU 20min)   (Playwright)   (DeepSeek LLM)
        S4 打包          S5 引擎
        package-assets   export-godot
        (atlas+manifest) (Godot 工程)
```

## 2. 后端能力（前端完全覆盖）
| 阶段 | 配置字段（schema 驱动，前端动态渲染） | 执行器 | 产物 |
|---|---|---|---|
| S0 生图 | persona/scene/view/exp/backend/model/size/ref/style_ref/force (10) | gen-portrait.py | 立绘/表情/小人 |
| S1 拆层 | src/save_dir/resolution/resolution_depth/steps/save_to_psd/tblr_split/seed (8) | see-through blockswap | 分层 PSD |
| S2 绑骨 | psd/out_dir/joints (3) | rig-psd.cjs (Playwright) | .stretch + Spine |
| S3 动画 | psd_or_stretch/task/max_steps/model/out_dir (5) | stretchy-agent.cjs (LLM) | 动画 + GIF |
| S4 打包 | input_zip/out_dir/atlas_size (3) | package-assets.py | atlas + manifest |
| S5 引擎 | package_dir/out_dir/godot_exe (3) | export-godot.py | Godot 工程 |

- **API**：/api/pipeline/stages（schema）、/api/pipeline/jobs（创建/列表/详情/重跑）、/api/artifacts、/api/config（掩码）、/api/pipeline/status、/api/health
- 前端从 `/api/pipeline/stages` 动态渲染配置表单 → **后端加字段，前端自动出现，永不漂移**

## 3. 前端（9 个 Tab，工业暗色主题）
| Tab | 内容 |
|---|---|
| 📊 总览 | 6 阶段 DAG 状态灯 + 最近任务 + 服务健康（8000/5173/5174） |
| 🎨~🎮 各阶段 | 左：配置表单（全部字段 + 必填/帮助/上下游提示） 右：job 列表 + 详情（状态/耗时/配置/产物/图片预览/日志）+ 重跑 |
| 🗂 资产库 | 图片预览网格 + 按 job 产物树（预览/下载） |
| ⚙️ 设置 | API Keys（掩码，env/.env）+ LLM 人设填充 + 说明 |

设计：CSS 变量设计系统（#111418 底 / #1b2129 面板 / #4c9aff 强调），grid2 双栏无重叠，全部卡片化。

## 4. 已验证（2026-08-14）
- 后端 6 阶段注册、job 创建/运行/产物/日志全通
- **S4 打包实测 done**：30 产物（atlas 266KB + manifest + 24 图），manifest 18 bones/25 slots/5 anims
- **S5 引擎实测 done**：Godot 工程 8 产物（project.godot/main.tscn/main.gd + atlas）
- 前端冒烟：9 Tab 渲染正常，配置字段数 = 后端 schema（10/8/3/5/3/3），零布局报错

## 5. 运行方式
- 后端：`tools/workbench/start-workbench.cmd`（FastAPI :8000 + 自动开浏览器）
- S2/S3 需 StretchyStudio 服务：`env/runtime/tools/stretchy-studio/start-stretchy.cmd`（5173/5174）
- 前端开发：`tools/workbench/web` 下 `npm run dev`（:5175，代理 /api→8000）

## 6. 已知待补（后续迭代）
- S0 生图依赖 Key 正确（env/.env）；S1 GPU 20min；S2/S3 依赖 stretchy 服务在线（Dashboard 有状态灯提示）
- 成本核算字段已留（cost），未接入真实计费
- S5 目前是 Godot 结构工程 + 简易呼吸演示；spine-godot 运行时接入为 M3 后续
