# AIGC 参考知识库索引（reference/aigc-km/INDEX.md）

> 来源：用户提供 GitHub 仓库 hsms4710-pixel/personal-homepage 的 aigc 目录（KM 内部文档，31 篇原始文本已下载到 reference/aigc-km/）
> 用途：作为本项目（角色 AIGC → AI NPC → 引擎接入 + Agent workflow 中心）的外部实践参考库
> 整理：2026-08-19 ｜ 精读：31/31 篇（含重点精读 10 篇）

---

## 一、分类清单与项目映射

### 2D（6 篇）— 对应 A2/A5 环节
| 文件 | 主题 | 项目价值 |
|---|---|---|
| 2D-610881 | **我用AI做游戏：打造2D角色生成工作流**（腾讯元宝+ComfyUI） | ★★★ 2D 角色管线参照：LoRA 锁画风 + ControlNet 姿态 + LayerDiffuse 透明 + Mixamo 动作框架 + OpenPose 校准 |
| 2D-610814 | 基于高斯表示的多模态高质量 2D 角色驱动方法 | ★★ 角色驱动（高斯表示） |
| 2D-643656 | Spine 动画 UE 接入流程 | ★★ A 路线 Spine 引擎接入 |
| 2D-646653 | Cavalry——新兴 2D 动画神器 | ★ 2D 动画工具备选 |
| 2D-647418 | **如何用 Nano Banana Pro 做骨骼动态合成**（TapNow） | ★★★ 骨骼动态合成：火柴人关节拖拽→AI 合成，一致性控制 |
| 2D-664211 | **QQ秀：实时高还原度 Spine 引擎角色形象生成** | ★★★ A 路线关键参考：全部件 AIGC + 白模绘制 + AI 补全拆分（连体服/裙摆遮挡）+ 睁眼生成/闭眼拟合 + 10s/0.01 元 |

### 3D-excluded（4 篇）— 对应 3D 后置线
| 文件 | 主题 | 项目价值 |
|---|---|---|
| 3D-excluded-606112 | AI 动作生成实践分享 | ★★ 3D 动作生成 |
| 3D-excluded-650444 | 腾讯混元 Motion 1.0（10 亿参数 DiT 文生动作） | ★★★ 3D 动作：文生动作开源标杆 |
| 3D-excluded-654999 | AI 驱动 3D 骨骼动画穿模修复工作流 | ★★ 穿模修复方法论（3D 类比 2D 撕裂校验） |
| 3D-excluded-656845 | 长视频动作驱动生成全链路（骨骼驱动→特效合成） | ★★ 视频驱动动作 |

### AIGC 通用（5 篇）
| 文件 | 主题 | 项目价值 |
|---|---|---|
| AIGC-663960 | zimage-ncnn：文生图/LanPaint 修图/ControlNet 控图 | ★★ 本地生图+修图+控图 |
| AIGC-664216 | AIGC 自定义 3D 导航车标 | ★ 通用 |
| AIGC-665175 | 鹅妹上班记：AIGC 让品牌 IP 长出灵魂 | ★ 通用 |
| AIGC-665822 | AIGC 多模态内容检测能力全景 | ★★ 内容检测（与 agent eval 相关） |
| AIGC-667571 | 腾讯云 AIGC 场景化 DEMO | ★ 通用 |

### Agent（6 篇）— 对应项目中心 agent workflow / W5
| 文件 | 主题 | 项目价值 |
|---|---|---|
| Agent-666702 | Agent 智造局：多智能体协作重塑广告视频与图片生产 | ★★★ 多 agent 协作生产 |
| Agent-667356 | **TencentDB Agent Memory：团队记忆实践（任何错误只犯一次）** | ★★★ W5/记忆齿核心参照：四大资产（Chat Memory/Wiki/CodeGraph/Skill）+ Memory Pack 分层装配 + 渐进式暴露 + 治理优先；SWE-bench 60%→80%、难任务 38%→62%、成本 -66% |
| Agent-667430 | **基于 TextGrad 的 Agent 调优思路** | ★★★ W5 调优齿：文本梯度（反向传播→自然语言反馈），Backward 产反馈/Optimizer 产新版分离；中间态归因+双变量决策树（改 Prompt vs KB）+Mini-batch+Momentum；0 分率 25.7%→3.8% |
| Agent-667527 | **Harness 的边界：工程里暂时很难驾驭的问题** | ★★★ 平衡视角：Harness 半衰期（约束随模型变强贬值）；高频收敛问题→Workflow、长尾低错成本→高自主 Agent、重 Harness 最不划算；值得投入=权限边界/成本控制/可观测性 |
| Agent-667634 | **DeepSeek Harness 拆解：一套能拼装的 Agent 运行时** | ★★★ 架构参照：Cordis 插件运行时 + 可逆副作用（Fiber/Effect/disposer，LIFO 逆转）+ 作用域隔离 + Agent Loop 可插拔钩子 + Preset Scope 链 |
| Agent-667656 | **评测→记忆→落地→控制：Agent 自进化飞轮** | ★★★ W5 评测/反馈闭环核心参照：四齿飞轮、进化瓶颈=环节衔接、评测可信度>系统复杂度 |

### ContentPipeline（3 篇）— 对应 W1 编排骨架 / 生产流水线
| 文件 | 主题 | 项目价值 |
|---|---|---|
| ContentPipeline-638591 | **热点中台智能专题 Agent** | ★★★ 多 Agent 分工（Query/RAG/规划/生成/验证 5 Agent）+ GraphRAG + 三层设计规范约束生成 + 质量门禁（置信度≥90% 才发布） |
| ContentPipeline-643967 | **QQ AI 有声小说智能生产管线** | ★★★ 生产流水线：四步 LLM Agent（角色提取/去重/对白标注/无名处理）+ RAG 别名 + Speech Token 缓存 + 投机解码（0.3 元/万字） |
| ContentPipeline-655477 | **AgentProxy：生产 Agent 调度框架的设计与演进** | ★★★ W1 工程实现参照：Redis 状态机+DrawFlow DAG+TTL KV 三层架构；四重故障防线；动态扩展 Agent；6 大需求 |

### GamePipeline（7 篇）— 对应游戏开发子路线
| 文件 | 主题 | 项目价值 |
|---|---|---|
| GamePipeline-633036 | 2025 GDOC：数字内容工业化下的美术资产生产挑战 | ★★★ 美术资产生产工业化（我们流水线的行业背景） |
| GamePipeline-657396 | 一个人+AI 上线手绘风 3D 塔防游戏 | ★★ 单人 AI 游戏实践 |
| GamePipeline-662185 | 狍子AI：从配置辅助到独立游戏开发助手 | ★★ AI 游戏开发助手 |
| GamePipeline-664041 | 游戏开发六大设计原则之开闭原则 | ★ 工程原则 |
| GamePipeline-665122 | 和平精英 AI+NPC 活人感塑造 | ★★★ P3 NPC Agent 参考 |
| GamePipeline-665329 | 2026 GDOC：设备端游戏 AI（NPU 实时推理） | ★★ 设备端 |
| GamePipeline-665530 | **MiniMax M3：AI 游戏开发与全面提效** | ★★★ 400B 开源 SOTA、1M 上下文、原生多模态、Godot 支持、AI in Game roleplay |

---

## 二、重点精读：10 篇落地启示

### 1) 2D-610881 我用 AI 做游戏：2D 角色生成工作流
- 失败路径：图生图（精度低、ControlNet 控制失效）
- 成功路径：**文生图 + LoRA（锁像素画风）+ ControlNet（稳姿态）+ LayerDiffuse（透明底）+ ComfyUI 自动化**
- 创新：**Mixamo 动画库做标准动作框架** + 智能体规范提示词 + **OpenPose 校准动作连续性**
- 对我们：8 向精灵/行动画借鉴"标准动作框架 + OpenPose 校准"；LayerDiffuse 替代 rembg 透明后处理；LoRA 锁画风（comfyui-lora-plan 印证）

### 2) 2D-664211 QQ秀 Spine 引擎角色生成（A 路线关键参考）
- **全部件 AIGC**：通用白模上绘制风格化角色 → **AI 补全拆分**（裙子遮挡的腿、肩膀衔接），解决连体服拆分
- 脸：只生成睁眼 + 算法拟合闭眼；**全脸定位拆分五官**（全脸图对拆分部件定位缩放）
- 全链路 10s / 0.01 元/次 / 日峰值 400 万次
- 对我们：A 路线 M0-1/M0-2（thigh/shin 拆分）采用"白模+AI 补全拆分"；表情差分简化（睁眼/闭眼拟合）

### 3) Agent-667356 TencentDB Agent Memory（W5/记忆齿核心参照）
- **协作带宽**：正确权限边界下可被理解的有效上下文；逻辑返工>缺上下文
- **三层 AI 组织架构**：上层治理（身份/权限/版本/审核）+ 中层任务现场 + 底层团队记忆底座
- **四大核心资产**：Chat Memory（为什么这样判断）+ Wiki（团队已知什么）+ **CodeGraph（改哪里影响什么）** + Skill（通常怎么做）
- **Memory Pack**：身份权限过滤 + 固定绑定（必需规则）+ 浮动召回（相关性检索）→ 精简资产包；**渐进式暴露**（先摘要后工具取细节）
- **治理优先**：像代码仓库一样管版本/权限/冲突/新鲜度/溯源/负反馈
- 效果：SWE-bench 60%→80%、Top50 难任务 38%→62%、成本 $807→$272
- 对我们：**项目底座知识 = 这套四资产**（尤其 CodeGraph 正是用户提到的 codegraph/handbook 路线）；agent workflow 的 A6 归档即"资产形成闭环"

### 4) Agent-667430 TextGrad Agent 调优（W5 调优齿）
- 文本梯度：Prompt/KB 视为变量，Judge 打分 → Backward 产自然语言反馈 → Optimizer 产新版本 → 验证集验收（变好保留/变差回滚）
- 关键：**Backward/Optimizer 分离**（可追溯）；**必须收集中间态**（refined_query/knowledge_content）归因"错在检索还是生成"；双变量归因决策树；四道人工闸门；Mini-batch+Momentum
- 效果：0 分率 25.7%→3.8%，1-2h/轮→20min/轮
- 对我们：W5 评测平台落地 = TextGrad 闭环 + 我们的 Vision Gate（Judge 角色）

### 5) Agent-667527 Harness 的边界（平衡视角，重要）
- **Harness 半衰期**：每条规则在补偿当前模型缺陷，模型变强后从"保护"变"枷锁"，腐化安静
- 双刃剑：托下限也压上限（加约束后 Agent 反而不如"乱翻"）
- 成功产品把力气花在"**给能力**"（开放探索/廉价反馈/自动上下文管理）而非"加约束"
- **反直觉推论**：高频收敛问题→Workflow（稳定可测）；长尾低错成本→高自主 Agent；**中间重 Harness 最不划算**
- 值得投入：权限边界、成本控制、可观测性（与模型能力无关）
- 对我们：agent workflow 设计准则——不过度 harness；Vision Gate/契约/门禁放在"边界+可观测"层；高频环节（如瓦片生成）workflow 化

### 6) Agent-667634 DeepSeek Harness 拆解（架构参照）
- Cordis 插件运行时：**一切皆插件**；**可逆副作用**（ctx.effect 注册副作用返回 disposer，卸载按 LIFO 逆转）→ 热插拔/失败回滚/级联清理（类比 React useEffect）
- 作用域隔离（Proxy 沿 Fiber 链向上找服务）；Agent Loop 可插拔（concludesTurn/粘性状态/turn-stopping 钩子/工具动态并发）
- 对我们：W1 编排骨架的工具/技能热插拔设计参照；skills 可逆装配

### 7) Agent-667656 Agent 自进化飞轮（W5 核心）
- **评测→记忆→落地→控制** 四齿飞轮；进化瓶颈=环节衔接（不是单点技术）
- 原则：**评测可信度 > 系统复杂度**；记忆核心是"从做过到记住到变好"
- 来源：Anthropic 递归自改进报告、Stanford CS329A、EvoAgentX
- 对我们：W5 agent eval 平台接自家 agent = 四齿飞轮落地；Vision Gate 已是我们"评测"齿

### 8) ContentPipeline-638591 智能专题 Agent（多 Agent 生产参照）
- **5 Agent 分工**：Query 生成/RAG 检索/专题规划/报告生成/数据验证，三阶段（信息补全→规划生成→质量验证）
- GraphRAG（事件图谱意图识别→多源定位→权威性+时效性聚合）；三层设计规范约束代码生成
- **质量门禁：事实溯源 + 置信度评分 ≥90% 才发布**
- 对我们：agent workflow 的 A1/A2/A3 分工模式 + "置信度门禁"思路（对应 Vision Gate）

### 9) ContentPipeline-643967 有声小说管线（TTS + 生产流水线）
- **四步 LLM Agent 工作流**：角色提取→角色入库去重→对白提取+情感标注→无名角色处理；RAG 解决角色别名
- 短句 TTS：Speech Token 缓存库（固定语气词直出）+ 重复感知采样（随机/top-p 动态切换）
- 投机解码（8 层草稿+24 层目标并行验证）+ vLLM PagedAttention → 1.4 倍提速、0.3 元/万字
- 对我们：P1 语音（GPT-SoVITS 已部署）+ 角色绑定 Agent 工作流（与 NPC 角色记忆相关）

### 10) ContentPipeline-655477 AgentProxy 生产调度框架（W1 工程实现参照）
- 三层架构：**任务队列层**（Redis ZSet：3 优先级×4 状态）+ **调度算法层**（三级动态配额防饿死）+ **工作流引擎层**（DrawFlow DAG，6 类节点）
- **四重故障防线**：失败重试/超时回收/实例重启孤儿检测/批量重置
- 动态扩展：运行时注册新 Agent 零部署；六大需求：可靠/高并发/优先级/可干预/可扩展/可观测
- 对我们：agent workflow 服务化（W5 后）现成架构模板；当前单会话编排用简化版（manifest + 分派规则）

---

## 三、如何使用
- 全文检索：`reference/aigc-km/*.txt`（每篇含标题/作者/AI摘要/正文）
- 按环节取用：A2/A5 → 2D 类；W1/W5 → ContentPipeline + Agent 类；3D → 3D-excluded；游戏子路线 → GamePipeline
- 精读入口：本文件"重点精读"10 篇已覆盖全部 31 篇的要点