# knowledge-2026-08-13-生图实测
- gpt-image-2（中转站 api.sisct2.xyz）：images.generate / images.edit（支持 mask+background=transparent）；gpt-image-1/4o/5.5 生图不可用
- 表情拼图 2x2 不可靠（模型画成一张大图）→ 逐表情生成+人脸层合成
- 三视图同理：逐视图 side/back 编辑，再合成审阅图
- 画风：文字点名已知风格（Octopath Traveler / Arknights style）+ 固定风格模板 + 负向约束；参考图在 images.edit 中只是编辑提示
- 参考图数据源：FGO=atlasacademy API（api.atlasacademy.io/nice/NA/servant/<id>）；明日方舟=PRTS MediaWiki API（aiprefix=立绘_/头像_<干员>）；PRTS 无干员表情差分 PNG

## 中转站 TLS 兼容修复（2026-08-13，关键基建）
- 现象：OpenAI Python 客户端/requests 调用 api.sisct2.xyz 超时（SSL handshake timeout）或连接重置(10054)，但 curl(schannel) 正常。
- 根因：中转站只支持 **TLS 1.2**（TLS 1.3 ClientHello 会挂起），且证书链不完整（unable to get local issuer）。Python OpenSSL 默认 TLS1.2+1.3 → 挂起。
- 修复（已固化到 tools/image_backend.py）：
  - `_make_openai_client()`：构造 TLS1.2-only + 跳过证书校验的 httpx2.HTTPTransport，作为 OpenAI(http_client=...) 传入。
  - `_download()`：urllib + TLS1.2-only + 跳过校验下载图片 URL。
- 影响面：所有走 image_backend.gen_image 的脚本（gen-portrait.py / gen-style-compare.py / 工作台）均已覆盖。若其他脚本直接 new OpenAI(...)，需同样处理。
- 经验：遇到"curl 通、Python 不通"先测 TLS 版本；`ssl` 模块强制 minimum/maximum_version 排查。

## gpt-image-2 画风迁移实测（2026-08-13）
- 新方法（多参考图分工 + 风格签名 + 角色分离 + 压缩上传）**首次成功**：multi-ref 55.7s 产出 1024x1536。
- 关键操作：参考图压到 1152px 再上传（2048px/2.6MB 上传易被中转站断连）；Image1=风格锚点(阿米娅_2 精英2立绘)，Image2=同风格细节(阿米娅_1)。
- 输出：assets/demo/style_attempts/gpt2_v10_styleSig.png（画风是否达标需用户目检）。

## v10 + chibi_v3 生成（2026-08-14，A2 完成）
- char_ailin_v10：full + bust + exp_{happy,sad,angry,neutral}(人脸编辑+合成,自检通过) + turn_side/back + exp_sheet + v10_review_sheet
- char_ailin_chibi_v3：full/side/back + idle/walk/attack/hurt 7 张全成功
- 关键修复：runtime venv 需 numpy（表情自检 _face_metrics 依赖）；gen-portrait 已自动压缩参考图(prep_style_refs→1152px)
- 模板固化：contracts/prompt-templates/{splash,chibi,pixel}.json；build_style_prompt 升级为风格签名+多图分工+No-Beautify；build_exp_edit_prompt 升级为保锁清单版
- 待用户目检：v10_review_sheet.png / chibi_review_sheet.png

## chibi_v4 一致性重做（2026-08-14）
- 根因：chibi_v3 的 side/back/动作 6 张是纯文字从零生成（无风格参考图/无角色锚点）→ 画风漂移。
- v4 方案（Hero Reference）：① 风格参考改用方舟 Q 版小人帧（阿米娅-报童 Attack 帧，512→放大1024）而非立绘；② front 生成 2 张候选（front_a/front_b）；③ 其余 6 视图从 front_a 编辑派生（build_chibi_pose_edit_prompt：同角色只换姿势 + 保锁 identity/服装/配色/比例/画风）。
- 产出：assets/demo/char_ailin_chibi_v4/（front_a/b + side/back/idle/walk/attack/hurt + 审阅拼图）
- 待用户目检 chibi_v4_review_sheet.png；若 front_b 更好，可把 poses 从 front_b 重做。

- 2026-08-14 终版：用户选定 front_b 为 hero，6 poses 已从 front_b 派生（chibi_v4 全 8 图一致）。chibi 资产定稿。

## P1-B 拆层方案落定（2026-08-14）
- 选型：See-through（shitagaki-lab，SIGGRAPH 2026）：单张动漫立绘 → 最多 23 层语义分层 + 深度 → layered.psd（Live2D 可直接用）。
- 8GB 显存方案：inference_psd_quantized.py（NF4 量化，~8GB 峰值，1280 分辨率；可 --resolution 1024 进一步降）。
- 依赖：torch 2.8.0+cu128 + requirements.txt + requirements-inference-bnb.txt；quantized 模型首次运行自动从 HF 下载。
- 输入：char_ailin_v10/portrait/full.png（1024x1536 透明背景立绘）。
- 备选：ComfyUI + ComfyUI-See-through 插件（jtydhr88）；SAM2+PS 手工管线（更重）。

## P1-B 拆层完成（2026-08-14）
- 方案：See-through（SIGGRAPH2026）官方仓库 inference_psd_blockswap.py（bf16 + blockswap，8GB 显存）
- 环境坑：bnb NF4 在 Windows 需系统 CUDA Toolkit(cuBLAS)，本机未装 → 改用 blockswap bf16（torch 自带 cuBLAS）
- 产出：assets/demo/char_ailin_v10/layered/（18 层 PNG + depth 图 + char_ailin_v10_layered.psd 8.2MB + reconstruction）
- PSD 图层：body(back hair/topwear/objects/neck/legwear/footwear/bottomwear/handwear) + head(eyebrow/ears/face/nose/mouth/eyewhite/eyelash/irides/front hair/headwear)
- B4 校验：tools/validate-layered.py 通过（head depth 已知缺失）

## start-demo.cmd 闪退修复（2026-08-14）
- 根因：cmd `start` 的 `--path "%~dp0"` 结尾反斜杠导致路径解析失败 → Godot 启动即退。
- 修复：`cd /d "%~dp0"` + `--path "%cd%"`；全英文 bat + CRLF + 无 chcp 65001。
- 通用教训：bat 里 start 传路径避免结尾反斜杠；中文 bat 避免 chcp 65001 切代码页（GBK 文件被 UTF-8 读会乱码）。

## Godot demo 小人大小统一（2026-08-14）
- 问题：chibi 7 帧都是 1024²，但角色主体占画布比例不同（front_b 76% vs walk/attack/hurt 91-96%），切帧时"变大"。
- 修复：demo.gd `_fit_height()` 用 `Image.get_used_rect()`（非透明 bbox）动态缩放，所有帧角色主体显示高度统一 547px。
- 用户确认：小人大小一致 ✅
