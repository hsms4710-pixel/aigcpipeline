# 2D 骨骼生成路线规划（spec/plan-2d-skeletal.md）

> 规划日期：2026-08-18 ｜ 触发：用户「规划 2D 骨骼生成路线」+ 此前挑刺式验收结论（walk 循环 6/10）
> 结论先行：**根治 AI 帧动画抖动 = A 路线（Spine 骨骼动画）**；当前 B 路线（AI 关键帧→逐帧对齐）只能做到"位置对齐"，无法消除 AI 逐帧重绘带来的轮廓/布料形变。
> 双路线定位：B 路线 = 快速产出（已跑通，可用但非专业级）；A 路线 = 工业级骨骼（五步法，根治抖动）。
> 本文是 2D 骨骼生成路线的唯一规划入口，替代/整合 plan-spine-rig-a.md（A 路线）与 dev-roadmap-2d3d.md（P1-C/P1-D 段）。

---

## 1. 现状与根因（为什么必须上骨骼）

### 1.1 已跑通（B 路线：AI 关键帧 → 帧动画）
- 艾琳侧视帧（像素 8/10、HD-2D 7.5/10 vision 验收）+ Godot AnimatedSprite2D 横板 demo
- walk 稳定性程序化指标达标：bottom 全 160、cy 漂移 <=1.3px、高度差 3px
- 但**挑刺式动画师视角验收仅 6/10**：重心微抖、脚滑、布料轮廓轻微形变

### 1.2 根因（2026-08-17/18 已定位）
- AI 逐帧重绘，帧间轮廓/布料/头发形变 → 无论怎么对齐位置，像素级形变无法消除
- 帧动画方案（B）的天花板：**位置对齐 ≠ 形变一致**，专业级 2D 游戏不用 AI 帧直接做循环动画
- 结论：**骨骼动画（A）骨骼驱动部件旋转/位移，天然无帧间形变，是根治方案**

### 1.3 工业共识（Spine/TRUETECH/Esoteric 官方）
2D 骨骼动画 = 五步法（详见 spec/pipeline-remaster-2d-skeletal.md §1.2）：
```
① 部件拆分（按关节切，关节重叠区画圆）→ ② 标准骨层级 + 真实关节枢轴
③ 网格蒙皮 + 顶点权重（合计 1.0，弯曲不撕裂）→ ④ IK 约束（脚 ground-lock / 膝肘弯曲方向）
⑤ 12 原则关键帧（pose-to-pose / squash&stretch / follow-through / arcs / bezier 缓动）
```
自动绑骨的瓶颈不在"生成骨架"，而在**枢轴落点 + 蒙皮权重**（调研见 spec/2d-skeletal-auto-research.md）。

---

## 2. 工具与方案对比（2025-2026 实测/调研）

| 方案 | 做法 | 自动程度 | 本项目结论 |
|---|---|---|---|
| **StretchyStudio**（MangoLion，FOSS，已部署） | PSD 分层 → DWPose 自动绑骨 → Live2D 参数 → Spine 4.0 导出 | 半自动 | **A 路线主引擎**（本地 env/runtime/tools/stretchy-studio/ 已部署，DWPose 模型已下载） |
| **See-Through / LayerDiff3D**（已部署） | 2.5D 分层 PSD（blockswap + Marigold depth） | 自动拆层 | A 路线前置拆层（阻塞：模型需 hf-mirror 下载） |
| spine-animation-ai（Genielabs，开源） | SIFT+RANSAC 部件定位 + 12 原则动画预设 + bezier | 动画自动 | 动画方法论参照（idle/walk/attack 预设数值可抄） |
| Spiritus（web，ACM 论文） | 语义分层 2D 角色 + ~30s 自动绑骨 + 初始动画 | 高（端到端） | 对照目标，不部署 |
| ASMR（EG 2025 论文） | 2D 先验自适应骨架-网格绑定+蒙皮权重 | 高 | **蒙皮权重 = 弯曲不撕裂关键**（我们 W1 遗留） |
| UniRig / Spine-Anim-AI / keyframe-mcp | NL 描述→自动 rig+IK+动画→Spine | 半自动 | 与 LLM 导演 agent 同思路，功能对照 |
| **PixelOver** | 像素骨骼动画 + IK（bilibili 大量教学） | 半自动 | **像素风小人专用**（B2 可选路线） |
| Retro Diffusion / SpriteForge / perfectpixel | 文本→精灵表（网格对齐/限色） | 高 | 像素风快速替代（无骨骼需求时） |

---

## 3. A 路线：Spine 骨骼动画（推荐主线，根治抖动）

### 3.1 前置资产（已完成，可复用）
- 画风锚点：char_ailin_v10 立绘 + chibi_v4 小人（透明、A-pose：transparent_v2/hero_hd2d_nobow_apose.png）
- 拆层验证：char_ailin_m04/layered/front_b.psd（17 层）+ 24 层 PNG + depth（See-Through 实测通过）
- 绑骨验证：char_ailin_m04（26 骨/2 IK/0 重复，validate-rig OK）+ chibi_apose_spine.zip（14 骨/12 slot/2 IK/真实枢轴）
- 动画验证：char_ailin_anim（4 clip + Parameters）、FK 播放器（render_fk_frames.py + spine-player.gd）
- 膝盖弯曲集成：split-spine-limb.py 切 thigh/shin + 绑定 knee 骨（27 纹理，Godot 自检 OK）

### 3.2 四个阶段（按序执行，每阶段过门禁）
```
[1] PSD 拆层（阻塞中）
    cd env/runtime/tools/see-through
    set HF_ENDPOINT=https://hf-mirror.com
    venv\Scripts\python.exe inference\scripts\inference_psd_blockswap.py ^
        --srcp assets/demo/style_batch/transparent_v2/hero_hd2d_nobow_apose.png ^
        --save_dir assets/demo/style_batch/transparent_v2/layered_hd2d --save_to_psd
    验收：>=17 层 See-Through blockswap PSD，validate-layered OK
    （阻塞：LayerDiff3D 模型下载，需 hf-mirror；首次运行 >7min）

[2] StretchyStudio 绑骨（DWPose 自动 + 人工微调）
    start-stretchy.cmd → node tools/rig-automation/rig-full.cjs <psd> <outdir> "<joint调整>"
    验收：*_spine.zip 13-18 bones + mesh + Idle/Parameters；validate-rig OK（weighted mesh 收敛 W1）

[3] 动画（LLM 导演 + 12 原则预设）
    node tools/rig-automation/stretchy-agent.cjs --load <psd> --task "idle/walk/attack/hurt" --out <dir> --max-steps 16
    参照 spine-animation-ai 预设：idle=正弦叠加 / walk=对侧摆+髋 bob / attack=蓄力→挥击→跟随
    验收：validate-anim OK（循环闭合/100% bezier）；render_bone_overlay 截图逐帧 vision 挑刺验收 >=7/10

[4] 引擎接入
    spine-godot / 2dguru 社区版加载 skeleton.json + atlas（spine-player.gd 已有 FK/膝感知基础）
    表情：Live2D 参数滑块打关键帧（happy/sad/angry/neutral）
    验收：Godot headless SETUP_OK/PARSE_OK；实机 idle/walk/attack/hurt 四帧差异 > 阈值；无撕裂
```

### 3.3 A 路线质量门禁（每个阶段强制）
| 门禁 | 工具 | 通过标准 |
|---|---|---|
| 拆层 | validate-layered.py | RESULT OK（warnings<=1） |
| 绑骨 | validate-rig.py | OK；关节枢轴落在部件内容（几何校验）；32/32 关节圆盘不透明（撕裂校验） |
| 动画 | validate-anim.py | 循环闭合、100% bezier、时长正确（秒非毫秒） |
| 视觉 | vision_review.py（gpt-5.5 挑刺模式） | 逐帧 review 无断裂/无穿模/动作可读 >=7/10 |

---

## 4. B 路线：AI 关键帧 → 帧动画（快速路径，已跑通）

- 适用：快速 demo、像素风限色场景、无骨骼预算时
- 已落地：gen-frame-cycle → align-game-frames（中心区域 55% 核心检测）→ 真像素化/HD-2D 侧视 → Godot AnimatedSprite2D
- 已知局限：帧间轮廓形变（6/10），仅"可用"
- 后续仅在 A 路线阻塞时作为兜底，不再投入打磨

---

## 5. 像素风 2D 小人路线（可选并行）

- 目标风格参考：chibi_pixel_hard / chibi_hd2d（透明背景）
- 骨骼方案：**PixelOver**（像素骨骼+IK，bilibili 教学充足）
- 快速方案（无骨骼）：Retro Diffusion / SpriteForge / perfectpixel-studio 出精灵表，LLM 视觉 gate 审动画
- 决策：若像素小人最终需求为"游戏内可动资产"，走 PixelOver 骨骼；若只是展示/占位，走精灵表快速路线

---

## 6. 任务拆解（可勾选进度）

### M0 拆层硬化（P1-B 收尾）
- [ ] M0-1 下载 LayerDiff3D（HF_ENDPOINT=hf-mirror.com）→ 跑通 blockswap PSD（阻塞项）
- [ ] M0-2 thigh/shin 膝盖弯曲完整集成（split-spine-limb.py 已就绪，待接入 A 路线新 PSD）
- [ ] M0-3 weighted mesh 蒙皮权重（ASMR 思路：同缝顶点同权重；收敛 validate-rig W1）

### M1 绑骨硬化（P1-C 收尾）
- [ ] M1-1 StretchyStudio 全自动绑骨（rig-full.cjs）在 A 路线新 PSD 上跑通
- [ ] M1-2 关节枢轴几何校验自动化（肩/肘/膝/踝落在部件内容）
- [ ] M1-3 立绘表情参数可动（眉/眼/嘴）

### M2 动画（P1-D 收尾）
- [ ] M2-1 12 原则预设（参照 spine-animation-ai）：idle/walk/attack/hurt 4 循环
- [ ] M2-2 表情切换（happy/sad/angry/neutral 参数过渡 >=0.3s）
- [ ] M2-3 全动画 vision 挑刺验收 >=7/10

### M3 引擎接入（P1-E 收尾）
- [ ] M3-1 Spine runtime 接入 Godot（spine-player.gd 扩展，支持新骨架）
- [ ] M3-2 横板 demo 切换骨骼动画角色（替换帧动画）
- [ ] M3-3 交互（按键触发表情/动作，对接 P3 Agent 入口）

### 进度快照（2026-08-18）
- ✅ B 路线全通；A 路线 [1] 拆层阻塞（hf-mirror）；[2] 绑骨已在小样本验证（char_ailin_m04/chibi_apose）
- ⚠️ 生图中转站 api.sisct2.xyz 间歇故障影响重生成/视觉验收
- ⏭ 待办优先级：M0-1（解除阻塞）→ M1 → M2 → M3

---

## 7. 风险与对策

| 风险 | 对策 |
|---|---|
| LayerDiff3D 下载慢/中断 | HF_ENDPOINT=hf-mirror.com；分步下载；必要时先下模型再离线 |
| 8GB VRAM blockswap 慢 | 已是 blockswap 模式；接受 ~10-20min/张 |
| DWPose 对 chibi 大关节不敏感 | rig-full.cjs 关节微调参数（如 leftElbow:+14,+6）；LLM agent 迭代 |
| Spine 动画"动作不科学" | stretchy-agent.cjs（DeepSeek 导演）+ 12 原则预设 + vision 挑刺验收 |
| 蒙皮权重未收敛 | M0-3 独立任务；先刚性腿满足 demo，再上权重 |
| 生图端点故障 | 本地重试 + 缓存产物；vision 验收可等端点恢复后补跑 |

---

## 8. 决策记录
- 2026-08-17：用户选择"先 B 帧动画看效果，再规划 A" → 本文档是 B 验收后的 A 路线正式规划
- 2026-08-18：挑刺验收 6/10 → 确认 A 路线（Spine）为根治方案；B 路线降级为兜底
- 像素小人：以 chibi_pixel_hard / chibi_hd2d 为锚点；骨骼走 PixelOver，展示走精灵表

## 9. 关联文档
- spec/pipeline-remaster-2d-skeletal.md（五步法权威基线）
- spec/2d-skeletal-auto-research.md（自动绑骨 + 像素小人调研）
- spec/plan-spine-rig-a.md（A 路线前身，被本文档 §3 整合）
- spec/dev-roadmap-2d3d.md（P1-B/C/D/E 阶段任务）
- spec/arm-animation-quality-fix.md / 2d-animation-quality.md（手臂/动画质量修复）