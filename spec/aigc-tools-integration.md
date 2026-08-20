# AIGC 开源工具集成清单 + 2D 地图类型调研（spec/aigc-tools-integration.md）

> 日期：2026-08-19 ｜ 触发：用户「找 GitHub 上很多 AIGC 开源工具并集成；holopix.cn/model 风格参考；2D 地图很多种（宝可梦式/八方旅人式）请参考」
> 结论：已实际集成 **ai-pixel-art**（无缝瓦片/精灵/动画 + 像素化 + QA 门禁，经中转站 gpt-image-2 验证 OK）；整理可集成工具清单与集成方案；地图路线 = 宝可梦式网格俯视（H2 升级）→ 八方旅人式 2.5D（H3）。

---

## 一、holopix.cn/model（风格参考）
- Holopix AI（广州市光绘科技）：商业游戏美术 AI 工具（风格转换/线稿/模型自定义训练/局部细化/拆补图层/一键抠图/4K 增强/3D 转视角），支持中文生成
- **定位**：风格参考/成品对比用，非开源不可直接集成；可参照其"风格转换 + 模型训练"思路（等价于我们的风格 LoRA / 画风锁死路线）

## 二、GitHub AIGC 开源工具清单（可集成）

### 已集成（本仓库 tools/vendor/）
| **GPT-Image2-Skill**（wuyoscar） | 生图方法论 skill | SKILL.md + craft + openai-cookbook + gallery 参考库；**已按 LangGraph 三级渐进披露运行时加载**（skills_library/gpt-image + tools/skill_loader.py + agent_a2_node.py；image_backend size 校验 + a2-pipeline 默认 1024 保留） | ✅ 2026-08-21（只 vendor skills/ 文本） |
| 工具 | 能力 | 集成状态 |
|---|---|---|
| **ai-pixel-art-image-generation**（ianlintner，MIT） | generate_sprite/tileset/animation + pixelize + **qa_report（palette/alpha/outline/baseline 硬门禁）** + Tiled TSX/TMJ 导出 + 变体控制 | ✅ 已克隆至 tools/vendor/ai-pixel-art；pixelize+qa 本地 PASS；generate_sprite 经中转站 key 验证 OK（QA 全 PASS）；openai_client.py 已打 TLS 补丁 |

### 建议集成（MCP / Skill / CLI，按优先级）
| 工具 | 类型 | 能力 | 集成方式 | 优先级 |
|---|---|---|---|---|
| **FrameRonin-MCP**（GOODDAYDAY） | MCP | 22 个像素资产工具（生成/去背景/精灵表/GIF→sprite/视频帧/像素化 + prompt 自动扩展） | codex mcp add（MCP server） | P0 |
| **pixellab-mcp**（pixellab-code） | MCP | 像素角色/动画/瓦片生成，接 Godot 2D | codex mcp add | P0 |
| **@mseep/game-asset-mcp** | MCP | 文本→2D/3D 资产（像素精灵/OBJ/GLB），HuggingFace Spaces | npm + codex mcp add | P1 |
| **agent-sprite-forge**（0x0funky） | Codex skill | $generate2dsprite/$generate2dmap：精灵/分层地图 + **Godot TileMapLayer 导出** | 安装 skill 进 .codex/skills | P0 |
| **fal-gamedev**（fal-ai-community） | Agent skill | 角色攻击/待机/地图精灵生成（32-bit 像素） | 安装 skill | P1 |
| **Gorest**（NO6KIKO） | 本地工作区 | Codex-assisted 精灵表生成 + 场景合成（浏览器可视化） | clone + 本地起服务 | P1 |
| **sprute**（sprited-ai） | CLI | 单参考图→8 向精灵（模板引导，Nano Banana） | npm 全局（需 Gemini key） | P1 |
| **perfectpixel-studio**（gykim80） | 应用/CLI | 文本→8 方向 100+ 动作精灵表 | clone + CLI | P2 |
| **spine-animation-ai**（Genielabs） | Claude skill | Spine 自动绑骨+动画预设 | 安装 skill | P1（A 路线） |
| **VibeGame**（tettethu） | 框架 | 自然语言→可玩 2D web 游戏（多 agent） | 参考架构（非主线） | P3 |
| **VibeJam Starter Pack**（chongdashu） | skill 包 | 3 个游戏 starter + isometric sprite workflow | 参考 | P2 |

### 集成方式说明
- **MCP 类**：`codex mcp add <server>`（用户环境已有 codex mcp 用法；MCP 走 openclaw mcp-portor 等已有集成思路）
- **Skill 类**：clone 到 `~/.codex/skills/` 或项目 `.codex/skills/`
- **CLI/本地类**：clone 到 `tools/vendor/`，venv 装依赖，写 wrapper 接 image_backend（TLS 补丁模式）
- **统一入口**：建议在 `tools/` 加 `aigc-toolkit.py`（按工具名路由，如 `--tool pixel-art --action tileset`），一条命令调所有集成工具

## 三、2D 地图类型调研（参考实现）

### 类型 A：宝可梦式（网格俯视 RPG）—— H2 升级方向
| 维度 | 实现 | 参考 |
|---|---|---|
| 地图 | TileMapLayer 网格（草地/水/树/建筑瓦片）+ 区域切换（门/边界 warp） | pokemon-godot-csharp（Godot 4 C# 复刻宝可梦红/蓝教程）、Pizza Legends Godot Overworld 系列 |
| 移动 | 网格对齐移动（4/8 向，格点吸附） | sandromaglione top-down grid movement |
| 交互 | 碰撞格、草丛遭遇（Area2D）、NPC 对话、宝箱 | 同上 |
| 视觉 | 俯视 2D 瓦片 + 角色 8 向精灵 + Y-sort | 我们已有：8 向精灵 ✅ + Y-sort ✅ |
| 差异 | 网格吸附移动 + 区域地图切换 + 事件系统 | **H2 待补：网格移动 + 多区域 + 遭遇** |

### 类型 B：八方旅人式（2.5D HD-2D）—— H3 方向
| 维度 | 实现 | 参考 |
|---|---|---|
| 场景 | 3D 场景 + 像素角色（纸片人）+ 正交相机 | Godot-Hybrid2D3D-Renderer-GDExtension（Godot 4.x 专用） |
| 地图 | 3D 建筑/地形 + 像素贴图 + 光影烘焙 | bilibili BV1He4y1u77n / YouTube A7txKkBkgXg（Godot 4 2.5D/HD-2D 关卡教程） |
| 视觉 | 景深/模糊/泛光后处理 + 像素角色 | 八方旅人/Live A Live/DQ3 重制同款流程 |
| 差异 | 3D 环境 + 像素角色混合渲染 | **H3 需集成 Hybrid2D3D 或 2.5D 教程流程** |

### 类型 C：其他（备选）
- **斜 45° isometric**（模拟人生/暗黑式）：blendi sprite-sheet-creator isometric 模式、Kenney isometric 资产
- **真 3D 像素**（Project Shadowglass 式）：透视相机 + 像素稳定渲染（后置）
- **横板**（已否决，归档）

## 四、路线（整合）
| 里程碑 | 内容 | 状态 |
|---|---|---|
| H1 8 向精灵 | 网格法 + rembg 抠图 | ✅ |
| H2 宝可梦式 demo | 俯视 8 向移动（已有）→ **升级：网格吸附移动 + 多区域地图 + 草丛遭遇/事件** | ✅ 基础 / ⏳ 升级 |
| H2.5 俯视 HD-2D 瓦片 | 用 ai-pixel-art generate_tileset（已集成）生成无缝俯视瓦片（32/48px）→ Tiled TSX/TMJ → Godot | 📋 可直接做 |
| H3 八方旅人式 2.5D | 集成 Godot-Hybrid2D3D 或 2.5D 教程流程（正交相机 + 3D 场景 + 像素角色） | 📋 |
| G3 QA 门禁 | ai-pixel-art qa_report 已可用 → 接入 pipeline gate | 📋 |

## 五、决策记录
- 2026-08-19：集成 ai-pixel-art（vendor + TLS 补丁 + 验证 OK）；地图双线：宝可梦式（H2 升级）+ 八方旅人式（H3）
- 已集成工具统一入口 aigc-toolkit.py（规划）；MCP 工具（FrameRonin/pixellab/game-asset）待 codex mcp add


## 六、Godot/AIGC 插件调研（2026-08-19）

### 候选工具清单
| 工具 | 类型 | 能力 | 集成方式/优先级 |
|---|---|---|---|
| **godot-ai**（JackyChenGit） | Godot MCP | 120 ops / 39 MCP 工具，控制 Godot 编辑器（场景操作/GDScript/资源管理） | P1：`codex mcp add`，让 AI 直接操作 Godot |
| **Godot AI Assistant tools MCP**（asset 4767） | Godot MCP | 32 个资产生成工具，generate 2D assets | P1 |
| **Sprite Pipeline**（asset 4764） | Godot 编辑器插件 | 编辑器内 AI 资产生成（BYOK），Pixel Art 风格 | P2：编辑器内插件 + KEY |
| **PixelMaker**（asset 5294） | Godot 编辑器插件 | 精灵/瓦片/walk 循环/动画生成（OpenAI key） | P2 |
| **SpriteCook skills** | Agent skill | 精灵表切分 + Godot AnimatedSprite2D/3D 工程生成 | P1 |
| **aseprite-mcp-pro** | MCP | Aseprite 控制 + 导出 .tres SpriteFrames 到 Godot | P1：需装 Aseprite |
| **godot-asset-generator**（skill） | Agent skill | 16-bit 像素资产生成 + Godot .import 配置 | P1 |
| **agent-sprite-forge generate2dsprite**（已装） | Codex skill | 精灵/瓦片/动画生成 + README，Pokemon 风格 | ✅ 已装并使用 |

### 本轮新增工具（2026-08-19）
- **tools/a2-pipeline.py**：A2 资产生成标准入口（视觉提示词→生图→Vision Gate→自动重试→manifest），已实测瓦片集 PASS 7.0
- **tools/godot-shot.py**：Godot MCP stdio 截图客户端（游戏内画面→Vision Gate）

### 已安装（2026-08-19）
- **godot-assistant**（npm，MIT）：零配置 Godot MCP（25 工具，~6.5k tokens）——读场景/改节点/GDScript 校验/**headless 运行 + 截图 PNG**，无需 addon、不会破坏场景。已注册为 Codex MCP 并指向 godot-pokemon-demo，`doctor` 全 PASS（Godot 4.7.1 + GODOT_PATH）。A3 视觉门禁可直接截图游戏画面验收。
- 配置：`[mcp_servers.godot-assistant] command="npx" args=["-y","godot-assistant","--project",<demo>] env.GODOT_PATH=<godot_console.exe>`

### 待装（live 编辑器控制）
- **godot-ai**（hi-godot，原 JackyChenGit）：120 ops/43 工具，需 Godot 编辑器插件 + uv + 编辑器常开 → 交互式编辑器操控时再装
- **godot-ai 结论**：已装 skill/MCP（agent-sprite-forge / FrameRonin / ai-pixel-art / godot-assistant）+ 视觉提示词设计师（prompt_vision.py）；godot-ai 留作 live 编辑器会话的可选项。所有 MCP 集成方式走 openclaw mcp-portor 思路（用户已有 codex mcp 用法）。

