# 审计日志（audit/audit-log.md）

## 2026-08-12 —— Part 0 地基
- **范围**：仓库骨架 / rule / spec 占位 / harness / task 拆解 / 审计机制
- **结果**：✅ 通过（地基自审）
- **说明**：P1 已拆出 t1-t7 可执行任务（含验收）；P3/P4/P2 为草稿；P5 明确后置不拆解
- **fixes**：无
- **下一步**：P1 开发（t1 工具链验证 → t2 schema → ...）

---

> 后续审计按此格式追加。清单见 audit/AUDIT.md。

## 2026-08-12 —— 选型主流性审计（专项）
- **范围**：P1-P4 全部技术选型对照工业主流（ComfyUI/InstantID/TTS 云 API+CosyVoice/Hunyuan3D/Ink-Yarn/记忆框架/引擎数据）
- **结果**：⚠️ 4 处非主流已修正（详见 spec/TECH-STACK.md 基线）
  - 生图编排：自研 CLI → **ComfyUI**（Ubisoft/Series 生产验证）
  - 角色一致性：CharForge → **InstantID/PuLID/IP-Adapter**
  - TTS：GPT-SoVITS 默认 → **云 API（火山/Azure/ElevenLabs）+ CosyVoice 多后端**
  - 3D：TripoSR → **Hunyuan3D 2.1/TRELLIS/Tripo API/Meshy**
- **新增**：`spec/TECH-STACK.md` 选型基线 + 原则 P9（工业主流优先，防"为省事选非主流"）
- **fixes**：t1/t3/t4/t5、SKILL_character-gen/voice-clone/workbench-web、P2/P3/P4 spec、reference 全部同步更新
- **下一步**：P1 开发（t1 按新基线验证 ComfyUI+InstantID+TTS 多后端）
