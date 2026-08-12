# t1：工具链验证（隔离环境执行）

状态：todo ｜ 依赖：无 ｜ 预估：2-3 天 ｜ 选型基线：spec/TECH-STACK.md
环境方案：**env/README.md（隔离环境执行，本机只做入口）** ｜ 环境事实：reference/env-report-2026-08-12.md

## 目标
在**隔离环境**（Docker Compose / WSL2 / 云机，三选一）里验证 P1 主链路可跑通，产出量化对比，为 t3/t4/t5 定实现；同时记录哪些环节需要云 API/更高显存。

## 前置（选定隔离形态后执行，见 env/README.md）
1. 选定形态：A Docker Compose（推荐）/ B WSL2 / C 云机
2. 部署 comfyui 服务（含 InstantID/IP-Adapter 节点）→ 验证生图
3. 部署 tts 服务（CosyVoice 本地 / 云 API key 进 .env）→ 验证语音
4. workbench 就位（本机浏览器访问）

## 验证内容
- **一致性**：SDXL + **InstantID**（首选）vs **IP-Adapter FaceID**（轻量备选）——4 表情（neutral/happy/sad/angry）身份一致性/耗时/显存
- **FLUX 探测**：隔离机显存够则跑 NF4/全精度对比；不够则标记"云 API/更高显存机项"
- **TTS**：本地 **CosyVoice** + 云 API（火山/Azure，key 进 .env）各 3 句
- **3D**：不在本阶段验证（API/租机项，见 env-report）

## 产出
- 4 表情测试图（InstantID 路径）+ 6 句语音（本地+云）+ 字幕
- 验证报告（harness/memory/knowledge/toolchain-2026-08.md）：引擎/模型/耗时/显存/成本/质量/一致性方案结论
- **决策清单**：哪些在隔离环境跑、哪些走云 API、是否需要升显存（写入报告 + ROADMAP 备注）

## 验收
- [ ] InstantID 路径生成 4 表情身份一致（肉眼确认）
- [ ] 一致性方案结论：InstantID / IP-Adapter 选一（附数据）
- [ ] 本地 + 云 TTS 各 3 句可播放
- [ ] FLUX 可行/不可行结论明确
- [ ] 本机/隔离/API 决策清单完成
- [ ] 报告含耗时/显存/成本

## 借鉴
- ComfyUI 生产案例（Ubisoft CHORD / Series Entertainment）
- InstantID/PuLID/IP-Adapter 对比（apatero 2025-12）
