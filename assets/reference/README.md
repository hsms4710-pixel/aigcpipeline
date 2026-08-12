# 参考图资产（assets/reference/）

> 用途：为生图一致性提供**同角色多形态 / 同画师多表情**的高清参考，避免闭门造车、避免混用画风。
> 获取方式全部走**官方数据源 / 页面 API**（不用爬虫硬撞、不抓模板示例页）。

## 源与方法（权威）
| 游戏 | 数据源 | 正确做法 |
|---|---|---|
| FGO | Atlas Academy DB（https://apps.atlasacademy.io/db/NA/servants → /servant/<id>/assets） | 页面背后的 API：`https://api.atlasacademy.io/nice/NA/servant/<id>` 一次拿到全部图档 URL；脚本 `tools/fetch_fgo_servant.py` |
| 明日方舟 | PRTS Wiki（https://prts.wiki/w/干员一览 → 干员页） | MediaWiki API：`action=query&list=allimages&aiprefix=立绘_<干员名>` / `头像_<干员名>` 列全部图档，`prop=imageinfo` 拿原图直链；脚本 `tools/fetch_prts_operator.py` |

> ⚠️ 之前犯过的错：只抓「模板页面（立绘差分/剧情立绘）」的示例图 → 不是干员的真实图档；FGO 只抓 1-2 张 → 不是全部阶段。
> 现在改为从「具体从者/干员页」取全套并分类命名。

## FGO 分类（2026-08-13 用户实测校正）
```
fgo/<Servant名>_<图鉴号>/
├─ 01_头像/           # faces：各阶段头像
├─ 02_立绘卡面_带背景/  # charaGraph：卡面立绘上下半(a@1/a@2, b@1/b@2) + full_a/full_b 合并完整立绘
├─ 03_侧边立绘_带背景/  # narrowFigure：窄版侧边立绘（实心背景，不是 chibi）
├─ 04_表情差分/        # charaFigure：用户实测为表情差分图
├─ 05_指令卡立绘/      # commands：FGO 指令卡立绘（不是 2D 小人）
├─ 06_无背景立绘/      # status：无背景立绘/状态图
├─ 07_2d小人模型/      # spriteModel：Modified Unity3D 模型 + 2048 贴图集 + manifest
└─ manifest.json
```

## 明日方舟（PRTS）说明
- `arknights/<干员名>/立绘/`：精英阶段 + 全部皮肤立绘（1024-2560px 原图）
- `arknights/<干员名>/头像/`：各形态头像
- ⚠️ **PRTS 干员页没有独立的"表情差分"PNG**（已三重验证：文件命名无「差分」、干员页 charinfo 查看器无差分 tab、wikitext 无差分模板）。
  干员的"表情/形态变化"体现在：不同形态立绘（精英/皮肤）+ 头像系列；剧情 NPC 的表情差分在 `Avg_*` 系列（`模板:立绘差分` 命名规则 `Avg_<type>_<name>_<n>.png`），不属于具体干员。
- 表情参考替代：FGO `04_表情差分`（同角色多表情）+ 本仓库 `assets/demo/char_ailin_splash_v7`（v7 生成的四表情集）。

## 使用建议（画风一致性）
1. **同画师同角色**为一组：明日方舟按「干员 + 皮肤」选参考（如阿米娅=唯@W），FGO 按「从者 + 图鉴号」选参考；不要跨画师混用。
2. 按意图区分：立绘展示（带背景完整卡面）/ 三视图 / 对话无边框立绘 / 表情差分。
3. 生图时用 `--style-ref <参考图>`（画风迁移：新角色同画风，不复制参考角色）。
