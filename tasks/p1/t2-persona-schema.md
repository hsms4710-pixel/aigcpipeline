# t2：人设卡 JSON Schema v0 + 资产包规范

状态：todo ｜ 依赖：无（可与 t1 并行） ｜ 预估：1 天

## 目标
定 L0 契约：人设卡 schema + 资产包目录/命名/metadata 规范，后续所有模块依赖它。

## 产出
- `spec/p1-character-voice/contracts/persona-schema.json`（JSON Schema v0）
- `spec/p1-character-voice/contracts/asset-package-spec.md`
- 校验脚本 `tools/validate-persona.ps1` + `tools/validate-asset-package.ps1`

## 人设卡字段（草案）
name / race / class / personality_tags[] / style_desc / background / voice(参考音/音色描述) / lines[{text, emotion}] / ref_image?

## 验收
- [ ] 示例 persona.json 通过 validate-persona
- [ ] 空资产包 + 示例资产包通过 validate-asset-package（一错一对）
- [ ] spec 评审通过（记录 decision）
