# t1：工具链验证（本机 8GB 显存路线）

状态：todo ｜ 依赖：无 ｜ 预估：2-3 天 ｜ 选型基线：spec/TECH-STACK.md ｜ 环境事实：reference/env-report-2026-08-12.md

## 目标
在**本机 RTX 4060 8GB** 上验证 P1 主链路可跑通，产出量化对比，为 t3/t4/t5 定实现；同时记录哪些环节需要租机/API。

## 前置（环境准备）
1. 启动 Clash Verge（下载依赖）
2. uv 建 Python 3.11 venv → 装 CUDA torch
3. 装 ffmpeg（winget/choco）
4. 装 ComfyUI + InstantID/IP-Adapter 节点

## 验证内容（8GB 约束下）
- **一致性**：SDXL + **InstantID**（首选）vs **IP-Adapter FaceID**（轻量备选）——4 表情（neutral/happy/sad/angry）身份一致性/耗时/显存
- **FLUX 探测**：NF4 量化版能否在 8GB 跑通（能则记录质量对比，不能则标记"租机/API 项"）
- **TTS**：本地 **CosyVoice** + **GPT-SoVITS**（研究）各 3 句；云 API（火山/Azure）留 key 后验证
- **3D**：本机不验证（标记 API/租机项）

## 产出
- 4 表情测试图（InstantID 路径）+ 3 句本地 TTS 语音 + 字幕
- 验证报告（harness/memory/knowledge/toolchain-2026-08.md）：引擎/模型/耗时/显存/成本/质量/一致性方案结论
- **决策清单**：哪些本机做、哪些走 API/租机（写入报告 + ROADMAP 备注）

## 验收
- [ ] InstantID 路径生成 4 表情身份一致（肉眼确认）
- [ ] 一致性方案结论：InstantID / IP-Adapter 选一（附数据）
- [ ] 本地 TTS 至少一条链路 3 句可播放
- [ ] FLUX 可行/不可行结论明确
- [ ] 本机/API/租机决策清单完成
- [ ] 报告含耗时/显存/成本

## 借鉴
- ComfyUI 生产案例（Ubisoft CHORD / Series Entertainment）
- InstantID/PuLID/IP-Adapter 对比（apatero 2025-12）
