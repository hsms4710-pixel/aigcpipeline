# SKILL：语音克隆与台词 TTS（P1）

## 触发
P1 台词语音生成、参考音克隆、TTS 后端切换。

## 流程
1. 校验参考音（5-10s 干声，无 BGM）
2. **TTS 多后端抽象**（tools/tts/ 接口）：
   - 生产后端（云 API）：火山引擎 / Azure / ElevenLabs（按区域/质量/成本）
   - 本地/离线后端：CosyVoice（首选开源）/ F5-TTS
   - GPT-SoVITS 仅研究/特殊音色，不默认
3. 台词逐句 TTS → WAV + txt 字幕；语速/情绪按人设卡
4. metadata 记录：后端/模型/参数/耗时/成本
5. 人工确认音色一致 → 落盘 assets/<character_id>/voice/

## 选型基线
见 spec/TECH-STACK.md（云 API + CosyVoice 优先）
