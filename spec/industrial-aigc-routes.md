# 2D/3D 工业化 AIGC 路线总清单（spec/industrial-aigc-routes.md）

> 整理日期：2026-08-18 ｜ 汇总来源：生图.md、spec/pipeline-unified-2d3d.md、spec/2d-asset-skeletal-workflow.md、spec/pipeline-remaster-2d-skeletal.md、spec/2d-skeletal-auto-research.md、spec/industrial-pipeline-v2.md、spec/TECH-STACK.md、spec/comfyui-lora-plan.md、spec/style-research.md、spec/frame-anim-workflow.md、spec/plan-2d-skeletal.md、spec/plan-3d-route.md
> 用途：所有调研到的 2D/3D 工业化 AIGC 路线索引；标注工业主流 / 备选 / 本项目落地状态。

---

## 一、2D 管线（生图 → 拆层 → 绑骨 → 动画 → 打包 → 引擎）

### S0 生图
| 路线 | 方案 | 状态 |
|---|---|---|
| 云 API | **GPT-Image-2**（多图参考、角色一致性 2026 断层第一）、**Nano Banana Pro/2**（带参考图/UV）、gpt-image-1/4o（批量/改图/抠图）、Z-Image Turbo（无缝纹理 ~4s） | 本项目主用 gpt-image-2 多参考，已验证 |
| 本地/开源 | ComfyUI + SDXL/Illustrious/NoobAI + **ControlNet**（OpenPose/seg/canny/depth）+ **InstantID/IP-Adapter/PuLID**（角色一致性）+ **风格 LoRA**（画风锁死 100%） | 规划中（本机 8GB 可跑 SDXL 系） |
| 专业角色管线 | **ComfyUI VNCCS 3.0**（Character/Clothes/Emotion/Pose Studio 端到端）、**mor-o 2d-character-pipeline**（cosmetic 分层精灵 + BiRefNet 去背景）、**AI Character Turnaround**（三视图）、**VNCCS Emotion Studio**（表情差分） | 调研/对照 |
| 表情差分（立绘） | 云 API：逐表情 images.edit + mask → **抠人脸合成回基底**（身体像素一致 100%）；本地：VNCCS Emotion Studio | 已落地（v7/v9/v10） |

### S1 拆层 / 抠图
| 路线 | 方案 | 状态 |
|---|---|---|
| 2.5D 分层 | **See-through / LayerDiff3D**（ComfyUI，单图→分层 PSD+深度排序） | 已部署（RTX4060 8GB ~20min/张），char_ailin_m04 拆出 17 层 |
| 动漫立绘分层 | **VTuber2D.AI**（头发/身体/眼睛/衣服→可编辑 PSD→Live2D） | 调研 |
| 万物分割+补全 | **SAM2 + PS 生成式补全**（单图→骨骼级全资产源文件）、img2rig（LLM+SAM 分层 rig）、BiRefNet 去背景 | 调研（thigh/shin 拆分参考） |
| 拆层契约 | Live2D 规范 PSD（头发/眉眼口/手/衣服分层、命名规范） | 已沉淀 |

### S2 骨骼绑定
| 路线 | 方案 | 状态 |
|---|---|---|
| 工业编辑器 | **Spine**（网格+权重+Skins）、**Live2D Cubism**（参数化）、DragonBones（开源）、PixelOver（像素骨骼+IK） | 选型 |
| AI 自动绑骨 | **StretchyStudio**（DWPose，FOSS）、**UniRig**、**Spine-Anim-AI**（SIFT+RANSAC）、**Spiritus**（~30s 端到端）、**ASMR**（蒙皮权重）、Adobe How-to-Train-Your-Dragon | StretchyStudio 已部署并跑通（26 骨/2 IK，领先网易 2D 段） |
| 五步工业法 | 部件拆分（关节重叠区画圆）→ 标准骨层级+真实关节枢轴 → 网格蒙皮权重（合计 1.0）→ IK 约束（脚 ground-lock/膝肘方向）→ 12 原则关键帧 | 权威基线 |

### S3 动画
| 路线 | 方案 | 状态 |
|---|---|---|
| 骨骼动画 | Spine runtime（程序化控制/动画混合/Skins）、Live2D 参数（表情/口型）、Godot AnimationPlayer/AnimationTree | A 路线规划中 |
| AI 动作 | **Motion Completion**（网易，in-betweening 补中间帧）、**SCAIL2**（ComfyUI 视频动作迁移+SAM3）、**PoseCap**（视频→Bip/fbx）、2dimg2motion（关键帧→序列帧） | 调研 |
| 帧动画（B 路线） | AI 关键帧（同一 matte hero 身份锚点 + 固定风格块）→ 核心身体对齐（高度/中心/地面线）→ Godot AnimatedSprite2D | **已跑通**（像素 8/10、HD-2D 7.5/10） |
| 动画方法论 | 12 原则 + spine-animation-ai 预设（idle 正弦/walk 对侧摆+髋 bob/attack 蓄力→挥击→跟随）+ bezier 缓动 | 已采用 |

### S4 打包 / 引擎
| 路线 | 方案 | 状态 |
|---|---|---|
| 图集 | Spine atlas / TexturePacker / Cutlas（网易） | 未做 atlas |
| 引擎 | Godot（本项目，2D 增长最快开源引擎）/ Unity / UE | Godot 4.7.1 横板 demo 已跑通 |
| 游戏内资产形态 | 正面立绘 + 表情差分 + SD 小人/战斗精灵 +（后置）Live2D 分层/Spine 骨骼 | 已明确（spec/2d-in-game-assets.md） |

---

## 二、3D 管线（生图优化 → 3D 生成 → 修正 → 绑骨 → 动作 → 引擎）

### F1 生图优化 + 三视图
- 云 API：Nano Banana（草图→三维渲染图）、gpt-image-2 多参考；**三视图一致性关键**（多视图精度>单图）
- 专业做法：**AI Character Turnaround**（ComfyUI OpenPose conditioning + 角色 LoRA + view-specific conditioning）；三视图→LoRA 精修（InstantID 初版→筛选→LoRA 训练 7-7）

### F2 3D 生成（image-to-3D，2026 最新）
| 路线 | 方案 | 本机（RTX 4060 8GB） |
|---|---|---|
| 开源本地 | **TRELLIS 2**（微软，MIT，4B，纹理保真 9/10，低显存 512³ ~8GB / 1024³ ~120s） | ✅ 可跑（低显存模式） |
| 开源本地 | **Hunyuan3D 2.5/2.1**（腾讯，Apache，10B，形状 6GB / 全量纹理 16GB；RTX 3060 12GB 形状 ~30s） | ⚠️ 仅形状生成可跑 |
| 商业 API | **Tripo v3.1/H3.1**（PBR 纹理、面数≤200 万、20-40s、Turbo）、**Meshy v6**（低模/硬表面）、Hyper3D Rodin | ✅ API（试用 key 有额度） |
| 平台 | DreamMaker 3D 平台（TripoAI/影眸）、seedream、hitem3D | 网易内部参考 |

### F3 修正链路（DCC）
- Blender（减面→重构 UV→法线传递→贴图）+ **DCC-MCP** 自动化（自研适配器经验，intern-learn dcc-mcp-creator）
- 生成模型短板：面数多、UV 待改进、高模不足 → 必须过修正链路

### F4 自动绑骨 / 蒙皮
| 路线 | 方案 | 说明 |
|---|---|---|
| 免费网页 | **Mixamo**（Adobe） | 上传模型自动绑骨蒙皮 + 动作库；免费基线 |
| 开源 | **UniRig**（VAST，SIGGRAPH 2025，支持人类/动物/幻想角色）、**RigNet**（SIGGRAPH 2020） | UniRig 已服务化进 Tripo API（/animations/rig + rig-check） |
| 商业 | Auto-Rig Pro（Blender）、Cascadeur AutoPosing、Reallusion AccuRig、Sorceress Rig | 2026 自动绑骨对比表现好 |
| 网易内部（不可用，缺口） | ailab_auto_skin / CharacterMaker / Muse（对标 Mixamo） | 功能作技术参照（深度学习权重预测） |

### F5 动作
- 动作库：Mixamo 动作库 / 手 K
- AI 动作生成：**Motion Completion**（补全型 in-betweening，网易 AAAI 2022）、**SCAIL2**（视频动作迁移）、**PoseCap**（视频→Bip/fbx）、80.lv 视频转动作插件
- 运行时：Godot AnimationPlayer / Unity Animator / UE AnimBP+Control Rig / messiah AITransitionGenerator（网易）
- 边界：**从零设计全新动作仍需手 K/动捕**；补全型与视频驱动已可用

### F6 进引擎
- Godot GLB 原生导入 + AnimationPlayer（本项目）
- UE Wuzu（网易内部，双向桥+VLM 匹配，不可用）→ 用程序化导入替代

---

## 三、横切能力（两条管线共用）

| 能力 | 工业化方案 | 本项目状态 |
|---|---|---|
| 画风锁死 | **ComfyUI + 风格 LoRA / IP-Adapter**（工业主流，100%）vs 云 API 多参考（接近） | 云 API 已打通；本地 LoRA 规划中（spec/comfyui-lora-plan.md） |
| 角色一致性 | InstantID（首选）/ PuLID / IP-Adapter FaceID / 角色 LoRA（10-20 图训练） | 调研（当前用多参考+prompt 锚点） |
| 工作流编排 | ComfyUI 节点 / SunshineFlow 蓝图（网易）/ 自研 orchestrator（状态机+契约+门禁+成本核算） | industrial-pipeline-v2 蓝图，单点工具齐 |
| 质量门禁 | 契约 schema + validate-*.py + **视觉模型验收**（vision_review gpt-5.5） | 已落地（每阶段 gate） |
| 反馈闭环 | lessons-learned / preferences 数据库、失败→原因→规则→自动规避 | 已建骨架 |
| DCC 加工 | DCC-MCP 适配器（Blender/Maya/UE） | 有 dcc-mcp-creator skill 经验 |
| 工作台交互 | tldraw 无限画布 / FastAPI+React | workbench v2 规划中 |
| 任务队列/服务化 | Celery/Redis、Temporal（生产）；SQLite+状态机（MVP） | 轻量 MVP |

---

## 四、本项目落地状态速览

| 环节 | 落地 | 状态 |
|---|---|---|
| 2D 生图（画风锚点+表情差分） | 艾琳 v10 立绘 + chibi_v4 小人 + 表情×4 | ✅ |
| 2D 拆层 | See-through 17 层 PSD（char_ailin_m04） | ✅（慢，~20min/张） |
| 2D 绑骨 | StretchyStudio DWPose + FK 播放器 + 膝盖弯曲集成 | ✅ 小样本跑通 |
| 2D 动画 | B 路线帧动画（横板 demo 在用）｜A 路线 Spine 阻塞（hf-mirror） | ✅ / ⏳ |
| 3D 生成 | 未开始（Tier1 Tripo POC / Tier2 本地对照已规划） | 📋 |
| 3D 绑骨/动作 | Mixamo / UniRig / SCAIL2 已选型 | 📋 |
| 引擎 | Godot 4.7.1 2D 横板 demo（地图+战斗+箭矢） | ✅ |

## 五、结论
- **2D 线**：全环节外部方案已齐，且 2D 自动绑骨（StretchyStudio）领先网易；最大差距在"编排+门禁+反馈"系统层（industrial-pipeline-v2）。
- **3D 线**：2026 开源拐点=TRELLIS 2 + Hunyuan3D；绑骨缺口用 Mixamo/UniRig 补；推荐 Tripo API POC 先行。
- **共同原则**：选工业主流（商业/大厂开源/生产验证），社区项目只作研究参考（TECH-STACK.md 总原则）。