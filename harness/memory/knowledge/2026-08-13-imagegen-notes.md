# knowledge-2026-08-13-生图实测
- gpt-image-2（中转站 api.sisct2.xyz）：images.generate / images.edit（支持 mask+background=transparent）；gpt-image-1/4o/5.5 生图不可用
- 表情拼图 2x2 不可靠（模型画成一张大图）→ 逐表情生成+人脸层合成
- 三视图同理：逐视图 side/back 编辑，再合成审阅图
- 画风：文字点名已知风格（Octopath Traveler / Arknights style）+ 固定风格模板 + 负向约束；参考图在 images.edit 中只是编辑提示
- 参考图数据源：FGO=atlasacademy API（api.atlasacademy.io/nice/NA/servant/<id>）；明日方舟=PRTS MediaWiki API（aiprefix=立绘_/头像_<干员>）；PRTS 无干员表情差分 PNG
