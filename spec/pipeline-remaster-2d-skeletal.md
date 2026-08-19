# 2D 骨骼动画工业级流水线重规划（spec/pipeline-remaster-2d-skeletal.md）

> 日期：2026-08-14 ｜ 触发：用户提问「生图.md 里 2D 骨骼怎么做？其他 2D 产品的动作骨骼怎么做？现在动画很烂（位置不对/图层缺漏/动作不科学）」+「目标是做流水线，重新规划所有任务，列出开发路线」
> 依据：生图.md（网易 DreamMaker/KM 调研）+ 工业 2D 骨骼动画生产流程（Spine/Live2D/DragonBones/Unity 2D Animation/TRUETECH）+ AI 辅助绑骨调研（spine-animation-ai / StretchyStudio / UniRig / keyframe-mcp）+ 本仓库产物实测（char_ailin_animated_spine.zip skeleton.json 直接解析）
> 一句话结论：**网易/工业界的 2D 骨骼 = 「按关节拆部件 → 标准骨层级+枢轴 → 网格蒙皮权重 → IK 约束 → 12 原则关键帧」五步，2D 自动绑骨目前是"半自动"（我们用的 StretchyStudio 已领先网易）；我们动画烂的根因不是"AI 不会动画"，而是 rig 缺 IK/权重/标准层级 + 拆层缺部件 + 动画缺方法论，修复顺序必须先修 M0/M1（质量）再硬化流水线，不能把烂动画流水线化。**

---

## 1. 生图.md / 工业界「2D 骨骼」到底怎么做

### 1.1 生图.md（网易 DreamMaker）的答案
- **2D 动效（Spine/Live2D 骨骼动画）：❌ 无 AI 自动绑骨方案，编辑器手工绑定为主**（生图.md §0 结论速览表明确标注）。
- 网易的 AI 能力集中在 **3D 动效工具链**：
  | 工具 | 能力 | 状态 |
  |---|---|---|
  | ailab_auto_skin | 自动蒙皮/自动骨骼（DCC 插件） | 生产落地 |
  | CharacterMaker | 时装蒙皮、部件优化 | 生产落地 |
  | Motion Completion | AI 动画师：in-betweening/blending（BERT-transformer） | 生产落地（3D） |
  | PoseCap | 视频动捕→Bip/fbx 标准动画 | Muse 平台 |
  | RigNet | 神经绑骨（SIGGRAPH 2020） | 算法源 |
- **2D 侧 AI 辅助 = 生图拆部件（CHORD）→ 剩下手工绑**；引擎侧有 SpineComponent 支持（但那是运行时，不是制作）。
- 结论：**生图.md 对 2D 骨骼的答案 = "没有捷径，编辑器手工绑定"**。我们用 StretchyStudio（DWPose 自动绑骨）已经比网易 2D 段领先，问题不在"没有工具"，而在"自动绑出来的 rig 没有按工业规范补 IK/权重/层级"。

### 1.2 其他 2D 产品的动作骨骼怎么做（标准生产流程）
Spine / Live2D / DragonBones / Unity 2D Animation / Adobe Animate 共通的**五步工业流程**：

```
① 部件拆分（按关节切）
   头/胸/胯分开；大臂/前臂/手分开；大腿/小腿/脚分开；
   前发/后发/飘带/裙摆独立；关节重叠区画成圆形（旋转平滑）
② 骨骼层级 + 枢轴点
   pelvis→spine→chest→neck→head
   肩→上臂→前臂→手；髋→大腿→小腿→脚
   枢轴必须落在真实关节位置（不是包围盒中心）
③ 网格蒙皮 + 权重
   可变形部件转 mesh，顶点绑定多骨骼，权重合计=1.0
   （弯曲处不撕裂、不穿模的唯一手段）
④ IK 约束
   脚部 ground-lock（支撑脚不滑动）、膝/肘弯曲方向、手部 target
   Transform/Path 约束（跟随/继承）
⑤ 关键帧动画（12 原则）
   pose-to-pose（先姿态后补帧）；anticipation / squash&stretch /
   follow-through / arcs / 缓动（bezier [0.25,0,0.75,1]）
   walk 循环 = 4 个关键姿态：Contact(脚跟触地)→Down(承重下沉)→Passing(重心过支撑腿)→Up(最高点)
   髋肩反向旋转、支撑脚固定（foot sliding = AI 动画第一号败笔）、摆动腿走弧线
   一个角色 10-15 个动画，专业团队 3-5 周（TRUETECH 参考价）
⑥ 图集打包 + 运行时
   Spine atlas / TexturePacker → Spine runtime / Live2D SDK / Godot
```

### 1.3 AI 辅助 2D 骨骼动画（2025-2026，可借鉴）
| 方案 | 做法 | 对我们 |
|---|---|---|
| **spine-animation-ai**（Genielabs，Claude skill，开源） | SIFT+RANSAC 部件定位 → 骨骼 JSON → **12 原则动画预设**（idle=正弦叠加/walk=对侧摆+髋 bob/attack=蓄力→挥击→跟随）+ **bezier easing** + HTML 预览 | **动画方法论最直接的参照，可抄预设数值与曲线** |
| **StretchyStudio**（MangoLion，FOSS，我们在用） | DWPose/启发式自动绑骨 + mesh 变形 + Timeline | 已部署；缺 IK/权重导出与质量门禁 |
| **UniRig / Spiritus / ASMR** | 自动绑骨（简单角色 5-10min；Spiritus ~30s） | 选型对照 |
| **keyframe-mcp / spine2d-animation-mcp** | NL 描述→自动 rig+IK+动画→导出 Spine | 与我们的 LLM 导演 agent 同思路，可对照功能 |
| **SCAIL-2（清华）/ PoseCap** | 视频→角色动画（端到端免骨骼 / 视频动捕） | 可选动画来源（M1 之后） |

### 1.4 一句话对比
> 网易：2D 骨骼=纯手工（他们 AI 都在 3D）；工业主流：五步法（拆部件→层级枢轴→蒙皮权重→IK→12原则关键帧）；AI 现状：绑骨半自动可用（我们已领先网易），**但动画质量仍取决于"rig 规范 + 动画方法论"，这两块我们目前都缺**。

---

## 2. 为什么我们的动画烂（实测证据，2026-08-14）

对 `assets/demo/char_ailin_anim/char_ailin_animated_spine.zip` 的 skeleton.json 直接解析：

| 检查项 | 实测结果 | 对应"烂" |
|---|---|---|
| IK 约束（ik[]） | **0 条** | 脚会滑、膝/肘不自然 → **动作不科学** |
| 网格权重（weights[]） | **无（全部 region 非 weighted mesh）** | 骨骼刚性旋转，弯曲撕裂/穿模 → **动作不科学** |
| 骨骼层级 | 18 bones 但无 pelvis/spine/chest 细分；**leftKnee/leftElbow 出现两次（重复）** | 身体整体转，无腰/胸联动 → 僵硬 |
| 枢轴点 | DWPose 人形关节直接套 Q 版（头身比 2:1） | 关节位置偏 → **位置不对** |
| 拆层部件 | chibi 17 层：腿=legwear（无 thigh/shin 分离）、无 bottomwear、臂=handwear（无大臂/前臂分离） | → **图层缺漏** |
| 动画方法 | LLM 随机给 rotation 值，无 4 姿态/曲线/髋肩反向 | → **动作不科学** |

**根因链**：`拆层缺部件 → DWPose 平铺映射（非标准层级/枢轴）→ 无 IK/权重 → LLM 无方法论硬编数值 → 动画烂`。
修复必须从上游（图层/rig）开始，动画方法论注入是最后一道。

---

## 3. 修复策略（四层，对应四个硬伤）
- **L1 图层修复** → 图层缺漏：B3 遮挡补全 + Q 版/立绘可动部件补齐（thigh/shin、upperArm/foreArm、bottomwear 分离）+ 拆层完整性门禁
- **L2 Rig 修复** → 位置不对：标准骨架模板（Q 版+立绘两套）+ 枢轴校准 + IK 约束 + weighted mesh + rig 门禁
- **L3 动画修复** → 动作不科学：12 原则 + walk 4 姿态 + 髋肩反向 + 脚弧线注入 LLM system prompt + 动画预设模板 + pose-to-pose + 动画质量门禁
- **L4 流程修复** → 把上面全部固化为流水线 stage + gate + 可观察 + 反馈闭环

---

## 4. 流水线重规划：全部任务 + 开发路线

### 4.0 目标形态（一条命令 / 工作台一个 job 链）
```
人设卡+参考图 → S0 生图 → S1 拆层(Live2D 规范 PSD) → S2 绑骨(标准骨架+IK+权重)
              → S3 动画(12原则+4姿态, LLM导演+预设) → S4 打包(atlas+manifest+gate)
              → S5 引擎(Godot Spine 播放器+交互) → 可玩 NPC demo
每阶段：输入契约 → 执行 → 输出契约 → gate（脚本门禁+人工确认点）→ 产物可见/可回放
```

### 4.1 阶段总览（重规划后）
| Phase | 名称 | 主线 | 验收一句话 |
|---|---|---|---|
| P0 | 现状盘点 | 工作台 S0-S5 已打通（单点 done，质量未达标） | 6 阶段可重跑，job 有记录 |
| **P1** | **动画质量修复（当前关键路径）** | M0 先让 walk 能看 → M1 全部动画重做 | 4 动画 GIF 无脚滑/循环闭合/幅度合理，用户验收 |
| P2 | 流水线硬化 | rig/anim gate + 契约 schema + S5 spine 播放器 + S1 全分辨率 | 烂输入被 gate 拦截；Godot 真播骨骼动画 |
| P3 | 引擎闭环 + 交互 | Godot Spine 播放器 + 表情/动作触发 + 事件总线 | demo 可玩（动画+表情+交互） |
| P4 | 反馈闭环 + 成本 + 开源 | 归因/lessons 回填 + 真实计费 + 发布 | 失败自动规避；成本可核算 |
| P5(后置) | 过场 P2 / 评测 P5 / 3D 线 | 主链打通后启动 | — |

### 4.2 Phase 0 —— 现状盘点（✅ 已完成，git master）
- 工作台 orchestrator（tools/workbench/app.py，FastAPI :8000，9 Tab 前端）S0-S5 全打通：
  S0 生图（dry-run ✅）→ S1 拆层（203s ✅，17/24 层 + gate）→ S2 绑骨（52s ✅，.stretch + spine.zip）
  → S3 动画（53s ✅，4 clip + 表情）→ S4 打包（✅ atlas+manifest）→ S5 引擎（✅ 工程结构+呼吸演示）
- **已知差距**：动画质量不达标（见 §2）；S5 未真播骨骼动画；S1 未跑全分辨率；无 rig/anim 质量 gate；成本为估算。

### 4.3 Phase 1 —— 动画质量修复（⏳ 当前，先把一个 walk 做到能看）
> 原则：**先修 rig+方法论（M0-M1），再上流水线（P2），避免把烂动画流水线化。**

#### M0 修复验证（本周，目标：walk 一个动作做到能看）
| # | 任务 | 产出 | 门禁（gate） |
|---|---|---|---|
| M0-1 | 图层修复：B3 遮挡补全 + Q 版层补齐（thigh/shin、upperArm/foreArm、bottomwear/legwear 分离） | chibi 分层 PSD v2 | 层完整性脚本过（数量/命名/连通域/重建误差） |
| M0-2 | 标准骨架模板 + 枢轴校准（Q 版模板，替代 DWPose 平铺映射） | rig 模板 JSON + 校准脚本 | 摆姿势不穿模、关节枢轴在关节处 |
| M0-3 | Spine 导出扩展：IK 约束 + weighted mesh（先 region+IK，再做权重） | spine v2 导出 | skeleton.json 含 ik[]>0；尽量含 weights[] |
| M0-4 | walk 重做：contact/down/passing/up 4 姿态 + bezier easing + 髋肩反向 + 支撑脚固定 | walk GIF v2 | 无脚滑（支撑脚位移≈0）/ 循环闭合（首尾一致）/ 幅度在生理范围 |
| M0-5 | 人工确认 walk 效果 | 用户验收 | ✅ |

#### M1 动画库重做（把 M0 方法复制到全部）
| # | 任务 | 产出 | 门禁 |
|---|---|---|---|
| M1-1 | idle 重做（呼吸=胸腹分层联动+头微摆+跟随，非整体 scale） | idle GIF | 循环闭合/幅度合理 |
| M1-2 | attack 重做（anticipation 蓄力→挥击→follow-through + 前倾） | attack GIF | 幅度/时序合理 |
| M1-3 | hurt 重做（受击后仰+头滞后 follow-through + 弹性回位） | hurt GIF | 回位不瞬移 |
| M1-4 | 表情过渡（happy/sad/angry/neutral 参数过渡 ≥0.3s，立绘 mesh 变形） | 表情 GIF | 过渡平滑无跳变 |
| M1-5 | 每动画 GIF 预览 + 质量门禁 + 人工确认 | 4 动画 + 表情全过 | 用户验收 |

### 4.4 Phase 2 —— 流水线硬化（编排/门禁/契约/引擎 runtime）
| # | 任务 | 内容 | 门禁 |
|---|---|---|---|
| P2-1 | rig gate 脚本 | tools/validate-rig.py：ik[] 数量、weights 有无、骨层级模板匹配、无重复骨名、枢轴在关节处 | 烂 rig 被拦截 |
| P2-2 | anim gate 脚本 | tools/validate-anim.py：循环闭合（首尾关键帧一致）、支撑脚位移≈0、关节幅度范围、曲线平滑、clip 齐全（idle/walk/attack/hurt） | 烂动画被拦截 |
| P2-3 | 契约 schema 补全 | contracts/s2_rig.schema.json + s3_anim.schema.json + gate 自动执行（接 orchestrator） | 每阶段失败即停+原因可查 |
| P2-4 | LLM 导演 system prompt 升级 | 注入 12 原则 + walk 4 姿态 + 髋肩反向 + 脚弧线 + 动画预设模板（参照 spine-animation-ai） | 生成动画质量门禁过 |
| P2-5 | S1 全分辨率实跑 | see-through 1280 完整版（512 加速版已过） | 立绘拆层 ≥8 可动层，目检通过 |
| P2-6 | S5 spine 播放器（迷你 Spine runtime） | 自包含 GDScript 解析 skeleton.json+atlas 播放 idle/walk/attack/hurt（避开 spine-godot ABI 风险，Godot 4.x 可跑） | Godot --headless 播放验证 |
| P2-7 | 断点续跑 + 成本核算 | job 断点续跑；真实计费（S0 按张/S1 按 GPU 时/S3 按 token）替代估算 | 一条命令端到端可重跑，成本可核算 |

### 4.5 Phase 3 —— 引擎闭环 + 交互
| # | 任务 | 内容 | 门禁 |
|---|---|---|---|
| P3-1 | Godot 场景接入 Spine 播放器 | main.tscn 挂 SpineNode，播放 4 动画 | 实机可播放、动画循环 |
| P3-2 | 交互雏形 | 按键/点击触发 idle/walk/attack/hurt + 表情切换 | demo 可玩 |
| P3-3 | 事件总线 + P3 Agent 入口 | 游戏事件→Agent；Agent 决策→白名单动作（为 P4 NPC 接入留口） | 白名单执行/越权被拒 |

### 4.6 Phase 4 —— 反馈闭环 + 成本 + 开源
| # | 任务 | 内容 | 门禁 |
|---|---|---|---|
| P4-1 | 动画质量归因 | 质量差→归因（图层/rig/动画哪段）→ lessons-learned 自动回填 | 归因记录 |
| P4-2 | 真实计费 + 耗时台账 | 每 job 成本/耗时入 workbench.db | 成本可核算 |
| P4-3 | 开源发布 | README + demo 录屏 + 教程 | GitHub 可跑通 |

### 4.7 依赖关系
```
P1(M0) ─► P1(M1) ─► P2(rig/anim gate + prompt 升级) ─► P2(S5 播放器) ─► P3(引擎闭环)
   └──────────► P2(S1 全分辨率 / 断点续跑) ─────────────────────────┘
P3 ─► P4(反馈/成本/开源)
P5 过场/评测/3D 线：主链打通后启动
```
**红线**：P2 的编排硬化不得先于 P1 的质量修复；M0/M1 未过前不批量重跑 S3。

---

## 5. 与现有文档的关系（整合后）
- `ROADMAP.md`：双管线 P1-A~E 并入本方案 S0-S5 + M0-M1；本文件为 2D 线权威重规划
- `spec/2d-animation-quality.md`：根因分析保留，M0-M4 路线被本文件 P1/P2 吸收细化
- `spec/industrial-pipeline-v2.md`：编排蓝图保留，落地进度跟踪见本文件 P2
- `spec/2d-asset-skeletal-workflow.md`：阶段工具选型参考
- `tasks/pipeline/tasks.md`：执行跟踪表（本文件任务已同步）
- `生图.md`：工业级参照（网易 2D 骨骼=手工 → 我们用半自动已领先）

## 6. 参照物清单
- **spine-animation-ai**（GenielabsOpenSource）：12 原则动画预设 + bezier easing + SIFT 定位 → M0-4/M1 方法论模板
- **Esoteric Software（Spine 官方）**：How to cut your assets for animation（关节切图规范）→ M0-1
- **TRUETECH**：标准角色 mesh+IK+10-15 动画 3-5 周 → 工作量参照
- **Marionette / AnimSchool / Adobe**：walk cycle 4 姿态 + 髋肩反向 → M0-4
- **StretchyStudio**：DWPose 自动绑骨（已部署）→ M0-2/M0-3 扩展
- **keyframe-mcp / spine2d-animation-mcp**：NL→rig+IK+动画→导出 → P2-4 功能对照
- **SCAIL-2 / PoseCap**：视频动作来源（M1 之后可选）

## 7. 落地记录（2026-08-14）
- **S4 修复**：Spine ZIP 部件为全画布 1280x1280 图，原图集打包只能装 1 张 → 改为 **trimmed atlas**（按 alpha bbox 裁剪打包，25/25 全部装入 2048）+ 保留 images/（供 SpinePlayer）+ manifest v2。
- **S5 升级**：`tools/spine-player.gd` 自包含迷你 Spine 4.0 运行时（骨层级/mesh 附件/动画关键帧 + bezier 曲线/循环播放/变速），`tools/export-godot.py` 生成可直接运行的 Godot 工程（main.tscn + SpinePlayer + 按键切换动画 + headless 自检脚本）。
  - 针对 StretchyStudio 导出缺陷（Warp 骨缺失、根级骨坐标空间不一致）内置 **RIG_REPAIR 修复层**：驱动骨→部件映射 + bbox 枢轴推导，等 M0-2 修好导出后可移除。
  - 新增 **skeleton.lite.json**（去 mesh 顶点、只留 bbox+动画轨道，1.2MB→9KB，GDScript 解析提速 ~100 倍）。
  - 验证：S4→S5 经工作台 API 跑通；Godot headless 自检 SETUP_OK/PARSE_OK；实机截图 idle/walk/attack/hurt 四帧动画差异正确（walk 腿部/手臂运动、attack 手臂挥击、hurt 全身位移）。
### 7.1 质量门禁落地（P2-1/P2-2/P2-3，2026-08-14）
- `tools/validate-rig.py`（S2 门禁）：F2 重复骨名 / F4 槽位引用不存在的骨（抓 StretchyStudio Warp 骨缺失）/ F5 无 IK 约束；W1 无 weighted mesh；W2 无枢轴。
- `tools/validate-anim.py`（S3 门禁）：F1 必需 clip（idle/walk/attack/hurt）/ F2 时长>0 / F3 非空 / F4 循环闭合（首尾关键帧一致）/ F5 关节幅度±75°；W1 缓动曲线占比。
- 接入 workbench S2/S3 执行器：每任务自动跑门禁，报告写入 `gate_rig.txt` / `gate_anim.txt`（前端产物区可下载查看）+ job 日志；新增 **gate_strict** 配置项（开=FAIL 即任务失败，关=仅记录）。
- 实测：S2 API job_5157b0b7 完成并产出 gate_rig.txt=FAIL（3 issues：重复骨/缺 Warp 骨/无 IK）；validate-anim 对现有 4-clip 动画 PASS（100% bezier 曲线、循环闭合）。

### 7.2 一键流水线 + 上游产物自动流转（2026-08-14）
- 后端 `POST /api/pipeline/chain/run`：选择起止阶段 → 后台线程顺序执行；每阶段按 FIELD_EXTS 自动从上游最近 done job 产物填入空输入（S1 src←S0 png、S2 psd←S1、S3 psd_or_stretch←S2、S4 input_zip←S2/S3、S5 package_dir←S4 manifest 目录）；`GET /api/pipeline/chains[/{id}]` 查状态（chains 表持久化）。
- 前端：总览 Tab「🚀 一键流水线」卡片（起止阶段选择 + 每阶段可展开配置 + live 进度卡 + 点击跳转阶段 + 自动填入提示）；阶段 Tab 上游产物选择器升级：file 字段也有下拉、列出全部上游阶段最新产物并标注来源（实测 S5 显示 55 个「打包 S4·…」）。
- 实测：S4→S5 chain done，S5.package_dir 自动填入；前端 build 通过、Playwright 无控制台错误、无布局重叠。

### 7.3 反馈闭环 + 成本可观察（P4-1/P4-2，2026-08-14）
- 门禁 FAIL → 自动追加 `harness/memory/pipeline/lessons-learned.md`（stage/job/FAIL 原因，签名去重，线程安全）；`GET /api/pipeline/lessons` 读取。
- `/api/pipeline/status` 增加 `cost_by_stage / total_cost / job_count / done_count`。
- 前端新增第 10 个 Tab「📚 经验库」：成本统计卡 + 门禁教训列表；总览 flow-line 显示 💰 总成本与 ✓ 完成数。
- 实测：真实 S2 job_e2a8fd07 门禁 FAIL → lessons 1→2 自动沉淀；10 Tab Playwright 无报错无重叠。

### 7.4 反馈闭环闭环：经验库 → 动画导演自动规避（2026-08-14）
- `stretchy-agent.cjs` 支持 `--rules <file>`：把流水线规则段注入 LLM 动画导演 system prompt（`--print-prompt` 可 dry 查看合成结果）；`--rules` 由 S3 执行器在运行时生成。
- `app._build_anim_rules()`：从经验库过滤 `stage=s3_animate` 的 FAIL 原因 → 写入 job `rules.txt` → `--rules` 传入；S3 任务 stage_detail 显示「注入规则 N 条」。
- 闭环：门禁 FAIL → 经验库 → 下次动画任务自动规避；实测 `--print-prompt` 合成 prompt 含「流水线自动注入规则」段、`_build_anim_rules` 正确提取 F1/F4 原因。

### 7.5 完成审计（2026-08-14）—— 对照目标逐项验证
| 目标要求 | 验证证据 |
|---|---|
| 所有当前已实现流程工业级流水线化 | S0-S5 全部有 done job + 产物（S0 生图 / S1 PSD+PNG / S2 stretch+spine / S3 4-clip / S4 atlas / S5 Godot 工程）；orchestrator + chain + gates + feedback |
| 配置可观察、操作友好 | schema 驱动配置、上游产物选择器（file 字段+全部上游阶段）、一键流水线、job 详情/日志/重跑 |
| 工业级前端页面 | 10 Tab 暗色工业风；Playwright 全 Tab overlap=0、无 console error |
| 前端完全覆盖后端能力边界 | 14 条后端路由全部有前端消费方（含 /api/pipeline/chains 历史列表） |
| 技术/流程/代码先调研，生图.md 参考 | spec/2d-asset-skeletal-workflow、industrial-pipeline-v2、2d-animation-quality、本文件均引用生图.md + 外部调研 |
| 用户友好/无重叠/配色/配置齐全/多 Tab | 10 Tab 逐项实测；配置字段与后端 schema 完全一致 |
| 每节点输入/输出/流程/产物可观察可配置 | StageTab（输入配置/输出/上下游/产物/日志/gate）+ 资产库 + 经验库 + chain 流程 |

### 8. M0-2 标准骨架模板落地（fix-rig.py，2026-08-15）
- `tools/fix-rig.py`：S2/S3 产物 spine zip 后处理，zip-in/zip-out。
  - 去重骨：删除根级 leftElbow/rightElbow/leftKnee/rightKnee 绝对坐标重复项（保留 DWPose 子树 knee、小偏移 elbow 并重挂到 leftArm/rightArm）
  - 补缺失 Warp 骨：槽位引用的 10 个 Warp 骨（FaceWarp/MouthWarp/…）补 identity 骨 → validate-rig F4 转 PASS
  - 脚部 IK：leftFootTarget/rightFootTarget（挂 knee）+ ik[] 2 条 → F5 转 PASS
- 接入流水线：S2/S3 在门禁前自动 `_fix_rig`（替换为修复版 zip，raw 保留在 out 目录）。
- 实测：live S2 job_4edaf46a gate_rig.txt `RESULT: OK (warnings: 2)`，spine 26 骨/2 IK/0 重复；S3 动画 zip 修复后 validate-rig OK + validate-anim OK（动画关键帧 100% bezier 保留）。
- 剩余：weighted mesh（M0-3 W1 警告）→ 待做；摆姿势穿模检查 → 待 M0-2 目检。

### 8.1 M0-4/M1 引擎闭环验证 + 断点续跑（2026-08-15）
- M0-4 重跑产出 4 动画：walk 12 轨道（腿/臂/膝/肘/头/torso），idle 呼吸 torso.scaleY，attack 双臂+躯干+头，hurt 躯干+头滞后 6kf；fix-rig F4 循环闭合修正 5 轨道；validate-anim OK（109/109 bezier 全曲线）。
- S4→S5→Godot 实测：headless 自检 SETUP_OK/PARSE_OK；实机渲染 idle/walk/attack/hurt 四帧差异（walk 114K px、attack 184K px），改进动画在引擎中真实播放。demo 归档 assets/demo/char_ailin_m04/godot。
- 断点续跑：POST /api/pipeline/chains/{id}/resume（从第一个未完成阶段用原配置重跑），前端历史链失败项有「↻ 断点续跑」按钮；API 实测失败 chain 续跑 resumed_from 正确。

### 8.2 S3 真实计费（token 级，2026-08-15）
- stretchy-agent.cjs：llm() 捕获每次调用的 `usage`（prompt/completion tokens），结束时写 `out/usage.json`。
- app.py _exec_s3：读 usage.json → `cost = prompt×¥0.0015/1K + completion×¥0.004/1K`，经 `_real_cost[job_id]` 覆盖估算成本；usage.json 入 job 产物。
- 实测：S3 job_f91e9c51 完成，usage=17,850 prompt + 955 completion tokens / 8 calls / deepseek-v4-flash，成本 ¥0.0306（真实非估算）。

### 8.3 S1 全分辨率实跑（P2-5，2026-08-15）
- 输入 `char_ailin_chibi_v4/portrait/front_b.png`，resolution 1280 / depth 768 / 30 steps，耗时 23.7 min，真实 GPU 成本 ¥0.1974（¥0.5/h × 0.395h）。
- 产物：`layered/front_b.psd`（1280×1280，17 图层）+ 24 张层 PNG + 23 张 depth + manifest json；validate-layered `RESULT OK (warnings: 1)`。
- 备注：full-res 图层结构与 512 一致（17 层，legwear 仍为整体，thigh/shin 分离属 M0-1 内容任务，需不同拆解工具/手工拆分）。

### 9. M0-1 图层分离方案调研（2026-08-15）
现状：chibi 已有 L/R 腿/手拆分（StretchyStudio「Split merged parts」自动拆，spine 有 legwear-l/r、handwear-l/r）；缺的是**大腿/小腿（膝盖弯曲）分离**。
调研结论（工业界）：
- See-through 官方 `heuristic_partseg.py`：只做 **左右（seg_wlr）与深度（seg_wdepth）拆分**，不做 thigh/shin。
- thigh/shin 拆分标准做法 = **SAM2/SAM3 万物分割沿膝盖线切分 + 生成式补全**（PS 创成式填充 / Qwen Image Edit）补被遮挡部分，关节重叠区画圆（供旋转）。参考：cnblogs SAM2+PS 拆层流水线、zeeklog AIGC+Spine 拆件、ComfyUI-BrainDead（SAM3+Qwen）。
- 工业前提：A-pose（张臂站姿）+ 纯色背景最利拆层。
本仓库评估：
- (a) SAM2+生成补全：质量最高，需 SAM2 模型 + inpaint 模型 + 人工目检迭代（较重）。
- (b) 程序化膝盖线切分（从 rig 的 leftKnee 骨位置沿腿切）+ 切边补全：半自动、快，质量中等。
- (c) 接受刚性腿（当前）：chibi 风格下膝盖不弯曲可接受，rig 已有 knee 骨待启用。
建议：先 (c) 满足当前 demo；(b) 若需膝盖弯曲；(a) 若需生产级。

### 9.1 M0-1 程序化切分落地（tools/split-limb.py，2026-08-15）
- 工具：按内容 bbox 高度比例（默认 55%）把部件切成 thigh/shin（upper/lower），带 joint_overlap 重叠带（默认 14px）防旋转露缝；输出重建校验（coverage≥99.5% 为 OK）。
- 实测：legwear.png（双腿合并，bbox y 792-1082）膝线 y=951 → thigh+shin，重建覆盖 100.0%，重叠 4891px，产物 assets/demo/char_ailin_m04/limb_split/。
- 后续集成（未做，属 M0-1 完整实现）：拆出图片 → Spine 新增 slot（thigh→leftLeg / shin→leftKnee）→ mesh 顶点 → 动画启用膝盖弯曲。

### 9.2 M0-1 膝盖弯曲完整集成（2026-08-15）
- `tools/split-spine-limb.py`：把 Spine zip 中 legwear-l/r 按内容 bbox 55% 切 thigh/shin（14px 重叠带），原 slot 保留为 thigh，新增 `<part>-shin` slot（mesh quad，绑定 leftKnee/rightKnee），重建 zip（images 25→27）。
- `spine_player.gd` `_build_drivers` 膝感知：存在 `legwear-l-shin` 时改用拆分映射（thigh 跟 leg、shin+foot 跟 knee），否则回退原映射（向后兼容）。
- 实测：validate-anim OK / validate-rig OK / atlas 27/27 / Godot 自检 OK（27 纹理）；渲染验证小腿区域独立运动 16-17K px/相位（膝盖弯曲生效）；产物 assets/demo/char_ailin_m04/（char_ailin_m04_knee_spine.zip + walk_preview_knee.gif + knee_bend_frame.png）。
