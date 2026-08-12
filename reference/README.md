# 调研引用（reference/）

> 按 part 分组。完整调研结论见根目录《工作流设计.md》《研究计划.md》。此处只存链接速查。

## P1 形象
- CharForge（单参考图训角色 LoRA）：https://github.com/RishiDesai/CharForge
- Flux Kontext / RefControl（参考图+pose，身份保持）：HF thedeoxen/refcontrol-flux-kontext-reference-pose-lora
- PaCo-FLUX.1-dev LoRA（RL 一致性）：https://huggingface.co/X-GenGroup/PaCo-FLUX.1-dev-Lora
- pixel_art_characters_lora：HF milliyin/pixel_art_characters_lora_flux_nf4
- 3D 候选：TripoSR / TRELLIS（CVPR2025）/ Hunyuan3D / InstantMesh

## P1 语音
- GPT-SoVITS / CosyVoice（阿里）/ F5-TTS（MIT）/ Fish-Speech 对比
  - 综述：https://www.msnao.com/2025/07/15/7843.html
- TTS 评测：MOS-N / S-MOS / UTMOS / SIM / WER-CER

## P1 形态 / 虚拟人栈
- handcrafted-persona-engine / aituber-kit / AITuberKit：https://docs.aituberkit.com/zh/
- prometheus-avatar：https://github.com/myths-labs/prometheus-avatar
- aituber-onair：https://github.com/shinshin86/aituber-onair
- 3dModelGenerator（job 轮询参考）

## P2 过场
- Cutscene Agent（论文 2604.25318 + CutsceneBench）：https://huggingface.co/papers/2604.25318
- studiomi300：https://github.com/bladedevoff/studiomi300
- Dialogic / Yarn Spinner / Ink / Naninovel

## P3 Agent
- AI-NPC（personality/memory/quest）：https://github.com/EchoSingh/AI-NPC
- ai-character-engine（本地离线）：https://github.com/Luciferjimmy/ai-character-engine
- MemoryRepository_for_AI_NPC：https://github.com/Formyselfonly/MemoryRepository_for_AI_NPC
- MindFox（离线记忆中间件）：https://github.com/kikyujin/MindFox
- 记忆框架：Letta(MemGPT) / Mem0 / Zep(时间知识图谱) / Cognee
  - 综述：Agent_Memory_Techniques（https://github.com/NirDiamant/Agent_Memory_Techniques）
- Gemma4NPC-it（HF）
- Narra（引擎无关 server）：（GitHub）

## P4 引擎
- Godot：noko（https://github.com/nthnn/noko）、godot-AI-Dialog（https://github.com/krishsharma0413/godot-AI-Dialog）、OpenGameAgent、openagentic-sdk-gdscript、Player2 AI NPC
- 现有游戏 Mod：StardewLivingNPCs（https://github.com/Nyx-Amanises/StardewLivingNPCs）、ValleyTalk（https://github.com/dandm1/ValleyTalk）、stardew-llm-dialog、SentientValley（NexusMods 41526）、Thrall（Valheim thunderstore）、Sigrid（BepInEx+HarmonyX）
- 中间件/商业：Oxyde（https://github.com/oxyde-labs/oxyde）、Inworld、Charisma、ego AI、NVIDIA ACE、Convai Modding

## 评测（后置参考，不实现）
- Orak（Krafton 12 游戏基准）/ M3-BENCH / FAIRGAMER / FlashAdventure
- CharacterBench（AAAI2025）/ RoleplayEval / ViStoryBench / HEART-BENCH / persona fidelity（ACL2025）
- 资源占用：Enriching Gameworlds With LLM NPCs
