# P1 Spec：角色形象 + 语音生成工作台（MVP）

> 状态：**规划中（即将进入开发）** ｜ 对应 ROADMAP Part 1
> 选型基线见 `spec/TECH-STACK.md`（工业主流优先，非主流方案已修正）

## 1. 目标
本地 Web 工作台：用户输入**人设卡（JSON）+ 可选参考图/参考音** → 生成**角色立绘（2D 分层，可进 Live2D/Spine 管线）+ 语音（多后端 TTS）** → 产出**标准资产包**（PNG 分层 / WAV+字幕 / 人设 JSON / metadata）可下载、可被 Godot 等引擎导入。

## 2. 非目标（第一版不做）
- 不做 3D 生成（glTF 作为 P1 扩展，后置）
- 不做 P2 过场 / P3 Agent / P4 引擎运行时（各有独立 part）
- 不做 P5 评测功能（后置）
- 不做在线多人/云平台，先本地单机

## 3. 输入/输出契约
### 输入
- `persona.json`（人设卡 v0）：名字/种族/职业/性格标签/文风/参考描述/台词清单(3+句)/情绪标签/可选参考图路径/可选参考音路径
- 参考图：单张全身/半身图（可选）；参考音：5-10s 干声（可选）

### 输出资产包（目录约定）
```
<character_id>/
├── persona.json            # 输入的人设卡（校验后副本）
├── metadata.json           # 生成记录：引擎/模型/参数/耗时/显存/成本/seed
├── portrait/
│   ├── full.png            # 全身/半身立绘
│   ├── layered/            # 分层输出（工业主流：Live2D/Spine 需要分图层）
│   │   ├── body/           #   body 分部件（头发/脸/身体/服饰…）
│   │   └── ...             #   由 ComfyUI workflow 或后处理拆分
│   ├── expressions/        # 可选：快速可玩表情图集（非主路径）
│   │   ├── neutral.png
│   │   └── ...
│   └── sheet.png           # 表情图集
├── voice/
│   ├── line_1.wav + line_1.txt（字幕）
│   ├── ...
└── preview.html            # 本地预览页（看图/听音）
```
> 表情方案（已修正）：**2D 走 Live2D/Umamo 绑定（参数化表情/口型），3D 走引擎原生 Blend Shapes/Morph Target**，都不靠 AIGC 生成表情图。
expressions/ 图集仅作无绑定的快速可玩占位，非主产物。

## 4. 子模块
| 模块 | 职责 | 技术（工业主流） |
|---|---|---|
| 形象生成 | 人设→ComfyUI workflow→立绘/分层/表情→落盘 | **ComfyUI** + **InstantID/PuLID**（一致性）+ LoRA（风格） |
| 语音克隆 | 参考音→克隆→台词 TTS→WAV+字幕 | **TTS 多后端抽象**：云 API（火山/Azure/ElevenLabs）+ CosyVoice（本地） |
| 任务编排 | Job 队列 + 阶段状态机 + 单步重试 | 轻量占位（SQLite+状态机），**接口抽象可换 Celery/Temporal** |
| 工作台 Web | 上传→预览→确认→下载 | FastAPI + 前端 |

## 5. 开源/论文/产品借鉴清单（已调研，按主流性排序）
### 生图后端（P1 首选：云 API = GPT + Nano Banana；本地 ComfyUI 为可选离线后端）
- **OpenAI GPT Image 2 / gpt-image-1**：角色一致性 2026 榜**断层第一**（比 Nano Banana 2 高 ~150 分）、2K/4K、文字精确 → 角色系列素材/分镜/关键帧首选；约 .04/张
- **Google Nano Banana 系**（工业常用）：Nano Banana（GA .039/张@1K）/ **Nano Banana Pro**（4K .13-0.24/张，游戏原画/概念/场景图/空间透视）/ Nano Banana 2（快速迭代）；**ComfyUI 原生节点**，API key 走 Gemini/fal/中转
- **本地 ComfyUI（可选离线后端）**：SDXL + InstantID/PuLID + LoRA → 开源发布时给无 key 用户自托管；精确 ID 锁定仍强于云模型，但首期不作为默认验证项
- **Qwen-Image（阿里开源 Apache 2.0）**：国内高质量生图本地化候选
- 决策记录：2026-08-12 用户决定 P1 生图先用 GPT + Nano Banana（云 API），本地 ComfyUI 降为可选

### 形象一致性（工业主流）
- **ComfyUI**：业界 AIGC 生产管线事实标准。Ubisoft 开源 CHORD 模型 + ComfyUI 节点（端到端 PBR 材质）；Series Entertainment 用 ComfyUI 生产 10 万+ 游戏/视频资产（180× 提速）；游戏道具设计实证研究（节点式生成工作流）。→ **执行引擎首选**
- **InstantID**：零样本身份保持，2025-12 社区共识"大多数应用的最佳平衡"（相似度高/效果好/速度合理/复杂度可控）→ **人脸一致性首选**
- **PuLID**：身份保持更稳（对比学习抗污染），但慢 30-45% → 高质量备选
- **IP-Adapter FaceID**：快、低显存（6GB+），基线方案 → 轻量备选
- **LoRA（角色/风格）**：按需训练锁定角色/风格 → 配合 InstantID 使用（不是默认必训）
- CharForge（社区项目）：仅研究参考（单参考图训 LoRA 流程），不默认进主线

### 2D 角色动画管线（工业主流，P1 预留）
- **Live2D Cubism**：二次元手游互动/表情/卡面标配；**FREE 版个人/年销售额<1000 万日元可商用**；SDK 发布需出版许可（开源 demo 本地运行无碍）
- **Umamo**（开源，GPLv3）：Live2D Cubism Editor 的 drop-in 替代（跨平台 rigging）→ 开源管线首选
- **DragonBones/LoongBones**（开源 2D 动画）→ 备选
- **Spine**：2D 骨骼动画行业标准，运行时性能好 → 大幅动作/战斗场景备选
- 目标管线：分层立绘（PSD/layered）→ Live2D Cubism/Umamo 绑定 → 参数化表情/口型（引擎内驱动）

### 3D 表情（P1 预留，引擎内完成）
- 3D 表情**不需要 AIGC 生成表情图**：Godot/Unity 用 **Blend Shapes**（SkinnedMeshRenderer.SetBlendShapeWeight）、UE 用 **Morph Targets**，引擎内调权重即可
- 参考 ARKit 46 blendshape 标准设计面部 morph 集合

### 语音（工业主流 + RVC 音色增强）
- 两条路线（都可，推荐组合）：
  1. **克隆 TTS 直接生成角色音色**（简单）：CosyVoice 零样本（本地）/ 火山克隆音色（云）
  2. **通用 TTS + RVC 音色转换**（高质量角色音色，推荐）：通用 TTS（火山/Azure，情感自然）→ **RVC**（用 5-10min 角色素材训练模型）转换音色 → 音色一致 + 情感自然（2026 实测组合自然度 90%+）
- RVC 定位：音色转换（非 TTS），音色相似度最高（9.5），开源活跃（RVC-Project WebUI）
- 设计：TTS 抽象 + **可选 RVC 后处理阶段**（tools/tts 加 rvc 步骤）

### 语音（工业主流）### 语音（工业主流）
- **云 API（生产后端）**：火山引擎 TTS（国内综合首选，中文自然度/定价合理）、Azure TTS（延迟最低/免费层大，游戏解说场景推荐）、ElevenLabs（情感/音质天花板，海外）—— 2026 TTS 选型评测
- **开源（本地/离线）**：**CosyVoice（阿里开源，流式低延迟/高音色一致性/情感控制，工业级）**、F5-TTS（快/MIT）
- GPT-SoVITS：社区热门，**仅作克隆研究候选**，不作为生产默认
- 设计：TTS 后端抽象，云/本地可切换（成本与质量权衡）

### 工作台/编排形态
- 3dModelGenerator：job 状态轮询 → 编排参照
- studiomi300：Director Agent + streaming 阶段输出 → 后续 P2 参照
- handcrafted-persona-engine / AITuberKit：角色卡交互参考（非主流，仅 UI 参考）

## 6. 技术选型（MVP，依据 TECH-STACK.md）
| 项 | 首选 | 备选 | 理由（工业主流） |
|---|---|---|---|
| 生图编排 | **ComfyUI**（节点 workflow，可复用社区节点） | 自研封装 | Ubisoft/Series 生产管线验证；社区节点生态（InstantID/PuLID/ControlNet 现成） |
| 身份一致性 | **InstantID** | PuLID / IP-Adapter FaceID | 2025-12 共识最佳平衡；PuLID 更稳但慢 |
| 风格/角色锁定 | LoRA（按需训练） | 现成风格 LoRA | 工作室通用做法 |
| 表情/动画 | 表情差分图集（MVP 快速）+ **layered/ 分层预留** | Live2D 绑定（后续） | 工业主流=Live2D/Spine；MVP 先可玩，契约已预留 |
| TTS | **多后端抽象**：云 API（火山/Azure）为主 + CosyVoice 本地 | F5-TTS / ElevenLabs | 工业=云 API+大厂开源；GPT-SoVITS 降为研究 |
| 3D（后置） | **Hunyuan3D 2.1 / TRELLIS / Tripo API / Meshy** | — | 生产级网格/PBR/UV；TripoSR 已过时 |
| 编排 | 轻量队列（接口抽象） | Celery/Temporal（生产） | MVP 占位可换主流 |
| Web | FastAPI + 前端 | Streamlit（原型） | 主流 |
| 引擎（P4） | Godot（主实现） | Unity/Unreal（导入目标） | Godot indie 2D 增长最快；资产/Agent 引擎无关 |

## 6.5 资产类型与测试场景（生图测试必须按场景，不能一张图了事）
> 参考 AIGC 实践：资产按用途分类型，每类有独立的生成模板、锚点机制与验收。

| 场景 | 资产类型 | 需要生成什么 | 一致性手段 | 验收要点 |
|---|---|---|---|---|
| **A. 2D 像素游戏** | 像素角色 | ① 基础角色（front 锚点）② **三视图**（front/side/back）③ **行为帧**（idle/walk/attack/hurt）④ 精灵表/方向表 | 风格锚点 + 参考图锚点（front 图带后续生成） | 视图间身份一致；动作帧风格统一；透明背景/像素干净 |
| **B. 高清立绘** | 立绘角色 | ① 主立绘 ② **表情差分** ③ **转面/多视图** ④ 战斗/动作立绘 | 风格锚点 + 表情模板 + seed 控制 | 表情/转面与主立绘一致；构图可用 |

**测试方法（每场景）**：
1. 生成锚点图 → 带锚点生成后续资产
2. 同 prompt 3 次取最优（三次生成规则）
3. 每项人工校验身份/风格一致（肉眼 + 结构检查）
4. 资产落盘到 assets/<character_id>/<scenario>/，记录 prompt/参数/耗时/成本

**多轮调整**：生成 → 审查（用户/画布批注）→ 调整（追加描述/换锚点/改风格参数）→ 重新生成，最多 3 轮，沉淀 prompt 经验（见 contracts/prompt-templates.md §7）。
## 7. MVP 验收标准（gate）
- [ ] ComfyUI + InstantID 从参考图/人设生成角色：4 表情差分，肉眼身份一致
- [ ] TTS 多后端：至少一条本地链路（CosyVoice）+ 一条云 API 链路跑通，3 句台词可播放
- [ ] 资产包结构与 metadata 完整，校验脚本通过（含 layered/ 预留说明）
- [ ] 工作台：上传→看到每阶段产物→选择→下载；单阶段失败可重试
- [ ] Godot 最小工程能导入立绘 + 播放语音
- [ ] P1 审计完成（audit/audit-log.md）

## 8. 开放问题
- InstantID vs PuLID 在当前显卡上的质量/速度实测（t1 验证）
- Live2D 分层如何自动生成/拆分（先人工拆分 + 规范，工具化后置）
- 无参考音时 TTS 音色如何选（预设音色库：云 API 音色 vs CosyVoice 克隆）
- 表情差分数量/情绪集合定多少（先 neutral/happy/sad/angry 4 个）


