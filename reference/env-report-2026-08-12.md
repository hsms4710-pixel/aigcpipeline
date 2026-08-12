# 本机环境检查报告（2026-08-12）

> 结论：**本机可作 P1 开发机（8GB 显存路线），3D 生成与 FLUX 高质量生图建议租机/API**。

## 硬件
| 项 | 值 | 对方案影响 |
|---|---|---|
| GPU | RTX 4060 Laptop，**8GB 显存**（当前空闲 ~6.4GB） | SDXL+InstantID/IP-Adapter 可行；FLUX 需量化；PuLID-Flux(24-40GB) 不行 |
| RAM | 15.2GB（空闲 ~5.9GB） | 一次只跑一条链路；ComfyUI+TTS 勿并发 |
| 磁盘 C | 285GB 空闲 | 模型下载足够（ComfyUI+SDXL+LoRA+GPT-SoVITS ≈ 20-30GB） |

## 软件
| 项 | 值 | 备注 |
|---|---|---|
| Python | 3.14.4（系统）+ **3.11.15（uv）** | 3.14 太新，ML 库不支持 → **用 uv 3.11 建 venv** |
| conda | 无 | 用 uv 即可 |
| torch | 系统 python 无 | 需在 3.11 venv 装 CUDA 版 |
| ffmpeg | ❌ 无 | TTS/音频处理需要，需安装（winget/choco） |
| ComfyUI | ❌ 未装 | 需安装（P1 执行引擎） |
| Godot | ❌ 未装 | P4 才需要（可后装） |
| git | 2.54.0 ✅ | — |
| Clash 代理 | ❌ 7897 未启动 | **下载前需先启动 Clash Verge** |

## 本机能力矩阵
| 任务 | 本机（8GB） | 建议 |
|---|---|---|
| SDXL + InstantID / IP-Adapter FaceID | ✅ 可行 | P1 一致性首选验证 |
| 角色/风格 LoRA（SDXL 小模型） | ✅ 可行 | — |
| FLUX.1-dev 全精度 | ❌ 太紧 | 用 NF4 量化版（8GB 勉强）或租机/API |
| PuLID-Flux | ❌ 24-40GB | 租机 |
| GPT-SoVITS / CosyVoice 推理 | ✅ 可行 | P1 语音本地链路 |
| Hunyuan3D / TRELLIS 3D 生成 | ⚠️ 8GB 很紧 | **建议 API（Tripo/Meshy）或租机** |
| 工作台 Web（FastAPI） | ✅ | — |
| Godot 工程 | ✅（轻量） | 需装 Godot |

## 租开发机建议（如需要）
- 触发：FLUX 高质量生图 / 3D 生成（Hunyuan3D）/ 并发评测
- 建议：云 GPU **RTX 4090 24GB**（或 L40S/A6000 48GB），按小时租
- 替代：**云 API** 更省事——3D 用 Tripo/Meshy API、高质量生图用 fal/Replicate 的 FLUX，TTS 用火山/Azure —— 租机不是必须
- 本机不达标时优先用 API 而非立即租机（成本/迭代速度权衡）

## 下一步（t1 前置）
1. 启动 Clash Verge（下载依赖必需）
2. uv 建 Python 3.11 venv → 装 CUDA torch
3. winget/choco 装 ffmpeg
4. 装 ComfyUI（+ InstantID/IP-Adapter 节点）→ 跑 SDXL+InstantID 验证
