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
