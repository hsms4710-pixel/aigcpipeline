# t1：工具链验证（生图 + TTS 跑通）

状态：todo ｜ 依赖：无 ｜ 预估：1-2 天

## 目标
验证两条关键链路可跑通，产出量化对比，为 t3/t4 定选型。

## 输入
- FLUX.1-dev（或 SDXL）环境；GPT-SoVITS（或 CosyVoice/F5-TTS）环境
- 1 张测试参考图、1 段 5-10s 参考音（可用合成素材）

## 产出
- 4 张表情差分测试图（neutral/happy/sad/angry）
- 3 句测试台词语音 + 字幕
- 验证报告（写入 `harness/memory/knowledge/toolchain-2026-08.md`）：
  模型/版本/耗时/显存/成本/质量主观评价

## 验收
- [ ] 4 表情身份一致（肉眼可确认）
- [ ] 3 句语音可播放，音色与参考一致（主观可接受）
- [ ] 报告含耗时/显存/成本三项数据
- [ ] 结论：选定 t3/t4 技术栈（附理由）

## 借鉴
- CharForge（LoRA 一致性）、GPT-SoVITS/CosyVoice/F5-TTS 对比
