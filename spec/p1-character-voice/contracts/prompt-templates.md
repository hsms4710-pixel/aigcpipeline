# 角色生成提示词模板体系（spec/p1-character-voice/contracts/prompt-templates.md）

> 目标：**不靠一次 prompt 碰运气**。把「角色卡 → 提示词」做成可复用的分层模板 + 锚点机制 + 多轮调整工作流。
> 参考实践：ai-game-spritesheets（GPT Image 2 + 锚点图 + 方向表 + idle/attack 精灵表）、大厂立绘流程（线稿→配色→立绘→三视图→游戏内效果）、像素精灵工作流（基础角色→三视图→行为帧）、三次生成规则、循环工程。

## 1. 提示词分层结构（任何资产类型通用）
按顺序组织：**主体 → 装备 → 服饰 → 细节 → 风格锚点 → 视图/行为 → 输出约束**
```
{角色主体：性别/年龄/种族/体型}
{装备：主武器/副手}
{服饰：上衣/下装/披风/盔甲材质}
{细节：发型/发色/瞳色/面部特征/纹身/配饰}
{风格锚点：<见 §2>}
{视图/行为：<见 §4>}
{输出约束：<见 §5>}
```

## 2. 风格锚点（Style Anchor）—— 一致性关键
> 每次生成都要带上，**同一角色所有资产共用同一套风格锚点**（参考 ai-game-spritesheets 的 anchors）。

### 2.1 像素风（pixel）
```
pixel art, {8-bit|16-bit|32-bit} style, limited color palette, hard edges, no anti-aliasing,
grid-aligned pixels, sprite-sheet ready, transparent background
```
- 调色板：固定主色/辅色/描边色（如 `palette: #2d2d2d outline, #a4d65e main`）
- 分辨率档位：16×16 / 32×32 / 64×64（按游戏需求）

### 2.2 高清立绘（splash）
```
high-quality game splash art, {anime|semi-realistic|cel-shaded} style, clean lineart,
detailed rendering, cinematic lighting, vibrant colors
```
- 大厂流程锚点：线稿→配色→立绘（对应风格固定后不再变）

## 3. 角色卡 → 视觉描述映射（persona.json → prompt 主体段）
> 参考"角色设定到AI提示词的映射体系"：{阵营}的{职业}，{性格}性格，{地位}身份
```
示例 persona：
{ "name":"艾琳", "race":"精灵", "class":"游侠", "personality":["冷静","敏锐"], "style":"pixel",
  "equipment":"复合弓", "outfit":"绿色皮甲", "detail":"银白长发、翠绿瞳色" }
→ 主体段：
pixel art game character, female elf ranger, slender build, calm and sharp-witted,
green leather armor, composite bow, long silver hair, emerald eyes, [风格锚点], [视图/行为], [输出约束]
```

## 4. 视图/行为模板（按资产类型）

### 4.1 像素角色
| 视图/行为 | 模板片段 |
|---|---|
| 三视图 | `character sheet, front / side / back three views, same character, consistent design` |
| 方向表 | `directional sprite sheet, 4 directions (down/up/left/right), same character` |
| 待机/行走/攻击/受伤 | `animation frame, {idle|walk|attack|hurt}, single frame, consistent with reference` |
| 完整精灵表 | `sprite sheet, {N} frames of {action}, evenly spaced grid, same character` |

### 4.2 高清立绘
| 视图/行为 | 模板片段 |
|---|---|
| 主立绘 | `full-body splash art, standing pose, facing viewer` |
| 表情差分 | `same character, {happy|sad|angry|neutral} expression, head-and-shoulders closeup` |
| 转面/多视图 | `same character, three-quarter / side / back view, same outfit and colors` |
| 战斗/动作立绘 | `same character, {attacking|casting|hurt} pose, dynamic` |

## 5. 输出约束
```
{sprite: transparent background, no background, pixel-perfect, alpha channel}
{立绘: clean solid background or transparent, high resolution 1024x1024+}
{统一: same character, consistent design, no text/watermark}
```

## 6. 参考图锚点机制（一致性最强手段）
- **GPT Image 2 支持多参考图**（身份保持）：第一张图（如正面）作为锚点 → 后续所有视图/行为/表情都**带上锚点图 + 追加指令**（"same character as reference"）
- 流程：① 生成锚点图（front view）→ ② 用锚点图生成 side/back（转面）→ ③ 用锚点图生成各行为帧
- 这比纯 prompt 保持一致性稳定得多（参考 ai-game-spritesheets：South Anchor 是最重要的图）

## 7. 多轮调整工作流（不是一次性生成）
```
生成 → 审查（用户/画布批注：哪里不对）→ 调整 → 重新生成（循环）
```
- **三次生成规则**：同 prompt 生成 3 次选最优；3 次都不达标 → 改 prompt 再试，不无限重试
- 调整手段（按优先级）：
  1. 追加/修改局部描述（"把披风改成红色"）
  2. 换参考图锚点（更清晰的正面图）
  3. 改风格锚点参数（调色板/分辨率/风格词）
  4. 图生图编辑（GPT Image 编辑能力，局部修改）
- 每次调整记录：输入 prompt / 输出 / 反馈 → 沉淀到 `harness/memory/knowledge/prompt-engineering.md`

## 8. 模板存放与使用
- 模板文件：`contracts/prompt-templates/`（pixel.md / splash.md 具体模板 JSON/YAML）
- 工具：`tools/gen-prompt.py`（persona.json + 资产类型 + 视图 → 提示词），供 CLI/工作台调用
- 工作台：用户在画布/表单上选"资产类型 + 视图 + 反馈" → 自动组 prompt → 生成 → 展示 → 可再次调整
