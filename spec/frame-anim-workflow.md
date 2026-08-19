# 帧动画工作流（B 路线）— spec/frame-anim-workflow.md

> 固化日期：2026-08-17 ｜ 适用：小人/角色帧动画（Godot AnimatedSprite2D）
> 解决的两个问题：① 动作衔接（切帧跳动）② 人物一致性（帧间漂移）

## 1. 为什么会有"一致性差 / 切帧跳动"
| 问题 | 根因 | 解法 |
|---|---|---|
| 帧间漂移（服装/脸/比例变） | 每帧独立生成，无统一锚点 | 所有帧从**同一个 matte hero 作为唯一身份锚点** + **固定风格块**（gen-frame-cycle.py） |
| 切帧跳动（大小/位置跳） | 各帧内容比例、位置不同 | **统一对齐画布（核心身体对齐）**：以**核心身体 bbox**（行宽 > 0.6×max 的行，忽略细弓/发梢延伸）为基准——核心高度归一 + 核心中心 X + 核心底部(地面线)对齐。全内容 bbox 会被弓/后仰偏移导致漂移，核心身体法解决（build-godot-anim-demo.py align_frames, core_ratio=0.60） |
| 动作不衔接（idle↔walk 突兀） | 无状态机 | Godot AnimatedSprite2D 动画 clip + 状态切换（loop/one-shot + _transition） |

## 2. 完整流程（已工具化）
```
1. 对齐 hero（matte，不重绘）
   rembg(u2net/isnet) 抠图 → 条件 defringe（仅替换"更接近背景色"的边缘像素）
   产物：transparent_v2/hero_{style}_final.png        [像素级=原图去背景]

2. 关键帧生成（gen-frame-cycle.py）
   python tools/gen-frame-cycle.py --style hd2d --hero <matte.png> --out <frames_dir>
   - 所有帧：CHAR 固定块 + STYLE 固定块 + 帧动作描述 + 透明约束
   - 动作集（v2）：idle×3 / walk×6(contact,down,recoil,passing,up,land) / attack×4(draw,aim,release,recovery) / hurt×3(impact,recoil,recover)
   - FRAMING 固定块：双足可见 + 同一地面线 + 构图/尺寸固定，防止脚被裁剪、攻击变大
   - quality=high + transparent=True

3. 一致性审查（gpt-5.5，拼图法）
   每个动作一行拼图（棋盘格）→ 审查：同角色/标签匹配/透明/无缺陷
   关键：walk 循环单独审查"是否平滑可循环"

4. Godot 动画工程（build-godot-anim-demo.py）
   python tools/build-godot-anim-demo.py --frames <dir> --out <godot_dir> --name <title> [--target-h 560]
   - align_frames：核心身体（行宽>0.6×max 的行）高度归一 + 中心 X + 地面线 → 画布统一（防跳动）
   - 生成 AnimatedSprite2D：idle/walk/back 循环、attack/hurt 一次性 + 状态切换
   - 产物：project.godot + demo.gd + demo.tscn + assets/*.png + start-demo.cmd

5. 验证
   Godot --headless --path <dir> --import
   Godot --headless --path <dir> --quit-after 120   # 无脚本错误
```

## 3. 关键参数与踩坑
- **const 不能用 `:=`**（GDScript 4 解析错误）；字典键必须加引号 `{ "fps": 8 }`
- **back 方向动画要 loop=true**（面向站立）
- 对齐画布用内容 bbox 而非整图：`get_used_rect()` 归一显示高度
- gpt-image-2 不能做真像素（见 style-research.md §8），pixel 风格是"像素风插画"

## 4. 资产（2026-08-17 v2 交付）
- 关键帧（v2，每风格 16 帧）：
  - `assets/demo/style_batch/transparent_v2/frames_hd2d_v2/`（idle3/walk6/attack4/hurt3）
  - `assets/demo/style_batch/transparent_v2/frames_pixel_hard/`（同上，硬边像素风）
- Godot 动画工程（headless 验证通过）：
  - `assets/demo/godot-chibi-anim-hd2d-v2/`
  - `assets/demo/godot-chibi-anim-pixel/`
- 游戏内接入：`assets/demo/godot-game-base/assets/ailin/`（HD-2D）+ `assets/ailin_pixel/`（像素，游戏中按 1/2 键切换）
- 审查拼图：`transparent_v2/_review/v2_{hd2d_v2,pixel_v2}_{walk,attack,idle,hurt}.jpg`
- walk_4（PASSING 帧）修正记录：首版脚底线上抬 100px+ 被 vision 门禁打回（6/10）→ 以 walk_1 为锚点重生成，底边对齐至 452（与其余帧 450-482 一致，行走起伏 ~±8px 正常）。AI 小图拼图审查对单帧仍存在误判风险，最终以玩家实机观感为准。

## 4.5 游戏内接入（对齐帧，2026-08-17）
- 问题：1024px 源帧在游戏内固定 scale 直接显示 → 各帧角色实际尺寸不一致（bbox 高度 865~964px）导致忽大忽小；1024→110px 双重缩放导致模糊。
- 解法：`tools/align-game-frames.py` 复用 align_frames（核心身体高度归一 target_h=128 + 中心X + 地面线）→ 统一画布裁边 → 游戏内 1:1 显示（scale=1.0）+ `texture_filter=NEAREST`。
- 产物：`assets/demo/godot-game-base/assets/ailin/`（HD2D 263x213）+ `ailin_pixel/`（像素 343x229），命名 action_<全局序号>.png。
- 踩坑：`body_entered` 只在新进入时触发，怪物已贴身时攻击不中 → 攻击窗口内额外轮询 `get_overlapping_bodies()`。

## 5. 后续
- 更多动作（jump/技能）扩展 FRAMES 表即可
- A 路线 Spine 骨骼动画见 spec/plan-spine-rig-a.md
