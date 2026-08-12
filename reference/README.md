# 调研引用（reference/）

> 按 part 分组。完整调研结论见根目录《工作流设计.md》《研究计划.md》+ `spec/TECH-STACK.md`（选型基线）。
> 此处存链接速查；标注【主流】的为工业证据。

## 选型基线证据（TECH-STACK.md）
- ComfyUI 生产：Ubisoft CHORD 开源（blog.comfy.org）、Series Entertainment 10万+资产（blog.comfy.org）
- 一致性方案对比：【主流】apatero.com/blog/pulid-vs-instantid-vs-ipadapter-faceid-comparison-2025（InstantID 2025-12 首选）
- TTS 选型：【主流】火山引擎开发者文章（2026-05）、msnao 开源 TTS 对比
- 3D 生成：【主流】2026 3D 生成技术演进（生产级网格/水密/PBR/UV，Hunyuan3D/TRELLIS/Tripo 开源拐点）
- 2D 动画：【主流】Spine（行业标准）+ Live2D（VTuber/二次元互动标配）对比
- 引擎采用：【主流】GMTK 2025（Unity 64%/Godot 20%/UE 11%）、JetBrains State of Game Dev 2025

## P1 形象（云生图，2026 格局）
- **Nano Banana 系**：Gemini 2.5 Flash Image（GA）/ Pro（Gemini 3 Pro Image，4K）/ 2（3.1 Flash Image）；ComfyUI 节点（ComfyUI_Gemini / comfyui-nano-banana）；$0.039-0.24/张
- **GPT Image 2**：角色一致性 2026 榜断层第一；2K/4K；~$0.04/张
- **Qwen-Image**（阿里，Apache 2.0，可本地、中文强）
- 实测对比：chatimg.ai 7 模型对比、xsctbench、CSDN IP 漫剧实测

## P1 形象
- ComfyUI（工业主流执行引擎）
- InstantID / PuLID / IP-Adapter FaceID / PhotoMaker（身份保持，主流）
- LoRA 训练（角色/风格锁定，按需）
- CharForge（社区，仅研究参考）：https://github.com/RishiDesai/CharForge
- 3D 候选（后置，主流）：Hunyuan3D 2.1（腾讯）/ TRELLIS（微软）/ Tripo API / Meshy；~~TripoSR~~（过时）

## 声音集训练 TTS（V1）
- GPT-SoVITS（微调 1-5min，中文最强，RVC-Boss/GPT-SoVITS）+ SLFork 分支（1min few-shot）
- CosyVoice 2（阿里，零样本+微调+情绪）、Spark-TTS（有 genshin 角色微调先例）、Qwen3-TTS（2026，neural codec 12Hz）、XTTS-v2（Coqui）
- 数据集工具：zh-tts-mini-corpus（预选文本+录音 → GPT-SoVITS/CosyVoice 结构）
- 教程：从视觉小说游戏提取配音微调角色 TTS（developer.baidu.com）；RVC-Project WebUI（2.3.260718）

## P1 语音
- 云 API（生产后端，主流）：火山引擎 TTS / Azure TTS / ElevenLabs / MiniMax
- 开源（本地）：CosyVoice（阿里，工业级）/ F5-TTS（MIT）；GPT-SoVITS（社区，仅研究）
- TTS 评测：MOS-N / S-MOS / UTMOS / SIM / WER-CER

## P1 形态 / 虚拟人栈（UI 参考）
- AITuberKit：https://docs.aituberkit.com/zh/ ｜ prometheus-avatar ｜ aituber-onair ｜ handcrafted-persona-engine
- 2D 动画（主流）：Live2D Cubism / Spine

## 动画化（NPC/游戏内，工业）
- **intern-learn 实践**：ue_lyra_kb animation 系列（UE5 动画蓝图 UAnimInstance/状态机、IK FABRIK、Motion Matching、Control Rig、程序化动画 Warping/PoseDriver/FullBodyIK、动画通知/性能优化）——工业 AAA 引擎内动画系统范式
- **AI 生成动画（工业落地）**：腾讯 VISVISE（GDC2026：3D 动画生成+自动绑骨+自动蒙皮+MIB 中间帧）、腾讯《异人之下》（实时 AI 过渡动画，UE）
- 2D 动画：Live2D/Spine（表情/口型/骨骼，二次元标配）
- 结论：NPC 动画化走引擎内动画系统；AIGC 视频（Veo/Kling/Wan）只用于过场播片

## P2 过场
- 范式 A 视频生成（2026）：Veo 3/3.1（Google，4K/原生音频/API）、Kling 3.0（快手，动作真实性第一）、Wan 2.1/2.7（阿里开源，音画同步）、Runway Gen-4.5、Seedance 2.0、Sora 2
  - 对比：wavespeed.ai/blog/zh-CN/posts/ai-video-generation-models-2026、elser.ai 2026 评测（Kling 3.0 与 Wan 2.1 动作真实性并列第一）
- 范式 A 关键帧→图生视频（2026 主流）：GPT Image 2 生成首尾关键帧 → Veo/Kling 动画化（dev.to savielyamani_videoai）
- Director Agent / 分镜：CineGen（HF MCP-1st-Birthday/CineGen）、open-director（GitHub seme-org）、storyboard-director（GitHub kevinchin12）、ComfyUI-Novel-Director（GitHub Work-Fisher）
- 工业实践：腾讯 VISVISE（GDC2026 全栈 AI 动画/绑骨/蒙皮/MIB）、腾讯《异人之下》实时 AI 过渡动画（UE）、Tripo+Topview+Seedance 2 过场流程、MJ 静态资产+引擎 Sequencer 实机过场

- 叙事脚本（shipped games，主流）：Ink（Disco Elysium/80 Days）、Yarn Spinner（Night in the Woods/A Short Hike）
- Cutscene Agent（论文 2604.25318 + CutsceneBench）：https://huggingface.co/papers/2604.25318
- studiomi300：https://github.com/bladedevoff/studiomi300

## P3 Agent
- 商业/工业实践（架构基准）：NVIDIA ACE（米哈游/网易/腾讯/育碧采用）、Inworld（Mecha Break/Second Me）、Convai、网易《逆水寒》AI NPC、腾讯《元梦之星》AI 伴玩
- 记忆框架（主流）：Letta(MemGPT) / Mem0 / Zep / Cognee；综述 Agent_Memory_Techniques（https://github.com/NirDiamant/Agent_Memory_Techniques）
- AI-NPC：https://github.com/EchoSingh/AI-NPC ｜ ai-character-engine：https://github.com/Luciferjimmy/ai-character-engine ｜ MindFox：https://github.com/kikyujin/MindFox ｜ Gemma4NPC-it（HF）｜ Narra

## P4 引擎
- Godot：noko（https://github.com/nthnn/noko）、godot-AI-Dialog、OpenGameAgent、openagentic-sdk-gdscript、Player2 AI NPC
- 现有游戏 Mod：StardewLivingNPCs（https://github.com/Nyx-Amanises/StardewLivingNPCs）、ValleyTalk（https://github.com/dandm1/ValleyTalk）、stardew-llm-dialog、SentientValley（NexusMods 41526）、Thrall（Valheim thunderstore）、Sigrid（BepInEx+HarmonyX）
- 中间件/商业：Oxyde（https://github.com/oxyde-labs/oxyde）、Inworld、Charisma、ego AI、NVIDIA ACE、Convai Modding

## 评测（后置参考，不实现）
- Orak（Krafton 12 游戏基准）/ M3-BENCH / FAIRGAMER / FlashAdventure
- CharacterBench（AAAI2025）/ RoleplayEval / ViStoryBench / HEART-BENCH / persona fidelity（ACL2025）
- 资源占用：Enriching Gameworlds With LLM NPCs

## Key 接入 / MCP（OpenClaw 方式）
- OpenClaw 配置：config.toml [model_providers.XXX]（base_url / api: openai-completions|anthropic-messages / wire_api）；docs.openclaw.ai + github.com/openclaw/openclaw
- MCP：OpenClaw 作为 MCP 客户端注册表（openclaw mcp add/list/show/doctor；mcp.servers；stdio/SSE/Streamable HTTP）；docs.openclaw.ai/cli/mcp
- 我们的落地：env/key-access.md + env/config.toml（不入库）

## 无限画布
- tldraw（开源 SDK）：tldraw.dev ｜ Cowart（tldraw+Codex AI 改图）：36kr 报道 ｜ tldraw-sandbox（画布+AI 终端）：github acoyfellow ｜ @xpert-ai/plugin-canvas（画布+Agent workspace）

## 二次元 GPT-SoVITS（V1 生态）
- 崩铁/原神/崩三/绝区零/蔚蓝档案 全角色 GPT-SoVITS 模型分享（B站 BV1FqsKegEHv、BV1GJ4m1e7x2 等）；整合包+AutoDL/Colab 教程；情感分类训练
- 开源：github RVC-Boss/GPT-SoVITS；SLFork 分支（1min few-shot）