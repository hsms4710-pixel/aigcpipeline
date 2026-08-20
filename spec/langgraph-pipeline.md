# LangGraph 重构完整 pipeline（spec/langgraph-pipeline.md）— P0 第一优先

> 日期：2026-08-21 ｜ 触发：用户「整理当前整个项目的文档和文件；把用 langgraph 重构整个 pipeline 作为第一重要任务」
> 更新：2026-08-21 v2 —— 完整链路全部 LangGraph 化（S0 生图→S5 引擎全接线真实工具）
> 更新：2026-08-21 v3 —— **三路线覆盖**：骨骼 A（S0-S5）+ 关键帧 B（kb1-kb2）+ 3D F（f1-f5，后续补充）；
>   **workflow 与节点实现解耦**（图只编排，实现层 pipeline/stage_executors.py 可被节点/workbench 复用，不冲突）
> 状态：**P0（第一优先）**，实现落地于 `pipeline/langgraph/` + `pipeline/stage_executors.py`，任务跟踪 `tasks/pipeline/tasks.md`（L0-L6）
> 上位文档：`spec/agent-workflow.md`（A1-A6 编排视图）、`spec/industrial-pipeline-v2.md`（S0-S5 蓝图）、
>   `spec/frame-anim-workflow.md`（B 关键帧路线）、`spec/plan-3d-route.md`（F 3D 路线）

---

## 0. 一句话结论

项目主体是 **agent 驱动的 AIGC pipeline**。把「脚本 + FastAPI workbench + 人工串联」的编排**完整重构为 LangGraph StateGraph**，
并**同时覆盖三条资产路线**：
- **A 骨骼路线**（Spine）：`A1 → S0 生图 → S1 拆层 → S2 绑骨 → S3 动画 → S4 打包 → S5 引擎 → A6`
- **B 关键帧路线**（帧动画）：`A1 → kb1 关键帧生成 → kb2 Godot 帧动画工程 → A6`
- **F 3D 路线**（后续补充）：`A1 → f1 生成 → f2 Blender → f3 绑骨 → f4 动作 → f5 Godot 3D → A6`

**workflow 与节点实现不冲突**：图（graph.py）只负责编排/路由/门禁；每个节点的具体实现
收敛到共享实现层 `pipeline/stage_executors.py`（纯函数，可被 LangGraph 节点、workbench、脚本复用），
实现只有一份、两处共用，不重复不冲突。

---

## 1. 架构（完整 pipeline StateGraph，三路线）

```
START ──► A1 a1_plan ──► 路线路由（state.route：skeletal / keyframe / 3d，可由 --route 覆盖）
                             │
   ┌─ skeletal（骨骼 A）: S0（persona→s0_gen_portrait ｜ demand→a2_skill→a2_prompt→a2_generate→a3_gate）
   │                      → S1 拆层 → S2 绑骨 → S3 动画 → S4 打包 → S5 引擎
   ├─ keyframe（关键帧 B）: kb1 关键帧生成（gen-frame-cycle）→ kb2 Godot 帧动画工程（对齐+AnimatedSprite2D）
   └─ 3d（后续补充 F）:    f1 生成 → f2 Blender → f3 绑骨 → f4 动作 → f5 Godot 3D
   各路线终点 → A6 归档 → END
```

**门禁/路由规则**（各路线统一）：
| 条件 | 去向 |
|---|---|
| S0 门禁 PASS/SKIP | 下一 stage |
| S0 门禁 FAIL & attempts < max_tries | a2_prompt（带 issues 修订重试；skill_ctx 复用） |
| S0 门禁 FAIL & attempts ≥ max_tries | A6（如实 FAIL） |
| 任意 stage FAIL | A6（gate_strict 严格模式即停；否则记录后 A6） |
| 任意 stage SKIP/STUB/WARN | 如实记录并前进下一启用 stage |

---

## 2. 状态设计（pipeline/langgraph/state.py）

`PipelineState`（TypedDict，节点间唯一契约通道）：
- **输入**：demand/style/atype/name/route/refs/baseline/size/…；persona/scene/backend/model（人物卡驱动）；
  s1_src/s2_psd/s3_input/s4_input/s5_input/godot_exe（单 stage 独立跑）；kb_hero/kb_style/kb_only/kb_frames（B 路线）
- **A1**：plan（asset.plan.v1，含 route + pipeline 视图）
- **各 stage 契约**：`stage_outputs[<stage>] = {status, out, gate, reason}`
  - s0.out={image_path}；s1.out={layered_dir,psd}；s2.out={rig_zip}；s3.out={anim_zip,gif,usage,cost}；s4.out={package_dir}；s5.out={godot_dir,project}
  - kb1.out={frames_dir,frames,meta}；kb2.out={godot_dir,project}；f1-f5.out={tool}（契约/桩）
- **A6**：manifest（asset.manifest.v2，含 route + stages 各状态/gate/reason + artifacts）、final_status、log

**诚实原则**：工具/服务缺失（See-through 未装、StretchyStudio 未起、3D 未实现等）时 status=STUB/SKIP/FAIL 并给原因，绝不假装 PASS。

---

## 3. 三路线节点与真实工具接线

### A 骨骼路线（Spine，当前主链）
| 节点 | 底层工具（真实接线） | 门禁 | 状态 |
|---|---|---|---|
| A1 a1_plan | 规则解析 demand→plan（含 route 判定） | — | ✅ |
| S0 s0_gen_portrait | tools/gen-portrait.py（persona→立绘/表情/小人） | — | ✅ |
| S0 a2_skill | **LangGraph 三级渐进披露加载 skill**（skills_library + skill_loader） | — | ✅ |
| S0 a2_prompt | tools/prompt_vision.design_prompt（skill_ctx 复用） | — | ✅ |
| S0 a2_generate | tools/image_backend.gen_image（openai/gemini/fal + TLS） | — | ✅ |
| S0 a3_gate | tools/vision_gate.run_gate()（threshold 7.0） | PASS/FAIL/SKIP | ✅ |
| S1 s1_decompose | See-through inference_psd_blockswap.py（HF offline） | validate-layered（WARN 非致命） | ✅ |
| S2 s2_rig | rig-automation/rig-psd.cjs + fix-rig | validate-rig（FAIL→lessons；strict 即停） | ✅ |
| S3 s3_animate | rig-automation/stretchy-agent.cjs（AGENT_MODEL + --rules 注入经验）+ fix-rig + usage 成本 | validate-anim | ✅ |
| S4 s4_package | package-assets.py（atlas） | validate-asset-package | ✅ |
| S5 s5_engine | export-godot.py（Godot SpinePlayer） | 工程生成 | ✅ |

### B 关键帧路线（帧动画，已覆盖）
| 节点 | 底层工具 | 门禁 | 状态 |
|---|---|---|---|
| kb1 kb1_keyframes | tools/gen-frame-cycle.py（单锚点 hero + 固定风格块 + FRAMING，idle/walk/attack/hurt） | frames+meta 存在 | ✅ |
| kb2 kb2_godot_anim | tools/build-godot-anim-demo.py（核心身体对齐 + AnimatedSprite2D + 状态机） | project.godot 生成 | ✅ |

### F 3D 路线（后续补充，契约+桩）
| 节点 | 规划工具 | 状态 |
|---|---|---|
| f1 f1_gen3d | 3D 生成：Tripo API / 混元3D / Meshy（text/image→glTF mesh+贴图） | 📋 桩（STUB，待 L4） |
| f2 f2_blender | Blender 修正：减面/UV/法线/材质（dcc-mcp-creator / Blender Python） | 📋 桩 |
| f3 f3_rig | 绑骨：Mixamo / RigNet / Blender Rigify（自动骨骼+蒙皮） | 📋 桩 |
| f4 f4_motion | 动作：动作库 / 手K / SCAIL2 动作迁移 | 📋 桩 |
| f5 f5_godot3d | Godot 3D 导入：glTF→场景+动画 demo（引擎无关资产） | 📋 桩 |

---

## 4. workflow 与节点实现解耦（不冲突）

> 用户明确：「langgraph workflow 和 workflow 每个节点的具体实现是不冲突的」。

- **编排层**（`pipeline/langgraph/`）：graph.py（StateGraph+路由+门禁）、state.py（契约）、nodes.py（节点=编排单元，薄封装）
- **实现层**（`pipeline/stage_executors.py`）：每个 stage 的具体实现是**纯函数** `exec_*`（入参 cfg/job_dir，返回
  {status, out, gate, reason, log_tail}），不依赖 LangGraph，也不依赖 workbench 的 DB——
  **LangGraph 节点调用它，workbench 也可以调用它**，实现只有一份，天然不冲突。
- 迁移路径：workbench 的 `_exec_sN` 后续改为调用 `stage_executors.exec_sN`（L6），前端 10 Tab 不变。

---

## 5. 任务拆解（L0-L6，跟踪见 tasks/pipeline/tasks.md）

| 任务 | 内容 | 状态 |
|---|---|---|
| L0 | 立项：spec + 任务表 + langgraph 依赖 | ✅ |
| L1 | pipeline/langgraph 包：state/nodes/graph/cli | ✅ |
| L2 | skill 三级渐进披露接入 S0 | ✅ |
| L3 | S0 门禁闭环：a3_gate 条件路由 + FAIL 带 issues 回退重试 | ✅ |
| L3.5 | **完整 S0-S5 接线**（骨骼 A） | ✅（离线验证） |
| L3.6 | **B 关键帧路线**（kb1-kb2）+ **F 3D 路线契约/桩** + **实现层 stage_executors 解耦** | ✅（离线验证） |
| L4 | 真实跑通：See-through/StretchyStudio/deepseek/Tripo 服务就绪后全链实测 | 📋 |
| L5 | 可观察性：job 记录/断点续跑/成本核算 + 前端接线 | 📋 |
| L6 | workbench 后端改调 stage_executors（前端 10 Tab 不变） | 📋 |

---

## 6. 用法（CLI）

```bash
# A 骨骼路线（persona 全链）
python pipeline/langgraph/cli.py --persona assets/demo/persona.json --scene splash --name ailin_v11 --out-dir pipeline/artifacts/job_xxx
# A 骨骼路线（demand 生图链）
python pipeline/langgraph/cli.py --demand "宝可梦风艾琳 4 向角色" --type character --name ailin_v11
# B 关键帧路线
python pipeline/langgraph/cli.py --demand "艾琳 4 向帧动画" --route keyframe --kb-hero assets/demo/style_batch/transparent_v2/hero_hd2d_final.png --kb-style hd2d --name ailin_kb
# F 3D 路线（桩，后续补充）
python pipeline/langgraph/cli.py --demand "3d 角色模型" --route 3d --name char_3d
# 离线冒烟（不执行外部工具）
python pipeline/langgraph/cli.py --demand "..." --route keyframe --dry-run
# 部分 stage（断点续跑）
python pipeline/langgraph/cli.py --demand "..." --stages s4,s5 --s4-input <zip> --out-dir <dir>
```

---

## 7. 验证与 gate

- **L1-L3.6 gate**：`py_compile` 全过；三路线 `--dry-run` 整图编译+路由+命令构造通过（骨骼：s0-s5；关键帧：kb1-kb2；3D：f1-f5 STUB）
- **L4 gate（真实跑）**：See-through（GPU）→ StretchyStudio（5173/5174）→ deepseek → package → godot；B 路线 gen-frame-cycle 出帧→Godot 工程；中转站恢复后 S0 Vision Gate threshold 7.0
- **后续**：F 3D 实现（L4.5）、可观察性（L5）、workbench 接线（L6）
