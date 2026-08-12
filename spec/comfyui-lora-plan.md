# ComfyUI + LoRA 画风锁死规划 + 生图参考 API 调研（spec/comfyui-lora-plan.md）

> 日期：2026-08-13 ｜ 状态：规划（待用户确认后实施）
> 目标：彻底解决"画风不落地"——云 API 只能"接近"，要 100% 锁死画风用本地 ComfyUI + 风格 LoRA / IP-Adapter。

## 0. 生图参考 API 调研结论（已读官方文档 + 中转站实测）
**OpenAI 官方（developers.openai.com / api/docs/guides/image-generation）**：
- `client.images.edit(model="gpt-image-2", image=[f1, f2, ...], prompt=...)` —— **image 参数支持多张参考图（数组）**，官方示例用 4 张参考图生成新图（gift basket）。
- `input_fidelity`：gpt-image-2 **不可调**（自动按高保真处理所有输入图）→ 直接省略该参数。
- mask 要求：与编辑图同尺寸同格式、<50MB、必须含 alpha 通道。
- Responses API：支持多轮编辑 + File ID 输入（中转站未验证，本项目走 Image API）。

**中转站实测（api.sisct2.xyz / gpt-image-2）**：
- ✅ `images.edit(image=[阿米娅_1.png, 阿米娅_2.png])` 多图引用**可用**（64.8s，产出 1.9MB PNG）→ `assets/demo/style_compare/multi_ref_style_test.png`；已在 chibi 生成中实测 2× 方舟 chibi 参考画风迁移（char_ailin_chibi/full.png 成功）
- ✅ mask + background=transparent 可用（v7 起一直用）
- 结论：**云 API 轨道可升级为"多张同画师参考图做风格迁移"**（1-3 张同画师作品），比单图更接近锁死。

## 1. 方案选择（两条轨道）
| 轨道 | 画风锁定度 | 成本/门槛 | 用途 |
|---|---|---|---|
| A. 云 API 多参考（本轮已打通） | 中（接近，靠 prompt+参考） | 每次 ~¥1-2 / 图 | 快速概念、迭代、无本地 GPU 时 |
| B. 本地 ComfyUI + 风格 LoRA（推荐最终） | 高（100% 锁死同画师画风） | 一次训练成本 + 8GB GPU | 生产资产、批量角色同画风 |

## 2. ComfyUI + LoRA 规划（轨道 B）
### 2.1 环境（本机已核）
- GPU：RTX 4060 8GB ｜ 系统：Windows ｜ 已装：uv venv 3.11、Godot 4.7.1
- 可跑：SDXL（含 InstantID / IP-Adapter / LoRA）；FLUX 需量化；PuLID-Flux 需租机
- 需装：ComfyUI 本体 + 模型（SDXL 或 Illustrious/NoobAI 系 2D 大模型）+ ControlNet（可选 OpenPose）+ ComfyUI_IPAdapter_plus + Krita/PS 辅助

### 2.2 风格 LoRA 训练流程（目标：唯@W 明日方舟画风 或用户选定画风）
1. **数据**：收集目标画师同画风图 20-40 张（如阿米娅全套立绘/皮肤，已抓 14 张 + 可再抓同画师其他干员）→ 裁切成统一尺寸（1024²）+ 打标（WD14 tagger）
2. **训练**：kohya_ss / sd-scripts 训 **style LoRA**（dim 16-32，lr 1e-4，20-40 epochs，8GB 可训 1024）
3. **工作流**：SDXL checkpoint + 风格 LoRA +（可选）InstantID/IP-Adapter 锁定角色 + ControlNet OpenPose 锁定姿态 → 批量出同画风立绘/表情/小人
4. **验证**：与参考图对比（画风相似度人工 + 可复用 v8 的"脸区均差/肤色占比"自检）

### 2.3 角色一致性（在画风锁死之上）
- 角色 LoRA（同角色 10-20 张多角度图训练）或 InstantID/IP-Adapter FaceID（单图即可）
- 顺序：先风格 LoRA（画风）→ 再角色锚点（InstantID 或角色 LoRA）→ 姿态/表情（ControlNet/prompt）

### 2.4 落地步骤（待用户确认后执行）
- [ ] P0 装 ComfyUI + SDXL/Illustrious + IP-Adapter（验证 8GB 可跑）
- [ ] P1 采集/清洗目标画师数据集 20-40 张 → 训风格 LoRA
- [ ] P2 工作流：风格 LoRA + 角色锚点 → 立绘/表情/小人批量生成 → 与 v9 对比
- [ ] P3 沉淀为 harness skill（SKILL_character-gen 升级：本地管线接入 gen-portrait）

## 3. 与现有管线的衔接
- `gen-portrait.py --style-ref a,b,c`（已支持多张）→ 云 API 快速轨道
- 本地轨道：gen-portrait 增加 `--backend comfy`（调 ComfyUI API）或独立 ComfyUI 工作流脚本
- 画风确定后：立绘/表情/小人全部统一该画风（见 spec/2d-in-game-assets.md）

