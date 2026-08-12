# t4：语音克隆子模块（TTS 多后端）

状态：todo ｜ 依赖：t1（选型）、t2（schema） ｜ 预估：2-3 天

## 目标
可复用的语音模块：参考音 + 台词 → WAV + 字幕 → 落盘 + metadata；TTS 后端可切换。

## 产出
- `tools/gen-voice/`：
  - TTS 后端抽象（接口）：本地 CosyVoice / 云 API（火山、Azure）/ 研究用 GPT-SoVITS
  - CLI：输入 persona.json（lines + 参考音）→ 输出 voice/ 目录（WAV + txt）
- 配置：后端选择 + key（.env，不入库）

## 验收
- [ ] 至少两个后端各生成 3+ 段台词 WAV + txt 字幕（一个本地 + 一个云）
- [ ] 音色与参考一致（人工确认）
- [ ] metadata 记录后端/模型/参数/耗时/成本
- [ ] ruff/black 通过
