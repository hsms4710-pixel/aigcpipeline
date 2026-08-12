# 2D 游戏内角色资产形态（spec/2d-in-game-assets.md）

> 目的：想清楚"2D 游戏落地到游戏内的角色模型到底是什么"，避免把概念图（三视图）当游戏资产。
> 结论：**2D 游戏内的"角色模型" = 正面立绘(tachi-e) + 表情差分 + SD 小人/战斗精灵 + （可选）Live2D 分层**；三视图只是概念设计，不直接进游戏。

## 1. 2D 游戏角色的真实资产清单
| 资产 | 用途 | 是否本管线已产出 |
|---|---|---|
| **立绘 / tachi-e**（正面全身，透明背景，面向镜头） | 对话/剧情/界面展示 | ✅ full.png |
| **半身立绘**（胸部以上） | 对话小窗/表情展示 | ✅ bust.png |
| **表情差分**（同构图只换脸） | 对话情绪变化 | ✅ exp_happy/sad/angry/neutral.png |
| **SD 小人 / 战斗精灵**（Q 版或像素，多帧：idle/walk/attack/hurt） | 战斗/地图上的"角色模型" | ✅ Q版 chibi（char_ailin_chibi：front/side/back + idle/walk/attack/hurt，方舟chibi多参考画风迁移）+ 像素版(t9) |
| **Live2D 分层 PSD**（瞳孔/眼白/眉毛/前发/后发分图层） | Live2D 动画（呼吸/眨眼/口型） | ❌ P6 后置（DCC 加工） |
| **Spine 骨骼**（或引擎内骨骼） | 2D 骨骼动画 | ❌ P4 后置 |
| **三视图/转面**（front/side/back） | 概念设计、确认角色设计一致性；**不是游戏内直接资产** | ✅ turnaround_sheet（概念用途） |

## 2. 为什么三视图"很难用"
- 游戏运行时用的是**正面立绘 + 表情差分 + 小人**，不是三视图。
- 三视图的价值：① 给美术/建模确认设计（服装背面/侧面细节）；② 给 SD 小人/3D 建模做参考；③ 角色设定集。
- 对纯 2D 游戏：三视图主要服务"立绘→小人"的转换参考，本身不进游戏。

## 3. 我们的管线怎么对齐
```
persona → full(立绘) → bust(半身) → 表情差分×4（同构图换脸）   ← 已在 v9 跑通
        → [待补] SD 小人/Q 版战斗精灵（多帧）                 ← 下一个实践点（t9 像素已覆盖像素版）
        → [后置] Live2D 分层 PSD / Spine（P6 DCC 加工）
```
- ✅ 已补：艾琳 Q 版 SD 小人（char_ailin_chibi：front/side/back + idle/walk/attack/hurt），用方舟 chibi×2 多参考画风迁移；与立绘共用 persona（persona_chibi.json）。
- 资产包规范（spec/p1/contracts/asset-package-spec.md）应明确：portrait/（full+bust+表情）、sprite/（SD 小人帧）、live2d/（分层 PSD，后置）。

## 4. 与画风调研的联动
- 画风确定后（见 spec/style-research.md），立绘/表情/小人全部统一该画风。
- 若最终走 HD-2D 或像素：SD 小人就是核心游戏资产（t9 已验证像素小人链路）。
- 若走高画质 2D：立绘+表情差分为主，SD 小人做 Q 版。

