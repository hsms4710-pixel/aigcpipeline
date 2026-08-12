# 画风模仿调研（spec/style-research.md）—— 为什么 gpt-image 画风没落地 + 怎么模仿

> 日期：2026-08-13 ｜ 来源：OpenAI 官方 prompting guide、社区（Reddit/OpenAI 论坛/知乎/贴吧/B站/图站）、ComfyUI 开源生态
> 结论先行：**云 API 的 images.edit 不是真正的"风格迁移"，只是"按图编辑"** —— 模型默认会画回自己的主流动漫风。
> 要真正锁死画风，工业做法 = **IP-Adapter / 风格 LoRA（本地 ComfyUI）**，或把风格写进 prompt 的文字描述（只能"接近"）。

## 1. 为什么 --style-ref 没生效（实测结论）
1. `images.edit` 每次是**全新重绘**（v7 已实测：带 mask 也会整体重绘，body 像素一致率 1.5%），风格参考图只是一个"编辑提示"，不是严格约束。
2. 单图 edit 无法像 IP-Adapter 那样把"风格"和"内容"分离抽取；模型倾向于用自己的先验画风。
3. 我们之前的 prompt 偏"别复制参考角色"→ 模型连"别复制风格"也一起听了。

## 2. 社区/官方认可的 prompt 设计要点（可立即采用）
| 方法 | 来源 | 做法 |
|---|---|---|
| **文字风格命名** | OpenAI cookbook / 社区 | 直接点名已知风格："Octopath Traveler style"、"Arknights official art style"、"1960s French New Wave poster" —— 模型对已知风格名词响应最好 |
| **风格母版图** | oschina 批量法 | 先做一张"母版图"作为风格锚点，把它的 色调/光影/构图 写成固定 prompt 模板（固定部分=风格/色调/光影/氛围；可变部分=主体/场景） |
| **多参考图分工** | tudingai 5 图玩法 | 1 张风格基准 + 4 张同风格细节参考，各自明确角色（"主体来自 A，环境来自 B"）；⚠️ 中转站 images.edit 只支持 1 图，此路在云 API 受限 |
| **负向约束** | tudingai | prompt 末尾加"风格一致性优先，禁止创新风格"，能显著降低模型自作主张 |
| **精确风格词** | Social Media Examiner | 上传参考图让模型先"分析共同元素"，再把分析结果写进 prompt（风格反推） |
| **双参考分工** | AndreaMontini | 1 张结构参考 + 1 张风格/观感参考 |
| **头身比/构图** | cys-migration-skill | 画面主体先画头，调整头部位置/负空间可控制构图 |

## 3. 工业级风格锁死（推荐路线）
- **IP-Adapter**（ComfyUI_IPAdapter_plus，cubiq）：官方定位"think of it as a 1-image lora"，就是专门做风格/主体迁移的；style transfer 模式
- **StyleLoRA / 风格 LoRA**：用目标画师作品（如唯@W 的明日方舟图）训练风格 LoRA，配合 SDXL/Illustrious 系 checkpoint → 画风 100% 锁定
- **StyleAligned / StyleWeaver**：多图风格一致（批量角色同画风）
- 本机 8GB 可跑 SDXL 系（含 IP-Adapter）；这是"画风问题"的真正解法，云 API 只能作为快速概念

## 4. 多画风实验（本次产出 assets/demo/style_compare/）
同一角色（艾琳）用 4 种文字风格 prompt 生成半身立绘：
- `hd2d.png`：HD-2D（八方旅人式：像素人物+现代光影）
- `anime2d.png`：高画质 2D（明日方舟官方风）
- `pixel.png`：像素立绘（16-bit RPG）
- `gacha2d.png`：高质量抽卡 2D（原神/方舟级）
- `compare_sheet.png`：四风格对比图 → **待用户目检，选定主画风方向**

## 5. 落地建议
1. 本轮先把 4 种画风给用户看，确定主画风（含 hd2d / 像素等备选）。
2. 若主画风 = 某游戏/画师风格 → 上**本地 ComfyUI + 风格 LoRA / IP-Adapter** 锁死（推荐，工业主流）。
3. 云 API 轨道：采用"风格母版图 + 固定风格 prompt 模板 + 负向约束"，作为快速概念/迭代。
