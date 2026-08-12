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