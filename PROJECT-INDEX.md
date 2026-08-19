# 角色 AIGC → AI NPC → 引擎接入 → 评测 ｜ 项目总览索引（PROJECT-INDEX.md）

> 整理日期：2026-08-19（2026-08-19 新增：A2 流水线 / godot-assistant / W2.1 地图） ｜ 本文件是**唯一入口索引**：整合全部零散文档、任务进度、代码、工程与产物。
> 更新规则：新增文档/任务/产物时，在本文件对应章节追加一行（保持本文件权威）。

---

## 0. 一句话定位
把「角色形象/语音 AIGC 生成 → AI NPC（记忆/行为/对话）→ 引擎接入（Godot 新建 / 现有游戏 Mod）→ 评测」做成可观察、可归因、可复用的工作流；当前聚焦 **2D 横板游戏 demo（艾琳主角）+ 2D 骨骼动画流水线**，3D 线后置。

## 1. 当前状态（2026-08-19）
- ✅ P1 形象+语音工作台已交付（2026-08-13）；2D 画风定稿（v10 立绘 + chibi_v4 小人锚点）
- ✅ 2D 帧动画 B 路线（对齐+合成+Godot AnimatedSprite2D）已跑通；艾琳**像素/HD-2D 双风格侧视帧**已接入横板 demo
- ✅ 2D 横板游戏基座（SunnyLand Forest 官方地图 + 箭矢/跳跃/攻击/落地缓冲 + 攻击自伤修复）可玩
- ⏳ **2D 骨骼动画 A 路线（Spine）**：规划完成（plan-2d-skeletal.md），阻塞点=See-Through LayerDiff3D 模型下载（需 hf-mirror）
- ⏸️ 3D 线后置（plan-3d-route.md 已重新调研）；P2 过场/P5 评测后置；P3 Agent/P4 引擎接入规划中
- ⚠️ 外部依赖：生图中转站 api.sisct2.xyz 间歇性故障（影响重生成/视觉验收）
- ✅ **2026-08-19 A2 资产生成标准入口**（tools/a2-pipeline.py）：视觉提示词→生图→Vision Gate→自动重试→manifest；瓦片集实测 PASS 7.0
- ✅ **2026-08-19 Godot MCP 实装**（godot-assistant）+ tools/godot-shot.py 游戏内截图→Vision Gate
- ✅ **2026-08-19 W2.1 地图打磨**：A2 瓦片集 + 域扭曲草地/有机湖/村庄/成林树丛；全景 gate 6、游戏内 5（未达 7，待办见 spec/agent-workflow.md）

## 2. 调研清单（spec/ 内，按主题）
| 文档 | 主题 | 状态 |
|---|---|---|
| spec/pipeline-unified-2d3d.md | 2D+3D 双管线统一分析（网易 DreamMaker 缺口对照） | 权威基线 |
| spec/2d-asset-skeletal-workflow.md | 2D 生图→资产→骨骼工业化 workflow | 权威基线 |
| spec/2d-skeletal-auto-research.md | 2D 自动绑骨 + 像素小人（bilibili 实践）调研 | 已完成 |
| spec/pipeline-remaster-2d-skeletal.md | 2D 骨骼动画工业级流水线重规划（烂因+五步法） | 权威 |
| spec/arm-animation-quality-fix.md | 手臂动画质量修复（拆臂/枢轴/FK） | 已完成 |
| spec/comfyui-lora-plan.md | ComfyUI + 风格 LoRA 锁画风 + 生图参考 API 调研 | 规划 |
| spec/style-research.md | 画风研究（pixel/hd2d/soft 等 8 风格） | 已完成 |
| spec/style-reference-constraints.md | 画风参考约束 | 已完成 |
| spec/TECH-STACK.md | 技术栈选型基线 | 权威 |
| spec/industrial-pipeline-v2.md | 工业流水线 v2 | 调研 |
| spec/pipeline-architecture.md + .svg | 流水线前后端架构（无 emoji） | 权威 |
| spec/plan-2d-skeletal.md | **2D 骨骼生成路线（本文件新增）** | 规划 |
| spec/plan-3d-route.md | **3D 模型路线（本文件新增，重新调研）** | 规划 |
| spec/godot-2d-aigc-practice-research.md | **Godot 2D/2.5D AIGC 实践调研**（bilibili/YouTube HD-2D/伪3D） | 2026-08-19 |
| spec/aigc-tools-integration.md | **AIGC 开源工具集成清单 + 2D 地图类型调研**（godot-assistant 已装 / godot-ai 待装） | 2026-08-19 |
| spec/agent-workflow.md | **Agent Workflow 中心规划**（A1-A6 + harness + Vision Gate + godot-assistant） | 权威（2026-08-19） |
| 生图.md / 工作流设计.md / 研究计划.md | 网易 DreamMaker 调研 / 管线衔接 / 研究问题 | 根目录 |
| ROADMAP.md | 实现路线（Part 0-6） | 权威 |

## 3. 实施路线
### 3.1 总路线（ROADMAP.md）
```
P0 地基 ✅ → P1 形象+语音 ✅ → P3 Agent(规划) → P4 引擎接入(M0✅) → P2 过场(后置) → P5 评测(后置)
DCC 加工层(P6) 横切：3D 修正 / 2D 分层绑定 / 引擎导出 / Mod 辅助
```
### 3.2 双管线（spec/dev-roadmap-2d3d.md）
| 阶段 | 名称 | 状态 |
|---|---|---|
| P1-A | 画风定稿 + 生图基线 | ✅ v10/chibi_v4 锚点 + style_batch 变体 |
| P1-B | 2D 资产拆层（→ Live2D 规范 PSD） | ✅ See-Through 拆层 18 层 PSD |
| P1-C | 2D 骨骼绑定 | ✅ StretchyStudio DWPose 自动绑骨（13-18 bones）|
| P1-D | 2D 动画 | ⚠️ B 帧动画 ✅；A 路线 Spine 阻塞（hf-mirror）|
| P1-E | 打包/引擎 | ✅ Godot 横板 demo（帧动画+地图+战斗）|
| P2-3D | 3D 线（后置） | 📋 已重新调研（plan-3d-route.md）|

### 3.3 2D 骨骼动画（当前重点，详见 spec/plan-2d-skeletal.md）
- **B 路线（帧动画，已跑通）**：AI 关键帧 → 对齐 → AnimatedSprite2D（当前横板在用）
- **A 路线（Spine 骨骼，规划）**：See-Through 拆层 PSD → StretchyStudio 绑骨 → Spine 导出 → Godot runtime；**根治 AI 帧抖动**
- 五步工业法：部件拆分→标准骨层级+枢轴→网格蒙皮权重→IK→12 原则关键帧

## 4. 任务与进度（tasks/）
| 文件 | 内容 |
|---|---|
| tasks/pipeline/tasks.md | **主进度表**（A0-A5/B1-B4/C1-C4/D1-E3/F1-F5 + G1-G3 + 2026-08-17/18 迭代记录）|
| tasks/backlog.md | 总 Backlog（Part 1-5 + 双管线 + M0 + chibi_apose + 风格/锚点）|
| tasks/p1/ | P1 形象+语音任务拆解（t1-t11 全 done）|
| tasks/p2..p5/, voice/ | 后置/规划占位 |

### 关键进度（最新）
- ✅ 攻击自伤修复（mask=2 + 排除自身 + 攻击窗口轮询）
- ✅ 箭矢投射物（水平方向修复）+ 命中验证 40→15
- ✅ 艾琳侧视帧（像素 8/10、HD-2D 7.5/10 vision 验收）
- ✅ walk 稳定性：重生成+锚点对齐（bottom 全 160、cy 漂移≤1.3px）；挑刺验收循环 6/10（AI 帧固有局限）
- ⏳ 根治方案：A 路线 Spine 骨骼动画（阻塞 See-Through 模型下载）

## 5. 参考文档（reference/）
- reference/style-library/（风格标杆库：阿米娅-唯@W）
- reference/ 其余为调研源（含 FGO/PRTS 素材站、OpenGameArt/Kenney/SunnyLand/TinyRPG 资产源）
- reference/aigc-km/（AIGC 方法论 KM 文章库：LoRA 锁画风 / 一致性控制 / 白模统一绘制 / GamePipeline 标准化，INDEX.md 含目录+要点）
- 外部资产源（env/assets/）：kenney(topdown/rpg-urban)、tiny-rpg-forest、sunny-land(+forest)

## 6. 主体文件（根目录）
README.md（总述）/ ROADMAP.md（路线）/ 研究计划.md（RQ+评测）/ 链路总览.md（Part 边界）/ 工作流设计.md（管线衔接）/ 生图.md（网易调研）/ PROJECT-INDEX.md（本文件）

## 7. 项目代码（tools/）
| 类别 | 工具 |
|---|---|
| 生图 | image_backend.py（统一后端）、gen_portrait.py、gen-chibi-*.py、gen-frame-cycle.py（关键帧）、gen-side-frames.py（侧视）、gen_prompt.py |
| 对齐/动画 | align-game-frames.py、align-side-frames.py、build-godot-anim-demo.py、build-frame-anim-godot.py、regen-walk*.py |
| 拆层/绑骨 | split-limb.py、split-spine-arm.py、split-spine-limb.py、fix-rig.py、render_fk_frames.py、render_bone_overlay.py、build-spine-from-image.py、check_joint_tear.py |
| 地图/资产 | port-tiny-rpg-map.py、port-sunnyland-map.py、build-kenney-atlas.py |
| 校验 | validate-*.py（persona/layered/rig/anim/asset-package）、vision_review.py（视觉验收）|
| 工作台 | pipeline/（FastAPI+React，见 spec/workbench-v2.md）、tools/rig-automation/stretchy-agent.cjs |

## 8. 工程文件（assets/demo/godot-*）
| 工程 | 内容 |
|---|---|
| **godot-game-base/** | **当前主游戏**：2D 横板（SunnyLand Forest 地图+艾琳侧视+箭矢+史莱姆→slug），启动 start-game.cmd |
| godot-chibi-anim-hd2d-v2/ godot-chibi-anim-pixel/ | 帧动画演示工程（B 路线产物）|
| godot-char-demo/ godot-chibi-v2-demo/ godot-import-demo/ | 早期角色展示/导入验证 |
| 引擎：Godot 4.7.1（C:\Users\26046\Documents\lovegaming\）|

## 9. 流水线产物（assets/demo/）
| 产物 | 说明 |
|---|---|
| char_ailin_v10/ + chibi_v4/ | 画风锚点（立绘+Q版）|
| style_batch/ | 8 风格变体 + transparent_v2（对齐 hero/pose/关键帧/审查拼图）|
| char_ailin_m04/ char_ailin_anim/ | 骨骼动画产物（FK 帧、Spine zip、预览 GIF）|
| godot-game-base/assets/ | 横板资产：ailin_pixel_side / ailin_hd2d_side / hero / slug / arrow / tiles / maps / bg |
| contracts/persona-schema.json + prompt-templates/ | 人设卡 schema + 提示词模板 |
| tiles_hd2d/ + maps/ai_forest.map.json | **G1 AI 瓦片地图**（HD-2D 128px atlas + Godot 横板地图，start-ai-map.cmd） |
| audit/ | 审计清单+日志 |

## 10. 外部依赖与阻塞
- 生图中转站 api.sisct2.xyz：生图/视觉间歇故障（影响重生成/验收）
- See-Through LayerDiff3D 模型：需 HF_ENDPOINT=https://hf-mirror.com 下载
- 3D 线：Tripo 试用 key 有额度；TRELLIS2/Hunyuan3D 2.5 可本地（6-12GB VRAM）

## 11. 下一步建议（按优先级）
1. **A 路线 Spine 骨骼**（根治动画抖动）：配 hf-mirror 下载 LayerDiff3D → 拆层 → StretchyStudio → Spine → Godot
2. 2D 侧视帧补全（jump/fall/land 专用帧，生图端点恢复后）
3. 横板 demo 打磨（角色放大、投射物可见度、像素一致性）
4. 3D 线 POC（plan-3d-route.md）：TRELLIS2/Hunyuan3D 本地或 Tripo API → Blender → Mixamo/UniRig → Godot
