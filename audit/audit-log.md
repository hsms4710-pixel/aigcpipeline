# 审计日志（audit/audit-log.md）

## 2026-08-12 —— Part 0 地基
- **范围**：仓库骨架 / rule / spec 占位 / harness / task 拆解 / 审计机制
- **结果**：✅ 通过（地基自审）
- **说明**：P1 已拆出 t1-t7 可执行任务（含验收）；P3/P4/P2 为草稿；P5 明确后置不拆解
- **fixes**：无
- **下一步**：P1 开发（t1 工具链验证 → t2 schema → ...）

---

> 后续审计按此格式追加。清单见 audit/AUDIT.md。

## 2026-08-12 —— 选型主流性审计（专项）
- **范围**：P1-P4 全部技术选型对照工业主流（ComfyUI/InstantID/TTS 云 API+CosyVoice/Hunyuan3D/Ink-Yarn/记忆框架/引擎数据）
- **结果**：⚠️ 4 处非主流已修正（详见 spec/TECH-STACK.md 基线）
  - 生图编排：自研 CLI → **ComfyUI**（Ubisoft/Series 生产验证）
  - 角色一致性：CharForge → **InstantID/PuLID/IP-Adapter**
  - TTS：GPT-SoVITS 默认 → **云 API（火山/Azure/ElevenLabs）+ CosyVoice 多后端**
  - 3D：TripoSR → **Hunyuan3D 2.1/TRELLIS/Tripo API/Meshy**
- **新增**：`spec/TECH-STACK.md` 选型基线 + 原则 P9（工业主流优先，防"为省事选非主流"）
- **fixes**：t1/t3/t4/t5、SKILL_character-gen/voice-clone/workbench-web、P2/P3/P4 spec、reference 全部同步更新
- **下一步**：P1 开发（t1 按新基线验证 ComfyUI+InstantID+TTS 多后端）

## 2026-08-12 —— 表情方案修正 + 环境核查（专项）
- **范围**：2D/3D 表情技术路径 + 本机环境能力
- **结论**：
  - 2D 表情：修正为 Live2D Cubism（免费版商用门槛<1000万日元）+ **Umamo（开源 rigging，drop-in）** 绑定，参数化表情/口型
  - 3D 表情：修正为**引擎原生 Blend Shapes/Morph Target**（Godot/Unity/UE 内调权重），不需要 AIGC 生成表情图
  - 环境：本机 RTX 4060 8GB / RAM 15.2GB / C 盘 285GB / uv 3.11 可用 / 无 ffmpeg·ComfyUI·Godot / 代理未启动
- **能力矩阵**：本机可跑 SDXL+InstantID+LoRA+GPT-SoVITS/CosyVoice；FLUX 需量化、PuLID-Flux/Hunyuan3D 需租机或 API
- **产物**：`reference/env-report-2026-08-12.md`；t1 按 8GB 约束重写（含本机/API/租机决策清单）
- **fixes**：TECH-STACK / P1 spec / SKILL_character-gen 同步更新
- **下一步**：t1 前置（启动 Clash → uv 3.11 venv → CUDA torch → ffmpeg → ComfyUI+InstantID）

## 2026-08-12 —— 生图选型调整 + P2 过场方案细化（专项）
- **生图**：用户决定 P1 生图先用 GPT Image 2 + Nano Banana（云 API），本地 ComfyUI（SDXL+InstantID）降为可选离线后端（开源自托管场景）
- **P2 过场**：重写 spec —— 三范式（A AIGC 视频 / B 引擎内 / C 混合），MVP 走 B 为主 + A 展示；管线：Ink → Director Agent 拆镜头 → GPT/Nano Banana 视觉资产 → Veo/Kling/Wan 动画化或 Godot 时间轴 → TTS 配音
- **更新**：TECH-STACK（生图行 + 视频生成行 + 过场编排行）、P1 spec、t1、ROADMAP、reference、tasks/p2
- **下一步**：P1 开发（t1 验证 GPT/Nano Banana + TTS 多后端）

## 2026-08-12 —— 优先级决策：过场动画后置，先做 NPC 生成（专项）
- **决策**：P2 过场整体后置；主链 = P1 形象+语音 → P3 Agent → P4 引擎接入（NPC 实体化+引擎内动画）
- **动画化工业实现**：两类——①游戏内角色动画=引擎内动画系统（UE5 AnimBP/Motion Matching/Control Rig，intern-learn Lyra 实践；本项目 Godot AnimationTree + Live2D/3D blendshape；AI 生成动画=腾讯 VISVISE/异人之下）②过场播片=AIGC 视频（Veo/Kling/Wan）
- **更新**：ROADMAP（主线章节）、P2 spec（§9 动画化工业实现 + 状态后置）、TECH-STACK（动画化行）、reference
- **下一步**：P1 开发（t1 验证 GPT/Nano Banana + TTS 多后端）

## 2026-08-12 —— 链路整理：Part 范围边界 + 分 Part 验证（专项）
- 产出 `链路总览.md`（根目录）：全链路一图流 + 每 Part 范围边界表（目标/输入/输出/做/不做/验证/gate/依赖/状态）+ 分 Part 验证策略 + 边界红线 8 条
- 边界关键：P1 不做 3D/引擎/Live2D 绑定；P3 不做游戏逻辑；P4 不做完整游戏；P2/P5 后置；云生图优先；资产中立；评测后置；一个 Part 一个 Part
- README/ROADMAP 已加引用
- **下一步**：Part 1（P1）开发，从 t1 工具链验证开始

## 2026-08-12 —— 执行环境定为本地隔离文件夹 + Key 申请清单（决策）
- 形态：**本地隔离文件夹** env/runtime/（uv venv 3.11 + portable 工具 + 模型缓存全在目录内），不装系统
- 生图云 API（GPT/Nano Banana）不占本地显存 → 本机 8GB 够 P1（工作台+TTS+音频）
- Key 申请链接写入 env/README.md + .env.example：OpenAI / Gemini(AI Studio 或 Vertex) / fal / OpenRouter / 火山 / Azure
- 更新：env/README、.env.example、env-report、t1、链路总览、ROADMAP
- **下一步**：等 key 就绪后跑 t1

## 2026-08-12 —— V1 语音管线独立（拆分实践）+ 声音集训练（专项）
- 决策：TTS 从 P1 拆为独立实践 **V1 语音管线**（零样本克隆 + 声音集训练定制 TTS + RVC 增强）
- 声音集训练主流：GPT-SoVITS 微调（1-5min，98%+ 相似度）/ CosyVoice2 / Spark-TTS / Qwen3-TTS / XTTS-v2；数据工具 zh-tts-mini-corpus；VN 提取配音微调教程
- 更新：链路总览（P1 拆形象 + V1 语音）、ROADMAP（Part 1 可并行）、spec/voice 新建、TECH-STACK、tasks/voice、reference
- 版权约束：仅用自有/授权声音集

## 2026-08-13 —— Key 接入（OpenClaw 方式）+ 无限画布 + GPT-SoVITS 主线（专项）
- **Key 接入**：按 OpenClaw config.toml 格式落地（env/config.toml：model_providers.OpenAI，中转站 api.sisct2.xyz/v1，wire_api=responses；model=gpt-5.5）；Tripo 试用 key 入 env/.env；**config.toml/.env 已加 .gitignore，不入库**；MCP 用 OpenClaw 集成（openclaw mcp / mcp.servers），复用 dcc-mcp，不自写（env/key-access.md）
- **无限画布**：新增 spec/canvas（tldraw 首选，角色板/分镜板/世界板 + 产物节点联动 + AI 批注后置）；TECH-STACK/链路总览/t5 同步
- **语音主线**：V1 语音确认 GPT-SoVITS 首选（国内二次元角色声音集生态成熟：崩铁/原神/崩三全角色模型+教程）
- **下一步**：P1 t1（GPT Image/Nano Banana 验证，key 已就位）+ V1 语音（GPT-SoVITS 声音集训练）

## 2026-08-13 —— t1 实跑：生图 + GPT-SoVITS 零样本克隆验证通过（执行）
- 环境：runtime venv（浅路径 C:\Users\26046\Desktop\inerview\runtime\.venv，py3.11+torch CPU）+ ffmpeg 9.0（winget）+ GPT-SoVITS（clone + v1 模型下载 hf-mirror）
- 生图 ✅：中转站 api.sisct2.xyz（gpt-image-2 列名；gpt-image-1 实测成功，1024px PNG）
- TTS ✅：GPT-SoVITS 零样本克隆（edge-tts 参考音 → 2.78s 台词 wav，CPU 5.7s）
- 坑已记录 knowledge：venv 路径/jieba_fast shim/torchaudio monkey-patch/TTS_Config custom/generator
- 待办：Nano Banana（Gemini key 用户未提供）、声音集微调（路线 B）、角色一致性对比

## 2026-08-13 —— 生图按场景测试框架落地（专项）
- 提示词模板体系：spec/p1/contracts/prompt-templates.md（分层 prompt + 风格锚点 + 视图/行为模板 + 参考图锚点 + 多轮调整 + 三次生成规则）
- t1 重写为按场景（像素三视图+行为帧 / 立绘+表情+转面）；新增 t8/t9/t10
- 样例：test_gpt-image-1.png + pixel_front_anchor.png（中转站 gpt-image）
- ⚠️ 外部依赖：中转站 gpt-image 503（responses-image 亦 503）→ 参考图锚点机制待中转站恢复/换渠道；纯 prompt 兜底
- 声音：用户决定暂缓；可选直接下载现成二次元角色 GPT-SoVITS 模型

## 2026-08-13 —— t2 完成 + 参考图机制确认
- t2 ✅：persona-schema.json v0（visual/style/assets/voice 对齐 prompt-templates）+ asset-package-spec.md + validate-persona.py + validate-asset-package.py（utf-8-sig 兼容 BOM）+ 示例 persona 通过校验
- 参考图：gpt-image-1 = responses-only；正确调用 = responses.create(input=[image, text])；中转站 gpt-image 后端 503 待恢复；gpt-4o/gpt-5.5 中转站 404
- 下一步：中转站恢复后跑场景 A/B（含参考图锚点）

## 2026-08-13 —— t3 提前执行：形象生成 CLI 代码框架完成
- tools/gen_prompt.py：persona + scene + view → 分层提示词（scene 优先；像素三视图/行为帧/立绘表情均验证）
- tools/gen-portrait.py：云生图 CLI（文生图 images.generate / 参考图锚点 responses；任务自动派生：pixel→front/side/back+行为帧，splash→立绘+表情；落盘资产包+metadata；dry-run 验证）
- 真实生成待中转站 gpt-image 恢复（503）
- 下一步：中转站恢复 → gen-portrait 实跑场景 A/B；或 t8 模板文件细化

## 2026-08-13 —— t5 工作台实现（后端+前端+无限画布）
- 后端：tools/workbench/app.py（FastAPI：角色创建/生成 job/SQLite 队列/静态资产）+ gen-portrait 子进程执行（中转站 503 时 job 记录失败可重试）
- 前端：web/（Vite + React + @tldraw/tldraw 无限画布）构建成功；侧栏上传/角色列表/资产树，画布区展示资产节点（+画布）
- 启动：start-workbench.cmd（uvicorn :8000）；浏览器 localhost:8000
- 验证：TestClient API 全通过 + GET / 返回前端
- 中转站仍 503（gpt-image 后端）；恢复后：工作台内生成自动跑通 + monitor 脚本可跑场景 A/B

## 2026-08-13 —— t8 完成 + t5 前端资源修复 + 中转站模型确认
- t8 ✅：contracts/prompt-templates/{pixel,splash}.json 模板文件（无 BOM）+ gen_prompt.py 读模板（--templates 覆盖 + 内置回退），像素三视图/立绘表情测试通过
- t5 ✅：角色资产改挂 /char-assets，前端 dist 由 mount / 兜底托管 → JS/CSS 200，页面完整可用
- 中转站模型：curl /v1/models = 唯一 gpt-image-2（生图后端确定；gpt-5.5 LLM 该 key 404）
- 待办：中转站 gpt-image 后端恢复 → 工作台/CLI 实跑场景 A/B

## 2026-08-13 —— 场景 A/B 纯 prompt 生成跑通（中转站恢复）
- 场景 A 像素：front/side/back + idle/walk/attack/hurt（7 张，assets/demo/char_ailin）校验通过
- 场景 B 立绘：主立绘 + 4 表情（5 张，assets/demo/char_ailin_splash）
- 纯 prompt（--no-ref）；参考图锚点后置为补充能力
- 生成资产不入库（.gitignore assets/demo/char_*/）；待用户审阅一致性后定 t9/t10 结论

## 2026-08-13 —— 一致性修复：参考图锚点启用（images.edit）
- 用户审阅 v1：hurt 画风不一致；场景 B 表情位置/画风漂移（纯 prompt 无锚点导致）
- 方案：中转站 responses 503 → 改用 images.edit（图生图）做锚点；seed 支持
- 重跑 v2：场景 A/B 全带锚点（assets/demo/char_ailin_v2、char_ailin_splash_v2）
- 待用户对比 v1/v2

## 2026-08-13 —— 表情连贯 + 透明背景（v3）+ 人设卡编辑器
- 表情方案：透明背景（background=transparent）+ mask edit（face_mask 生成脸部 mask，只编辑表情区域，构图不变）→ 二次元立绘表情切换工业做法
- v3 验证：全 RGBA 透明背景（full 68万+ 透明像素）；待用户审阅表情连贯性
- 人设卡编辑器：工作台前端 PersonaForm（名字/种族/职业/性格/视觉/装备/服饰/细节/风格类型/资产勾选）→ 生成 persona.json → 创建角色；build 成功
- 参考图锚点确认：images.edit（responses 仍 503）

## 2026-08-13 —— 表情拼图切分方案（v6）+ start-workbench.cmd 修复
- 表情：mask 忽略 + seed 不稳定 → 2x2 拼图切分（同一张图天然一致），v6 达标（透明背景+同批）
- start-workbench.cmd：修复 cd 层级 + 错误捕获 + 已验证 uvicorn health OK
- 待办：t6 Godot 导入验证（需装 Godot）、t7 审计
