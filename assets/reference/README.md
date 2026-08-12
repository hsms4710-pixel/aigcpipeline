# 参考图资产（assets/reference/）

> 用途：为生图一致性提供**同角色多形态 / 同画师多表情**的高清参考，避免闭门造车、避免混用画风。
> 获取方式全部走**官方数据源 / 页面 API**（不用爬虫硬撞、不抓模板示例页）。

## 源与方法（权威）
| 游戏 | 数据源 | 正确做法 |
|---|---|---|
| FGO | Atlas Academy DB（https://apps.atlasacademy.io/db/NA/servants → /servant/<id>/assets） | 页面背后的 API：`https://api.atlasacademy.io/nice/NA/servant/<id>` 一次拿到全部图档 URL（faces 头像 / charaGraph 立绘上下半 / narrowFigure 小人 / charaFigure 战斗立绘 / commands / status），脚本 `tools/fetch_fgo_servant.py` |
| 明日方舟 | PRTS Wiki（https://prts.wiki/w/干员一览 → 干员页） | MediaWiki API：`action=query&list=allimages&aiprefix=立绘_<干员名>` / `头像_<干员名>` 列全部图档，`prop=imageinfo` 拿原图直链。文件命名规则见 `模板:立绘差分` / `模板:剧情立绘`（`立绘_<干员>_<精英/皮肤>.png`、`头像_<干员>_*.png`），脚本 `tools/fetch_prts_operator.py` |

> ⚠️ 之前犯过的错：只抓了「模板页面（立绘差分/剧情立绘）」上的示例图 → 不是干员的真实差分；FGO 只抓 1-2 张 → 不是全部阶段。现在改为从「具体从者/干员页」取全套并分类命名。

## 目录结构（规范）
```
reference/
├─ README.md
├─ fgo/                     # 按从者分文件夹（fetch_fgo_servant.py 输出）
│  └─ <Servant名>_<图鉴号>/
│     ├─ 01_face/        # 各阶段头像（表情/差分参考）
│     ├─ 02_stage_art/   # 立绘上下半 + full_<a/b>.png（上下合并完整立绘）
│     ├─ 03_chibi/       # 小人立绘
│     ├─ 04_figure/      # 战斗立绘
│     ├─ 05_commands/ 06_status/
│     └─ manifest.json
└─ arknights/                # 按干员分文件夹（fetch_prts_operator.py 输出）
   └─ <干员名>/
      ├─ 立绘/            # 精英阶段 + 全部皮肤立绘（高清 1024-2560px）
      ├─ 头像/            # 各形态头像
      └─ manifest.json
```

## 已抓取
- `fgo/BB Dubai_421/`：头像×4 + 立绘×4（合并为 full_a/full_b 两张完整立绘）+ 小人×4 + 战斗立绘×2 + 指令卡×3 + 状态×3
- `arknights/阿米娅/`：立绘×14（医疗/近卫/默认×精英与皮肤，1024-2560px）+ 头像×16（唯@W 原画）

## 使用建议（画风一致性）
1. **同画师同角色**为一组：明日方舟按「干员 + 皮肤」选参考，FGO 按「从者 + 图鉴号」选参考；不要跨画师混用。
2. 按意图区分：立绘展示（带背景完整卡面）/ 三视图 / 对话无边框立绘 / 表情差分（头像或立绘局部）。
3. 生图时用 `--style-ref <参考图>`（画风迁移：新角色同画风，不复制参考角色）。
