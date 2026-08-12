# 隔离环境执行方案（env/）

> 决定：P1 管线（ComfyUI 生图 / TTS / 工作台）在**隔离环境**执行，不在本机系统里安装。
> 本机只做入口：浏览器访问工作台 + git 管理代码。

## 为什么隔离
- 不污染本机 Windows 系统（避免 Python 3.14/系统依赖冲突）
- 可复现：同一套编排在本机 Docker / WSL2 / 云开发机都能跑
- 可切换：本机 8GB 显存不够的环节（FLUX/PuLID/3D）在云机上跑同一套编排

## 隔离环境形态（三选一，推荐 A）
| 形态 | 说明 | 适用 |
|---|---|---|
| **A. Docker Compose（推荐）** | 容器编排：comfyui / tts / workbench，GPU 透传 | 本机 Docker Desktop（WSL2 backend）或云 Linux 机 |
| B. WSL2 裸装 | 不装 Docker，直接在 WSL2 里 venv 安装 | 只用本机、想省容器层 |
| C. 云开发机 | 租 GPU 机（4090 24GB+），Docker 或裸装 | 需要 FLUX/PuLID/3D |

## 服务编排（docker-compose.yml 骨架）
```
comfyui     # 生图执行引擎（ComfyUI + InstantID/IP-Adapter 节点），GPU 必需
tts         # TTS 服务（CosyVoice 本地 / 云 API 走 workbench 直连）
workbench   # FastAPI 工作台 + Job 队列 + 阶段状态机
```
- 数据卷：`../assets` 挂载 → 产物在宿主机可见（本机/宿主机直接看）
- 模型卷：`comfy-models`、`tts-models` 持久化（避免重启重下）
- 端口：workbench 8000（本机浏览器入口）、comfyui 8188（调试用）

## 本机/宿主机职责
- 浏览器访问 `http://localhost:8000`（工作台）
- git / 文档 / 审计（代码在仓库，管线在容器）
- 云 API key 放 `.env`（不入库）：火山/Azure TTS、Tripo/Meshy 3D（按需）

## GPU 透传（Windows Docker Desktop）
- 需 WSL2 backend + NVIDIA Container Toolkit（winget 装）
- Linux 云机：`nvidia-container-toolkit` 一行安装

## 租开发机建议（2026-08 调研）
| 平台 | 4090 24GB 时租 | 特点 | 适合 |
|---|---|---|---|
| **AutoDL（首选）** | ¥1.2-2.7/时 | 国内最主流、按秒计费、Docker 容器、镜像丰富、停机保留数据约 1 个月、新用户赠额度 | 本课题（国内访问 HF 走 hf-mirror） |
| 恒源云 | ¥1.3-1.8/时 | 稳定、免费存储 | 备选 |
| 矩池云 | ¥2.0-5/时 | 镜像丰富、省心 | 快速复现 |
| RunPod（国外） | ~\.34-0.69/时 | 均衡默认、ComfyUI 模板、秒级计费 | 访问 HF/GitHub 顺畅时 |
| Vast.ai（国外） | ~\.1-0.6/时 | 最便宜但 P2P 无 SLA | 预算极致、能折腾 |
- 推荐配置：**RTX 4090 24GB**（ComfyUI FLUX/SDXL + CosyVoice 足够；PuLID-Flux 需 48GB L40S/A6000）
- 选型：短期调试 AutoDL 按秒计费；长期跑租月卡更划算
- 我们编排（env/docker-compose.yml）可直接部署到租的 Linux 机

## 部署步骤（选定形态后执行）
1. 复制 `.env.example` → `.env`，填 key
2. `docker compose up -d comfyui` → 装节点（InstantID/IP-Adapter）→ 验证生图
3. `docker compose up -d tts` → 验证 TTS
4. `docker compose up -d workbench` → 浏览器走通上传→生成→下载
5. 跑 `tools/validate-*` 校验资产包

