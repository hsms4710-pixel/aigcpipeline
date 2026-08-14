# 工业级工作流整合方案（spec/industrial-pipeline-v2.md）

> 日期：2026-08-14 ｜ 背景：用户要求"不再单点推进，重新整合成一套工业级工作流"
> 依据：`生图.md`（网易 DreamMaker 调研）+ `spec/2d-asset-skeletal-workflow.md`（工业化对照）+ 本仓库 P1-A~E 实际沉淀
> 状态：本文件是整合蓝图（v2），替代"各 spec 各说各话"的现状，成为唯一权威工作流定义。

---

## 0. 一句话结论
**单点工具已经齐了（甚至 2D 自动绑骨领先网易），缺的是"编排层 + 资产契约 + 阶段门禁 + 可观察性 + 反馈闭环"。**
整合目标：把 `生图 → 拆层 → 绑骨 → 动画 → 打包 → 引擎` 变成一条**可重跑、可审计、可归因、成本可核算**的管线，每阶段由 LLM agent 执行 + 契约校验 + 人工确认点。

---

## 1. 差距分析（现状 vs 生图.md 工业级）

### 1.1 逐环节对照
| 环节 | 生图.md / 工业级 | 我们当前 | 差距 | 优先级 |
|---|---|---|---|---|
| **0 生图** | DreamMaker 底座 + SunshineFlow 蓝图编排、批量、单张成本核算（0.008元）、效果预览 | GPT-Image-2 多参考 + prompt 模板（contracts/prompt-templates）+ tools/image_backend.py | 无编排、无 job 队列、无批量、无成本/耗时核算 | P0 |
| **1 拆层** | CHORD 分解+超分，180s 端到端 | See-through blockswap bf16，~20min/张 | 慢 6x；缺超分（1k→2k）；遮挡补全 B3 未做；无标准 PSD 命名门禁 | P0 |
| **2 绑骨** | ❌ 网易无 2D 自动绑骨（编辑器手工） | **StretchyStudio DWPose 自动绑骨 ✅（领先）+ LLM 微调 + .stretch/Spine 导出** | 已领先；但未固化为 pipeline stage、无 rig 质量门禁 | P1 |
| **3 动画** | 编辑器为主 + AI 动作补全（3D 已落地） | **LLM agent（deepseek）生成骨骼关键帧 ✅ + Spine 4 动画导出** | 已领先；缺动画质量门禁（幅度/曲线/循环闭合检查） | P1 |
| **4 打包** | Cutlas 图集自动化 + SpineComponent | 帧动画 Godot demo + spine zip（未打 atlas） | 未做 Spine atlas / 图集打包 / runtime 接入 | P0 |
| **5 引擎** | Wuzu 替换链路（UE） | Godot 帧动画 demo（chibi 7 姿势） | 未接 Spine runtime；未接 LLM agent 动画到引擎 | P1 |
| **横切-编排** | SunshineFlow 蓝图、job 状态机、阶段产物可见 | 独立脚本/工具 + 文档，人工串联 | **最大差距：无统一编排** | P0 |
| **横切-契约** | 资产管线 schema 校验 | 分散 validate-*.py（persona/layered/asset） | 无统一 contract schema + gate 自动执行 | P0 |
| **横切-可观察** | 阶段进度/耗时/成本/产物 | 无 | job 记录、成本核算、审计自动归档 | P0 |
| **横切-反馈** | 效果回填、自动重试 | lessons-learned.md 手工记录；A5 反馈飞轮 todo | 反馈未闭环（失败→原因→规则→自动规避） | P1 |

### 1.2 核心判断
1. **单点能力已超过生图.md 的 2D 段**（网易 2D 自动绑骨是缺口，我们用 StretchyStudio+LLM 补上了）。
2. **差距集中在"系统层"**：编排、契约、门禁、可观察性、反馈。这些是"工业级" vs "脚本堆积"的分水岭。
3. **不重造工具**：所有 stage 复用已有工具/脚本/agent，只加一层编排 + 契约 + gate。

---

## 2. 目标架构（v2 工作流）

```
┌─────────────────────────────────────────────────────────────────────┐
│  pipeline orchestrator（编排层，Node/Python 状态机）                  │
│  job 记录：阶段 / 耗时 / 成本 / 产物 hash / 人工确认点 / audit        │
└───────┬─────────────────────────────────────────────────────────────┘
        │ 每个 stage：输入契约 → LLM/工具 agent 执行 → 输出契约 → gate
        ▼
┌───────┴────────┐   ┌──────────────┐   ┌─────────────┐   ┌────────────┐
│ S0 生图         │ → │ S1 拆层       │ → │ S2 绑骨      │ → │ S3 动画     │
│ 立绘/表情/小人  │   │ See-through   │   │ Stretchy     │   │ LLM agent  │
│ GPT-Image-2    │   │ blockswap     │   │ Studio+DWPose│   │ 关键帧      │
│ +prompt模板    │   │ +超分(补)     │   │ +LLM微调     │   │ Spine导出  │
└───────┬────────┘   └──────┬───────┘   └──────┬──────┘   └─────┬──────┘
        │契约: persona+ref │契约: Live2D PSD  │契约: .stretch  │契约: spine
        ▼                  ▼                  ▼                ▼
┌───────┴────────┐   ┌──────────────┐   ┌─────────────────────────────┐
│ S4 打包        │ → │ S5 引擎接入   │   │ 反馈闭环（memory/lessons）    │
│ Spine atlas   │   │ Godot runtime │   │ 失败→原因→规则→自动规避      │
│ 图集/清单      │   │ + 交互 demo   │   └─────────────────────────────┘
└────────────────┘   └──────────────┘
       每阶段 gate：validate schema + 质量检查 + 人工确认（AIGC 随机性保留挑选权）
```

### 2.1 编排层设计（pipeline/）
```
pipeline/
├── orchestrator.py        # 状态机：stage 注册 / 依赖 / 重试 / 断点续跑
├── contracts/             # 每阶段 JSON schema（input/output）
│   ├── s0_persona.schema.json
│   ├── s0_artifacts.schema.json     # full/bust/exp/chibi + metadata
│   ├── s1_layered_psd.schema.json   # 层命名/数量/尺寸/透明
│   ├── s2_rig.schema.json           # bones/slots/params/animations
│   ├── s3_anim.schema.json          # clips/关键帧/循环闭合
│   └── s4_package.schema.json       # atlas + 清单 + 引擎中立
├── gates/                 # 每阶段自动门禁脚本（复用现有 validate-*.py）
├── jobs/                  # job 记录：stage/耗时/成本/产物hash/确认点
├── agents/                # 每阶段 LLM agent（复用 stretchy-agent 模式）
│   ├── stage_agent_base.py
│   ├── agent_rig.py       # 调 stretchy-studio + __ss 桥
│   ├── agent_anim.py      # 调 stretchy-agent.cjs（deepseek）
│   └── agent_eval.py      # LLM 质量门禁（幅度/一致性/循环）
└── memory/                # 反馈闭环：lessons 自动回填 + 规则库
```

### 2.2 每阶段 LLM agent 化（延续"不要硬脚本"）
- 每个 stage 一个 agent，输入契约 JSON + 任务描述 → LLM 决策 → 调用底层工具（image_backend / see-through / __ss 桥）→ 输出契约 JSON
- orchestrator 只做**流程编排**（依赖/重试/门禁/记录），不写死创作参数
- 人工确认点：每阶段产物可预览（立绘/分层/绑骨姿势/动画 GIF），确认后进下一阶段（保留 AIGC 挑选权）

### 2.3 资产契约（标准包）
每个 stage 输出 = `artifact + manifest.json`，manifest 含：schema 版本、产物 hash、耗时、成本、参数、agent 版本、人工确认状态。跨阶段只认 manifest。

---

## 3. 落地路线（增量，不推翻现有）
| 里程碑 | 内容 | 产出 | 验证 |
|---|---|---|---|
| **M0 编排骨架** | orchestrator + jobs 记录 + 阶段注册（S0-S5 占位接现有工具） | 一条命令跑通现有单点（生图→拆层→绑骨→动画→导出） | 端到端可重跑，job 有记录 |
| **M1 契约+门禁** | contracts schema + gates 自动执行（复用 validate-*.py，补 rig/anim gate） | 每阶段失败即停 + 原因可查 | 故意坏输入被 gate 拦截 |
| **M2 阶段 agent 化** | S2/S3 接 LLM agent（rig 微调/动画创作），S0/S1 接参数化 agent | 每阶段"描述任务→agent 干活" | LLM 决策产出可复现（seed 记录） |
| **M3 引擎闭环** | S4 atlas + S5 Godot Spine runtime 接入 + 反馈闭环 | Godot 播放 LLM 动画 + lessons 自动回填 | demo 可玩 + 失败自动规避 |

**建议起点**：M0（编排骨架）+ S4 打包（Spine atlas）先行——前者解决"系统层"最大差距，后者补最明显的"没进引擎"缺口。

---

## 4. 与现有文档的关系（整合后）
- `链路总览.md`：Part 边界保留，但把"工作台"形态升级为"pipeline orchestrator"
- `ROADMAP.md`：双管线（2D 线 P1-A~E）并入本方案的 S0-S5 阶段
- `spec/2d-asset-skeletal-workflow.md`：作为阶段工具选型参考，不重复定义流程
- `生图.md`：作为工业级参照（编排/成本/反馈），差距对照见本文件 §1
- 现有 tools/*.py 全部保留，作为 stage 的底层执行器

---

## 5. 本轮已落地成果（整合前的基础）
- P1-A 画风 ✅ / P1-B 拆层 ✅ / P1-C 绑骨 ✅（StretchyStudio 领先）/ P1-D 动画 ✅（LLM agent 驱动）
- 关键新能力：`window.__ss` 桥接（编程控制编辑器）+ `stretchy-agent.cjs`（LLM 驱动动画）+ `keep-awake`/`rig-psd`/`preview-anim` 工具
- 动画产出：`assets/demo/char_ailin_anim/`（4 动画 .stretch + Spine + GIF 预览）
