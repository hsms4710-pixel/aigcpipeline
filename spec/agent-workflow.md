# Agent Workflow 中心规划（spec/agent-workflow.md）

> 日期：2026-08-19 ｜ 触发：用户「项目中心应该是一个 agent workflow；先装齐插件/MCP/skills，再规划实现路线」
> 更新：2026-08-19 ｜ 用户「视觉模型验收也是流水线的一部分」→ Vision Gate 正式化为 A3 门禁环节
> 结论：把「角色 AIGC → AI NPC → 引擎接入」项目从"工具堆积"重构为 **以编排 agent 为中心的工作流**：自然语言需求 → 编排 agent 拆解 → 分派到带 harness（skills/tools/MCP）的执行 agent → 契约校验 + 质量门禁（程序化 QA + **Vision Gate 视觉验收**）→ Godot 可运行产物。

---

## 1. 中心架构（Agent Workflow）

```
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR（编排 agent，本会话 / Codex 主 agent）            │
│  接收自然语言需求 → 拆解任务 → 分派 → 汇总 → 验收 → 归档         │
└───────┬──────────────────────────────────────────┬────────────┘
        │ 分派（每环节一个执行 agent + 专属 harness）  │ 反馈/沉淀
        ▼                                          ▼
┌───────────────┐  ┌───────────────┐  ┌──────────────────────────┐
│ A1 需求/规划   │  │ A2 资产生成    │  │ A3 质量门禁               │
│ 解析需求→spec  │→│ 生图/像素化/    │→│ 程序化 QA(validate/qa)    │
│ 地图/角色/场景 │  │ 精灵/瓦片/动画  │  │ + Vision Gate(视觉验收)   │
└───────────────┘  └───────┬───────┘  └────────────┬─────────────┘
                           │                       │ 通过
                           ▼                       ▼
┌───────────────┐  ┌───────────────┐  ┌──────────────────────────┐
│ A4 引擎集成    │←─│ A5 Spine/骨骼  │  │ A6 归档/反馈              │
│ Godot 工程生成 │  │ 绑骨/动画      │  │ 资产入库 + lessons 回填   │
│ TileMap/场景   │  │ (spine-anim-ai)│  │ (A/B 路线)               │
└───────────────┘  └───────────────┘  └──────────────────────────┘
```

**核心原则**：
1. 编排 agent 不做具体资产活，只做拆解/分派/验收（延续"不要硬脚本"）
2. 每个执行环节 = agent + 专属 harness（skill/mcp/tool），harness 可独立替换
3. 环节间只认**资产契约**（manifest JSON：schema 版本/hash/参数/耗时/成本/验收状态）
4. 每个环节过**质量门禁**才进下一步，门禁 = 程序化 QA（qa_report/validate-*）+ **Vision Gate（视觉模型验收，正式环节）**
5. 反馈闭环：失败→原因→规则→自动规避（lessons-learned）

---

## 2. 工具层（harness 清单，已装）

### 2.1 Skills（已装到 C:\Users\26046\.codex\skills\，6 个）
| Skill | 归属环节 | 能力 |
|---|---|---|
| agent-sprite-forge-generate2dsprite | A2 | 文本→精灵表/角色/怪物/道具（Codex 原生，含对齐/透明/QA） |
| agent-sprite-forge-generate2dmap | A2/A4 | 文本→分层地图 + **Godot TileMapLayer 导出**（碰撞/区域/y-sort） |
| agent-sprite-forge-video2dsprite | A2 | 视频→精灵帧（动画来源） |
| ai-pixel-art-image-generation | A2/A3 | 精灵/无缝瓦片/动画 + **QA 硬门禁**（palette/alpha/outline/baseline）+ Tiled TSX/TMJ |
| spine-animation-ai | A5 | Spine 自动绑骨/动画（SIFT+RANSAC + 12 原则预设） |
| character-animation-creator | A2 | 文本/参考图→64x64 像素角色 8 向 walk/attack 精灵表 |

### 2.2 MCP（已注册）

> **Skill 运行时加载（2026-08-21）**：项目主体是 agent 驱动的 pipeline，skill 不静态写死。gpt-image skill 已按 **LangGraph 三级渐进披露**接入：`skills_library/gpt-image/`（注册表）+ `tools/skill_loader.py`（discover/select/load/resource）+ `tools/agent_a2_node.py`（A2 的 LangGraph StateGraph 节点：skill_context→design_prompt→generate→vision_gate→条件重试→archive）。`a2-pipeline.py --agent` 走该节点；详见 harness/skills/SKILL_gpt-image-2.md §9.4。
| MCP | 归属环节 | 能力 | 状态 |
|---|---|---|---|
| **frame-ronin** | A2/A3/A4 | 22 个像素工具：生成（dalle/gemini/siliconflow 后端）、**抠图(matting)/像素化/GIF/精灵表/Godot 工程导出** | ✅ enabled（本地工具无需 key） |
| layout_forge | A4 | Layout Forge V2 项目（已有） | enabled |
| **godot-assistant** | A3/A4 | 零配置 Godot MCP：读/改场景 + GDScript 校验 + **headless 运行 + 截图 PNG**（A3 视觉门禁直接验游戏画面） | ✅ enabled（2026-08-19，doctor PASS） |
| figma / github | 通用 | 设计稿 / GitHub | enabled |

### 2.3 本地工具（tools/ + vendor/）
- **aigc-toolkit.py**：统一入口（sprite/tileset/animation/pixelize/qa/export-tiled）
- **a2-pipeline.py**：A2 标准入口（prompt_vision→生图→Vision Gate→重试→manifest，一条命令）
- **godot-shot.py**：godot-assistant MCP stdio 客户端，场景截图（游戏内画面→Vision Gate）
- **contracts/style-assets.json**：风格资产契约（palette / 像素规格 / STYLE 块 / 场景模板），A2 生成时由 aigc-toolkit `--style` 注入 STYLE 块 + palette
- **image_backend.py**：生图统一后端（gpt-image-2 中转站，TLS 补丁）
- **prompt_vision.py**：**视觉提示词设计师**（gpt-5.5 视觉模型根据需求+风格基底+参考图，生成/修订生图 prompt；替代人工写提示词，A2 第一步）
- **vision_review.py**：gpt-5.5 视觉验收基础调用
- **vision_gate.py**：**Vision Gate 正式门禁**（类型化模板/阈值/结构化报告/manifest 写入）
- **validate-\*.py / qa_report**：程序化门禁
- **vendor/**：ai-pixel-art（已验证）、agent-sprite-forge、spine-animation-ai、FrameRonin-MCP、character-animation-creator
- 待装（网络恢复/需 key）：game-asset-mcp（HF token）、sprute（Gemini）、perfectpixel-studio、Gorest、pixellab-mcp（远程云端，需 pixellab token）

### 2.4 Vision Gate（视觉模型验收门禁，正式环节）
- **定位**：流水线正式验收环节，所有资产产出后**强制**过审（非临时评审）
- **执行**：gpt-5.5 挑刺式验收，按资产类型用标准验收模板（sprite/tileset/map/animation/spine/character）
- **输出**：结构化 JSON 报告（多维评分 + overall + verdict + issues + improvements + summary），写入资产 manifest 的 `qa.vision` 段
- **阈值**：默认 7.0（可配置 `--threshold`）；PASS 才进下一环节
- **用法**：`python tools/vision_gate.py <img...> --type map --name xxx --threshold 7.0 [--ref 锚点] [--manifest m.json]`
- **多维评分**：每类资产 5 个维度（如 map=布局自然度/瓦片平铺/物件风格统一/可玩性结构/整体观感）
- **结论驱动**：FAIL 时以 issues/improvements 作为下一轮迭代输入（W2 地图正式 gate 4.1 → 打磨项明确：降噪/过渡瓦片/地标/树丛群落）

---

## 3. 资产契约（环节间传递）

```json
{
  "schema": "asset.manifest.v1",
  "type": "sprite | tileset | map | animation | spine | godot-project",
  "artifacts": ["assets/demo/xxx/yyy.png"],
  "meta": {"prompt": "...", "params": {...}, "model": "gpt-image-2", "cost_cny": 0.5, "duration_s": 90},
  "qa": {
    "programmatic": {"palette_fidelity": 1.0, "alpha_crispness": 1.0, "gate": "PASS"},
    "vision": {"overall": 7.5, "scores": {...}, "verdict": "PASS", "issues": [], "gate_result": "PASS"}
  },
  "confirmed": false
}
```
- 每个环节产出 = artifact + manifest；跨环节只认 manifest
- 人工确认点：精灵/地图/动画预览确认后进下一步（保留 AIGC 挑选权）

---

## 4. 执行流程示例（自然语言 → Godot 产物）

**用户输入**：「生成一个宝可梦式的俯视地图，艾琳 8 向移动，草/水/树地形」
```
[编排] 解析需求 → spec（地图类型=宝可梦式网格、地形=草/水/树、角色=艾琳8向、引擎=Godot）
  → 分派：
   A2 资产生成：
     - prompt_vision.py（视觉模型生成/修订生图 prompt：需求+风格基底+参考图 → prompt JSON）
     - ai-pixel-art generate_tileset（无缝俯视瓦片）→ 程序化 QA 门禁
     - generate_sprite（树）→ pixelize（角色 8 向 64px，与瓦片同调色板）
   A3 质量门禁：
     - 程序化 QA：qa_report（palette/alpha/seam 硬门禁）→ 全 PASS
     - Vision Gate：vision_gate.py --type map（gpt-5.5 结构化验收）→ >=7.0 PASS
   A4 引擎集成：Godot TileMapLayer 场景（网格地图 + 碰撞 + Y-sort + 8 向移动）
  → 汇总：manifest + start cmd → 用户运行验收
[归档] 产物入库 + lessons-learned 回填（FAIL 的 issues/improvements 成为下轮输入）
```

---

## 5. 实现路线（分阶段）
| 阶段 | 内容 | 状态 |
|---|---|---|
| **W0 工具层** | skills 6 + frame-ronin MCP + vendor + aigc-toolkit + **vision_gate** | ✅ |
| **W1 编排骨架** | manifest schema + 分派规则（本会话即编排 agent） | ✅（约定已定） |
| **W2 宝可梦式地图全链** | 自然语言→瓦片→地图→Godot demo（首个端到端用例） | ✅ 闭环完成（godot-pokemon-demo/）；正式 gate FAIL(4.1<7) → W2.1 打磨 |
| W2.1 地图打磨 | 新瓦片集 + 域扭曲大块草地/有机湖/道路/村庄地标/成林树丛，全景 gate 6、游戏内 5（vision issues 驱动，未达 7 继续） | ⏳ 进行中（2026-08-19：3→6） |
| **W3 角色/动画全链** | 8 向精灵→行动画→Spine（A 路线）接入 | 📋 |
| **W4 八方旅人式 2.5D** | Hybrid2D3D 集成（H3） | 📋 |
| **W5 评测/反馈闭环** | agent eval 平台接自家 agent（harness 质量/执行质量多维评分） | 📋 |

---

## 6. 与现有文档关系
- 本文件 = 项目中心（编排层）；industrial-pipeline-v2.md（S0-S5 orchestrator）作为底层实现参考
- godot-2d-aigc-practice-research.md（H 系列）= 游戏开发子路线，挂在 A2/A4 环节下
- aigc-tools-integration.md = 工具层清单（harness 来源）
- PROJECT-INDEX.md = 总索引

## 7. 决策记录
- 2026-08-19：确定项目中心 = agent workflow（编排 agent + 执行 agent + harness + 契约 + 门禁 + 反馈）
- 2026-08-19：**Vision Gate 正式化为流水线环节**（vision_gate.py，类型化模板/阈值/结构化报告/manifest 写入）；W2 地图首个标准用例 gate FAIL(4.1) → 打磨项驱动 W2.1
- 工具层已装：6 skills + frame-ronin MCP + 6 vendor 工具；待装 5 个（网络/key 限制）
