# P2 Spec：过场动画 AIGC（详细方案）

> 状态：**规划中（Part 4，依赖 P1 资产 + 生图 GPT/Nano Banana）** ｜ 选型基线：TECH-STACK.md

## 1. 三种范式（先想清楚做什么）
| 范式 | 做法 | 优点 | 缺点 | 用途 |
|---|---|---|---|---|
| **A. AIGC 视频过场（播片）** | 关键帧（GPT/Nano Banana）→ 图生视频（Veo/Kling/Wan）→ 配音配乐 → mp4 | 视觉冲击强、可做预告/买量 | 成本高（每镜视频费）、可控弱、不可交互 | 预告片、展示素材、非交互剧情段 |
| **B. 引擎内程序化过场（实机）** | 剧本 → 引擎时间轴（Godot AnimationPlayer）+ P1 资产（立绘分层/Live2D 表情口型/3D blendshape）+ 语音 → 实机渲染 | 可控可交互、资产复用、成本低、与游戏一致 | 视觉上限取决于资产 | 游戏内对话/叙事（视觉小说/CRPG 主流） |
| **C. 混合（推荐）** | Director Agent 逐镜决策：关键/情感镜头走 A，对话/交互镜头走 B | 质量与成本平衡、可交互 | 需编排复杂度 | 完整过场 |

**结论**：P2 MVP 走 **B（引擎内）** 为主 + **A（AIGC 视频）** 做展示/预告；C 是最终形态。

## 2. 过场管线（详细）
```
1. 剧本：Ink 格式（shipped games 主流叙事语言）
2. Director Agent（LLM）拆镜头：镜头列表 [景别/运镜/时长/台词/情绪/角色/背景]
3. 视觉资产：
   - 角色设定图/多视图：GPT Image 2（角色一致性第一）→ 锚点
   - 场景/背景图：Nano Banana Pro（空间透视/构图精度）
   - 分镜图（带台词文字）：Nano Banana Pro（文字渲染强）
   - 关键帧（首尾帧锚点）：GPT Image 2 → 供视频模型
4. 动画化：
   - 范式 A：图生视频 Veo 3 / Kling 3.0 / Wan 2.1（镜头级生成）
   - 范式 B：Godot AnimationPlayer 时间轴 + Live2D/Spine 表情口型（2D）或 blendshape（3D）+ 运镜
5. 配音：TTS 多后端（火山/Azure/CosyVoice）按台词生成；可选配乐
6. 输出：A → mp4；B → Godot 过场场景；C → 混合导出
```

## 3. GPT / Nano Banana 在过场中的角色（用户指定先用）
| 环节 | 用谁 | 为什么 |
|---|---|---|
| 角色设定图/多视图/表情变体 | **GPT Image 2** | 角色一致性 2026 榜断层第一 → 跨镜头不串脸 |
| 场景/背景图（空间透视） | **Nano Banana Pro** | 构图精度/多对象关系强 |
| 分镜图（含台词文字） | **Nano Banana Pro** | 文字渲染精确（分镜上写字清晰） |
| 关键帧锚点（首尾帧） | **GPT Image 2** | 精确构图 → 喂图生视频 |
| 概念/买量图 | Nano Banana 系 | 工业常用、快速 |

## 4. 视频生成选型（范式 A）
| 模型 | 特点 | 选型 |
|---|---|---|
| **Veo 3/3.1**（Google） | 4K、原生音频、指令保真高、API（Vertex/Gemini） | 首选（质量） |
| **Kling 3.0**（快手） | 动作真实性第一（Elo 第一）、复杂物理动作好 | 国内首选/备选 |
| **Wan 2.1/2.7**（阿里开源） | 开源、音画同步、动作真实 | 开源/本地候选 |
| Runway Gen-4.5 / Seedance 2.0 / Hailuo / Sora 2 | — | 备选 |

**工作流（2026 主流）**：GPT Image 2 / Nano Banana 生成静态关键帧 → 独立视频模型动画化（"静态关键帧 + 运动模型"模式，Veo/Claude 实测案例均如此）。

## 5. Director Agent / 分镜工具（编排层，范式 A/C）
- **CineGen**（AI Director：脚本→分镜→角色设计→视频合成）
- **open-director**（开源：一句话→brief→story→storyboard→voiceover→images→BGM；角色/场景 T2I，分镜帧 I2I 保参考）→ 结构参照
- **storyboard-director**（Codex skill：脚本→逐镜线稿→HTML 审阅→聚合视频 prompt）
- **ComfyUI-Novel-Director**（LLM JSON 脚本 → 音画对齐/角色一致/批量/后期合并）
- **Cutscene Agent**（论文 2604.25318：MCP+director 3D 过场 + CutsceneBench）→ 3D 进阶参照
- **studiomi300**（Director Agent + 6 镜头分镜 + 配乐/配音）

## 6. 引擎内过场（范式 B，MVP 重点）
- Godot AnimationPlayer 时间轴：镜头（Camera2D/3D 轨迹）+ 角色（表情/口型切换）+ 语音播放
- 2D：P1 立绘分层 → Live2D/Umamo 绑定（表情/口型参数）或 Spine 骨骼
- 3D：模型 blendshape + 骨骼动画（引擎内调）
- 台词来自 P3 Agent 或预写剧本（先预写，Agent 驱动后置）
- 输出：Godot 过场场景（可播放/可导出）

## 7. 里程碑与验收（gate）
| 里程碑 | 内容 | 验收 |
|---|---|---|
| M2-1 | 剧本（Ink）→ Director Agent 拆镜头 JSON | 镜头列表可审阅（HTML 预览） |
| M2-2 | GPT Image 2 角色设定 + Nano Banana Pro 场景/分镜 | 角色跨镜头一致（肉眼） |
| M2-3 | 范式 B：Godot 时间轴过场（2 镜头：表情+运镜+语音） | 可播放过场 demo |
| M2-4 | 范式 A POC：关键帧 → Veo/Kling 图生视频 1 条 | 10s 视频 demo |
| M2-5 | 配音（TTS 多后端）+ 合成 | 完整过场 demo + 成本记录 |

**MVP 收敛**：先做 M2-1→M2-3（范式 B，引擎内），M2-4（范式 A POC）作为展示，不做 M2-5 配乐（后置）。

## 8. 依赖与前置
- P1：角色立绘（分层）+ 语音（台词 TTS）
- P3（可选）：Agent 驱动的动态台词（先预写剧本）
- 云 key：GPT（gpt-image）/ Gemini（Nano Banana）/ 视频模型（Veo 走 Vertex 或 Kling 国内）进 .env
