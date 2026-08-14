# 2D 骨骼动画质量：根因分析 + 工业做法 + 修复方案（spec/2d-animation-quality.md）

> 日期：2026-08-14 ｜ 触发：用户反馈"现在的动画非常烂，位置不对，图层缺漏，动作不科学"
> 依据：生图.md（网易 2D 动效=编辑器手工绑定）+ 工业 2D 动画生产流程调研（Spine/Live2D/DragonBones/spine-animation-ai）+ 本仓库产物实测
> 结论：**烂的根因不在"AI 不会动画"，而在"rig 缺 IK/权重 + 动画缺方法论 + 拆层缺门禁"**。

---

## 1. 现状产物实测：三处硬伤
对 `char_ailin_animated_spine.zip` 的 skeleton.json 实测：
| 检查项 | 结果 | 影响 |
|---|---|---|
| IK 约束（ik[]） | ❌ 无 | 脚会滑、膝盖/肘不自然弯曲 → "动作不科学" |
| 网格权重（weights[]） | ❌ 无（unweighted mesh） | 骨骼刚性旋转，弯曲处撕裂/穿模 → "动作不科学" |
| 骨骼层级 | 18 bones，无 pelvis/spine/chest 细分 | 身体只能整体转，无腰/胸联动 → 僵硬 |
| DWPose→Q版映射 | 人形关节点直接套 Q 版 | 关节位置偏 → "位置不对" |
| 拆层完整性 | chibi 17 层，legwear 拆不开、无 bottomwear | "图层缺漏" |
| 动画方法 | LLM 随机给旋转值，无关键姿态/曲线 | 动作不自然 |

---

## 2. 工业界 2D 骨骼动画到底怎么做

### 2.1 生图.md（网易）的答案
- **2D 动效（Spine/Live2D）= 编辑器手工绑定为主，无 AI 自动绑骨**（生图.md §0 结论表明确标注）
- 网易的 AI 能力集中在 3D：`ailab_auto_skin`（自动蒙皮）+ `Motion Completion`（AI 动画师，in-betweening/blending，BERT-transformer）+ `PoseCap`（视频动捕→Bip/fbx）
- 2D 侧 AI 辅助 = 生图拆部件（CHORD）→ 剩下手工绑

### 2.2 工业 Spine/Live2D/DragonBones 标准生产流程（TRUETECH/Esoteric 等）
```
① 参考与风格规范（卡通 vs 写实、动作幅度）
② 部件拆分（按骨骼切部件：头/身/上臂/前臂/手/大腿/小腿/脚…）
③ 骨骼层级 + 枢轴点（pelvis→spine→chest→neck→head；肩→上臂→前臂→手；髋→大腿→小腿→脚）
④ 网格蒙皮 + 权重（可变形部件绑定多骨骼，顶点加权）
⑤ IK 约束（脚部 ground-lock 防滑、手部定位）+ Transform/Path 约束
⑥ 关键帧动画（12 原则：anticipation/squash&stretch/follow-through/arcs…）
⑦ 图集打包（Spine atlas/TexturePacker）+ 引擎运行时（SpineComponent/Godot）
```
一个角色 10-15 个动画，专业团队 3-5 周。

### 2.3 walk cycle 关键方法（Adobe/Marionette 标准）
- **4 个关键姿态**：Contact（脚跟触地）→ Down/Recoil（承重下沉）→ Passing（重心过支撑腿）→ Up/High point（最高点）
- **髋肩反向旋转**：髋向左转时肩向右转（上半身与下半身反相）
- **脚部固定**：支撑脚不能滑（foot sliding = AI 动画第一号败笔）
- **腿走弧线**：摆动腿划弧，不是直线前后
- 16 帧/步循环（contact=1, passing=9, 等）或按时间对称

### 2.4 AI 辅助 2D 动画的正确姿势（开源/业界 2025-2026）
| 方案 | 做法 | 对本项目 |
|---|---|---|
| **spine-animation-ai**（开源 Claude skill） | SIFT+RANSAC 定位部件 → Spine JSON → **12 原则动画预设**（idle 正弦叠加/walk 对侧摆+髋 bob/attack 蓄力→挥击→跟随）+ **bezier easing [0.25,0,0.75,1]** | **最贴近的工业化参照，可直接集成** |
| SCAIL-2（清华） | 视频→角色动画，**端到端免骨骼**（含手指/重心/衣摆物理） | 动画来源可换参考视频 |
| PoseCap / 视频动捕 | 视频→Bip/fbx 标准动画 | 可选动作来源 |
| Motion Completion | in-betweening/动作补全 | 关键帧之间自动补 |

---

## 3. 修复方案（三层，对应三个硬伤）

### L1 图层修复（对应"图层缺漏"）
- [ ] B3 遮挡补全（SAM2/PS 生成式，补拆层缺口）
- [ ] 拆层完整性门禁：层数量 ≥ N、命名规范、无粘连（连通域检查）、与参考图重建误差
- [ ] 关键层补齐：Q 版必须有 bottomwear/legwear 分离、左右手/脚分离

### L2 Rig 修复（对应"位置不对/动作不科学"）
- [ ] 标准骨架模板（Q 版 + 立绘两套）：
  `root>pelvis>spine>chest>neck>head` / `shoulder>upperArm>foreArm>hand` / `hip>thigh>shin>foot`
  （替代 DWPose 平铺映射）
- [ ] 枢轴点按图层包围盒 + 模板比例校准（Q 版头身比 2:1 的关节位置）
- [ ] IK 约束：脚部 ground-lock + 膝/肘自然弯曲（Spine export 增加 ik[]）
- [ ] 网格权重：Spine 导出 weighted mesh（或降级用 region+IK，先做对姿态再做变形）
- [ ] rig 门禁：摆姿势不穿模、层齐全、枢轴在关节处

### L3 动画修复（对应"动作不科学"）
- [ ] **12 原则 + walk 4 姿态 + 髋肩反向 + 脚弧线** 注入 LLM agent 知识（stretchy-agent system prompt 升级）
- [ ] 动画预设模板（参照 spine-animation-ai）：idle/walk/attack/hurt 的 pose 序列 + **bezier easing**
- [ ] pose-to-pose 关键帧（先姿态后补帧，而非随机数值）
- [ ] 动画质量门禁：循环闭合（首尾一致）、无脚滑（支撑脚位移≈0）、关节幅度在生理范围、曲线平滑
- [ ] （可选）参考驱动：SCAIL-2 / PoseCap 视频动作作为动画来源

### L4 流程修复（工业级流水线，承接 industrial-pipeline-v2）
- [ ] 编排层 orchestrator（阶段状态机/job/断点续跑）
- [ ] 契约 schema + gate 自动执行（L1/L2/L3 的门禁全部脚本化）
- [ ] 反馈闭环：动画质量差 → 归因（图层/rig/动画哪段）→ 规则回填 → 自动规避

---

## 4. 开发路线（重新规划全部任务）

### M0 修复验证（本周，先让"一个 walk"做到能看）
| # | 任务 | 产出 | 门禁 |
|---|---|---|---|
| M0-1 | 图层修复：B3 遮挡补全 + chibi 层补齐（bottomwear/legwear 分离） | chibi 分层 PSD v2 | 层完整性脚本过 |
| M0-2 | 标准骨架模板 + 枢轴校准（Q 版模板） | rig 模板 JSON + 校准脚本 | 摆姿势不穿模 |
| M0-3 | Spine 导出扩展：IK 约束 + weighted mesh（或先 region+IK） | spine v2 导出 | ik[]/weights[] 存在 |
| M0-4 | 动画方法论重做 walk：4 姿态 + bezier + 髋肩反向 | walk GIF v2 | 无脚滑/循环闭合/幅度合理 |
| M0-5 | 人工确认 walk 效果 | 用户验收 | ✅ |

### M1 动画库重做（把 M0 方法复制到全部）
- idle/walk/attack/hurt 按方法论重做 + 表情（happy/sad/angry/neutral 参数过渡）
- 每动画 GIF 预览 + 质量门禁 + 人工确认

### M2 流水线编排（工业级，承接 v2 蓝图）
- orchestrator + contracts schema + gates（L1-L3 门禁脚本化）+ job 记录 + 断点续跑
- 一条命令：`生图→拆层→rig→动画→导出` 全自动 + 每阶段人工确认点

### M3 打包 + 引擎
- Spine atlas 打包 + Godot Spine runtime 接入 + 交互（表情/动作触发）

### M4 反馈闭环 + 成本 + 开源
- 动画质量归因 + lessons 自动回填 + 成本/耗时核算 + 发布

**原则**：先修 rig+方法论（M0-M1），再上流水线（M2），避免把"烂动画"流水线化。

---

## 5. 参照物清单（可复用）
- spine-animation-ai（GitHub GenielabsOpenSource）：SIFT+RANSAC 定位 + 12 原则动画预设 + bezier easing → **动画方法论参照**
- Esoteric Software spine-tips：IK/权重/约束最佳实践
- Adobe walk cycle 教程：4 姿态 + 髋肩反向 + 脚跟先着地
- SCAIL-2（清华，端到端视频→动画）：可选动作来源
- 生图.md §7 工具表：PoseCap/Motion Completion/2dimg2motion
