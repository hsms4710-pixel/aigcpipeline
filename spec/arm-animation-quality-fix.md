# 手臂/攻击动画质量：根因 + 业界做法 + 修复方案（spec/arm-animation-quality-fix.md）

> 日期：2026-08-15 ｜ 触发：用户反馈 M0-5 动画不达标 ——
> ① 手/胳膊骨骼绑定有问题；② 攻击动画与绑定也有问题；③ 手臂挥动时与身体出现断裂。
> 依据：`m04_limb_spine.zip` skeleton.json 实测 + Spine 官方 / TRUETECH / Esoteric forum / spine-animation-ai 等业界资料 + 本仓库已有工具链。

---

## 0. 结论速览

| 用户反馈 | 实测根因 | 业界方案 | 本仓库落地 |
|---|---|---|---|
| ① 手/胳膊绑定有问题 | 手臂只有 `handwear-l/r` **单一刚性部件**，无上臂/前臂拆分；`leftElbow/rightElbow` 骨存在但**无任何槽位挂载**（成了死骨） | 按关节拆分部件：**肩→上臂→前臂→手**；每段独立骨骼、枢轴落在真实关节 | 复制腿部已验证的拆分模式：`split-spine-arm.py` 把 handwear 拆 upper+forearm，forearm 挂 `leftElbow/rightElbow` |
| ② 攻击动画与绑定有问题 | attack 只有 `rightArm` 单链 0→50°→-60°→-10°，整臂刚性大摆、**无肘部弯曲**、无「蓄力→挥击→跟随」节奏 | 三段式攻击（anticipation→strike→follow-through）+ **前臂驱动挥击** + 弧线/bezier 缓动 | 升级 `stretchy-agent.cjs` 的 attack 方法论：右臂=大臂小幅定位 + **rightElbow 承担挥击主幅度** |
| ③ 手臂挥动与身体断裂 | 枢轴在身体内（位置对），但**单刚性部件大角度旋转 + 关节重叠不足 + 手臂被遮挡部分未补全** → 旋转时根部与身体错位/露空 | ① 关节处**画圆收尾 + 重叠覆盖带**；② 枢轴=**真实肩关节**；③ 手臂**完整绘制**（被遮挡部分也补全）；④ weighted mesh 顶点权重防撕裂 | split 沿用 14px 重叠带；枢轴=bbox 顶部（肩）；补全与权重列入后续 M0-3/M0-1(b) |

---

## 1. 实测诊断（在 m04_limb_spine.zip 上复核）

### 1.1 手臂绑定：单部件 = 结构性缺陷
```
骨骼: leftArm/rightArm（父=root）、leftElbow/rightElbow（父=leftArm/rightArm）
槽位: handwear-l → bone=leftArm ｜ handwear-r → bone=rightArm
手臂相关槽位仅 2 个：['handwear-l','handwear-r']，无 upperArm/foreArm/hand 拆分
```
- `leftElbow/rightElbow` 骨存在但**没有任何 slot 引用** → 肘关节骨是"死骨"，动画里无法让肘弯曲。
- 整条手臂 = 一个刚性矩形部件，任何 rotation 都是整臂刚体转 → 手/胳膊"绑定有问题"的直接原因。

### 1.2 攻击动画：单链大摆 + 无节奏
```
attack.rightArm.rotate: t0=0 → t0.4=+50° → t0.8=-60° → t1.2=-10° → t2=0
attack.leftArm.rotate : t0=0 → t0.4=-10° → t0.8=+20° → t1.2=0 → t2=0
attack.torso.rotate  : t0=0 → t0.4=-8° → t0.8=+10° → t1.2=0 → t2=0
```
- 右臂在 0.8s 内从 +50° 甩到 -60°（幅度 110°），只有 `handwear-r` 单槽位跟随 → 整条袖子刚体甩动、肘不能弯，视觉上就是"棍子挥 + 撕裂"。
- 虽然 SYSTEM_PROMPT 已写了三段式 attack，但**没有可弯曲的肘骨骼可驱动**，方法论落了空。

### 1.3 断裂：枢轴正确，但缺重叠 + 缺补全 + 缺权重
- 手臂 bbox 顶部中心（肩部附近）落在身体 bbox 内 → 枢轴**位置正确**（非根因）。
- 根因组合：① 单刚性部件大角度旋转时根部与身体衔接处错位；② 关节重叠区不足（拆分时只有 14px 带）；③ 手臂被身体遮挡的背面部分没补全，旋转到外侧时会露空。

---

## 2. 业界是怎么解决这三个问题的

### 2.1 手臂/手绑定（Spine 官方切割指南 + TRUETECH 骨骼规范）
- **按关节切部件，不是按素材切**：`shoulder(上臂) / elbow(前臂) / hand(手)` 三段独立，每段一个部件、一根骨。
- **骨骼数 = 关节数**：肩→上臂→前臂→手，4 个关节位 4 段骨；缺一段骨就少一个自由度，动画必然僵硬/撕裂。
- **枢轴 = 真实关节**：上臂枢轴在肩关节、前臂枢轴在肘关节，**不是 bbox 中心**。bbox 顶部/侧边对齐关节是常见近似，但要落在身体/相邻部件正确一侧。
- **关节画圆收尾**：关节重叠区画成圆形，旋转时不会露出方形断口。

### 2.2 攻击动画（spine-animation-ai / 12 原则 / Esoteric 分段动画）
- **三段式，不是直上直下**：
  - **Anticipation 蓄力**（≈0.25s）：手臂后拉、身体后仰、重心下沉 —— 为发力蓄势；
  - **Strike 挥击**（≈0.3s）：前臂主导快速前挥 + 身体前倾 + 躯干旋转（torque 力量感）；
  - **Follow-through 跟随**（≈0.3s）：手臂惯性继续前伸再弹性回位。
- **挥击幅度主要给前臂（elbow），不是整条手臂**：上臂只做小范围定位，肘弯（forearm 相对上臂 -90°~-130°）产生真正的"挥"。
- **弧线 + 缓动**：手沿弧线轨迹（非直线）；关键帧用 bezier 缓动制造"慢→快→停"节奏；攻击通常 **0.6–0.9s 一气呵成**，而非 2s 匀速。
- 攻击前躯干反向扭转（anticipation 时 torso 后仰 +8°，挥击时前倾 -10°），肩髋/躯干-头有滞后跟随。

### 2.3 手臂与身体断裂（Spine 蒙皮权重指南 + 社区共识）
| 方案 | 说明 |
|---|---|
| 关节重叠带 | 相邻部件在关节处重叠（圆形收尾），旋转时互相覆盖不露缝 |
| 完整绘制 | 手臂被身体遮挡的**背面部分也画全**，转出外侧时不露空（生成式补全：PS 创成式填充 / SAM2 / Qwen Image Edit） |
| 枢轴校准 | 枢轴在真实肩/肘关节，且手臂根部在身体内（当前已满足肩部） |
| weighted mesh | 可变形部件转网格 + 顶点权重（weights[]），弯曲处顶点平滑过渡不撕裂 —— 我们当前是 region+IK 降级方案，M0-3 待做 |
| IK 肘约束 | 肘部 IK 保证弯曲方向正确（手 target 定位时肘自动弯向身体外侧） |

---

## 3. 修复方案（复用本仓库已验证的腿部拆分链路）

> 腿部已验证链路：`split-spine-limb.py`（thigh/shin 拆分 + 新增 shin slot 挂 knee 骨）→ `spine_player.gd` 膝感知 → 门禁通过 → Godot 实机渲染验证。**手臂复制同一模式即可，风险低。**

### 3.1 手臂拆分器 `tools/split-spine-arm.py`（新，仿 split-spine-limb.py）
- 输入 `m04_limb_spine.zip`，把 `handwear-l/r` 按内容 bbox **横向 55%**（肩→肘→手）切成：
  - `handwear-l`（保留原 slot，= 上臂，继续挂 `leftArm`）
  - `handwear-l-forearm`（新 slot + mesh quad，绑定 `leftElbow`）
- 沿用 `split-spine-limb.py` 的 14px 关节重叠带逻辑，**垂直切**（左臂从右往左切，右臂从左往右切），保证肩/肘处圆滑衔接。
- 输出重建 zip（images 27→29），跑 `validate-rig.py` / `validate-anim.py` 保持门禁绿。
- 手部（hand 段）：Q 版 sleeve 已含手，先不做三段；若后续要手指/手掌拆分，同法再切。

### 3.2 Godot 播放器臂感知 `tools/spine-player.gd`
- 在 `_build_drivers()` 加与膝感知对称的分支：
  - 若存在 `handwear-l-forearm`：`leftArm=["handwear-l"]`、`leftElbow=["handwear-l-forearm"]`（右臂同理）；
  - 否则回退现有 `leftArm=["handwear-l"]`（向后兼容）。

### 3.3 动画方法论升级 `tools/rig-automation/stretchy-agent.cjs`（SYSTEM_PROMPT）
attack 段改为：
- **用 rightElbow（前臂）承担挥击主幅度**：rightArm（上臂）只做 ±20° 定位，rightElbow 做 -90°~-130° 屈肘；三段时间约 0.25s/0.3s/0.3s，总 0.85~1.0s。
- 蓄力：上臂后拉 -15~-25 + 前臂收肘 -60~-90 + torso 后仰 +8；
- 挥击：前臂快速甩直（rightElbow 0°附近）+ torso 前倾 -10 + 上臂前送 +30~+45；
- 跟随：手臂惯性继续前伸再弹性回位。
- 保持 bezier 缓动 + 首尾闭合（现有门禁已强制）。

### 3.4 门禁补强 `tools/validate-rig.py`
- F3 增加：若存在 `handwear-l`，要求 `leftElbow` 被槽位引用（**死骨检查**：所有 arm/leg 关节骨必须挂至少一个 slot）。
- 新增 F6（W 级）：手臂拆分完整性 —— 拆臂后 `handwear-l-forearm` 存在。

### 3.5 验证闭环（复用现有流程）
1. `python tools/split-spine-arm.py <m04 zip>` → `validate-rig.py` / `validate-anim.py` 绿
2. Godot headless 自检 + 实机渲染（复用 `capture3.gd` + `limb_godot_dir` 流程）输出 attack 分帧
3. 人工验收：肘弯是否自然、肩部是否断裂、攻击是否三段节奏

---

## 4. 任务拆分（写入 tasks/backlog）
| Task | 内容 | 门禁 |
|---|---|---|
| M0-6 | `split-spine-arm.py` 上臂/前臂拆分 + slot 挂肘骨 | validate-rig F3(死骨) + F6 绿 |
| M0-7 | `spine_player.gd` 臂感知 + attack 动画用肘重做（SYSTEM_PROMPT 升级） | validate-anim 绿 + 无脚滑/无断裂目检 |
| M0-8 | Godot 实机渲染 attack 分帧 + 用户验收 | 肘弯自然、肩不裂、三段节奏 ✅ |

**备注（后续可选，不在本轮）**：① 手臂背面补全（SAM2/生成式）用于大角度转出时防露空；② weighted mesh（M0-3 遗留）让弯曲处顶点平滑；③ hand 段独立拆分（需更高清素材）。

---

## 5. 参照物清单
- Spine 官方切割指南（按关节切部件、枢轴=关节、关节画圆）
- TRUETECH 2D 骨骼规范（肩→上臂→前臂→手 层级）
- spine-animation-ai（Genielabs）：12 原则 attack=蓄力→挥击→跟随 + bezier easing
- Esoteric Software 蒙皮权重指南（weighted mesh 防撕裂）
- 本仓库已验证：`tools/split-spine-limb.py`（thigh/shin 拆分）+ `spine_player.gd` 膝感知（M0-1 全链路通过）
---

## 6. 腿部同样不对：实测诊断（用户 2026-08-15 反馈）

### 6.1 实测（m04_limb_spine.zip）
```
腿部槽位: legwear-l/r(thigh)→leftLeg/rightLeg ｜ legwear-l/r-shin→leftKnee/rightKnee ｜ footwear-l/r→leftLeg/rightLeg
IK: leftFootTarget/rightFootTarget（bones=[leftLeg,leftKnee]，bendPositive=true）
walk 腿部轨道:
  leftLeg.rotate: 0=-30° → 0.5=0 → 1=-20° → 1.5=0 → 2=-30°
  leftKnee.rotate: 0=10° → 0.5=30° → 1=0° → 1.5=10° → 2=10°
  rightKnee.rotate: 几乎全 0（只有一处 -10°）
膝骨偏移: leftKnee(x=+53,y=-251) vs rightKnee(x=-33,y=-236) ← 左右不对称
```

### 6.2 四个根因（与手臂同构，但多两个专属问题）
| # | 根因 | 影响 |
|---|---|---|
| L1 | **shin 枢轴=bbox 中心，不是膝盖**：`spine_player.gd` 的 `PIVOT_MODE` 只有 leftLeg/rightLeg top_center，`leftKnee/rightKnee` 落到默认 `center` → 小腿绕自身中心转，像"小腿中间折" | 腿型不对的直接原因 |
| L2 | **脚没锁地**：`footwear-l/r` 被并入 knee 驱动（跟小腿一起转），无独立脚骨/脚跟枢轴 → 走路时脚随小腿翘起、脚滑 | 脚看起来飘/滑 |
| L3 | **膝弯曲没驱动**：walk 左膝最大才 30°、右膝≈0（passing/摆动相应 60-90°）；且左右膝骨偏移不对称（+53 vs -33）→ 弯曲不对称 | 走路无膝盖屈伸感 |
| L4 | **weighted mesh 缺失 + 刚性 thigh/shin**：弯曲处膝盖位置易出硬缝（同手臂） | 膝盖撕裂感 |

### 6.3 腿部修复（M0-9，复用 split-spine 模式 + 两个小改）
- **L1**：`spine_player.gd` `PIVOT_MODE` 增加 `leftKnee/rightKnee: "top_center"`（枢轴=膝，shin bbox 顶部）、`foot: "top_center"`（脚跟）。
- **L2**：footwear 从 knee 驱动拆分出来，绑到 `leftFootTarget/rightFootTarget`（IK 目标骨），walk 中脚保持触地不滑（foot lock）；或至少新增 foot 骨 slot。
- **L3**：`stretchy-agent.cjs` walk 方法论补充：passing/摆动相膝弯 60-90°（挂在 leftKnee/rightKnee），左右膝对称；顺带修 `split-spine-limb.py` 的左右膝骨偏移不对称（切分线按各自骨位，不再统一 55%）。
- **L4**：沿用 14px 重叠带 + 后续 weighted mesh（M0-3）。
- 门禁：`validate-anim.py` 增加"walk 膝轨最大弯曲 ≥ 45°"（W 级）+ `validate-rig.py` 死骨检查扩展到 knee。

---

## 7. 「生图时多生成一些关键帧」有没有用？（方法论回答）

**结论：对当前骨骼动画链路，不能解决腿/臂问题——因为根因在 rig 数据（枢轴/脚锁定/膝驱动/权重），不在"图不够"。** 再多生成几张静态关键帧图，shin 也不会绕膝枢轴转、脚也不会锁地。关键帧图只在两种场景下有用：

### 7.1 有用场景 A：pose 参考图（reference board）→ 指导 pose-to-pose
- 做法：在 LLM 导演打关键帧**之前**，为每个动画生成"姿态参考"：walk=Contact/Down/Passing/Up 四姿态，attack=蓄力/挥击/跟随，hurt=受击/滞后。
- 价值：解决**"动作不科学"**（腿摆幅、脚触地角度、攻击发力身体姿态、肘膝弯曲方向）——导演照参考图定姿态，再换算到已绑定角色。
- 注意：AI 参考图与已 rig 角色的比例/角度不一致，**参考的是姿态意图，不能抄坐标**；每个动画每角色多 4-8 张图，成本可控。
- 落地：作为 `stretchy-agent.cjs --rules` 注入的姿态说明 + 可选给导演提供 reference 图 URL。

### 7.2 有用场景 B：改走"像素逐帧动画"管线（spritesheet）
- 那关键帧图就是动画本身，帧数越多越顺——但这是**另一条管线**（非骨骼），且 AI 逐帧一致性是硬伤：风格/位置漂移、一张大图被拆几份（本轮已踩过）。
- 需要 ControlNet/姿态锁定 img2img/animatediff + 背景抠除 + 逐帧对齐注册；成本随帧数线性涨（8-12 帧/秒 × 10 动画 × 角色）。
- 工业做法 = **关键姿态图（不逐帧）+ 中间帧工具补**（Motion Completion in-betweening / 骨骼插值 / Runway 类补帧），而不是全帧生成。

### 7.3 当前骨骼管线真正该做的"多关键帧"
- 不是生图阶段多生成图，而是**动画时间轴多打关键帧**：让 LLM 导演按 pose-to-pose 在每个动画打 8-30 个关键帧（现有能力），并且：
  1. 正确驱动 elbow/knee/foot 骨（先修 rig，否则多打帧只是把错误拍得更密）；
  2. 关键姿态先用参考图校准（7.1），再打帧；
  3. 中间帧靠 bezier 缓动（已启用），而非逐帧硬拍。

**一句话**：腿/臂不对 = rig 数据问题，改 rig；关键帧图 = 姿态参考（有用，指导姿态）+ 逐帧管线（另一条路，成本高）；骨骼管线要多的是**时间轴关键帧**，不是生图关键帧。

---

## 8. 实施结果（2026-08-15，M0-6/7/8/9 已落地）

### 8.1 代码/工具（已改）
| 文件 | 改动 |
|---|---|
| `tools/split-spine-arm.py`（新） | handwear-l/r 沿主轴拆 upper+forearm，forearm 挂 leftElbow/rightElbow；footwear-l/r 重绑到 leftFootTarget/rightFootTarget；14px 重叠带 |
| `tools/spine-player.gd` | ① PIVOT_MODE 增加 leftElbow/rightElbow/leftKnee/rightKnee/leftFootTarget/rightFootTarget=top_center；② 臂/脚拆分感知（有 forearm/shin 自动换映射，向后兼容）；③ **FK 层级累积**（arm→elbow、leg→knee→footTarget，子部件跟随父骨）；④ 新增 debug_world_pose 调试接口 |
| `tools/rig-automation/stretchy-agent.cjs` | 动画方法论升级：attack=rightElbow 屈肘-50~-70→甩直（肘驱动，非整臂大摆），三段式 0.85-1.0s；walk=支撑腿膝直、摆动腿膝弯 55~70°、footTarget 反向补偿脚贴地；boneRole 列表补齐 |
| `tools/validate-rig.py` | F6 死骨检查（elbow/knee/footTarget 必须被槽位引用）+ W3 手臂拆分完整性 |
| `tools/validate-anim.py` | W2 attack 未驱动肘、W3 walk 膝弯<40° 提示 |

### 8.2 产物（已验证）
- `assets/demo/char_ailin_m04/char_ailin_m04_arm_spine.zip`：27→29 图，4 个 forearm slot，footwear 重绑 footTarget
- 门禁：validate-rig **OK**（W1 weighted mesh / W2 root 为已知遗留）｜ validate-anim **OK**（W2/W3 因 zip 仍是旧动画，LLM 重跑后消除）
- 对照组：base knee zip 现在被 F6 正确拦截（死肘骨+死脚骨）
- Godot 自检：`godot_arm/` SETUP_OK/PARSE_OK；`godot_base/` 向后兼容通过
- FK 数值验证：attack t0.4 时右肘关节随上臂移动 121px、world rot=50°；walk t0 时膝/脚关节随大腿移动 76/118px、膝 world rot=-20°（leftLeg -30 + leftKnee 10 累积正确）
- 关节撕裂校验 `check_joint_tear.py`：walk/attack 8 帧 × 4 关节 = **32/32 全绿**（关节圆盘 100% 不透明，无断裂）
- 预览帧：`assets/demo/char_ailin_m04/frames_arm/walk_*.png`、`attack_*.png`（Python FK 渲染，供人工目检）

### 8.3 遗留/下一步
- [ ] **动画重生成（LLM）**：zip 里 attack/walk 仍是旧关键帧（W2/W3 警告）。需启动 StretchyStudio dev server（5173）+ DeepSeek key，跑 `stretchy-agent.cjs` 按新方法论重做 attack/walk → 门禁 W2/W3 消除
- [ ] weighted mesh（M0-3 遗留）：弯曲处顶点权重，消除刚性段间硬缝
- [ ] 手臂背面 SAM2/生成式补全：大角度转出时防露空（当前 FK+重叠带已解决断裂，补全进一步提升）

---

## 9. 黑帧修复 + 真实关节枢轴（M0-11，2026-08-16）

### 9.1 frames_arm 纯黑修复
- 根因：`render_fk_frames.py` 的 `imgs` 以带 `.png` 文件名做 key，而 slot 名不带后缀 → 所有部件 `continue` 跳过 → 画布全黑。
- 修复：按 slot 名取图；背景改深灰(24,24,32)。数值验证非黑：角色 bbox x[234..991] y[150..1082]，attack 挥臂扩展至 x=1107。

### 9.2 骨骼自检发现并修复：枢轴不在真实关节
- 斜臂 `handwear-l` 的 bbox 顶部中心 (796,584) 离真实肩点 ~100px（手臂是斜向，bbox 空角被当作枢轴）→ 旋转支点错。
- 修复：拆分工具写 `_pivots`（真实关节枢轴）：
  - 肩 = 手臂根端（topmost 内容点）：leftArm(703,586) / rightArm(581,587)
  - 肘 = 前臂内容中离肩最近的点（真实附着点）：leftElbow(798,703) / rightElbow(536,731)
  - 膝/踝 = 部件内容 top_center：leftKnee(760,932) / rightKnee(549,930) / 脚踝 ~(791,1051)
- 链路：`split-spine-arm.py` 写 `_pivots` → `export-godot.py` lite 透传 → `spine_player.gd` 解析覆盖 bbox 推导（向后兼容）。
- 校验：肩/肘/膝/踝关节均落在部件内容（9/10 直接命中，rightLeg 髋在内容上缘 2px 由身体覆盖）；撕裂校验 32/32 全绿；Godot FK 肘随臂 127px、膝/脚随腿 76/119px；Godot 主场景实机启动无错误。

### 9.3 视觉模型审查受限（证据）
- 用户 key `sk-c222...`：仅文本可用（gpt-5.4 回复 OK）；中转站对图片输入一律 502 "Upstream access forbidden"（5 个模型 × 2 端点全测）。
- 替代：骨骼叠加截图 `overlay_arm/` + 几何/撕裂/FK 数值校验（见 spec/2d-skeletal-auto-research.md §3）。
