# 开发路线：2D 线优先 + 3D 线后置（spec/dev-roadmap-2d3d.md）

> 依据：`spec/pipeline-unified-2d3d.md`（双管线统一分析）+ `assets/workflow-2d3d-unified.png`（链路图）
> 原则：2D 线先行（外部工具齐、差异化在 2D 骨骼）；3D 线后置（缺口多但可替代，非主线）
> 阶段验收：每阶段产出物 + 验收清单 + audit 记录（沿用项目 verify/audit 文化）

## 阶段总览
| 阶段 | 名称 | 主线 | 预估 | 验收一句话 |
|---|---|---|---|---|
| P1-A | 画风定稿+生图基线 | 选定主画风 → 立绘/表情/小人同画风产出 | 0.5-1 天 | 一套同画风三件套，用户确认 |
| P1-B | 2D 资产拆层 | 立绘 → 可动部件分层（Live2D 规范 PSD） | 1-2 天 | 拆出 ≥8 可动层，可导入 Spine/Live2D |
| P1-C | 2D 骨骼绑定 | Spine/Live2D + 自动绑骨 | 1-2 天 | 小人/立绘可摆姿势+表情参数 |
| P1-D | 2D 动画 | 基础动画 + AI 补帧验证 | 1-2 天 | idle/walk/attack/hurt + 表情切换可循环 |
| P1-E | 打包/引擎 | 图集 + Godot 导入 | 1 天 | Godot demo 可分层显示/播放动画 |
| P2-3D | 3D 线（后置） | 3D 生成→修正→绑骨→动作→引擎 | 3-5 天 | 一个 3D 角色资产进 Godot 可动 |

---
## P1-A 画风定稿 + 生图基线（0.5-1 天）
### 任务
- [ ] A0 **建风格标杆库 + 反馈飞轮**：`reference/style-library/<画师-系列>/`（精选 3-8 张同画师图 + manifest）；`harness/memory/style/lessons-learned.md + preferences.md`（已完成骨架，需随尝试填充）
- [ ] A1 用户选定主画风（style_attempts / compare_sheet / 风格标杆库 选一）
- [ ] A2 按约束**分离式参考**重生成基线三件套：立绘(full+bust) + 表情×4 + Q版小人
      —— `--style-ref 风格图×1-3（风格标杆库）` + `--ref 角色锚点` 分开；prompt 点名 known_names + 正向表述（约束见 spec/style-reference-constraints.md）
- [ ] A3 画风锁定决策：云 API 多参考（快） vs ComfyUI+风格 LoRA（锁死）——若 A2 达标选云 API，否则上 ComfyUI
- [ ] A4 沉淀画风 prompt 模板（固定=风格/色调/光影；可变=主体/场景）
- [ ] A5 **反馈飞轮**：审图通过→回填标杆库（manifest 标 quality:high）；不通过→记 lessons-learned（原因+规避）
### 产出物
- reference/style-library/（风格标杆库：阿米娅-唯@W 已建）
- assets/demo/char_ailin_v10/（同画风 full+bust+exp×4）
- assets/demo/char_ailin_chibi_v3/（同画风 Q 版小人）
- 画风模板（contracts/prompt-templates/）+ lessons-learned 记录
### 验收
- [ ] 立绘/表情/小人三件套画风一致且被用户确认
- [ ] 风格标杆库 ≥1 个画风系列（manifest 完整）
- [ ] 表情自检通过（脸区均差/肤色占比阈值，复用 v8 机制）
- [ ] audit：画风决策记录（云 API or ComfyUI+LoRA）+ lessons-learned 已记录

---
## P1-B 2D 资产拆层（1-2 天）
### 任务
- [ ] B1 搭拆层管线：ComfyUI-See-through 或 VTuber2D.AI 类工作流（本地 8GB 可跑 SDXL）
- [ ] B2 立绘拆层 → Live2D 规范 PSD：前发/后发/左右眼(眼皮/眼白/瞳孔分)/眉/嘴/身体/手臂/衣服
- [ ] B3 遮挡区域补全（PS 生成式 / SAM2 修补）
- [ ] B4 拆层校验脚本：层完整性/对齐/透明度/命名规范
### 产出物
- tools/split-layers.py + 拆层工作流（ComfyUI json）
- assets/demo/char_ailin_layered/（分图层 PNG + PSD）
### 验收
- [ ] 一张立绘拆出 ≥8 个可动部件层
- [ ] PSD 可被 Live2D Cubism / Spine 直接导入（图层命名/结构合规）
- [ ] Godot 可分层显示（部件独立可见）

---
## P1-C 2D 骨骼绑定（1-2 天）
### 任务
- [ ] C1 装 Spine（或 Live2D Cubism 免费版）
- [ ] C2 自动绑骨验证：UniRig（ComfyUI 工作流）或 Spine-Anim-AI（生成骨骼 JSON，SIFT+RANSAC 定位部件）
- [ ] C3 骨骼/网格/权重校验与修正（手工精修少量）
- [ ] C4 绑定小人 + 立绘（表情参数：眉/眼/嘴可动）
### 产出物
- tools/rig-workflow.md（绑骨流程沉淀）
- assets/demo/char_ailin_rigged/（Spine 工程/Live2D model + 导出资源）
### 验收
- [ ] Q版小人完成骨骼绑定，可摆姿势（手臂/腿/头）
- [ ] 立绘表情参数可动（眉毛/眼睛/嘴）
- [ ] 导出 Spine atlas 或 Live2D model3.json 可加载

---
## P1-D 2D 动画（1-2 天）
### 任务
- [ ] D1 基础动画：idle / walk / attack / hurt（Spine 关键帧 或 程序化 runtime）
- [ ] D2 表情切换动画（立绘：happy/sad/angry/neutral 参数过渡）
- [ ] D3 可选 AI 补帧验证：SCAIL2（视频动作迁移）或 2dimg2motion（序列帧）
### 产出物
- assets/demo/char_ailin_anim/（动画资源 + 播放预览）
### 验收
- [ ] 一套可循环动画（idle/walk/attack/hurt）
- [ ] 表情切换流畅（参数过渡 ≥ 0.3s）
- [ ] （可选）AI 补帧前后对比记录

---
## P1-E 打包/引擎接入（1 天）
### 任务
- [ ] E1 图集打包：Spine atlas / TexturePacker / 自研脚本
- [ ] E2 Godot 导入：分层立绘 + Spine atlas + 动画播放
- [ ] E3 交互雏形：点击/按键触发表情切换与动作（对接 P3 Agent 的入口）
### 产出物
- assets/demo/char_ailin_godot/（Godot 场景：分层立绘 + 小人动画 + 表情切换）
### 验收
- [ ] Godot demo 可显示分层立绘 + 播放小人动画 + 触发表情切换
- [ ] 资源中立（PNG/Spine atlas/JSON，引擎无关）

---
## P2-3D 线（后置，可选 3-5 天）
### 任务
- [ ] F1 3D 生成：Tripo API / 混元3D / Meshy（多视图→mesh+贴图）
- [ ] F2 修正：Blender 减面/UV/法线传递/贴图（DCC-MCP 自动化）
- [ ] F3 绑骨：Mixamo（免费）或 RigNet（开源）
- [ ] F4 动作：Mixamo 动作库 / 手K / SCAIL2 迁移
- [ ] F5 Godot 导入（GLB + 动画）
### 验收
- [ ] 一个 3D 角色资产进 Godot，可摆姿势/播放动作
- [ ] 记录生成/修正/绑骨各环节耗时与问题

---
## 横切项
- 画风 LoRA 训练（若选 ComfyUI 路线，见 spec/comfyui-lora-plan.md）
- 工作台 v2 前端重做（后续阶段，用户指定核心前端 skills）
- 每阶段结束：audit 追加 + memory 沉淀（decision/knowledge/error）

## 推进方式
一个阶段一个阶段推进，每阶段过"任务→产出→验收→audit"再进下一阶段（沿用 ROADMAP 总原则）。

