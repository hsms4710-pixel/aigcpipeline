# 工具链验证记录（2026-08-13，P1 t1 第一部分）

## 生图链路 ✅
- 中转站：https://api.sisct2.xyz/v1（OpenAI 兼容，wire_api=responses），key 有效
- 支持模型（models.list）：**gpt-image-2**（仅列出 1 个）
- 实测：`gpt-image-1` 调用成功 → 1024x1024 PNG（2.07MB）
- 样例：env/runtime/logs/test_gpt-image-1.png
- 耗时：约 50s（含模型探测/生成/下载）｜ 成本：待核对中转站账单
- 结论：**生图云后端（GPT Image）已通**；gpt-image-1/2 均可用
- 待办：Nano Banana（需 Gemini key，用户未提供）；角色一致性对比（GPT Image 2 vs Nano Banana Pro）

## 环境
- runtime venv：Python 3.11.15（uv）+ openai 3.0.0 / python-dotenv / pillow / requests
- 代理：Clash 127.0.0.1:7897（google/hf-mirror 可达）
- ffmpeg：待装（portable 到 runtime/tools/）

## GPT-SoVITS 零样本克隆 ✅（2026-08-13）
- 模型：v1 系（s1bert25hz-2kh + s2G488k + s2D488k + cnhubert + chinese-roberta-wwm-ext-large），CPU 推理
- 参考音：edge-tts 合成中文（8.2s）→ ffmpeg 转 32k mono
- 台词：`我会在这个世界留下我的传说。` → 输出 32kHz 2.78s wav（tts_output_v1.wav）
- 推理耗时：约 5.7s（CPU，一句）｜ 首次加载模型 ~30s
- 环境坑（已解决）：
  - venv 路径过深 → torch 装到浅路径 C:\Users\26046\Desktop\inerview\runtime\.venv
  - jieba_fast 无 Windows wheel → shim 指向 jieba（jieba_fast/ + posseg.py）
  - torchaudio 2.11 需 torchcodec → monkey-patch torchaudio.load 用 librosa
  - TTS_Config 传 dict 且带 "custom" 键才生效（"v1" 字符串不生效）
  - run() 是 generator → next(tts.run(params)) 取 (sr, audio)
  - fast_langdetect 需缓存目录 + hf-mirror
- 结论：**GPT-SoVITS 本地零样本克隆链路通**；下一步路线 B 声音集微调（二次元角色声音集）
## 生图场景化测试（2026-08-13）
- 场景框架就绪：t1 重写（场景 A 像素三视图+行为帧 / 场景 B 立绘+表情+转面）、提示词模板（contracts/prompt-templates.md）、gen-assets.py、t8/t9/t10
- 已生成：test_gpt-image-1.png（1024px 立绘样例）、pixel_front_anchor.png（像素 front 锚点，501KB）
- ⚠️ 中转站状态：gpt-image 曾成功；后续 503 "No available compatible accounts"；responses-image（参考图锚点）也 503 → **外部服务不稳定，待恢复或换 fal/官方 key**
- 参考图锚点：openai 3.0 images.generate 无参考图参数；需 responses API（中转站暂 503）→ 锚点机制实现待定，纯 prompt + 风格锚点先兜底
- 待办：中转站恢复后跑完场景 A（side/back/行为帧）与场景 B；或用户提供更稳生图渠道
## 参考图机制确认（2026-08-13）
- **gpt-image-1 是 responses-only 模型**：chat.completions 返回 400 "not supported on Chat Completions endpoint"；images.generate 无参考图参数
- **参考图正确调用 = responses API**：
  client.responses.create(model="gpt-image-1", input=[{"type":"image","image_url":"data:image/png;base64,..."},{"type":"text","text":"..."}])
- 中转站状态：gpt-image 后端整体 503（images.generate 与 responses 都 "No available compatible accounts"）→ **待恢复**；gpt-4o/gpt-5.5 在中转站 LLM 组 404（模型名可能不同）
- 一旦恢复：用 test-ref.py（responses 带图）验证参考图锚点；与用户 CLI 传参考图方式一致
## 中转站模型清单（2026-08-13 curl /v1/models）
- 唯一模型：**gpt-image-2**（生图后端确定；gpt-image-1 亦兼容，曾成功）
- 无 Nano Banana / 其他生图模型（需 Gemini/fal key，用户暂缓）
- gpt-5.5（用户 config 里的 LLM）在中转站 404 → 该 key 是生图专用组，LLM 需另配
- 参考图锚点 = responses API（gpt-image-1/2 responses-only）
## 场景 A/B 生成成功（2026-08-13，中转站恢复）
- 中转站恢复（gpt-image-2，1024x1024；256 尺寸 400 不支持）
- 场景 A（像素，纯 prompt 无参考图）：front/side/back + idle/walk/attack/hurt 共 7 张，每张 50-100s，资产包校验通过（assets/demo/char_ailin）
- 场景 B（立绘）：主立绘 + happy/sad/angry/neutral 表情 5 张（assets/demo/char_ailin_splash）
- 纯 prompt 无参考图流程跑通（--no-ref）；参考图锚点（responses）作为后续补充能力
- 一致性观察：纯 prompt 三视图/行为帧需要肉眼确认（待用户看效果）
## 参考图锚点方案：images.edit（2026-08-13 确认）
- responses API 仍 503 → 改用 **images.edit**（中转站支持）：front/主立绘生成后，后续任务 image=锚点图 + prompt 编辑 → 保持角色
- seed 参数也支持（extra_body）
- v2 重跑：场景 A（char_ailin_v2）7 张 + 场景 B（char_ailin_splash_v2）5 张，全部带锚点
- 待用户对比 v1（纯 prompt）vs v2（锚点）一致性