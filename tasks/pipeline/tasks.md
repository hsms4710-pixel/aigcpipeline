# 管线开发任务跟踪（tasks/pipeline/tasks.md）

> 路线详见 spec/dev-roadmap-2d3d.md；本表为执行跟踪。状态：todo / in_progress / done / blocked

## P1-A 画风定稿 + 生图基线
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| A0 | 建风格标杆库 + 反馈飞轮（manifest/lessons/preferences） | in_progress | style-library 阿米娅-唯@W 已建 |
| A1 | 用户选定主画风（style_attempts/compare_sheet/标杆库） | done | 方舟/唯@W 画风，gpt2_v10_styleSig.png 达标 |
| A2 | 分离式参考重生成三件套（风格图+角色锚点，v10） | done | char_ailin_v10（full/bust/4表情/转面）+ chibi_v4（Hero=front_b，8视图一致，已定稿） |
| A3 | 画风锁定决策：**云API失败→ComfyUI+风格LoRA/IP-Adapter** | done | lessons-learned 已记录 |
| A3.1 | 论坛调研 gpt-image-2 生图方法（linux.do sallyn 15维反推 / junyeo skill / tudingai 5图 / aiskillstore） | done | harness/skills/SKILL_gpt-image-2.md 已沉淀 |
| A3.2 | 新方法实测（多图分工+风格签名+TLS修复）：multi-ref 成功产出 gpt2_v10_styleSig.png | done | 待用户目检画风 |
| A4 | 沉淀画风 prompt 模板（升级 build_style_prompt：风格签名+角色分工+保锁清单+No-Beautify） | done | contracts/prompt-templates/{splash,chibi,pixel}.json + gen_prompt.py 已升级 |
| A5 | 反馈飞轮（审图回填 + lessons-learned） | todo | manifest quality + lessons 记录 |

## P1-B 2D 资产拆层
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| B1 | 搭拆层管线（See-through SIGGRAPH2026 官方仓库 + bf16 blockswap 8GB） | done | env/runtime/tools/see-through + venv(torch2.8+cu128) |
| B2 | 立绘拆层 → 分层 PSD（inference_psd_blockswap.py） | done | char_ailin_v10/layered/ 18层PNG+PSD+深度图 |
| B3 | 遮挡补全（PS 生成式/SAM2 修补） | todo | 待目检图层缺口；reconstruction.png 已生成 |
| B4 | 拆层校验脚本 | done | tools/validate-layered.py（PSD 18层 + 23 depth 配套，head depth 已知缺失） |

## P1-C 2D 骨骼绑定
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| C1 | 装 Spine / Live2D（StretchyStudio 部署：本地化 DWPose+wasm） | done | StretchyStudio @ env/runtime/tools/stretchy-studio，start-stretchy.cmd 一键启动 |
| C2 | 自动绑骨（DWPose，本地 ONNX） | done | char_ailin_v10 立绘自动绑骨成功（13 bones/25 slots，零报错） |
| C3 | 骨骼/权重校验修正 | done | 自动化绑定验证通过（立绘 13 bones/25 slots；chibi 18 bones/25 slots），浏览器可微调黄点 |
| C4 | 绑定小人+立绘表情参数 | done | 立绘+chibi 均完成：DWPose 绑骨 + Live2D 参数 + Spine 4.0 导出（spine_export.zip / front_b_spine.zip） |

## P1-D 2D 动画
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| D1 | 基础动画 idle/walk/attack/hurt | [注意]  已生成但质量不合格（无IK/权重/方法论），待 M0-M1 重做 |
| D2 | 表情切换动画 | in_progress | 4 表情 set_param 预览截图完成（happy/sad/angry/neutral）；mesh 变形表情仅 Live2D 导出支持，Spine 暂不支持 |
| D3 | 可选 AI 补帧（SCAIL2/2dimg2motion） | todo | 前后对比 |

## P1-E 打包/引擎
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| E1 | 图集打包（Spine atlas/TexturePacker） | todo | atlas 资源 |
| E2 | Godot 导入定稿资产（chibi_v4 + v10） | in_progress | godot-char-demo 已更新，headless 验证通过 |
| E3 | 交互雏形（移动/攻击/受伤/表情） | in_progress | demo.gd 可玩版完成，待用户试玩 |

## P2-3D 线（后置）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| F1 | 3D 生成（Tripo/混元3D/Meshy） | todo | mesh+贴图 |
| F2 | Blender 修正（减面/UV/法线） | todo | 修正模型 |
| F3 | Mixamo/RigNet 绑骨 | todo | 绑定模型 |
| F4 | 动作（动作库/手K/SCAIL2） | todo | 动画资源 |
| F5 | Godot 导入 | todo | 3D demo |












## 动画质量修复 + 流水线重规划（2026-08-14，依据 spec/2d-animation-quality.md）
> 触发：用户反馈"动画烂（位置不对/图层缺漏/动作不科学）"。根因：rig 缺 IK/权重、动画缺方法论、拆层缺门禁。

| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| M0-1 | 图层修复：B3 遮挡补全 + chibi 层补齐（bottomwear/legwear 分离） | todo | 分层 PSD v2，层完整性脚本过 |
| M0-2 | 标准骨架模板 + 枢轴校准（Q 版/立绘两套） | todo | rig 模板 JSON + 校准脚本，摆姿势不穿模 |
| M0-3 | Spine 导出扩展：IK 约束 + weighted mesh（或 region+IK 先行） | todo | spine v2 导出含 ik[]/weights[] |
| M0-4 | 动画方法论重做 walk：contact/down/passing/up + bezier + 髋肩反向 | done(待目检) | LLM 导演重跑：walk 12 轨道(含膝)，validate-anim OK(0 警告,109/109 bezier)，F4 循环闭合修正 5 轨道；walk_preview.gif 已生成 → 待用户目检 |
| M0-5 | 人工确认 walk 效果 | 待用户目检 | walk_preview.gif + Godot demo 已备好（assets/demo/char_ailin_m04/） |
| M1 | idle/walk/attack/hurt 按方法论全部重做（M0-4 重跑产出） | done(待目检) | 4 clip 全部轨道循环闭合+100% bezier；walk 12 轨道；Godot 实机渲染帧差异验证；表情仅 StretchyStudio 预览（Spine 限制） |
| M2 | 流水线编排（orchestrator + contracts + gates + job 记录） | done | tools/workbench orchestrator + chain + gates 全落地 |
| M3 | Spine atlas 打包 + Godot runtime 接入 + 交互 | done | trimmed atlas 25/25 + SpinePlayer Godot 播放（实机截图验证） |
| M4 | 反馈闭环 + 成本核算 + 开源发布 | todo | 归因/回填/成本记录 |

## P1-D 现状标记（旧条目保留，标注质量问题）

---

## 2D 骨骼动画工业级流水线重规划（2026-08-14，权威：spec/pipeline-remaster-2d-skeletal.md）
> 触发：动画烂（位置不对/图层缺漏/动作不科学）。根因：rig 缺 IK/权重/标准层级 + 拆层缺部件 + 动画缺方法论。
> 原则：**先修质量（P1）再硬化流水线（P2）**，不能把烂动画流水线化。

### Phase 1 —— 动画质量修复（⏳ 当前关键路径）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| M0-1 | 图层修复：B3 遮挡补全 + Q版层补齐（thigh/shin、upperArm/foreArm、bottomwear/legwear 分离） | todo | chibi 分层 PSD v2，层完整性脚本过 |
| M0-2 | 标准骨架模板 + 枢轴校准（fix-rig.py 后处理：去重骨/补 Warp 骨/肘骨挂臂/脚部 IK） | done | live S2 job_4edaf46a gate_rig.txt=OK；spine 26骨/2IK/0重复；S3 动画 zip 双 gate 均 OK |
| M0-3 | Spine 导出扩展：IK 约束（已加，fix-rig）+ weighted mesh（待做） | in_progress | ik[]=2 条；weighted mesh 仍无（W1 警告） |
| M0-4 | walk 重做：contact/down/passing/up + bezier + 髋肩反向 + 支撑脚固定 | todo | walk GIF v2，无脚滑/循环闭合 |
| M0-5 | 人工确认 walk 效果 | 待用户目检 | walk_preview.gif + Godot demo 已备好（assets/demo/char_ailin_m04/） |
| M1-1 | idle 重做（胸腹分层呼吸+头微摆+跟随） | todo | idle GIF，循环闭合 |
| M1-2 | attack 重做（anticipation→挥击→follow-through） | todo | attack GIF，幅度/时序合理 |
| M1-3 | hurt 重做（后仰+头滞后+弹性回位） | todo | hurt GIF，回位不瞬移 |
| M1-4 | 表情过渡（happy/sad/angry/neutral ≥0.3s，立绘 mesh 变形） | todo | 表情 GIF，过渡平滑 |
| M1-5 | 全部动画 GIF 预览 + 质量门禁 + 人工确认 | todo | 4 动画+表情全过 |

### Phase 2 —— 流水线硬化
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| P2-1 | rig gate：tools/validate-rig.py（ik 数量/权重/层级模板/无重复骨名/槽位骨存在） | done | 现有 rig FAIL（重复骨/缺 Warp 骨/无 IK），经 API S2 实测 gate_rig.txt 产出 |
| P2-2 | anim gate：tools/validate-anim.py（clip 齐全/循环闭合/关节幅度/缓动曲线） | done | 现有 4-clip 动画 PASS（100% bezier），缺 clip/超幅度会被拦截 |
| P2-3 | 契约 schema 补全 + gate 自动执行（S2/S3 接入 + gate_strict 开关） | done | S2/S3 任务自动跑 gate，gate_strict 开时 FAIL 即停 |
| P2-4 | LLM 导演 system prompt 升级（12原则+4姿态+预设模板） | todo | 生成动画质量门禁过 |
| P2-5 | S1 全分辨率实跑（see-through 1280 完整版） | done | job_78215fb5：1280x1280 PSD 17 层 + 24 PNG + 23 depth，validate-layered OK，真实 GPU 成本 ¥0.1974 |
| P2-6 | S5 spine 播放器（自包含 GDScript 迷你 Spine runtime，避 ABI 风险） | done | Godot --headless 自检过 + 实机截图 4 帧动画不同（tools/spine-player.gd + skeleton.lite.json 快速解析） |
| P2-7 | 断点续跑 + 真实计费（S0 按张/S1 按 GPU 时/S3 按 token） | todo | 一条命令端到端可重跑 |

### Phase 3 —— 引擎闭环 + 交互
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| P3-1 | Godot 场景接入 Spine 播放器，播放 4 动画 | todo | 实机可播放 |
| P3-2 | 交互雏形（按键/点击触发动作+表情切换） | todo | demo 可玩 |
| P3-3 | 事件总线 + P3 Agent 入口（白名单动作） | todo | 越权被拒 |

### Phase 4 —— 反馈闭环 + 成本 + 开源
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| P4-1 | 动画质量归因 + lessons 自动回填 | todo | 归因记录 |
| P4-2 | 真实计费 + 耗时台账（入 workbench.db） | todo | 成本可核算 |
| P4-3 | 开源发布（README + demo 录屏 + 教程） | todo | GitHub 可跑通 |

| P2-8 | 一键流水线 chain run（后端 /api/pipeline/chain/run 顺序执行 + 上游产物自动填入下游 + 前端总览一键卡片） | done | S4→S5 chain 实测 done，S5.package_dir 自动填入 S4 产物目录；前端无报错无重叠 |
| P2-9 | 前端上游产物选择器升级（file 字段也有下拉；列出全部上游阶段最新 done job 产物，标注来源阶段） | done | S5 Tab 显示 55 个 S4 产物，标注「打包 S4·…」 |

| P4-1b | 反馈闭环闭环：S3 动画导演自动注入经验库规避规则（stretchy-agent --rules + app 生成 rules.txt） | done | --print-prompt 实测合成 prompt 含规则段；_build_anim_rules 正确提取 s3_animate FAIL 原因 |

| P2-7b | 断点续跑：POST /api/pipeline/chains/{id}/resume + 前端历史链「↻ 断点续跑」按钮 | done | 失败 chain 续跑返回新 chain（resumed_from 正确），任务重跑 |

| M0-1 | 图层分离方案调研（SAM2+生成补全 vs 程序化膝盖线切分 vs 接受刚性腿） | done(调研) | chibi 已有 L/R 腿；thigh/shin 需 SAM2+inpaint（spec §9 已记录方案） |
| P4-3 | 开源发布准备：流水线 README（架构/安装/运行/门禁/目录） | in_progress | tools/workbench/README.md 已写，引用文件全部存在；发布动作待做 |

| M0-1b | 程序化切分工具 tools/split-limb.py（thigh/shin + 重叠带 + 重建校验） | done(基础) | legwear 膝线切分 100% 重建覆盖；Spine slot 集成待后续 |
| M0-5 | walk 目检辅助：old vs new 对比 GIF（新 walk 运动 2.4×） | 辅助已备 | assets/demo/char_ailin_m04/walk_old_vs_new.gif 待用户确认 |

| M0-1c | 膝盖弯曲完整集成：split-spine-limb.py（legwear→thigh+shin+Spine slot）+ SpinePlayer 膝感知驱动 | done | 门禁 OK；Godot 自检 OK（27 纹理）；小腿独立运动 16-17K px/相位（膝弯生效）；walk_preview_knee.gif 已生成 |

| P4-3 | 发布准备：README + 演示素材（Godot 实机 4 帧 strip / knee walk GIF / 对比 GIF）+ MIT LICENSE | done(素材) | tools/workbench/README.md + assets/demo/char_ailin_m04/* + LICENSE；正式发布动作待做 |
| M0-3 | weighted mesh：评估后如实 defer（StretchyStudio 导出非标准 mesh 格式、无 Spine runtime 验证，盲改会造错误数据） | deferred | W1 警告不阻塞；region+IK 已满足 spec 第一阶段；待上游导出支持或加验证 harness |


---

## 当前权威状态（2026-08-15 汇总，去重后）
> 旧的 P1-A~E / M0-M4 / P2-P4 多张表有重复条目；本表为唯一事实来源。

### [完成]  已完成
| 项 | 证据 |
|---|---|
| 流水线工业化 | S0-S5 orchestrator + 10 Tab 前端 + 一键全链路 + 上游自动流转 + 断点续跑 |
| 质量门禁 | validate-layered/rig/anim + gate_strict（rig/anims 均 OK） |
| 反馈闭环 | 门禁 FAIL→经验库→S3 自动注入规避 |
| 真实计费 | S3 token 级（¥0.0306 实测）+ S1 GPU 小时（¥0.1974） |
| S4 打包 | trimmed atlas 25/25→27/27 |
| S5 引擎 | SpinePlayer Godot 播放（实机 4 帧验证） |
| M0-2 标准骨架 | fix-rig（去重骨/补 Warp 骨/脚部 IK）rig gate FAIL→OK |
| M0-4/M1 动画方法论 | walk 12 轨道 + 4 姿态 + 100% bezier + 循环闭合 |
| M0-1 膝盖弯曲 | split-spine-limb（thigh/shin）+ SpinePlayer 膝感知，小腿独立运动 16-17K px |
| S1 全分辨率 | 1280 PSD 17 层 + 24 PNG，validate-layered OK |
| 发布素材 | README + MIT LICENSE + Godot 实机 demo strip + knee/对比 GIF |

### ⏳ 剩余（需用户/外部）
| 项 | 状态 | 阻塞点 |
|---|---|---|
| **M0-5 walk 目检** | 待用户确认 | 需用户看 assets/demo/char_ailin_m04/（godot_engine_demo.png + walk_preview_knee.gif + walk_old_vs_new.gif）并验收 |
| **P4-3 正式发布** | 素材齐，待发布 | 需用户指定平台/仓库/账号 |
| M0-3 weighted mesh | deferred | 需上游 StretchyStudio 导出支持或加 Spine runtime 验证 harness（避免造错误数据） |
| F1-F5 3D 线 | 后置 | ROADMAP 明确 3D 线后置，非本主链 |
| P1 内容润色（A5 反馈飞轮/B3 遮挡/D3 AI 补帧/表情 Spine 导出） | 部分完成/可选 | 内容迭代，需用户目检反馈 |


## 2026-08-17 对齐定稿 + 帧动画 B 路线（新）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| T1 | 对齐透明 hero（**matte 不重绘**：rembg 抠图 + 条件 defringe，像素级=原图去背景） | done | transparent_v2/hero_{hd2d,pixel}_final.png（§9 style-research） |
| T2 | 全套姿势（hd2d+pixel × idle/walk/attack/hurt/side/back） | done | transparent_v2/{hd2d,pixel}_pose_*.png，审查全 PASS |
| T3 | 无弓 A-pose（建骨底图） | done | hero_{hd2d,pixel}_nobow_apose.png，PASS |
| T4 | **B 帧动画关键帧**（单锚点+固定风格块，v2 每风格 16 帧：idle3/walk6/attack4/hurt3） | done | frames_hd2d_v2/ + frames_pixel_hard/，gpt-5.5 帧间一致 PASS（tools/gen-frame-cycle.py）；walk_4 PASSING 帧经 walk_1 锚点重生成对齐地面线 |
| T5 | **Godot AnimatedSprite2D 动画工程**（核心身体对齐防跳动 + 状态机衔接；walk/idle/attack/hurt 全部审查 PASS） | done | godot-chibi-anim-hd2d-v2/ + godot-chibi-anim-pixel/，headless import+run exit 0（tools/build-godot-anim-demo.py） |
| T6 | 工作流固化 | done | spec/frame-anim-workflow.md（B 路线）+ spec/plan-spine-rig-a.md（A 计划） |
| T7 | **A 路线 Spine 工业管线**（See-Through PSD → StretchyStudio → Spine） | pending | 阻塞：LayerDiff3D 需 HF 下载（huggingface 不通，配 HF_ENDPOINT=hf-mirror）+ 慢；待 B 验收后执行（spec/plan-spine-rig-a.md） |
| T8 | pixel 风格走同流程（关键帧+Godot） | done | frames_pixel_hard/ + godot-chibi-anim-pixel/（硬边像素风），headless 验证通过 |


## Backlog（待办，非阻塞）
| 待办 | 说明 | 状态 |
|---|---|---|
| B-A 修复帧动画质量问题 | v2 已解决：walk 6 帧/attack 4 帧/hurt 3 帧；FRAMING 固定双足+地面线防裁脚/变大；walk_4 重生成对齐；左右翻转由 flip_h + 朝向判定。剩余：单帧 AI 小图审查有误判风险，以实机观感为准 | done（2026-08-17） |
| B-B hard-pixel 风格动画 | gen-frame-cycle --style pixel 完成 16 帧 + godot-chibi-anim-pixel 工程；真·像素需算法后处理（gpt-image-2 出的是像素风插画，style-research §8.1） | done（2026-08-17） |
| A 路线 Spine 骨骼动画 | See-Through PSD → StretchyStudio → Spine 4.0 + LLM 动画 agent（详见 spec/plan-spine-rig-a.md，阻塞：LayerDiff3D HF 下载需 hf-mirror + 慢） | 待办（沉淀） |


## 2026-08-17 游戏基座（新方向）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| G1 | Godot 2D 俯视角游戏（星露谷式）：Kenney 瓦片 TileMap 地图(草地/沙/水/石墙/树/岩/箱/花，水墙物理) + Camera2D 跟随 + y-sort + 玩家(艾琳 v2 帧 idle3/walk6/attack4/hurt3，1/2 键切换 HD-2D/像素) + 史莱姆怪物 + UI(HP/击杀/重开) | done | assets/demo/godot-game-base/，headless 300帧无错 + 冒烟测试 ALL PASS；tools/build-kenney-atlas.py 可换瓦片/改图 |
| G2 | 怪物资产：史莱姆 idle/hurt（HD-2D 画风匹配，透明） | done | godot-game-base_assets/slime/ |
| G3 | A 路线 Spine 接入游戏（spine-godot 运行时） | 待办 | spec/plan-spine-rig-a.md |


## 2026-08-17 二次迭代：官方森林地图 + 攻击修复 + 帧对齐（用户反馈轮）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| U1 | 地图更换：Tiny RPG - Forest（ansimuz，公有领域）官方 60x45 地图移植（双层 TileMap + 行合并碰撞 868 格 + y-sort 树冠） | done | assets/demo/godot-game-base/，headless 300帧无错；assets/maps/forest-preview.png；tools/port-tiny-rpg-map.py |
| U2 | 攻击无法击杀：根因 area_entered 对 CharacterBody2D 不触发 + 贴身时 body_entered 不触发 → 改 body_entered + 攻击窗口轮询 get_overlapping_bodies | done | 冒烟测试新增攻击命中验证：monster hp 60->35（ALL PASS） |
| U3 | 人物忽大忽小/模糊：帧预处理对齐（align-game-frames.py，核心身体 target_h=128 + 地面线 + 中心X + 统一画布）→ 游戏内 1:1 + NEAREST | done | assets/ailin（HD2D 263x213）+ ailin_pixel（343x229） |
| U4 | 默认风格改像素（与像素地图匹配），1/2 键仍可切换 | done | main.gd setup_animations(AILIN_PIXEL_DIR) |
| G3 | A 路线 Spine 接入游戏（spine-godot 运行时） | 待办 | spec/plan-spine-rig-a.md |


## 2026-08-17 三次迭代：地图黑灰根因修复 + 英雄角色（用户反馈轮2）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| V1 | 地图全黑灰根因：TileSet.tile_size 默认 16 vs 瓦片 64 → 瓦片按 16px 间距平铺原点附近，摄像机视野内是空白 → 显式设置 tile_size=64 | done | GUI 截图确认：屏幕 100% 渲染（棕褐土地+粉紫树冠），vision 审核通过 |
| V2 | 组合图集：tileset.png(1088) + objects.png(360) 拼接（1448 瓦片，覆盖层 gid>=1097 的 objects 瓦片此前指向无效区域） | done | assets/tiles/atlas.png 2176x2752 + atlas.json |
| V3 | 玩家忽大忽小/效果差：默认改 Tiny RPG Forest 包内 4 向弓箭手英雄（32x32 原生像素，4向 idle/walk/attack，与地图同画师、零漂移）；艾琳保留 1/2 键切换 | done | assets/hero/ 30 帧；player.gd 皮肤系统（hero/ailin） |


## 2026-08-17 四次迭代：改为 2D 横板 + 攻击自伤修复（用户需求轮3）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| W1 | 改为 2D 横板平台游戏：重力/跳跃/奔跑/近战，SunnyLand Forest（ansimuz 公有领域）官方 160x25 地图移植（20x12 瓦片集 4x 放大 + 双层视差背景 + slug 敌人巡逻） | done | main/player/monster 全重写；headless 测试 ALL PASS + GUI 截图确认渲染 |
| W2 | 主角 = 艾琳（像素帧，对齐 1:1 + NEAREST + 落地阴影），横板左/右 flip | done | player.gd 横板物理；截图确认角色居中显示 |
| W3 | 攻击自伤 bug：攻击区 Area2D 覆盖玩家自身（朝左/右时）→ 攻击区 collision_mask=2 只检测敌人层 + _try_hit 排除 self + 攻击区前移 | done | 冒烟测试新增断言：攻击后怪物 40->15、玩家 HP 100->100（无自伤）ALL PASS |
| W4 | 图像优化：艾琳侧面帧生成（idle2/walk4/attack3/hurt1 像素风） | blocked(待中转站恢复) | 生图端点 images.generate 挂起；恢复后跑 tools/gen-side-frames.py + align 接入 |


## 2026-08-17 五次迭代：角色帧对齐算法升级（用户反馈轮4：没有脚部/忽大忽小）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| X1 | 忽大忽小根因：align 用"全行宽核心检测"被攻击帧的弓干扰（attack_2 高228 vs idle 166）→ 改为**中心区域(55%)核心检测**，排除弓/披风/武器延伸 | done | 重新对齐后：HD2D 全帧高 154-163（差9px，原差68px）；像素 150-168（差18px，原差62px） |
| X2 | 没有脚部：源帧 attack_3（脚像素0）/walk_1（390）/walk_3（1613）/hurt_2（253）生成时脚缺失 → 已确认其他帧脚部完整且对齐后底部有内容；缺脚帧需重生成 | done(部分) | 待生图中转站恢复后重生成这几帧（tools/gen-side-frames.py 同法） |


## 2026-08-17 六次迭代：箭矢/稳定idle/落地 + 全链路覆盖评估（用户反馈轮5）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| Y1 | 攻击射箭：新增 arrow.gd 投射物（Tiny RPG arrow.png，2.5x），J 键攻击发射箭矢沿朝向飞行，命中敌人(层2)扣 25、命中地面/超时消失 | done | 冒烟测试：怪物 40->15（箭矢命中）、玩家 HP 100->100（无自伤）、kill 计数 ALL PASS |
| Y2 | idle 抖动：AI 3 帧"呼吸"实为重绘差异（帧间差异 1200-1900px）→ 算法合成稳定 idle（3帧 alpha 加权平均为单帧）+ 代码平滑呼吸（sin 缩放1.2% + 1.5px 浮动） | done | blend-idle 输出 idle_0.png；单帧循环 + 平滑呼吸无闪抖 |
| Y3 | 落地完整：落地瞬间 squash 缓冲（scale.y 压扁恢复 0.16s）+ 空中 walk 帧 | done | player.gd _land_t 落地缓冲 |
| Y4 | 帧尺寸统一：align 改中心区域(55%)核心检测排除弓干扰（详见上轮 X1） | done | 已并入；attack/walk/hurt/idle 高度 150-168px |
| Y5 | 2D 全链路覆盖评估（见下） | done | 链路图已更新 |

## 2D 全链路生成覆盖评估（2026-08-17）
| 环节 | 实现 | 状态 | 质量缺口 |
|---|---|---|---|
| S0 生图 | gen-frame-cycle / gen-portrait（gpt-image-2） | 已实现 | 帧间身份/脚部稳定性（部分帧缺脚，待重生成） |
| S0.5 对齐+帧动画 | align-game-frames（中心区域核心检测）+ build-godot-anim-demo | 已实现 | 已解决尺寸漂移；AI 帧固有抖动靠合成 idle 缓解 |
| S1 拆层 | See-Through LayerDiff3D → 分层 PSD | 已实现 | — |
| S2 绑骨 | StretchyStudio DWPose → Spine 4.0 | 已实现 | — |
| S3 动画(A 路线 Spine) | stretchy-agent LLM 导演 | 阻塞 | LayerDiff3D HF 下载需 hf-mirror；生图端点挂起 |
| S4 打包 | package-assets / validate-* | 部分 | — |
| S5 视觉审查 | vision_review(gpt-5.5) | 阻塞 | 中转站 api.sisct2.xyz 当前 502/挂起，恢复后跑拼图验收 |
| 游戏接入 | 2D 横板 demo（艾琳主角） | 已实现 | 攻击/跳跃/箭矢/落地已通；缺脚帧重生成待端点恢复 |

## 阻塞（外部）
- 生图端点 images.generate 挂起（无响应 90s+，多次探测）；vision 502 Upstream access forbidden
- 恢复后待办：①重生成缺脚帧 attack_3/walk_1/walk_3/hurt_2 ②生成横板侧视帧 ③vision 拼图验收（idle 稳定性/攻击箭矢/落地过渡）


## 2026-08-18：视觉模型验收 + 侧视帧 + 箭矢修复（用户反馈轮6）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| Z1 | 视觉模型验收（中转站恢复）：源帧脚部检查（vision 确认所有帧脚部完整，之前统计误判）、对齐帧验收 8/10（idle 最稳/无忽大忽小/脚底对齐） | done | vision_review 拼图：aligned_check 8/10 |
| Z2 | 生成横板侧视帧（艾琳 10 帧：idle2/walk4/attack3/hurt1，像素风） | done | frames_pixel_side/，vision 验收 8/10（侧面向右/身份一致/透明/脚完整） |
| Z3 | 5 帧背景不透明（transparent 参数偶发失效）→ 边缘 flood-fill 抠图（每帧抠 67-77 万px） | done | walk_2/3 attack_2/3 hurt_1 抠图完成 |
| Z4 | 侧视帧对齐（中心区域核心检测+杂点清理）→ 统一画布 247x161（bottom 全 161）→ **真像素化**（缩 32px 网格 BOX + 最近邻 4x，与 16px 瓦片地图像素密度一致） | done | ailin_pixel_side/ 接入游戏默认角色 |
| Z5 | 游戏截图 vision 验收 7/10：角色侧视稳定/无渲染问题；扣分=箭矢视觉不明显 + 风格混搭 → 箭矢加大 4x+发光拖尾；角色像素化 | done | shot_idle/attack 已验收 |
| Z6 | 箭矢 headless 测试根因：怪物传送到玩家 feet 高度**陷入地面 11px**（capsule 底部超出地面）→ 物理体被地面排斥错位，箭矢穿体 | done | 测试怪物传送抬高 11px 后箭矢命中 40->15，ALL PASS |

## 2026-08-18 视觉验收结论
- 对齐帧（正面像素）：**8/10**，idle 最稳、无大幅忽大忽小、脚底对齐
- 侧视帧（新生成）：**8/10**，侧面正确、身份一致、透明、脚部完整
- 游戏内截图（侧视+像素化）：**7/10**，待机稳定、无渲染问题；箭矢已增强（加大+发光）
- 待办：箭矢在真实游戏的视觉确认（GUI 试玩）；若风格仍混搭可加深像素化或统一调色板


## 2026-08-18 二次迭代：像素化回退 + HD-2D侧视 + 箭矢方向（用户反馈轮7）
| 任务 | 内容 | 状态 | 验收 |
|---|---|---|---|
| W1 | 角色模糊/质量低：BOX 平均像素化造成软边模糊 → **回退像素化**，恢复 AI 硬边像素帧 | done | 游戏截图 vision 确认清晰、非过度像素化 |
| W2 | 没有足部：回退像素化后脚部可见（vision 确认"可见且未被切掉"） | done | vision 截图验收 |
| W3 | 缺 HD-2D：生成 **HD-2D 侧视帧 10 帧**（Octopath 式）并接入，1/2 键切换 HD2D/像素 | done | HD2D 侧视帧 vision 验收 7.5/10（身份一致） |
| W4 | 箭矢竖着射：arrow.png 纵向(5x19) rotation=0 朝上 → 改为 rotation=PI/2（水平，箭头朝飞行方向） | done | 游戏截图 vision 确认"箭矢水平向右飞出" |
| W5 | 全流程视觉模型确认（见下） | done | 逐步 vision 验收记录 |

## 全流程视觉模型验收记录（2026-08-18）
| 环节 | 验收对象 | vision 评分/结论 |
|---|---|---|
| 生图-像素侧视 | frames_pixel_side 拼图 | 8/10：侧面向右、身份一致、透明、脚完整 |
| 生图-HD2D侧视 | frames_hd2d_side 拼图 | 7.5/10：HD-2D 风格、身份一致；脚部/地面线轻微需加强 |
| 对齐-正面 | ailin_pixel 对齐帧拼图 | 8/10：idle 最稳、无忽大忽小、脚底对齐 |
| 对齐-侧视 | ailin_*_side 对齐帧 | 像素 247x161 / HD2D 209x162 统一画布，脚底一致 |
| 接入-游戏 | 游戏截图（像素+回退后） | 7.5/10：清晰、脚可见、箭矢水平、待机稳定 |
| 缺陷待办 | 角色占比偏小（可放大）；HD2D 侧视脚部/地面线微调 | 下一轮 |


## 2026-08-18 三次迭代：switch_style修复 + walk稳定性 + 挑刺式验收（用户反馈轮8）
| 任务 | 内容 | 状态 | 验收 |
|---|---|---|---|
| V1 | SCRIPT ERROR switch_style：横板版 player.gd 缺该方法（俯视角版遗留）→ 补上（重载帧+保留当前动画） | done | headless 运行 NO ERRORS |
| V2 | 移动抖动：walk 帧重生成（强一致性 prompt：只有腿/臂运动，头发/披风/衣摆静止）+ walk_7 用 walk_6 锚点针对性重生成 | done | 程序化：bottom 全160、cy 漂移<=1.3px、高度差3px |
| V3 | walk 播放速度 8->6fps（更慢更稳，降低抖动感知） | done | ALL PASS |
| V4 | **挑刺式视觉验收**（严格动画师视角）：walk 循环 | done | 循环 6/10：重心微抖、脚滑、布料轮廓轻微形变；"能用但不精" |

## 挑刺式视觉验收结论（2026-08-18）
- walk 循环：**6/10**——问题为 AI 逐帧生成的固有局限（帧间轮廓/布料形变），位置/脚底已严格对齐
- 已确认改善：帧间 bottom 完全一致(160)、质心漂移<=1.3px、高度差3px
- **根治方案**：A 路线 Spine 骨骼动画（骨骼驱动天然平滑无帧间抖动）；当前阻塞 LayerDiff3D HF 下载（需 hf-mirror）
- 当前水平：可用（6/10），非专业级


## 2026-08-19：A2 标准入口 + godot-assistant MCP + W2.1 地图打磨（任务 1/2/3）
| 任务 | 内容 | 状态 | 验收 |
|---|---|---|---|
| T1 | **A2 标准入口** tools/a2-pipeline.py：视觉提示词(prompt_vision)→生图(image_backend)→Vision Gate→FAIL 带问题修订重试→manifest，一条命令 | done | overworld_v2 瓦片集首轮 PASS 7.0（风格统一8/语义9/无缝7/像素5）；house FAIL 3 但重试闭环正常 |
| T2 | **godot-assistant MCP 实装**：零配置 Godot MCP（25 工具）注册进 Codex，doctor PASS；tools/godot-shot.py（新行分隔 JSON-RPC stdio 客户端）截图游戏画面 | done | 场景 offscreen 截图成功（960x600 PNG）；游戏内画面喂 Vision Gate 打通 |
| T3 | **W2.1 地图打磨**：新 8/12 瓦片统一 atlas（A2 生成 3草/2水/沙/土/路）+ 域扭曲大块草地 + 有机湖/浅滩/沙滩 + 主干道支路/桥 + 村庄6房/广场 + 成林树丛；接入 demo（main.gd 12格 atlas + houses + spawn） | done(核心) | 全景 gate：v1 3→v2.2 6→v2.4 **6**（可玩结构7/画风7/统一7，条纹消除）；游戏内截图 gate：2→5（物件统一7） |
| T3.1 | 地图未达 7 的原因与待办 | 待办 | 见 spec/style-assets.md §6 / agent-workflow.md W2.1：草地大块编辑痕迹/水岸过渡硬/道路层级弱 → 需更丰富瓦片变体+过渡瓦片+路标地标+统一描边/阴影 |
