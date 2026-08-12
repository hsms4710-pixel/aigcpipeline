# t4：语音克隆子模块 CLI

状态：todo ｜ 依赖：t1（选型）、t2（schema） ｜ 预估：2 天

## 目标
可复用的语音 CLI：参考音 + 台词 → WAV + 字幕 → 资产落盘 + metadata。

## 产出
- `tools/gen-voice.py`：输入 persona.json（lines + 参考音）→ 输出 voice/ 目录
- TTS 后端抽象（首选 GPT-SoVITS，可切换 CosyVoice/F5-TTS）

## 验收
- [ ] CLI 生成 3+ 段台词 WAV + 对应 txt 字幕
- [ ] 音色与参考一致（人工确认）
- [ ] metadata.json 记录模型/参数/耗时/成本
- [ ] ruff/black 通过
