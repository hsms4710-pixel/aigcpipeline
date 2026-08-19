# 2D 骨骼生成自动化 + 像素 2D 小人：调研与实践映射（spec/2d-skeletal-auto-research.md）

> 日期：2026-08-16 ｜ 触发：目标「调研 2D 图像骨骼生成的自动化解决方法，或像素 2D 小人（bilibili AI 做游戏实践），用调研到的方法生成完善的 2D 人物模型并在 Godot 测试；所有骨骼截图检验」
> 结论速览：**自动绑骨在 2D 侧工业界=「部件定位(SIFT/RANSAC 或深度学习) + 标准骨层级 + 枢轴/IK/权重」，我们已用 StretchyStudio + 自研拆分/FK 播放器闭环；bilibili 像素实践=「AI 生成角色→姿态控制→逐帧/骨骼动画」两派。本次落地=真实关节枢轴 + FK 层级累积 + 骨骼叠加截图校验。**

---

## 1. 2D 图像骨骼生成自动化（方法清单）

| 方案 | 做法 | 自动程度 | 对本项目 |
|---|---|---|---|
| **spine-animation-ai**（Genielabs, Claude skill） | SIFT+RANSAC 从参考图定位部件 → 构建骨架 JSON（层级+绘制序）→ 12 原则动画预设（idle/walk/run/attack）+ bezier 缓动 | 部件定位+动画自动 | 动画方法论参照（我们已抄 attack/walk 三段式） |
| **spine2d-animation-mcp / naosen**（MCP server） | 分层 PSD → Spine 4.2 工程（skeleton+atlas），NL 描述自动绑骨+动画 | 半自动 | 与我们「LLM 导演 agent」同思路 |
| **Spiritus**（web 工具；ACM "Outline and Detail" 论文） | 语义驱动分层 2D 角色生成 + **约 30s 自动骨架绑定** + 初始动画 | 高（端到端） | 对照目标：一条龙 30s 出可动角色 |
| **ASMR**（EG 2025 论文） | 2D 生成先验做**自适应骨架-网格绑定+蒙皮**（权重学习） | 高 | **蒙皮权重 = 弯曲不撕裂的关键**（我们 W1 遗留） |
| **How to Train Your Dragon**（CGF 2025） | 扩散模型自动绑定，支持多样拓扑 | 高 | 可换拓扑时用 |
| **Auto-Connect RigFormer+DPO**（2025） | 保连通性 tokenization 的自动绑定 | 高 | 学术参考 |
| **StretchyStudio**（MangoLion, FOSS，我们已用） | DWPose/启发式**自动绑骨 + mesh 变形** + 时间线 | 半自动 | 已部署；缺 IK/权重导出与质量门禁（已补门禁） |

**工业共识（Spine/TRUETECH/Esoteric）**：部件按关节切 → 标准骨层级（肩→上臂→前臂→手；髋→大腿→小腿→脚）→ **枢轴=真实关节** → IK/权重 → 12 原则关键帧。自动化的瓶颈在「枢轴/权重」，不是「生成骨架」——**本次我们正是补齐了「枢轴=真实关节」+「FK 层级累积」这两块**。

## 2. 像素 2D 小人（bilibili 实践 + 开源工具）

### 2.1 bilibili 常见工作流（两类）
| 流派 | 流程 | 代表视频 |
|---|---|---|
| **逐帧动画派** | MidJourney/即梦 角色原型 → Nano Banana 控制姿态 → 即梦/Sora2 生成初始动画 → PS 精简帧导出逐帧序列 | BV15QHazWEA8、BV1fDyxBJEu3 |
| **骨骼动画派** | Nano Banana 生成像素美术 → ComfyUI 高质量抠图 → **PixelOver/Spine 骨骼动画** | BV1oNiiBHEWL（含 ComfyUI 抠图工作流） |

### 2.2 像素专用工具（可直接用）
| 工具 | 能力 |
|---|---|
| **PixelOver** | 像素骨骼动画 + IK（bilibili 有大量教学） |
| **Retro Diffusion / rd-animation**（Replicate） | 网格对齐、风格一致、限色像素精灵/精灵表（48x48 等） |
| **SpriteForge** | base 角色 PNG + YAML（调色板/动画/规则）→ 两阶段 AI 管线出游戏可用精灵表 |
| **perfectpixel-studio** | 文本 → 8 方向、100+ 动作的精灵表 |
| **pixellab-mcp** | 像素角色/动画/瓦片生成 MCP（可接 Codex） |

## 3. 本次实践：用「枢轴=真实关节 + FK 层级累积」生成完善模型（char_ailin）

> 依据第 1 节「枢轴/权重是自动绑骨瓶颈」的调研结论，本次把 char_ailin 从「刚性单部件 + 无继承」升级为「拆分部件 + 真实关节枢轴 + FK 父子继承」。

### 3.1 修复黑帧（用户报告）
- 根因：`render_fk_frames.py` 用带 `.png` 的文件名做 key，slot 名无后缀 → 所有部件被跳过 → 纯黑画布。
- 修复：按 slot 名取图 + 背景改深灰(24,24,32)。**已数值验证非黑**（角色 bbox x[234..991] y[150..1082]，攻击挥臂扩展到 x=1107）。

### 3.2 骨骼自检（截图 + 几何校验）
- **截图**：`assets/demo/char_ailin_m04/overlay_arm/`（overlay_rest / walk_050 / attack_080）——骨骼红线 + 关节绿点 + 骨名标注，叠加在角色图上。
- **几何校验**（关节是否落在部件内容上）：
  - 肩：leftArm(703,586)/rightArm(581,587) **落在手臂/身体内容** ✓（自检发现原 bbox 顶部中心 (796,584) 偏 100px，已修）
  - 肘：leftElbow(798,703)/rightElbow(536,731) = **前臂内容中离肩最近的点**（真实附着点）✓
  - 膝/踝：leftKnee(760,932)/rightKnee(549,930)/脚踝 ~(791,1051) ✓
- **撕裂校验**：walk/attack 8 帧 × 4 关节 = **32/32 关节圆盘 100% 不透明**（无断裂/穿洞）。
- **Godot FK 数值**：attack 肘关节随上臂移动 127px；walk 膝/脚随大腿移动 76/119px；膝世界角=leftLeg+leftKnee 正确累积。
- **Godot 主场景实机启动**：`godot --path godot_arm` 无脚本错误，动画正常渲染播放。

### 3.3 视觉模型审查受限（记录证据）
- 用户提供 key `sk-c222...`，经测试仅支持文本（gpt-5.4 正常回复"OK"）；
- **该中转站对图片输入一律 502 "Upstream access forbidden"**（chat/completions 与 responses 端点、gpt-5.4/5.5/5.6-terra/5.6-sol 全部测试）；
- 结论：此 key 无视觉能力 → 截图审查改用「骨骼叠加图 + 几何/撕裂/FK 数值校验」，叠加图可供用户/后续视觉模型复查。

### 3.4 产物与门禁
- `char_ailin_m04_arm_spine.zip`：26 骨 / 29 槽位 / 2 IK / `_pivots`（真实关节枢轴）/ arm+leg+foot 拆分
- `validate-rig.py`：**OK**（W1 weighted mesh、W2 root 枢轴为已知遗留）
- `validate-anim.py`：OK（W2/W3 因 zip 仍是旧动画，LLM 重跑后消除）
- `godot_arm/`：Godot 工程（自检 SETUP_OK/PARSE_OK + 主场景实机启动 OK）
- `frames_arm/`：动画帧（非黑）；`overlay_arm/`：骨骼叠加截图

## 4. 后续建议（优先级）
1. **动画 LLM 重生成**（消除 W2/W3）：启动 StretchyStudio dev server + DeepSeek key，跑 stretchy-agent.cjs 按新方法论（肘驱动 attack / 膝弯 walk）。
2. **weighted mesh（M0-3）**：按 ASMR/Spine 实践给拆分部件加双骨权重（上臂→arm+elbow、前臂→elbow、shin→knee），弯曲顶点平滑；需 Spine/Godot Spine runtime 展示（我们的自定义播放器仍为刚体+重叠带）。
3. **像素分支**：用 Retro Diffusion/SpriteForge 生成像素角色 → PixelOver/Spine 骨骼动画 → Godot（对照 bilibili 骨骼动画派）。
4. **端到端 30s 对标 Spiritus**：若后续接入更强的自动绑骨（如 ASMR/扩散绑骨），可对标"一条龙出可动角色"。
---

## 5. 新增：单图自动生成可绑定小人（2026-08-16，新角色 chibi_apose）

> 触发：用户反馈原 char_ailin「视觉不连续」，要求从生图一步重做。按 调研→验证→实施 完成。

### 5.1 验证（根因）
- 视觉审查（gpt-5.5，新 key `sk-5ef3...` 支持图片，gpt-5.5/5.6-sol 可用）确认：**原源图「层级太复杂」**——披风/长发/弓/下摆遮挡肩肘关节、双臂不对称未与身体干净分离 → 拆分后动画粘连/不连续。

### 5.2 实施：单图 → 可绑定 Spine 模型（tools/build-spine-from-image.py）
1. **生图**：gpt-image-2 生成 A-pose 像素精灵（无披风/武器/长发遮挡，四肢分离）→ `assets/demo/chibi_apose/front.png`
2. **自动切分**（逐行段分析）：脖子 338 / 臂根 437 / 腿缝 637 / 腿缝 x=510 → 头/躯干/双臂/双腿，覆盖 100%、重叠 0
3. **肢段拆分**：上臂/前臂（60%），大腿/小腿/脚（52%/82%）
4. **Spine 构建**：14 骨（标准层级+elbow/knee/footTarget）+ 12 slot + 2 IK + 真实枢轴 `_pivots` + 基础循环动画（idle/walk/attack/hurt）
5. **门禁**：validate-rig OK（W1 weighted mesh 遗留）、validate-anim OK（2.00s/循环闭合/100% 缓动）
6. **Godot**：自检 SETUP_OK/PARSE_OK、FK 继承 PASS、主场景实机启动无错误

### 5.3 视觉复查（用户核心诉求"不连续"已解决）
| 检查 | 结果 |
|---|---|
| walk 帧连续性 | gpt-5.5：颜色正常可见、手臂/腿与身体连续、关节无裂痕、整体完整 |
| attack 挥臂 | gpt-5.5：手臂连续、肘弯自然、整体完整 |
| 骨骼叠加 | gpt-5.5：无明显错位（肩/肘/膝/踝落位；膝/踝略偏低为小优化项） |
| 撕裂校验 | 32/32 关节圆盘全不透明 |
| 帧颜色 | mean_rgb≈[155,134,114]（非黑；修复了部件 RGB=0 的渲染 bug） |

### 5.4 关键 bug 修复（过程中发现）
- **部件 RGB=0**：mask_to_png 只写 alpha 不写 RGB → 角色渲染纯黑；修复为保留原图颜色
- **动画关键帧时间单位**：误写毫秒（500）而播放器/门禁用秒（0.5）→ 动画 1000 倍速；修复为秒
- **腿起点/臂根误判**：须用「持续多行的段结构」判定（臂根=外侧段宽≥30px 持续 3 行；腿起点=恰好 2 段持续 10 行）

### 5.5 产物
- `assets/demo/chibi_apose/front.png`（A-pose 源图）+ meta.json
- `assets/demo/chibi_apose/chibi_apose_spine.zip`（14 骨/12 slot/2 IK/真实枢轴）
- `assets/demo/chibi_apose/godot/`（Godot 工程，主场景可运行）
- `assets/demo/chibi_apose/frames/`、`overlay/`、`review_sheet.png`

### 5.6 后续（可选）
- 膝/踝枢轴微调（视觉建议略偏低）；weighted mesh；LLM 重生成动画替换基础动画；多方向（侧/背）生成。

---

## 6. 断裂/反人类动作/连续帧：工业调研 + 全量视觉审查 + 关键帧路线（2026-08-16 续）

### 6.1 工业界怎么解决（调研结论）
| 问题 | 工业做法 |
|---|---|
| **断裂/穿模** | ① Spine 官方「How to cut your assets」：关节处**画圆收尾 + 重叠**；② 上下两段式肢体优于单段自叠（Esoteric forum：单段自叠=valley of tears）；③ 蒙皮权重（同缝顶点同权重）平滑弯曲；④ Live2D 网格形变（权重）用于大开大阖动作 |
| **动作反人类/僵硬** | ① **视频/参考驱动**：FlexiClip(ICML'25)、AnyMoLe(CVPR'25)、SCAIL、PoseCap 动捕；② 规范关键帧（12 原则：anticipation/follow-through/arcs）；③ **正面视角的固有局限**：前后摆腿在纵深方向，2D 旋转表现不出 → 工业用侧/3/4 视图或帧动画 |
| **连续帧** | **视频→序列帧是主流**（bilibili/cocos 工作流：豆包AI→视频→序列帧→Spine，全程无需手动绑定）；Retro Diffusion/SpriteForge 出精灵表；**SpriteForge 用 LLM 视觉 gate 审动画**（同角色/动作逻辑/无跳变）——与本项目"视觉审查"一致 |

### 6.2 全量视觉审查（本次：所有 4 个动画逐帧 gpt-5.5 review）
| 动画 | 断裂/穿模 | 动作问题 |
|---|---|---|
| walk | 无 | 手臂"张开-放下"不像摆臂、腿部交替弱（正面视角局限 + 关键帧幅度小） |
| attack | 无 | 无蓄力转体、命中帧像"摊手"、发力方向不明 |
| idle | 无 | 太静态（无呼吸微动） |
| hurt | 无 | 与 idle 几乎一样（无受击反馈） |
> 结论：**断裂已基本解决**（视觉 8 帧均无）；剩余问题是"动作不自然"（骨骼关键帧弱 + 正面视角限制）。

### 6.3 实施：双管齐下
1. **修骨骼关键帧**（build-spine-from-image.py）：walk 4 姿态摆臂反相+膝弯、attack 蓄力(后拉+转体12°)+挥击(前倾-16°+前移)+跟随、idle 呼吸缩放+手臂微动、hurt 后仰18°+头滞后+双臂外甩+弹性回位。门禁绿、撕裂 32/32。
2. **连续帧路线（实测可行）**：gpt-image-2 以 A-pose 源图为参考锚点，生成 walk 4 关键姿态（contact/down/passing/up）→ **gpt-5.5 审查：同一角色、动作可读、无断裂**；对齐（底部地面线+水平中心）→ Godot AnimatedSprite2D 帧动画（运行时 ImageTexture 加载，自检 FRAME_COUNT=4）+ walk_cycle.gif。
   - 关键帧自带透明背景（80%），无需抠图。
   - 产物：`assets/demo/chibi_apose/keyframes/`、`godot_frameanim/`、`walk_cycle.gif`。

### 6.4 结论/建议
- **断裂**：视觉确认已消；若要进一步彻底，按 Spine 官方做圆角收尾 + 蒙皮权重（M0-3）。
- **动作反人类**：骨骼正面视角有固有局限；**连续帧路线（视频/关键帧生成）是工业主流且我们已跑通 walk**，建议后续把 idle/attack/hurt 也改为关键帧生成，或用视频模型（即梦/Sora2/豆包，需相应 key）→ 序列帧。
- **视觉审查**：已建立"生成→渲染帧→gpt-5.5 逐帧审查→迭代"的闭环，所有动画都应过审。
