# 隔离环境执行方案（env/）

> 决定：P1 管线（ComfyUI 生图 / TTS / 工作台）在**隔离环境**执行，不在本机系统里安装。
> 本机只做入口：浏览器访问工作台 + git 管理代码。

## 为什么隔离
- 不污染本机 Windows 系统（避免 Python 3.14/系统依赖冲突）
- 可复现：同一套编排在本机 Docker / WSL2 / 云开发机都能跑
- 可切换：本机 8GB 显存不够的环节（FLUX/PuLID/3D）在云机上跑同一套编排

## 隔离环境形态（✅ 已选定：本地隔离文件夹）
| 形态 | 说明 | 状态 |
|---|---|---|
| **D. 本地隔离文件夹（选定）** | 本机独立目录 env/runtime/：uv venv（Python 3.11）+ 依赖/模型/工具全部放目录内，不污染系统；生图走云 API（GPT/Nano Banana），本地只跑工作台 + TTS + 音频 | ✅ 当前 |
| A. Docker Compose | 容器编排：comfyui / tts / workbench，GPU 透传 | 备用（需升显存时） |
| B. WSL2 裸装 | 不装 Docker，WSL2 里 venv 安装 | 备用 |
| C. 云开发机 | 租 GPU 机（4090 24GB+） | 备用（3D/PuLID 时） |

## 服务编排（docker-compose.yml 骨架）
```
comfyui     # 生图执行引擎（ComfyUI + InstantID/IP-Adapter 节点），GPU 必需
tts         # TTS 服务（CosyVoice 本地 / 云 API 走 workbench 直连）
workbench   # FastAPI 工作台 + Job 队列 + 阶段状态机
```
- 数据卷：`../assets` 挂载 → 产物在宿主机可见（本机/宿主机直接看）
- 模型卷：`comfy-models`、`tts-models` 持久化（避免重启重下）
- 端口：workbench 8000（本机浏览器入口）、comfyui 8188（调试用）

## 本地隔离文件夹布局（env/runtime/，不入库）
\\\
env/runtime/
├── .venv/          # uv 创建，Python 3.11（ML 库兼容）
├── tools/          # portable ffmpeg 等（不装系统）
├── models/         # 本地模型缓存（CosyVoice 等，可删可重建）
├── logs/           # 工作台/任务日志
└── app/            # 工作台代码（或软链 tools/workbench）
\\\
- 隔离原则：**一切可执行文件/依赖/缓存都在 runtime/ 内**；系统只装通用工具（git 已有）
- 生图云 API 不占本地显存；CosyVoice 可 CPU 推理 → 本机 8GB 完全够 P1

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

## 部署步骤（本地隔离文件夹，当前）
1. 复制 env/.env.example → env/.env，填 key（见下）
2. 建隔离环境：uv venv --python 3.11 env/runtime/.venv → 激活 → 装依赖（FastAPI/uvicorn 等）
3. 装 portable ffmpeg 到 env/runtime/tools/（音频处理必需）
4. 装 CosyVoice（本地 TTS，可选 CPU）→ 验证语音
5. 启动工作台 → 浏览器 localhost:8000 走通上传→生成→下载
6. 跑 	ools/validate-* 校验资产包

### Key 申请链接（用户自行申请，填进 env/.env）
| 用途 | 链接 | 说明 |
|---|---|---|
| GPT Image（OpenAI） | https://platform.openai.com/api-keys | 需账号+充值；国内需代理/中转 |
| Nano Banana（Google Gemini） | https://aistudio.google.com/app/apikey | Gemini API key；或 Vertex AI：console.cloud.google.com/vertex-ai |
| Nano Banana 聚合（国内友好） | https://fal.ai ｜ https://openrouter.ai | 聚合 Nano Banana/GPT 等，按量付费 |
| TTS 火山引擎（豆包） | https://console.volcengine.com/ark | 国内首选 TTS，音色/克隆 |
| TTS Azure | https://portal.azure.com（Speech 服务） | 低延迟/免费层 |