# 风格标杆库（reference/style-library/）

> 目的：给生图提供**已人工确认的同画师风格参考**（生图.md「风格标杆库 + 正反馈飞轮」机制）。
> 规则：
> 1. **一个文件夹 = 一个画师/一个画风系列**，严禁混画师（约束见 spec/style-reference-constraints.md）
> 2. 每库含 `manifest.json`：画师 / 来源 / style_desc / known_names（可点名的风格名）/ refs（精选图+角色）
> 3. manifest 用**相对路径**引用规范目录（reference/arknights、reference/fgo 等），不重复存图
> 4. 每次生图从库中选 **1-3 张** 作 `--style-ref`（角色锚点 `--ref` 与风格参考分开）

## 使用流程
- **出库**：读 manifest → 取 refs 前 1-3 张 → `gen-portrait.py --style-ref <图1>,<图2>`
- **入库**：新画师/系列 → 建文件夹 + 精选 3-8 张（高清/无水印/同画风/构图干净）→ 写 manifest
- **反馈（正反馈飞轮）**：审图通过 → 把该次参考图标记为高权重（manifest 加 `quality: high`）；不通过 → 记 `harness/memory/style/lessons-learned.md`（原因+调整）

## 现有库
- `阿米娅-唯@W/`：明日方舟官方画风（唯@W），5 张精选（默认/精二/皮肤/头像）
