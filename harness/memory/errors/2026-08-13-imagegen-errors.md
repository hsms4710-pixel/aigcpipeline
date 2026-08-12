# error-2026-08-13-表情neutral失真
- 现象：exp_neutral 严重失真；指标：脸区均差 45.7(正常12-14)、肤色占比 0.334(基底0.484)
- 根因：images.edit 每次全新重绘，neutral 抽到"坏样本"（脸部重绘成不同比例）
- 修复：人脸合成 + 质量自检（肤色占比<基底-0.08 或 均差>30 判定异常）→ 自动重试最多 3 次

# error-2026-08-13-参数错位
- 现象：gen-style-compare 报 No such file or directory（输出路径）
- 根因：gen_image(client, prompt, out) 把 client 当位置参数传入 → prompt/out/ref 全串位
- 教训：image_backend.gen_image 的 client 是第 8 个参数，必须关键字传（client=...）或直接不传（懒加载）
