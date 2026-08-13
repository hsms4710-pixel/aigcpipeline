# lessons-learned（风格生图踩坑记录，harness/memory/style/lessons-learned.md）
> 每次不理想尝试记一条：现象 / 原因归类 / 规避动作。原因分类见 spec/style-reference-constraints.md §0。

## 2026-08-13 画风尝试不理想（v8/v9/style_attempts/compare_sheet）
| 尝试 | 现象 | 原因归类 | 规避动作 |
|---|---|---|---|
| v8/v9 --style-ref 单/双图 | 画风仍非方舟 | 参考图角色风格混合；跨题材迁移弱；无 style 通道 | 分离式参考（风格图+角色图）；风格点名；建标杆库 |
| style_attempts 2/3ref | 画风不落地 | 混用精英/皮肤（风格微差被平均）；"Do NOT copy"负向削弱 | 精选同画师同一时期；正向表述"保留风格换新角色" |
| compare_sheet 纯文字风格 | 风格不稳 | 抽象风格词 < 点名已知风格；无参考图 | 用 known_names（"Arknights official art style"）+ 参考图 |
| 阿米娅作为风格源 | 题材跨度大 | 阿米娅素淡写实 vs 艾琳奇幻精灵 | 题材相近的画风库（RPG/方舟）+ 明确只学技法 |

## 有效做法（positive 记录）
- 多图参考 images.edit 可用（中转站实测）；2 张同画师图比 1 张稳
- 表情/小人用"人脸层合成"保证身体 100% 一致（v7-v9 验证）
