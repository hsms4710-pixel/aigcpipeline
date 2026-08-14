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
| D1 | 基础动画 idle/walk/attack/hurt | ⚠️ 已生成但质量不合格（无IK/权重/方法论），待 M0-M1 重做 |
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
| M0-4 | 动画方法论重做 walk：contact/down/passing/up + bezier + 髋肩反向 | todo | walk GIF v2，无脚滑/循环闭合 |
| M0-5 | 人工确认 walk 效果 | todo | 用户验收 |
| M1 | idle/walk/attack/hurt + 表情按方法论全部重做 | todo | 4 动画 GIF + 质量门禁 |
| M2 | 流水线编排（orchestrator + contracts + gates + job 记录） | todo | 一条命令全自动 + 阶段确认点 |
| M3 | Spine atlas 打包 + Godot runtime 接入 + 交互 | todo | Godot 播放动画 |
| M4 | 反馈闭环 + 成本核算 + 开源发布 | todo | 归因/回填/成本记录 |

## P1-D 现状标记（旧条目保留，标注质量问题）