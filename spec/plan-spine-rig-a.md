# A 路线：Spine 骨骼动画工业管线实现计划 — spec/plan-spine-rig-a.md

> 规划日期：2026-08-17 ｜ 目标：帧动画效果验收后，为角色做**骨骼动画（Spine）**
> 结论先行：A 路线 = See-Through/LayerDiff3D 拆层 PSD → StretchyStudio(DWPose 自动绑骨) → Spine 4.0 导出
> 现状：几何自动建骨（build-spine-from-image.py）对 chibi 大头/平滑头肩**不可靠**（neck 检测失败），不推荐。

## 1. 为什么走 StretchyStudio（而非几何建骨）
- 几何切分（build-spine）对"大头 chibi + 平滑头肩过渡"的 neck/armpit 检测失败（整角色被当"脸"）
- StretchyStudio = 团队已打通的开源管线（MangoLion/stretchystudio，MIT）：PSD 分层 → DWPose AI 绑骨 → Live2D 参数 → Spine 4.0 导出
- 本地已部署：`env/runtime/tools/stretchy-studio/`（5173/5174），DWPose 模型已下载
- 参考：`tools/rig-workflow.md`（已打通端到端 + LLM 动画 agent stretchy-agent.cjs）

## 2. 前置：PSD 拆层（当前阻塞点）
StretchyStudio **只吃 See-Through 分层 PSD**（不接收扁平 PNG）。
- 工具：`env/runtime/tools/see-through/`（LayerDiff3D，venv 有 CUDA RTX4060 8GB）
- 命令：`inference_psd_blockswap.py --srcp <png> --save_dir <dir> --save_to_psd`
- **阻塞点 1：模型下载** — huggingface.co 不通 → 必须 `HF_ENDPOINT=https://hf-mirror.com`
- **阻塞点 2：慢** — 首次运行 >7min（blockswap + Marigold depth），曾被中断
- **输入要求**：无弓 A-pose 透明 PNG（已有：`transparent_v2/hero_hd2d_nobow_apose.png`）

## 3. 实施步骤（待 B 验收后执行）
```
[1] PSD 拆层
    cd env/runtime/tools/see-through
    set HF_ENDPOINT=https://hf-mirror.com
    venv\Scripts\python.exe inference\scripts\inference_psd_blockswap.py ^
        --srcp assets/demo/style_batch/transparent_v2/hero_hd2d_nobow_apose.png ^
        --save_dir assets/demo/style_batch/transparent_v2/layered_hd2d --save_to_psd
    验收：layered_hd2d/*.psd（17+ 层，See-Through blockswap）

[2] StretchyStudio 绑骨
    启动：start-stretchy.cmd（5173/5174）
    全自动：node tools/rig-automation/rig-full.cjs <psd> <outdir> "<joint调整>"
    验收：<outdir>/*_spine.zip（13-18 bones，mesh，Idle+Parameters）

[3] 动画（LLM 导演）
    node tools/rig-automation/stretchy-agent.cjs --load <psd> --task "idle/walk/attack/hurt 关键帧循环动画" --out <dir> --max-steps 16
    参考：assets/demo/char_ailin_anim/（4 clip + Parameters）

[4] 引擎接入
    Spine runtime：Godot 用 spine-godot / 2dguru 社区版，加载 skeleton.json + atlas
    表情：Live2D 参数滑块打关键帧（happy/sad/angry/neutral）
```

## 4. 风险与对策
| 风险 | 对策 |
|---|---|
| LayerDiff3D 下载慢/中断 | HF_ENDPOINT=hf-mirror.com；分步下载；必要时先下载模型再离线 |
| 8GB VRAM blockswap 慢 | 已是 blockswap 模式；接受 ~10-20min/张 |
| DWPose 对 chibi 小人关键点不准 | rig-full.cjs 支持关节微调参数（`leftElbow:+14,+6`）；LLM agent 迭代 |
| Spine 动画"动作不科学" | 用 stretchy-agent.cjs（DeepSeek 导演）+ 首尾关键帧一致约束 |

## 5. 决策记录
- 2026-08-17：用户选择"先 B 帧动画看效果，再规划 A"；本计划待 B 验收后启动。
