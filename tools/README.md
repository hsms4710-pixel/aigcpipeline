# tools/ 工具目录（AI 工作流 harness）

> 更新时间：2026-08-19 ｜ 本文件是 tools/ 的索引：按功能归类，区分【核心】与【迭代/一次性】。
> 规则：新增脚本时在本文件追加一行；一次性的迭代脚本保留（历史可追溯），但不再优先维护。

## 1. Agent Workflow 核心（当前主链路，优先维护）

| 工具 | 功能 | 备注 |
|---|---|---|
| **a2-pipeline.py** | A2 资产生成标准入口：视觉提示词 → 生图 → Vision Gate → 失败带问题修订重试 → manifest | 一条命令闭环，2026-08-19 |
| **prompt_vision.py** | 视觉提示词设计师：gpt-5.5 视觉模型根据需求+风格基底+参考图生成/修订生图 prompt | A2 第一步 |
| **vision_gate.py** | Vision Gate 正式门禁：类型化验收模板 + 多维评分 + threshold + manifest 写入 | A3 |
| **vision_review.py** | 视觉验收基础调用（早期版本，vision_gate 的前身） | 基础 |
| **godot-shot.py** | godot-assistant MCP stdio 客户端：场景截图 PNG（游戏内画面 → Vision Gate） | 2026-08-19 |
| **image_backend.py** | 生图统一后端（openai 中转站 gpt-image-2 / gemini / fal，TLS 补丁） | 生图底座 |
| **aigc-toolkit.py** | AIGC 工具统一入口（ai-pixel-art 包装：sprite/tileset/animation/pixelize/qa/export-tiled） | --style 注入 |

## 2. 地图管线（W2 宝可梦式 demo）

| 工具 | 功能 | 备注 |
|---|---|---|
| **build-pokemon-map-v2.py** | 程序化地图生成 v2.4：域扭曲草地 / 有机湖 / 沙滩 / 主干道支路桥 / 村庄 / 成林树丛 | 核心 |
| **render-map-png.py** | map.json → 全景 PNG（Vision Gate 用，不依赖 Godot） | 核心 |
| **build-pokemon-demo.py** | 生成 Godot 俯视 demo（早期版本，已被手改版取代） | 历史 |
| generate-pixel-tiles.py | 单纹理无缝瓦片（512 无缝 + 4 变体） | G1 横板瓦片 |
| generate-sideview-tiles.py | 侧视瓦片 | 迭代 |
| build-ai-map.py | 横板 AI 瓦片地图（hd2d 128px atlas） | G1 |
| port-sunnyland-map.py / port-tiny-rpg-map.py | 移植 SunnyLand / TinyRPG 官方地图 | 复用资产 |
| build-kenney-atlas.py | Kenney 图集打包 + 预览 | 复用资产 |

## 3. 角色生图（画风/立绘/Q版/帧）

| 工具 | 功能 | 备注 |
|---|---|---|
| gen_prompt.py | 画风 prompt 模板（风格签名+角色分工+保锁清单+No-Beautify） | 核心（A4） |
| gen-portrait.py | 立绘生成（full/bust/表情） | 核心 |
| gen-ailin-walk-sheet.py | 艾琳 4向x4帧 walk sheet（视觉模型提示词） | 当前角色 |
| gen-chibi-v4.py / gen-chibi-final.py / gen-riggable-chibi.py | Q版小人（v4 定稿/最终/可绑骨） | 迭代 |
| gen-4dir-refined.py / gen-pokemon-4dir.py / gen-pixel-8dir-grid.py / gen-8dir-chibi*.py | 方向帧/精灵表 | 迭代 |
| gen-frame-cycle.py / gen-side-frames.py / gen-transparent-variants.py | 帧循环 / 侧视帧 / 透明变体 | 迭代 |
| gen-style-compare.py / test-gpt2-style-method.py | 风格对比 / 新方法实测 | 迭代 |
| rebuild-review-collages.py | 审查拼图重建 | 迭代 |

## 4. 帧对齐 / 动画 / 引擎

| 工具 | 功能 | 备注 |
|---|---|---|
| align-game-frames.py / align-side-frames.py | 帧对齐（中心/脚底/杂点清理） | 核心（B 路线） |
| build-godot-anim-demo.py / build-frame-anim-godot.py / build-topdown-demo.py | Godot 动画 demo 生成 | 迭代 |
| build-spine-from-image.py | 图 → Spine 工程（SIFT+RANSAC） | A 路线 |
| regen-walk*.py（regen-walk4/v2/v3/walk7/stable） | walk 帧重生成迭代 | 一次性（历史） |
| export-godot.py | Godot 导出 | 核心 |
| package-assets.py | 资产打包 | 核心 |

## 5. 拆层 / 绑骨 / 骨骼

| 工具 | 功能 | 备注 |
|---|---|---|
| split-limb.py / split-spine-arm.py / split-spine-limb.py | 部件拆分 | A 路线 |
| fix-rig.py / check_joint_tear.py | 骨骼修正 / 关节撕裂检测 | A 路线 |
| render_bone_overlay.py / render_fk_frames.py | 骨骼叠加 / FK 帧渲染 | A 路线 |
| validate-rig.py / validate-anim.py | 骨骼 / 动画校验 | A 路线 |

## 6. 素材站抓取 / 校验

| 工具 | 功能 | 备注 |
|---|---|---|
| fetch_fgo_servant.py / fetch_prts_operator.py | FGO / 明日方舟素材站抓取 | 参考图来源 |
| validate-layered.py / validate-persona.py / validate-asset-package.py | 分层 PSD / 人设卡 / 资产包校验 | QA |

## 7. 应用 / 供应商（子目录）

| 路径 | 内容 |
|---|---|
| workbench/ | 工作台 FastAPI + React（阶段状态机 + 预览/下载/单步重试） |
| rig-automation/ | StretchyStudio 自动绑骨 agent（stretchy-agent.cjs） |
| vendor/ | 第三方 skills/MCP 本地副本（ai-pixel-art、FrameRonin-MCP、spine-animation-ai、character-animation-creator、**GPT-Image2-Skill**） |

## 8. 环境要求
- Python venv：`C:\Users\26046\Desktop\inerview\runtime\.venv`（PIL / openai / dotenv）
- 生图 key：`env/.env`（GPT_API_KEY / GPT_BASE_URL，中转站 api.sisct2.xyz）
- 视觉 key：`vision_gate.py` / `prompt_vision.py` 内 DEFAULT_KEY（gpt-5.5）
- Godot 4.7.1：`C:\Users\26046\Documents\lovegaming\`；Godot MCP：`npx -y godot-assistant`（已注册 Codex MCP）
