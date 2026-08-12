# 技术选型基线（spec/TECH-STACK.md）—— 工业主流优先

> 目的：防止"为了省事/MVP 采用非主流"。本表是选型唯一依据，改动需记录 decision。
> 证据截至 2026-08（调研日期），每条标注来源类型：商业产品 / 大厂开源 / 主流开源 / 社区项目。

## 总原则
1. 首选 = 工业主流（商业产品、大厂开源、被 shipped games / 生产管线验证的开源）
2. 社区项目只作**研究参考**，不默认进主线；如必须用，标注理由 + 主流替代
3. MVP 可以"落在主流方案的一个子集上"，但不能"选一条非主流的旁路"

## 逐层选型
| 层 | 首选（工业主流） | 备选 | 明确不用 | 证据 |
|---|---|---|---|---|
| 生图编排 | **ComfyUI**（节点工作流） | 自研调用 | 纯自研 CLI | Ubisoft CHORD 开源 ComfyUI 节点；Series Entertainment 用 ComfyUI 生产 10 万+ 资产；游戏道具生成实证研究 |
| 云生图 API（质量/兜底） | **Google Nano Banana 系**（Gemini 2.5 Flash Image GA / Pro / 2；$0.039-0.24/张；**ComfyUI 原生节点**，工业常用于游戏买量/原画/概念） | **OpenAI gpt-image-1 / GPT Image 2**（角色一致性榜断层第一、2K/4K）；**Qwen-Image**（阿里开源 Apache2.0，可本地部署、中文强） | Banana.dev（非主流生图 API，仅可选 serverless 部署） | fal/OpenRouter/Vertex 聚合；GPT Image 2 角色一致性 2026 榜第一；Nano Banana Pro 4K 文字精确；Qwen-Image 国内可本地 |
| 角色一致性 | **InstantID**（首选）/ PuLID / IP-Adapter FaceID | 按需训练角色 LoRA | CharForge 当默认 | 2025-12 社区共识 InstantID 最佳平衡；PuLID 高质量慢；IP-Adapter 快低显存 |
| 风格锁定 | 角色 LoRA（按需训练） | 风格 LoRA | — | 大厂/工作室通用做法 |
| 2D 角色动画 | **Live2D Cubism**（免费版个人/小规模<1000万日元可商用）+ **Umamo**（开源 rigging，Cubism 的 drop-in）+ **Spine** | DragonBones（开源） | 只出静态表情 PNG（不够） | Live2D 二次元标配；Umamo 开源替代（GPLv3）；Spine 2D 骨骼行业标准 |
| TTS | **云 API：火山引擎（国内综合）/ Azure（延迟/免费）/ ElevenLabs（情感）**；**开源：CosyVoice（阿里，本地/离线）** | F5-TTS（快/MIT）、MiniMax、Fish-Speech | GPT-SoVITS 当生产默认 | 2026 TTS 选型评测：火山综合首选、Azure 低延迟、ElevenLabs 音质天花板；CosyVoice 大厂开源工业级 |
| 3D 表情 | **引擎原生 Blend Shapes / Morph Target**（Godot/Unity/UE 内调权重） | ARKit 46 blendshape 标准 | AIGC 生成表情图（不需要） | Unity SkinnedMeshRenderer.SetBlendShapeWeight；UE Morph Targets；Godot 支持 blend shapes |
| 3D 生成（后置） | **Hunyuan3D 2.1（腾讯开源）/ TRELLIS（微软）/ Tripo API / Meshy** | — | TripoSR（2024 旧模型） | 2025-2026 3D 生成报告：开源拐点=腾讯 Hunyuan3D + 微软 TRELLIS；生产级要求水密网格/PBR/UV |
| 对话/叙事脚本 | **Ink（Disco Elysium/80 Days）/ Yarn Spinner（Night in the Woods/A Short Hike）** | Dialogic（Godot 插件） | — | 均被 shipped games 使用；Ink 适合大规模分支，Yarn Spinner 适合中小 |
| Agent 记忆 | Letta / Mem0 / Zep / Cognee（开源主流）+ 自研分层 | MindFox（本地轻量） | — | 主流记忆框架对比（2026） |
| NPC 运行时参考 | Inworld / Convai / NVIDIA ACE（商业，米哈游/网易/腾讯/育碧采用） | 自研（研究用途） | — | NVIDIA ACE 采用列表；网易《逆水寒》AI NPC 落地；腾讯《元梦之星》AI 伴玩 |
| 任务队列（服务化） | Celery/Redis、Temporal | 轻量（SQLite+状态机，仅 MVP） | — | 生产 AIGC 服务标准做法；轻量仅作占位，接口需可替换 |
| DCC 资产加工 | **DCC-MCP（dcc-mcp-core，自研适配器）** 控制 Blender/Maya/Houdini/UE | Blender 官方 MCP / 社区 MCP | 人工 DCC 操作（不可自动化） | 已有 dcc-mcp-creator skill（intern-learn 664011）+ layout-forge dccBridge 经验 |
| Web 后端 | FastAPI（主流） | Streamlit（仅原型） | — | — |
| 引擎 | Godot（主实现，indie 2D 增长最快） | Unity / Unreal（作为导入目标） | 绑定单一引擎 | GMTK 2025：Unity 64% / Godot 20% / Unreal 11%；工业主导 Unity/Unreal，Godot 增长快且开源 |

## 证据链接
- ComfyUI 生产案例：Ubisoft CHORD（blog.comfy.org）、Series Entertainment（blog.comfy.org）
- 一致性方案对比：apatero.com/blog/pulid-vs-instantid-vs-ipadapter-faceid-comparison-2025
- TTS 对比：volcengine 开发者文章、msnao 开源 TTS 对比
- 3D 报告：3D 生成技术演进（生产级网格/水密/PBR）
- Live2D/Spine：2D 骨骼动画 2026 对比、二次元手游标配（bilibili 图形引擎实战）
- 引擎采用：GMTK 2025 / JetBrains State of Game Dev / Outlook Respawn



