# SKILL：语音克隆与台词 TTS（P1，含 RVC 音色）

## 触发
P1 台词语音生成、参考音克隆、RVC 音色转换、TTS 后端切换。

## 流程
1. 校验参考音（5-10s 干声，无 BGM）
2. **TTS 多后端抽象**（tools/tts/ 接口）：云 API（火山 / Azure / ElevenLabs）或本地 CosyVoice
3. **RVC 音色后处理（可选增强，推荐高质量角色音色）**：
   - 用 5-10min 角色素材训练 RVC 模型（tools/rvc/）
   - 通用 TTS 生成带情感的台词 → RVC 转换音色 → 角色语音
4. 台词逐句 TTS（+可选 RVC）→ WAV + txt 字幕；语速/情绪按人设卡
5. metadata 记录：后端/模型/RVC/参数/耗时/成本
6. 人工确认音色一致 → 落盘 assets/<character_id>/voice/

## 选型基线
见 spec/TECH-STACK.md（云 API + CosyVoice + RVC 增强；GPT-SoVITS 仅研究）
