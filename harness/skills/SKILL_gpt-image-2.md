# SKILL：gpt-image-2 生图（云 API 轨道）

> 版本：2026-08-13 ｜ 来源：linux.do(sallyn) / junyeo217/codex-gpt-image-2-skill / tudingai / aiskillstore / freestylefly awesome-gpt-image-2 / OpenAI 官方 image docs
> 用途：当用**中转站云 API（gpt-image-2）生图/改图**时，按本 skill 组织参考图与 prompt；画风锁死失败时的最终兜底是 ComfyUI + 风格 LoRA / IP-Adapter（见 spec/comfyui-lora-plan.md）。

## 0. 触发
- 调用 `tools/image_backend.py` / `gen_portrait` / 工作台生图，模型 = `gpt-image-2`
- 需要"按参考图画风"、"同一角色多张一致"、"只改表情/局部"等

## 1. 三条总原则（社区共识，来自 junyeo skill + tudingai 实测）
1. **参考图每张只承担一个职责**，prompt 里按编号明确分工（"Image 1 = 风格基准 / Image 2 = 面部上色参考 / Image 3 = 构图"）。堆 5 张互相打架的图 = 平均主义 = 谁都不像。
2. **Change only X + 保锁清单**：编辑类请求必须同时写"改什么"和"锁什么"（identity/pose/构图/光线方向/阴影/背景物/logo），抽象"preserve identity"单独出现会被无视。
3. **风格用"签名"写，不用形容词**：把参考图反推成可复现的视觉参数（线稿/上色/阴影/调色板 HEX/光比），而不是"同款画风、唯美、高级感"这种死词。

## 2. 参考图纪律
- 一组参考图必须**同一画师/同一系列**（本项目=唯@W 阿米娅系），严禁跨画师混用；色调 LUT 一致，别冷暖混放。
- 参考图 **≥1024px**、无压缩噪点、无水印、无 UI；低清图宁可不放。
- 角色信息与风格信息分离：风格参考尽量不含目标角色；必须用时显式声明"只学线稿/上色/渲染，忽略角色/姿势/服装"。
- 数量：**1-3 张最稳**；3 张对齐的参考 > 5 张互相干扰的参考。
- 给每张图分配角色：`Image 1 controls camera, crop, and background.` / `Image 2 is the style reference.`

## 3. 6 种参考图组合（tudingai，按需选用）
| 组合 | 参考图 | 适用 |
|---|---|---|
| ① 风格保持 | 1 风格基准 + 4 同风格细节 | 新主体走既有画风（本项目主场景） |
| ② 元素拼接 | 商品底图 + 场景 + 模特 | 把角色放进场景 |
| ③ 多角度一致 | 2-3 张同角色不同角度 | 三视图/转面 |
| ④ 构图锁定 | 1 构图骨架 + 3-4 风格补充 | 构图是硬约束 |
| ⑤ SKU 家族 | 4-5 张同系列 | 批量同画风 |
| ⑥ 色彩锁定 | 1 色彩基准 + 4 内容 | 只锁色调 |

## 4. 15 维风格反推（sallyn/linux.do）——把参考图变成可复现签名
给 LLM/自己看参考图，按以下 15 维输出自然语言描述，拼进 prompt：
**基础维度**：①画面风格 ②成分组成 ③构图方式 ④分镜类型 ⑤光影特质 ⑥色调与色彩 ⑦媒介与材质 ⑧情绪与氛围 ⑨渲染参数
**进阶维度**：⑩时代感与文化语境 ⑪空间逻辑与透视 ⑫信息密度与留白 ⑬动态状态(瞬时感) ⑭后期处理与数字痕迹 ⑮符号化特征

反推模板（可直接用）：
```
请作为顶级 AI 绘画提示词专家，分析这张参考图的视觉风格。
任务：提取并反推其艺术风格，生成一份通用 Prompt；必须剥离原图中的具体角色/姿势/服装，
只保留可复现的风格签名（线稿质量、上色方式、阴影技法、调色板 HEX、光比、质感、渲染完成度）。
按 15 维框架逐项输出，最后合成一段 80-150 词的"风格签名"。
```

### 本项目风格签名示例（唯@W / 明日方舟）
```
Arknights official art style (artist Wei@W style signature):
thin clean elegant lineart, soft painterly cel-shading with gentle gradients,
low-saturation muted warm-gray palette (#B8AD9E #6E6558 #F5F0E8), delicate fabric
and armor detail rendering, soft diffuse lighting, gentle highlight roll-off,
subtle film-like finish, semi-realistic proportions, no heavy outline, no CG plastic skin.
```

## 5. 编辑/风格迁移配方（junyeo edit-workflows + character-consistency）
### 5.1 风格迁移（把图2的风格套到图1上）
```
Preserve everything in Image 1 exactly — subject, pose, composition, and crop.
Apply only the color tone and grading style of Image 2 to Image 1.
Do not change Image 1's identity, geometry, or background objects.
```
注意：风格不能只写一个词（cinematic/moody），要写可见属性（色温/颗粒/对比/调色板）；参考图顺序必须与 prompt 句子一致。

### 5.2 只改表情（本项目表情差分场景）
```
Change only the facial expression to [happy/sad/angry/...]. Preserve exactly:
identity (same face shape, same eyes, same hairstyle and hair color, same skin tone),
pose and body geometry (same posture, same limb positions, same proportions),
camera angle, crop, and framing, lighting direction and shadow placement,
every background object, outfit, and colors.
Keep everything else in the image unchanged.
```

### 5.3 新角色套风格（本项目主场景：生成艾琳→方舟画风）
参考图组合：1 张风格基准(阿米娅_2 立绘) + 1 张面部上色细节(阿米娅头像)。
```
Image 1 is the art-style anchor: learn ONLY its lineart, coloring, shading,
painterly texture and finish. Image 2 is a face-coloring detail reference.
Draw a NEW original character in EXACTLY this art style: [角色描述 subject/outfit/
detail]。Full-body standing pose, facing viewer, clean simple background.
Do NOT copy the reference character's face, pose, or outfit.
Match the line weight, coloring/shading technique, level of detail and finish
exactly. Style consistency first; do not invent a new style.
[风格签名段] natural skin texture, no text, no watermark. AR 3:4
```

### 5.4 角色一致性（多张同角色）
- **Hero Reference 策略**：先出一张最高质量"英雄图"（3 视图或代表场景），之后每张都拿它当 input reference + 重复"身份锁"段落，而不是每张从零生成。
- **身份锁**（每张都要列，别只说 same character）：脸骨/下颌线、眼型与眼距、鼻梁、唇型、发型发色、肤色肤质、体型比例、特征点。
- **No-Beautify 条款**：`Do not replace the face with a generalized, beautified, or idealized face. Keep the exact bone structure, jawline, eye shape and spacing, and skin texture from the reference.`
- **一次只改一个变量**：姿势→角度→光线→服装，逐项改；同时改 5 个变量 → 失败无法归因。

## 6. 铁律（junyeo core-grammar 提炼）
- **不写否定句**：场景排除一律"改写成该有什么"（`no crowd`→`one person in frame, solo subject`）；唯一例外是文字渲染的白名单冻结句。
- **不用死词/舞台词**：美丽/高级/炫酷/award-winning/8k/ultra-detailed/masterpiece 全部禁掉；形容词→数值（HEX 调色板 3-5 色、色温 warm/3200K、光比 key:fill 1:2、留白 %）。
- **设备名→结果**：写 Canon R5 f1.4 无效，写"shallow depth of field, background falls off softly"。
- **尺寸只用 6 个白名单**：1024²、1024x1536、1536x1024、1792x1024、1024x1792、2048²；不写 auto。
- **1 张图 = 1 次调用**：不要 grid/矩阵塞多张（除非该类型本身是网格：三视图 sheet、对比图）。
- **透明背景不支持**：gpt-image-2 不支持 background transparent → 出图后单独抠图（本项目已有 rembg/SAM2 计划）。

## 7. 项目落地接线
- `tools/image_backend.py`：`gen_image(style_ref=[...])` 已支持多图（images.edit image 数组）；**先确认中转站是否真的透传多图**（实测为准）。
- `tools/gen_prompt.py`：`build_style_prompt` 需升级为"风格签名段 + 角色分工 + 保锁清单 + No-Beautify"结构（见 5.3），替换现有单段式 prompt。
- 失败判定/回填：达标图 → 回填 `reference/style-library/`；不达标 → 记 `harness/memory/style/lessons-learned.md`。
- 兜底：云 API 连续失败 → ComfyUI + 风格 LoRA/IP-Adapter（spec/comfyui-lora-plan.md），这是工业主流锁画风手段。

## 8. 来源
- junyeo217/codex-gpt-image-2-skill（SKILL.md / core-grammar / edit-workflows / character-consistency）：https://github.com/junyeo217/codex-gpt-image-2-skill
- linux.do sallyn：GPT-Image-2 绘图 Prompt 方法论与风格合集（15 维反推框架）：https://git.lyz.one/SidneyZhang/myWiki（articles/gpt-image2-prompt-collection.md）
- tudingai：5 张参考图 6 组合 + 3 翻车模式：https://tudingai.cn/blog/202604/gpt-image-2-5-reference-images-playbook/
- aiskillstore gpt-image-2（ChatGPT 订阅走 Codex CLI 生图，多参考合成）：https://github.com/aiskillstore/marketplace/blob/main/skills/agentspace-so/gpt-image-2/SKILL.md
- freestylefly/awesome-gpt-image-2（500+ 反推案例、工业模板库、style-library skill）：https://github.com/freestylefly/awesome-gpt-image-2


## 9. GPT-Image2-Skill 方法论接入（2026-08-21，wuyoscar/GPT-Image2-Skill）
> vendor：tools/vendor/GPT-Image2-Skill（skills/gpt-image/，含 SKILL.md / craft.md / openai-cookbook.md / gallery-*.md / generate.py）
> 原则：**不要盲目生成图片**——生成前按本 skill 的方法论组织提示词与参数。

### 9.1 提示词方法论（已注入 tools/prompt_vision.py 系统提示词）
1. 结构先行：`画布/长宽比/布局 → 背景/场景 → 主体 → 关键细节 → 约束`，并声明用途（sprite sheet/地图/tileset/UI）
2. 一个主角 + 配角（One hero, supporting cast）
3. 场景密度 > 形容词：5-12 个具体名词 + 2-4 个材质/光照约束；禁空形容词
4. 风格锚点具体且有边界（"Pokemon Black and White NDS sprite style"，不是"像素风"）
5. 材质 / 光照 / 调色板分开控制
6. 长宽比先行并在 prompt 里重申；引用文字加引号
7. 编辑类：先写目标变换，再显式保锁（identity/layout/位置不变）；多参考按编号分工（Image 1=…, Image 2=…）
8. 密集文字/图表/多面板/精灵表用 quality=high

### 9.2 参数语义（已接入 tools/image_backend.py + a2-pipeline.py）
- size：16px 倍数、总像素 **655k–8.3M**（下限约 1024x1024）；a2-pipeline 默认已由 512→1024x1024；`image_backend._check_size()` 对 <655k 告警
- quality：low=草稿 / medium=探索 / high=最终（本项目默认 high）
- 端点：generations（文生图）/ edits（参考图、多参考、mask 局部重绘 opaque=保留/transparent=重绘）
- gpt-image-2 不接受 input_fidelity
- 与 §6 铁律的差异：本 skill 说 gpt-image-2 的 background 为 auto/opaque（auto 可能带透明）；本项目实测中转站支持 `background="transparent"` 出透明底（walk sheet 已验证），透明底仍按需 + 必要时后处理抠图

### 9.3 参考画廊（按资产类型先查再写）
- gallery-pixel-art.md（像素画）｜ gallery-character-design.md（角色设定图）｜ gallery-isometric.md（等距地图/村庄）｜ gallery-gaming.md（游戏）｜ gallery-anime-and-manga.md（动漫）
