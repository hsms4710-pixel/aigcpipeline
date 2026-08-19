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

---

## 6. 新角色风格批次（2026-08-16，chibi_apose 银发精灵游侠）
> 触发：用户反馈帧动画连续性 OK 但风格与旧小人不同，要求尝试不同风格的小人与立绘。
> 方法：A-pose 源图为身份锚点 + 点名风格词（style-reference-constraints.md 的结论），gpt-image-2 生成 8 种风格 → gpt-5.5 视觉审查。

### 6.1 2D 小人（4 种）— assets/demo/style_batch/chibi_compare.png
| 风格 | gpt-5.5 点评 | 适用 |
|---|---|---|
| chibi_pixel16 | 非真像素（仍是插画式，缺硬边/限色阶） | 需按真实像素规格重绘才可作像素素材 |
| **chibi_flat** | **轮廓清晰、阴影简单、最易拆层，最适合 2D 骨骼动画** ⭐ | Spine/Live2D/帧动画小人 |
| chibi_anime | 二次元 Q 版精致，拆层成本略高 | 精致 Q 版 RPG/战斗小人 |
| chibi_hd2d | 高清 Q 版，细节密，动画成本最高 | 高清手游小人参考 |

### 6.2 2D 立绘（4 种）— assets/demo/style_batch/splash_compare.png
| 风格 | gpt-5.5 点评 | 适用 |
|---|---|---|
| **splash_arknights** | **成熟/商业感最强、上限最高，最适合游戏/抽卡立绘** ⭐ | 干员档案/抽卡展示/主推卡面 |
| splash_anime | 标准日系赛璐璐，清晰稳定 | 日系轻手游/养成 |
| splash_painterly | 半厚涂，亲民但冲击力弱 | 休闲 RPG/NPC/低星立绘 |
| splash_pastel | 粉彩绘本，幼化 | 儿童向/头像/表情 |

### 6.3 建议
- 游戏小人：选 **chibi_flat** 作为设计稿（可吸收 chibi_anime 的可爱细节），用 `build-spine-from-image.py` 建骨 + 关键帧生成动画。
- 游戏立绘：选 **splash_arknights**（或 splash_anime）作抽卡/展示立绘。
- 若要真像素：按 16/24/32 像素规格重绘，而不是把高分辨率图缩小。

---

## 7. 锚点定稿 + 变体批次（2026-08-17）
> 用户选定：**char_ailin_splash_v9 = 立绘锚点**，**char_ailin_chibi_v4 = 小人锚点**，并补充多种画风。
> 方法：gpt-5.5 提取两锚点风格特征 → 以锚点图为参考 + 变体 prompt，gpt-image-2 生成各 4 种变体 → gpt-5.5 审查。

### 7.1 锚点风格特征（gpt-5.5 提取）
- **splash_v9（立绘）**：细线/暗褐线稿、厚涂带赛璐璐、低饱和冷暗调（银白/深绿/黑褐/暗金灰）、单主光源细高光、二次元美型比例（修长）、暗色奇幻优雅游侠气质
- **chibi_v4（小人）**：细-中细线稿（墨绿/暗棕）、赛璐璐+轻柔渐变、低饱和冷暗（银白/墨绿/黑灰皮甲）、约 2.5 头身、插画感 sprite（非硬边像素）、冷静敏捷森林游侠气质

### 7.2 立绘变体（assets/demo/style_batch/v9_v4_variants/liping_compare.png）
| 变体 | gpt-5.5 | 适用 |
|---|---|---|
| **liping_bright** | 最醒目、缩略图辨识度最高、抽卡稀有感最强 ⭐ | 抽卡池封面/SSR 展示 |
| **liping_warm** | 黄昏暖光、商业感稳、角色突出 ⭐ | 角色详情页/通用主立绘 |
| liping_painterly | 艺术质感最好但辨识弱 | 角色档案/剧情 CG/设定集 |
| liping_cold | 氛围好但偏暗 | 冷调/夜战变体 |

### 7.3 小人变体（assets/demo/style_batch/v9_v4_variants/chibi_compare.png）
| 变体 | gpt-5.5 | 适用 |
|---|---|---|
| **chibi_pixel_hard** | 轮廓最干净、背景最干净、最易抠图/拆层动画 ⭐ | 游戏内小人/帧动画基础 |
| **chibi_soft** | 萌系、适合 Spine/Live2D 骨骼动画 ⭐ | 萌系骨骼动画/头像 |
| chibi_bright | 展示强但需去背景简化 | 明快童话风展示 |
| chibi_hd2d | 氛围最好但最不宜拆层 | 概念图/场景氛围 |

### 7.4 下一步（待用户选）
- 小人源图 = chibi_pixel_hard 或 chibi_soft（清透明底+简化发丝装饰）→ build-spine-from-image.py 建骨 → 关键帧动画 → Godot
- 立绘 = liping_bright 或 liping_warm → 作为展示/抽卡立绘


---

## 8. 透明背景定稿 + quality 对照（2026-08-17）
> 触发：用户要求「所有小人和立绘都无背景」，选定 hd2d + pixel_hard 两个小人方向；立绘参考
> yingtu.ai《GPT Image 2 噪点与纹理伪影排查清单》（quality=low/medium/high/auto；background 可 auto/transparent；PNG 默认输出）。
> 方法：`image_backend.py` 新增 `quality` 参数（默认不传=auto；最终资产用 high）；单变量对照（同 prompt/ref/size，仅改 quality）。

### 8.1 结论
1. **中转站（api.sisct2.xyz）接受 `quality=high` + `background=transparent` 组合**（实测 OK，每张 45-95s）。
2. **quality=high 明显优于默认档**（gpt-5.5 双图对照）：立绘 B(high) 细节更锐、材质/发丝/铠甲更清晰、轮廓更干净、更少糊边；默认档偏软偏糊。
3. **gpt-image-2 做不出真·硬边像素**（复现 §6.1 结论）：`pixel_hard` prompt 无论怎么加强仍是「像素风插画」（抗锯齿边缘+平滑渐变）。真像素必须**算法后处理**：透明 PNG → 裁剪包围盒（保纵横比）→ 降采样到 64/96px → 16 色 MEDIANCUT 量化（无抖动）→ 最近邻放大 1024 → **1:1 原生裁切通过 gpt-5.5 审查**。
4. 审查注意：透明底图叠**棋盘格**再交 gpt-5.5 审查（vision_review 会把透明压成 RGB 黑底，直接审查会误报"黑背景"）；像素图审查必须给 1:1 原生裁切（1024→640 下采样会糊掉像素边缘）。

### 8.2 资产（assets/demo/style_batch/transparent_v1/）
| 文件 | 内容 | 审查 |
|---|---|---|
| `chibi_hd2d_t.png` | 小人 HD-2D 透明底（A-pose 带弓） | PASS（隔离/身份/风格/肢体） |
| `chibi_pixel_hard_t.png` | 小人像素风透明底（gpt 原图，像素风插画） | 透明/身份 PASS；非真像素 |
| `chibi_pixel_hard_true_96px.png` | 真·像素 96px（算法后处理） | PASS（1:1 裁切：硬边/限色/可读） |
| `chibi_pixel_hard_true_64px.png` | 真·像素 64px | 同法生成 |
| `splash_v9_high_t.png` | 立绘 v9 透明底 quality=high ⭐ | PASS（质量对照胜出） |
| `splash_v9_default_t.png` | 立绘 v9 透明底 quality=default | PASS 可用（偏软） |
| `transparent_v1_overview.png` | 6 图总览（棋盘格预览） | 用户目检 |

### 8.3 下一步（待用户选）
- 小人定稿：`chibi_hd2d_t`（HD-2D）或 `chibi_pixel_hard_true_96px`（真像素）→ 走 `build-spine-from-image.py` 建骨/`build-frame-anim-godot.py` 帧动画；弓建议单独对象层（A-pose 无弓底图可再出）。
- 立绘定稿：`splash_v9_high_t` → 表情差分/三视图继续基于该透明底（face_mask 通道已支持透明）。
- 所有后续生图统一 `quality=high` + `transparent=True`（已在 `image_backend.gen_image` 提供 `quality` 参数）。


### 8.4 用户定稿（2026-08-17 第二轮）
- 用户选定「观感最好」的 4 个小人：`v9_v4_variants/chibi_hd2d.png`、`v9_v4_variants/chibi_pixel_hard.png`（原图）+ `transparent_v1/chibi_hd2d_t.png`、`transparent_v1/chibi_pixel_hard_t.png`（透明版）。
- 逐对对照审查（gpt-5.5，opaque vs transparent）：**两对均 PASS**——透明版是原图的「忠实且等优/更优」复制（同角色/同画风/更清晰的孤立 sprite）。
- **最终游戏资产 = 透明版**：`chibi_hd2d_t.png`（HD-2D）+ `chibi_pixel_hard_t.png`（像素风，gpt 原图）。**真·像素 96/64px 算法版不做主选**（用户偏好 gpt 像素风插画观感，保留作备选）。
- 透明版需入游戏时：`chibi_pixel_hard_t.png` 边缘较原图略柔（可接受，不破坏剪影）。
- 下一步候选：① 基于透明 hero 派生全套姿势（side/back/idle/walk/attack/hurt，参考 gen-chibi-v4.py 的 hero 编辑流程）；② `build-spine-from-image.py` 建骨 / 帧动画；③ 弓作独立对象层出 A-pose 无弓底图。


---

## 9. 对齐定稿 + 姿势/无弓/建骨动画（2026-08-17 第三轮）
> 触发：用户指出 transparent_v1 与 v9_v4_variants 原图"有些微不同"，要求**以两张原图为基准对齐**，
> 然后生成全套姿势、建骨、动画、无弓版。

### 9.1 对齐方法（关键结论）
- **images.edit 重绘必然漂移**（复现 §1.1）：`reproduce exactly + 透明背景` 的 prompt 仍会把角色重画成不同姿态/服装。**对齐不能靠重绘**。
- **正确做法 = matting（抠图），像素级忠实**：`rembg`（u2net / isnet-general-use，模型从 hf-mirror 下载）直接对原图抠背景，角色 100% 保持原样。
- 抠图后边缘有**暗色 fringe**：分析确认边缘像素颜色距背景 dist 4.8、距角色内部 36.8（61.5% 偏暗）——是**原图角色自身暗褐线稿 + 场景环境光**，属于原图真实观感（§7.1 风格特征），非污染。条件 defringe（仅替换"更接近背景色"的边缘像素）后保留角色本色边缘。
- mask 引导的 images.edit（角色区保护 + 只重绘背景为透明）虽透明干净，但**角色仍被重绘**（mask 保护不严格）→ 不可用作"对齐"。

### 9.2 对齐 hero（像素级 = 原图去背景）
| 文件 | 说明 |
|---|---|
| `transparent_v2/hero_hd2d_final.png` | chibi_hd2d 原图 matte + 条件 defringe（带弓正面） |
| `transparent_v2/hero_pixel_final.png` | chibi_pixel_hard 原图 matte + 条件 defringe |
| `transparent_v2/hero_hd2d_matted.png` 等 | matte 中间产物（u2net / isnet / maskedit / threshold） |

### 9.3 姿势 / 无弓（gpt-image-2 hero-edit，透明，quality=high）
- 12 姿势：`{hd2d,pixel}_pose_{idle,walk,attack,hurt,side,back}.png` — gpt-5.5 拼图审查**全部 PASS**（同角色/标签匹配/透明/无缺陷）。
- 无弓 A-pose：`hero_{hd2d,pixel}_nobow_apose.png` — 审查 PASS（无弓、A-pose、可建骨）。
- 对照拼图：`transparent_v2/_review/poses2_{hd2d,pixel}.jpg`、`nobow_{hd2d,pixel}.jpg`。

### 9.4 建骨 + 动画（现状）
- **几何自动建骨（build-spine-from-image.py）失败**：chibi 大头 + 平滑头肩过渡，neck/armpit 检测把整个角色当"脸"（head+body 混为 face 75% 高度）→ 复现此前"自动建骨质量差"结论。需更干净分离的 A-pose 或改用工业管线。
- **工业管线 = See-Through/LayerDiff3D 拆层 PSD → StretchyStudio(DWPose 自动绑骨) → Spine**：本地已装（see-through venv 有 CUDA RTX4060），但 LayerDiff3D 首次运行需从 HF 下载模型（huggingface.co 不通，需 HF_ENDPOINT=hf-mirror.com），运行慢（>7min）且被用户中断。**待用户决定是否恢复该管线。**
- **帧动画 demo（已交付）**：`assets/demo/godot-chibi-v2-demo/` — 新角色（hero + 6 姿势 + 无弓）接入 Godot 可玩 demo（沿用 godot-char-demo 模式，Sprite2D 切换 + bbox 高度归一），headless import + 运行 120 帧无错误。
