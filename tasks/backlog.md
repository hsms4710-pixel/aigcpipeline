# Task Backlog（总表）

> 状态：todo / in_progress / done / blocked ｜ 一个 part 一个 part 推进

## Part 1 —— P1 形象+语音工作台（当前）
| Task | 内容 | 状态 |
|---|---|---|
| t1 | 工具链验证：生图（Flux/SDXL）+ TTS（GPT-SoVITS）跑通 | done（生图场景A/B全过；TTS 归入 t4 暂缓） |
| t2 | 人设卡 JSON Schema v0 + 资产包规范 | done |
| t3 | 形象生成子模块（立绘+表情差分）CLI | done |
| t4 | 语音克隆子模块 CLI | 暂缓（用户决定声音后置） |
| t5 | 工作台 Web（Job 队列 + 阶段状态机 + 预览/重试/下载） | done |
| t6 | 资产包导出 + Godot 最小工程导入验证 | done |
| t7 | P1 审计 + 归档 | done（2026-08-13） |
| t8 | 提示词模板实现（gen-prompt.py + 模板文件） | done |
| t9 | 场景 A 像素角色完整测试（三视图+行为帧+精灵表） | done |
| t10 | 场景 B 立绘完整测试（表情+转面） | done（v9） |
| t11 | Godot 角色展示链路（立绘+表情+小人，P4 M0） | done（2026-08-13） |

## Part 2 —— P3 Agent 服务（规划中，占位）
- 草稿：Agent 协议契约 / 沙盒对话 / 跨会话记忆 / 白名单动作 —— 见 tasks/p3/

## Part 3 —— P4 引擎接入（规划中，占位）
- 草稿：Godot 资产导入 / 对话接入 / 白名单执行器 / Mod POC —— 见 tasks/p4/

## Part 4 —— P2 过场（暂缓，占位）
- 草稿：程序化过场 demo —— 见 tasks/p2/

## Part 5 —— P5 评测（⏸️ 后置，不拆解）
- 明确：不拆 task、不实现。触发条件见 spec/p5-eval/spec.md




## 双管线推进阶段（2026-08-13，详见 tasks/pipeline/tasks.md）
| 阶段 | 内容 | 状态 |
|---|---|---|
| P1-A | 画风定稿 + 生图基线（三件套同画风） | todo |
| P1-B | 2D 资产拆层（→ Live2D 规范 PSD） | todo |
| P1-C | 2D 骨骼绑定（Spine/Live2D + 自动绑骨） | todo |
| P1-D | 2D 动画（基础动画 + AI 补帧） | todo |
| P1-E | 打包/引擎（图集 + Godot 导入） | todo |
| P2-3D | 3D 线（后置：生成→修正→绑骨→动作→引擎） | todo（后置） |

## M0 动画修复（2026-08-15）
| Task | 内容 | 状态 |
|---|---|---|
| M0-6 | split-spine-arm.py 上臂/前臂拆分 + slot 挂肘骨 + footwear 重绑 footTarget | done（arm_spine.zip + 门禁绿） |
| M0-7 | spine_player.gd 臂/脚感知 + 肘/膝/脚枢轴 top_center + FK 层级累积；stretchy-agent 方法论升级（肘驱动 attack / 膝弯 walk） | done（Godot 自检 + FK 验证过） |
| M0-8 | Godot 实机渲染 attack/walk 分帧 + 关节撕裂校验 | done（frames_arm/ 32/32 绿） |
| M0-9 | 膝枢轴 top_center + foot 独立驱动 + walk 膝弯方法论 | done（同 M0-7 落地） |
| M0-10 | LLM 重生成 attack/walk（需启动 StretchyStudio dev server + key） | todo（消除 W2/W3） |

## M0-11 黑帧修复 + 真实关节枢轴（2026-08-16）
| Task | 内容 | 状态 |
|---|---|---|
| M0-11a | frames_arm 纯黑修复（slot 名取图 + 深灰底） | done（数值验证非黑） |
| M0-11b | 真实关节枢轴 `_pivots`（肩=手臂根端、肘=前臂附着点、膝/踝=内容 top）写入拆分→lite→播放器 | done（9/10 关节命中内容，撕裂 32/32 绿） |
| M0-11c | 骨骼叠加截图 overlay_arm/ + Godot 主场景实机启动 | done |
| M0-11d | 视觉 key 测试：中转站不支持图片（502），已记录证据 | done（改用叠加图+数值校验） |
| M0-12 | 调研 2D 骨骼自动化/像素小人 → spec/2d-skeletal-auto-research.md | done |
| M0-13 | LLM 重生成动画（需 StretchyStudio dev server）+ weighted mesh（ASMR 实践） | todo |

## chibi_apose 单图自动骨骼生成（2026-08-16）
| Task | 内容 | 状态 |
|---|---|---|
| c1 | 验证新 vision key（gpt-5.5/5.6-sol 支持图片；gpt-5.4 不支持） | done |
| c2 | 视觉定位原小人"不连续"根因（源图层级复杂/遮挡） | done |
| c3 | gpt-image-2 生成 A-pose 可绑定像素小人（无遮挡） | done |
| c4 | build-spine-from-image.py 自动切分+建骨+枢轴+动画+zip | done（门禁绿） |
| c5 | Godot 自检/FK/实机启动 + 撕裂 32/32 | done |
| c6 | 视觉复查：颜色正常、连续无裂痕、骨骼无明显错位 | done |
| c7 | 微调膝/踝枢轴 + weighted mesh + LLM 重做动画 | todo（可选） |

## 断裂/反人类/连续帧（2026-08-16 续）
| Task | 内容 | 状态 |
|---|---|---|
| d1 | 工业调研：断裂(圆角/重叠/两段式/蒙皮)、反人类(视频驱动/规范关键帧/正面局限)、连续帧(视频→序列帧主流) | done |
| d2 | 全量视觉审查：4 个动画逐帧 gpt-5.5（断裂已消、动作不自然定位） | done |
| d3 | 修骨骼关键帧（walk 摆臂/attack 蓄力转体/idle 呼吸/hurt 受击）门禁+撕裂绿 | done |
| d4 | 连续帧路线实测：gpt-image 参考锚点生成 walk 4 姿态（gpt-5.5 验证一致/自然）→ 对齐 → Godot AnimatedSprite2D + GIF | done |
| d5 | idle/attack/hurt 关键帧化 + 视频模型(即梦/Sora2/豆包)序列帧 + 蒙皮权重 | todo |

## 风格探索（2026-08-16）
| Task | 内容 | 状态 |
|---|---|---|
| s1 | 8 种风格批次生成（4 小人 + 4 立绘），A-pose 身份锚点 + 点名风格词 | done（style_batch/） |
| s2 | gpt-5.5 审查：小人推荐 chibi_flat（易拆层）；立绘推荐 splash_arknights（商业感） | done |
| s3 | 选定风格后：重绘角色+关键帧 → build-spine/帧动画 → Godot | todo（待用户选） |

## 锚点定稿+变体（2026-08-17）
| Task | 内容 | 状态 |
|---|---|---|
| v1 | 用户选定 v9 立绘 + chibi_v4 小人为锚点 | done |
| v2 | gpt-5.5 提取两锚点风格特征 | done |
| v3 | 各 4 种变体生成+审查（立绘：bright/warm 推荐；小人：pixel_hard/soft 推荐） | done |
| v4 | 按选定变体重绘源图→建骨/帧动画→Godot | todo（待用户选） |
