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

## 2026-08-12 —— 表情方案修正 + 环境核查（专项）
- **范围**：2D/3D 表情技术路径 + 本机环境能力
- **结论**：
  - 2D 表情：修正为 Live2D Cubism（免费版商用门槛<1000万日元）+ **Umamo（开源 rigging，drop-in）** 绑定，参数化表情/口型
  - 3D 表情：修正为**引擎原生 Blend Shapes/Morph Target**（Godot/Unity/UE 内调权重），不需要 AIGC 生成表情图
  - 环境：本机 RTX 4060 8GB / RAM 15.2GB / C 盘 285GB / uv 3.11 可用 / 无 ffmpeg·ComfyUI·Godot / 代理未启动
- **能力矩阵**：本机可跑 SDXL+InstantID+LoRA+GPT-SoVITS/CosyVoice；FLUX 需量化、PuLID-Flux/Hunyuan3D 需租机或 API
- **产物**：`reference/env-report-2026-08-12.md`；t1 按 8GB 约束重写（含本机/API/租机决策清单）
- **fixes**：TECH-STACK / P1 spec / SKILL_character-gen 同步更新
- **下一步**：t1 前置（启动 Clash → uv 3.11 venv → CUDA torch → ffmpeg → ComfyUI+InstantID）

## 2026-08-12 —— 生图选型调整 + P2 过场方案细化（专项）
- **生图**：用户决定 P1 生图先用 GPT Image 2 + Nano Banana（云 API），本地 ComfyUI（SDXL+InstantID）降为可选离线后端（开源自托管场景）
- **P2 过场**：重写 spec —— 三范式（A AIGC 视频 / B 引擎内 / C 混合），MVP 走 B 为主 + A 展示；管线：Ink → Director Agent 拆镜头 → GPT/Nano Banana 视觉资产 → Veo/Kling/Wan 动画化或 Godot 时间轴 → TTS 配音
- **更新**：TECH-STACK（生图行 + 视频生成行 + 过场编排行）、P1 spec、t1、ROADMAP、reference、tasks/p2
- **下一步**：P1 开发（t1 验证 GPT/Nano Banana + TTS 多后端）
