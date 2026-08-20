# 运行环境与工具配置说明（env/）

> 更新：2026-08-19 ｜ 本文件是**环境重建/复现的唯一入口**：隔离环境形态、key 配置、每个工具从哪 clone、怎么装、模型怎么下载、当前阻塞点。
> 原则：`env/` 不入库（含 key/大体积运行依赖）；公开仓库只保留本说明 + `.env.example` + `config.toml.example`。

---

## 0. 一句话
本项目所有可执行依赖都放**本地隔离目录**（不污染系统），生图走云 API；新机器复现 = 建 venv + 填 key + clone 下面几个工具 + 下载模型。

## 1. 隔离环境形态（当前：本地隔离文件夹）
| 形态 | 说明 | 状态 |
|---|---|---|
| **D. 本地隔离文件夹（当前）** | 独立目录 env/runtime/ + 项目级 venv；生图走云 API（GPT 中转站），本地只跑工作台/TTS/音频 | ✅ |
| A. Docker Compose（env/docker-compose.yml） | comfyui / tts / workbench 容器编排，GPU 透传 | 备用 |
| B. WSL2 裸装 / C. 云开发机（4090 24GB+，3D/PuLID 时） | 备用 | 备用 |

## 2. Key 配置（⚠️ 不入库）
### 2.1 `env/.env`（从 `.env.example` 复制后填写）
```bash
# 生图/LLM 中转站（OpenAI 兼容）
GPT_API_KEY=sk-xxx
GPT_BASE_URL=https://api.sisct2.xyz/v1
GPT_MODEL=gpt-5.5
# 视觉验收/视觉提示词（vision_gate.py / prompt_vision.py / vision_review.py 读取）
VISION_KEY=sk-xxx
# 3D（Tripo 试用，额度有限）
TRIPO_API_KEY=tcli_xxx
# 语音（按需）
TTS_PROVIDER=cosyvoice
VOLC_API_KEY=
# 视频/生图备选（按需）
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
HF_ENDPOINT=https://hf-mirror.com   # 国内下载 HF 模型用镜像
```
### 2.2 `env/config.toml`（OpenClaw 风格，LLM/审阅/Agent 框架用）
- 模板见 `env/config.toml.example`（已脱敏，复制为 config.toml 填真实 key）
- 结构：`[model_providers.OpenAI]` base_url=中转站 /v1，wire_api="responses"，requires_openai_auth=true
- 原则：**不自己写 key 接入**——LLM/生图参照 OpenClaw config.toml 格式；MCP 用 OpenClaw/现有集成（`openclaw mcp add`），复用 dcc-mcp 等 adapter
### 2.3 Key 申请链接
| 用途 | 链接 |
|---|---|
| GPT Image / gpt-5.5 | https://platform.openai.com/api-keys（国内需中转/代理） |
| Gemini Nano Banana | https://aistudio.google.com/app/apikey ｜ fal.ai ｜ openrouter.ai |
| TTS 火山（豆包） | https://console.volcengine.com/ark |
| TTS Azure | https://portal.azure.com（Speech） |

## 3. Python 环境
- **项目工具 venv（当前实际使用）**：`C:\Users\26046\Desktop\inerview\runtime\.venv`（Python 3.11，含 PIL/openai/python-dotenv/httpx2 等）
  ```powershell
  # 重建
  cd C:\Users\26046\Desktop\inerview
  python -m venv runtime\.venv
  runtime\.venv\Scripts\pip install pillow openai python-dotenv numpy httpx2 langgraph  # langgraph: A2 节点 StateGraph + skill 加载
  ```
- env/runtime/.venv（备用，ML 工具用，含 torch 2.8+cu128）

## 4. 工具清单（clone/安装方式 + 用途 + 使用入口）

### 4.1 本仓库自带（tools/，已上传）
| 工具 | 用途 | 运行 |
|---|---|---|
| a2-pipeline.py | A2 资产生成标准入口（视觉提示词→生图→Vision Gate→重试→manifest） | `python tools/a2-pipeline.py --demand "..." --style pokemon-nds-bw --type character --name xxx` |
| prompt_vision.py | 视觉提示词设计师（gpt-5.5 视觉模型出 prompt） | 被 a2-pipeline 调用 |
| vision_gate.py | Vision Gate 视觉验收门禁（多维评分，阈值 7.0） | `python tools/vision_gate.py <img> --type map --baseline <基准> --out gate.json` |
| vision_review.py | 视觉审查基础调用 | `python tools/vision_review.py <img>` |
| godot-shot.py | Godot MCP 截图（游戏内画面→Vision Gate） | `python tools/godot-shot.py --scene res://main.tscn --out shot.png` |
| image_backend.py / aigc-toolkit.py | 生图统一后端 / AIGC 工具统一入口 | 被各生成脚本调用 |
| build-pokemon-map-v2.py / render-map-png.py | 程序化地图生成 / 地图渲染 PNG | `python tools/build-pokemon-map-v2.py --seed 20260819` |
| workbench/ | 工作台 FastAPI+React（阶段状态机） | `python tools/workbench/app.py` |
| rig-automation/ | StretchyStudio 自动绑骨 agent | `node tools/rig-automation/stretchy-agent.cjs` |

### 4.2 第三方工具（clone/安装，按需；`env/runtime/tools/`）
| 工具 | 来源（clone URL） | 用途 | 本仓库用法 | 体积/依赖 |
|---|---|---|---|---|
| **See-through** | https://github.com/shitagaki-lab/see-through.git | 单图动漫立绘拆层（SIGGRAPH 2026）→ 分层 PSD | P1-B 拆层（char_ailin_v10 → 18层 PSD） | ~12GB（venv+依赖）；**模型待下载（见 §5）** |
| **StretchyStudio** | https://github.com/MangoLion/stretchystudio.git | Spine/Live2D 自动绑骨（DWPose 本地 wasm） | P1-C 绑骨（13-18 bones），start-stretchy.cmd | ~1.2GB |
| **GPT-SoVITS** | https://github.com/RVC-Boss/GPT-SoVITS | 声音克隆 TTS（声音集训练） | P1 语音路线 B | ~1.4GB |
| **ComfyUI** | https://github.com/comfyanonymous/ComfyUI | 本地生图后端（可选离线） | 备用后端（comfyui-lora-plan.md） | ~83MB（不含模型） |
| **Godot 4.7.1** | https://godotengine.org/download | 引擎（demo 运行/截图） | 装在 `C:\Users\26046\Documents\lovegaming\`；console exe 被 godot-shot/headless 测试调用 | ~1GB |
| **godot-assistant（npm MCP）** | `npx -y godot-assistant` | Godot MCP（读场景/运行/截图 25 工具） | 已注册 Codex MCP，指向 godot-pokemon-demo；`npx -y godot-assistant doctor --project <demo>` | npm 包 |

### 4.3 已 vendor 的 skills（tools/vendor/，已入库；也可从上游重新 clone）
| skill | 来源 | 用途 |
|---|---|---|
| ai-pixel-art-image-generation | https://github.com/ianlintner/ai-pixel-art-image-generation | 精灵/无缝瓦片/动画 + QA 门禁 + Tiled 导出（**已打 TLS 补丁**，中转站可用） |
| agent-sprite-forge | https://github.com/0x0funky/agent-sprite-forge | 精灵/分层地图生成 + Godot TileMapLayer 导出 |
| spine-animation-ai | https://github.com/GenielabsOpenSource/spine-animation-ai | Spine 自动绑骨/动画 |
| character-animation-creator | https://github.com/tachikomared/character-animation-creator-skill | 文本/参考图→64px 像素角色精灵表 |
| FrameRonin-MCP | https://github.com/GOODDAYDAY/FrameRonin-MCP | 22 个像素资产 MCP 工具（已注册 codex mcp） |
| pixellab-mcp | https://github.com/pixellab-code/pixellab-mcp | 像素角色/动画/瓦片 MCP |

### 4.4 外部免费资产包（env/assets/，CC0，可重下）
- SunnyLand（ansimuz）、TinyRPG Forest、Kenney（topdown / rpg-urban）：横板/俯视地图与角色资产源

## 5. 需要手动下载的模型（当前阻塞点）
| 模型 | 用于 | 下载方式 |
|---|---|---|
| **See-Through LayerDiff3D** | 立绘拆层（P1-B）→ **2D 骨骼 A 路线（Spine）前置** | HF：`HF_ENDPOINT=https://hf-mirror.com` 下载到 `env/runtime/tools/see-through/downloads/`；**当前阻塞（模型未下载）** |
| GPT-SoVITS 预训练模型 | 声音克隆 | `python env/runtime/tools/download-gptsovits-models.py` |
| DWPose 模型 | StretchyStudio 绑骨 | StretchyStudio 本地模型首次加载约 8s 自动拉取 |

## 6. MCP 注册（Codex）
```bash
codex mcp add godot-assistant --env GODOT_PATH="C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64_console.exe" -- npx -y godot-assistant --project <demo>
codex mcp add frame-ronin -- python -m frame_ronin_mcp.server
```
- 已注册：godot-assistant / frame-ronin / layout_forge / figma / github
- 验证：`npx -y godot-assistant doctor --project <demo>`（All checks passed）

## 7. 从零重建步骤（新机器）
1. clone 仓库 → 读 README.md / PROJECT-INDEX.md
2. 建 venv（§3）+ 装依赖
3. 复制 `env/.env.example` → `env/.env`、`env/config.toml.example` → `env/config.toml`，填 key（§2）
4. 按需 clone §4.2 工具（先 See-through + StretchyStudio + Godot + GPT-SoVITS）
5. 下载 §5 模型（HF 走 hf-mirror）
6. 注册 MCP（§6）
7. 跑通：`python tools/a2-pipeline.py ...` → `python tools/vision_gate.py ...` → `start-pokemon.cmd` / `start-game.cmd`

## 8. 付费 API 清单与成本
- 详见 `env/api-costs.md`（按管线分阶段：生图/视觉/3D/语音，标注必需/后置/免费替代）
- 3D：Tripo 试用 key 额度有限；TRELLIS2/Hunyuan3D 2.5 可本地（6-12GB VRAM）

## 9. 安全
- `env/.env`、`env/config.toml` 含真实 key，已在 .gitignore，**禁止提交**
- 审计：`git ls-files | grep -iE "config.toml|\.env"` 应为空；脚本中禁止硬编码 key（全部读 env）

