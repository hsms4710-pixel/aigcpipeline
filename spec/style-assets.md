# 生图风格资产规范（spec/style-assets.md）

> 日期：2026-08-19 ｜ 触发：用户「只看 aigc 目录下的文章，确立生图风格资产，确保地图、角色画风一致」
> 依据：reference/aigc-km/（2D-610881 LoRA 锁画风、2D-647418 一致性控制、2D-664211 白模统一绘制、GamePipeline-633036 标准化/参数化/自动化、AIGC-663960）
> 结论：**画风一致 = 所有资产生成共享同一「风格资产」**（像素规格 + 调色板 + STYLE prompt 块 + 锁定手段），角色与瓦片必须**同一风格资产原生生成**（禁止高清图事后 pixelize 冒充统一）。当前主风格 = 像素风（db32 调色板，宝可梦式地图）；备选 = HD-2D（H3）。

---

## 1. 风格资产定义（三类资产统一遵循）

### 1.1 风格基准（当前：像素风 PX-DB32）
| 维度 | 规范 |
|---|---|
| 风格 | 2D 像素艺术（SNES/RPG 俯视） |
| 像素规格 | 角色 64x64 / 瓦片 32x32 / 树 32x32（统一 32px 网格体系） |
| 调色板 | **db32**（所有资产同 palette，= 文章 LoRA 锁画风的等价物） |
| 渲染 | 硬边无抗锯齿、限制色阶、平坦光照、无文字无边框 |
| 锁定手段 | ai-pixel-art palette 量化（确定性）+ STYLE prompt 块 + 生成后端统一（gpt-image-2 中转站） |

### 1.2 STYLE 固定块（所有 prompt 共享，可拼装）
```
STYLE: 2D pixel art, top-down RPG overworld, flat shading, hard pixel edges,
limited palette, no anti-aliasing, no blur, no text, no watermark
PALETTE: db32
```
- 角色/瓦片/地图三类 prompt = 角色描述块（可变） + STYLE 块（固定） + PALETTE（固定）

### 1.3 锁定手段（对应 aigc 文章方法论）
| 手段 | aigc 依据 | 本项目落地 |
|---|---|---|
| 统一调色板量化 | 2D-610881 LoRA 固定像素画风 | ai-pixel-art `--palette db32`（确定性量化） |
| 统一 STYLE prompt | 2D-610881 元宝智能体规范提示词 | contracts/prompt-templates 共享 STYLE 块 |
| 统一生成后端 | 2D-610881 ComfyUI 自动化 | image_backend / aigc-toolkit（gpt-image-2） |
| 参考图锚定 | 2D-647418 一致性控制 | 风格基准图作 ref（vision gate 对比） |
| 白模统一绘制 | 2D-664211 全部件 AIGC | 角色统一从 A-pose 白模风格锚点生成 |
| 标准化/参数化 | GamePipeline-633036 Substance | contracts/ 资产 schema（规格/调色板/光照固定） |

## 2. 三类资产模板

### 2.1 角色 sprite（64x64 db32）
```
[角色描述：艾琳=银白高马尾+精灵耳+绿眼+深绿游侠服+披风+弓]
STYLE 块 + PALETTE db32 + 透明背景 + 全身 + 单方向视角
生成：ai-pixel-art generate_sprite（原生生成，禁止事后 pixelize 高清图）
```

### 2.2 瓦片 tileset（32x32 db32）
```
[地形类型：草/水/土/路/树]
STYLE 块 + PALETTE db32 + 无缝 tileable
生成：ai-pixel-art generate_tileset（--seamless edge_match，QA 门禁）
```

### 2.3 地图（32px 网格）
```
[布局规则：噪声湖岸/蜿蜒路/树簇]
瓦片 = 2.2 资产；角色 = 2.1 资产；统一 32px 网格体系
```

## 3. 画风一致性门禁（Vision Gate 扩展）
- 每类资产验收时**必带基准 ref**：`--ref 风格基准图（瓦片 db32 基准）`
- 验收 prompt 增加维度："与参考基准的画风一致性（像素规格/调色板/光照/边缘处理）"
- 阈值：风格一致性维度 >=7 才 PASS；角色/瓦片交叉对比（角色放瓦片旁）视为地图级一致性
- 落地：vision_gate.py 的 sprite/character/tileset 模板已含画风维度；加 --ref 基准图强制

## 4. 落实记录
- 2026-08-19：确立主风格 = 像素风 PX-DB32（瓦片已用 db32 生成）；**角色改用 ai-pixel-art 原生生成（db32）替代高清插画事后 pixelize**
- 遗留：高清插画版角色（char_ailin_chibi_8dir + char_pixel）降级为"非标准风格"参考；游戏内角色统一用 PX-DB32 原生资产

## 5. 关联
- reference/aigc-km/INDEX.md（方法论来源）
- contracts/prompt-templates/（prompt 模板，STYLE 块并入）
- spec/comfyui-lora-plan.md（风格 LoRA 升级路径：palette 量化 → 真 LoRA，进一步锁死画风）
- spec/agent-workflow.md（A2 资产生成：aigc-toolkit `--style` 注入 + 程序化 QA + A3 Vision Gate `--baseline` 画风一致性）
- 落实记录 2026-08-19：人物/单资产 Vision Gate 达标（sprite 7.0、动画 walk_gate overall 7.0 PASS，帧一致性 8 / 节奏 8）；地图布局 gate 4-6 FAIL，归入 W2.1 单独打磨

## 6. 风格资产版本对比（2026-08-19）

### 版本演变 vs 当前
| 维度 | 早期（GBA 像素风） | 当前 pokemon-nds-bw | 备选 hd2d-octopath |
|---|---|---|---|
| 参考系 | GBA Pokemon-style 泛化 | NDS era + Pokémon Black and White inspired（用户精确提示词） | Octopath Traveler + Square Enix HD-2D |
| 视角 | 俯视 top-down | isometric top-down | isometric + 3D diorama 微缩 |
| 调色板 | aap64 | 16-bit color palette | custom_cinematic（金色时刻/电影光） |
| 描边 | bold dark outline | clean pixel outlines | - |
| 场景模板 | 无/简单 | 5 个（town/route/battle/character/gym） | 6 个 + 调参 |
| 调参 | 无 | retro / hd_remake / ratio / text | tilt-shift / lighting / pixel / oil / night / japanese / ratio |

### 已落实 contracts/style-assets.json
- **pokemon-nds-bw**：用户提示词体系 → 精确参考系 + 16-bit + isometric + 5 场景模板（town/route/battle/character/gym）+ 调参 retro/hd_remake/ratio/text
- **hd2d-octopath**：八方旅人 HD-2D 备选（H3/H4）+ 6 场景模板（town/forest/battle/party/tavern/boss）+ 调参 miniature/lighting/pixel/oil/night/japanese/ratio
- **aigc-toolkit --style 注入**：所有资产生成统一走 pokemon-nds-bw 风格基底（style_block + palette 自动注入）
- 现状：人物/单资产画风已达 7-8 PASS；地图布局/可玩结构 4-6 FAIL 继续打磨（W2.1）
