# Character AIGC 工业级流水线工作台（Workbench）

> 从「人设卡/参考图」到「可玩 Godot 骨骼动画」的 6 阶段 AIGC 流水线，带**可观察、可配置、门禁、反馈闭环、成本核算**的工业级前端。

## 流水线（6 阶段）
```
S0 生图 ──► S1 拆层 ──► S2 绑骨 ──► S3 动画 ──► S4 打包 ──► S5 引擎
人设/参考图   See-through   StretchyStudio   LLM 动画导演   trimmed atlas   Godot SpinePlayer
              (1280 PSD)    DWPose + fix-rig  (方法论注入)   + manifest      (骨骼播放)
```
- **S0 生图**：GPT-Image-2 / Gemini / FAL，人设卡 persona.json → 立绘/表情/小人
- **S1 拆层**：See-through blockswap → 分层 PSD（17+ 层，1280px，含 depth）
- **S2 绑骨**：StretchyStudio DWPose 自动绑骨 → `.stretch` + Spine → **fix-rig 标准骨架修复**（去重骨/补 Warp 骨/脚部 IK）
- **S3 动画**：DeepSeek「动画导演」按工业方法论（12 原则 / walk 4 姿态 / bezier）生成 idle/walk/attack/hurt + 表情预览 → **fix-rig 循环闭合**
- **S4 打包**：trimmed atlas（按 alpha bbox 裁剪，25/25 装入 2048）+ 每部件图 + manifest
- **S5 引擎**：SpinePlayer（自包含迷你 Spine 4.0 运行时）→ 可玩 Godot 工程

## 质量门禁（每阶段自动执行）
| 门禁 | 脚本 | 检查 |
|---|---|---|
| 拆层 | `validate-layered.py` | 层完整/PSD/命名 |
| 绑骨 | `validate-rig.py` | 重复骨名/槽位骨存在/IK/权重 |
| 动画 | `validate-anim.py` | 必需 clip/循环闭合/关节幅度/缓动曲线 |

`gate_strict` 开关：开=门禁 FAIL 即任务失败；关=仅记录 `gate_*.txt` 告警。

## 反馈闭环（自进化）
门禁 FAIL → 自动沉淀 `harness/memory/pipeline/lessons-learned.md` → 下次 S3 动画任务**自动注入规避规则**到 LLM system prompt。

## 前端（10 Tab）
总览（DAG + 一键流水线 + 历史/断点续跑）· 生图 · 拆层 · 绑骨 · 动画 · 打包 · 引擎 · 资产库 · 经验库（成本+教训）· 设置（API Keys / LLM 人设填充）
- **一键流水线**：起止阶段选择 → 顺序执行 → 上游产物自动填入下游输入
- 每个节点：输入配置 / 输出说明 / 上下游 / 产物 / 日志 / 门禁，均可从前端观察与配置

## 启动
```bat
:: 1. 后端 + 前端（自动开浏览器 http://127.0.0.1:8000）
tools\workbench\start-workbench.cmd

:: 2. 绑骨/动画依赖 StretchyStudio（5173/5174）
env\runtime\tools\stretchy-studio\start-stretchy.cmd
```
Key 配置：`env/.env`（GPT/DEEPSEEK/GEMINI/TRIPO），或工作台「设置」页填写（掩码存储）。

## 目录
```
tools/workbench/          # 后端 orchestrator（app.py）+ 前端（web/，React+Vite）
tools/spine-player.gd     # 迷你 Spine 4.0 运行时（Godot）
tools/fix-rig.py          # 标准骨架修复（去重/补骨/IK/循环闭合）
tools/validate-*.py       # 拆层/绑骨/动画门禁
tools/package-assets.py   # trimmed atlas 打包
tools/export-godot.py     # Godot 工程生成
tools/rig-automation/     # StretchyStudio 自动化（绑骨/动画导演/预览）
pipeline/artifacts/       # 每 job 产物归档
harness/memory/pipeline/  # 门禁经验库（自动沉淀）
```


## 演示（2026-08-15，角色「艾琳」Q 版，含膝盖弯曲）
```
assets/demo/char_ailin_m04/
├── walk_preview_knee.gif     # 膝盖弯曲版 walk 动画（4 姿态循环）
├── walk_old_vs_new.gif       # 旧 vs 新 walk 对比（新 walk 运动量 2.4×）
├── godot_engine_demo.png     # Godot 实机 4 动画帧（idle/walk/attack/hurt）
├── char_ailin_m04_knee_spine.zip  # 完整骨架+资产（thigh/shin 拆分、脚部 IK）
└── godot/                    # 可直接打开的 Godot 工程（SpinePlayer 播放）
```
```
## 技术栈
FastAPI + SQLite（orchestrator）· React + Vite（前端）· StretchyStudio + DWPose（绑骨）· DeepSeek（动画导演）· See-through（拆层）· Godot 4.x + GDScript（引擎播放）· Spine 4.0 JSON（资产格式）
