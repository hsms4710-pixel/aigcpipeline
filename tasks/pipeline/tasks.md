# 管线开发任务跟踪（tasks/pipeline/tasks.md）

> 路线详见 spec/dev-roadmap-2d3d.md；本表为执行跟踪。状态：todo / in_progress / done / blocked

## P1-A 画风定稿 + 生图基线
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| A0 | 建风格标杆库 + 反馈飞轮（manifest/lessons/preferences） | in_progress | style-library 阿米娅-唯@W 已建 |
| A1 | 用户选定主画风（style_attempts/compare_sheet/标杆库） | todo | 主画风确定 |
| A2 | 分离式参考重生成三件套（风格图+角色锚点，v10） | todo | char_ailin_v10 + chibi_v3 |
| A3 | 画风锁定决策（云API vs ComfyUI+LoRA） | todo | decision 记录 |
| A4 | 沉淀画风 prompt 模板 | todo | contracts/prompt-templates |
| A5 | 反馈飞轮（审图回填 + lessons-learned） | todo | manifest quality + lessons 记录 |

## P1-B 2D 资产拆层
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| B1 | 搭拆层管线（See-through/VTuber2D.AI/SAM2+PS） | todo | ComfyUI json + tools/split-layers.py |
| B2 | 立绘拆层 → Live2D 规范 PSD | todo | char_ailin_layered/ |
| B3 | 遮挡补全（PS 生成式/SAM2 修补） | todo | 层无缺口 |
| B4 | 拆层校验脚本 | todo | 校验通过 |

## P1-C 2D 骨骼绑定
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| C1 | 装 Spine / Live2D | todo | 工具就绪 |
| C2 | 自动绑骨（UniRig / Spine-Anim-AI） | todo | rig 工程 |
| C3 | 骨骼/权重校验修正 | todo | 可摆姿势 |
| C4 | 绑定小人+立绘表情参数 | todo | 导出 atlas/model3.json |

## P1-D 2D 动画
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| D1 | 基础动画 idle/walk/attack/hurt | todo | 动画资源 |
| D2 | 表情切换动画 | todo | 参数过渡 |
| D3 | 可选 AI 补帧（SCAIL2/2dimg2motion） | todo | 前后对比 |

## P1-E 打包/引擎
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| E1 | 图集打包（Spine atlas/TexturePacker） | todo | atlas 资源 |
| E2 | Godot 导入分层立绘+动画 | todo | char_ailin_godot/ |
| E3 | 交互雏形（表情/动作触发） | todo | demo 可玩 |

## P2-3D 线（后置）
| 任务 | 内容 | 状态 | 产出/验收 |
|---|---|---|---|
| F1 | 3D 生成（Tripo/混元3D/Meshy） | todo | mesh+贴图 |
| F2 | Blender 修正（减面/UV/法线） | todo | 修正模型 |
| F3 | Mixamo/RigNet 绑骨 | todo | 绑定模型 |
| F4 | 动作（动作库/手K/SCAIL2） | todo | 动画资源 |
| F5 | Godot 导入 | todo | 3D demo |

