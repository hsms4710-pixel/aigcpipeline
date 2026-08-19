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

## 2026-08-13 云 API 画风迁移判定失败（最终结论）
- 尝试：v8/v9/style_attempts(a/b/c)/attempt_d(风格签名+精选参考) 共 8 次，画风均无变化
- 结论：**中转站 gpt-image-2 的 images.edit 不具备风格迁移能力**（每次重绘回自身默认动漫风），云 API 轨道画风无法落地
- 决策：**P1-A 画风锁定 = ComfyUI + 风格 LoRA / IP-Adapter**（工业解法）；云 API 仅用于快速概念/非风格敏感资产

## 2026-08-13 社区方法调研（gpt-image-2 云 API 画风）
- 结论：云 API 单图/双图 style-ref 8 次失败 ≠ 方法已穷尽。社区有完整方法论可再试：
  1. 参考图"每张一个职责"按编号分工（Image1=风格基准 / Image2=面部上色 / Image3=构图），避免平均主义。
  2. 风格用"15 维反推签名"写（线稿/上色/阴影/HEX 调色板/光比/质感），不用抽象形容词。
  3. 编辑类请求必须 "Change only X + 保锁清单"（identity/pose/构图/光线/阴影/背景物逐项列出）。
  4. 角色一致性用 Hero Reference 策略 + 身份锁 + No-Beautify 条款 + 一次只改一个变量。
  5. 兜底不变：连续失败 → ComfyUI + 风格 LoRA / IP-Adapter（工业主流）。
- 待验证：中转站(api.sisct2.xyz) images.edit 是否真透传多图（image 数组）；Nano Banana 图生图风格迁移社区评价更高，可作备选。

## 2026-08-13 新方法实测结果
- ✅ 多参考图分工 + 风格签名 + 角色分离 + 压缩上传(1152px) → 云 API 画风迁移**首次成功产出**（gpt2_v10_styleSig.png，multi-ref 55.7s）。
- 相比旧方法（v7-v9/style_attempts a/b/c/d）的差异点：① 参考图按编号分工不再混用；② 风格写成"签名"（线稿/上色/HEX/光比）而非抽象词；③ 上传前压缩避免断连。
- 待用户目检是否真达到方舟画风；若达标 → 回填风格标杆库，A4 模板固化；若不达标 → 记录差异，仍按计划转 ComfyUI+风格LoRA。

## 2026-08-14 A5 反馈记录
- 用户目检 gpt2_v10_styleSig.png：**勉强达标**（方舟/唯@W 画风方向可用，但非完美）。
- 有效组合确认：多图分工（阿米娅_2 精英2立绘=风格锚点 + 阿米娅_1=细节）+ 风格签名 + 角色分离 → 可复现。
- v10/chibi_v3 全套已按此生成；后续微调方向（待用户反馈）：线稿粗细/上色饱和度/构图。

## 2026-08-14 chibi 一致性教训
- ❌ 多视图各自从零生成（纯文字）→ 画风/人物必漂。正确：风格参考图 + Hero Reference 编辑派生。
- ❌ chibi 用立绘做画风参考 → 比例/线稿不对。Q 版必须用 Q 版小人帧做风格锚点。
- ✅ build_chibi_pose_edit_prompt：Same character + 只换姿势 + 保锁清单，从 hero 编辑。
