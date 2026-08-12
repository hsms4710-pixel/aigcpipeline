# t1：工具链验证（ComfyUI + 一致性 + TTS 多后端跑通）

状态：todo ｜ 依赖：无 ｜ 预估：2-3 天 ｜ 选型基线：spec/TECH-STACK.md

## 目标
验证三条工业主流链路可跑通，产出量化对比，为 t3/t4/t5 定实现。

## 输入
- ComfyUI 环境（含 InstantID / PuLID / IP-Adapter 节点）
- TTS 后端：CosyVoice（本地）+ 至少一条云 API（火山/Azure，key 可配）
- 1 张测试参考图、1 段 5-10s 参考音

## 产出
- 4 张表情差分测试图（neutral/happy/sad/angry），记录 InstantID vs PuLID vs IP-Adapter 质量/耗时/显存
- 3 句测试台词语音 + 字幕（CosyVoice + 云 API 各一份）
- 验证报告（写入 harness/memory/knowledge/toolchain-2026-08.md）：
  引擎/模型/版本/耗时/显存/成本/质量主观评价/一致性方案结论

## 验收
- [ ] ComfyUI 管线生成 4 表情，身份一致（肉眼可确认）
- [ ] 一致性方案结论：InstantID / PuLID / IP-Adapter 选一（附数据）
- [ ] TTS 两条链路（本地 CosyVoice + 一条云 API）各 3 句可播放
- [ ] 报告含耗时/显存/成本三项数据
- [ ] 结论：选定 t3/t4/t5 技术栈（附理由，符合 TECH-STACK.md）

## 借鉴
- ComfyUI 生产案例（Ubisoft CHORD / Series Entertainment）
- InstantID/PuLID/IP-Adapter 对比（apatero 2025-12）
- 2026 TTS 选型评测（火山/Azure/ElevenLabs）
