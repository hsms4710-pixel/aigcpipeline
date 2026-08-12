# SKILL：语音克隆与台词 TTS（P1）

## 触发
P1 台词语音生成、参考音克隆。

## 流程
1. 校验参考音（5-10s 干声，无 BGM）
2. GPT-SoVITS 零样本克隆（首选）→ 台词逐句 TTS → WAV + txt 字幕
3. 语速/情绪按人设卡调整；无参考音 → 预设音色库
4. metadata 记录：模型/参数/耗时/成本
5. 人工确认音色一致 → 落盘 assets/<character_id>/voice/

## 选型
- 首选 GPT-SoVITS；备选 CosyVoice（流式/情感）、F5-TTS（快/MIT）
- 保留 TTS 后端抽象，可切换
