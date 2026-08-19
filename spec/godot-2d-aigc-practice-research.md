# Godot 2.5D / 俯视角 AIGC 实践调研与推进路线（spec/godot-2d-aigc-practice-research.md）

> 更新日期：2026-08-19 ｜ 触发：用户**否决 2D 横板地图**，方向改为「8 视角 / 八方旅人 HD-2D / 垂直·透视像素 3D」
> 原横板路线（G1 横板瓦片 + SunnyLand 地图）归档为已否决，不再投入。
> 结论：三个方向本质同属 **2.5D/俯视角** 家族，工业实现与 AI 资产生成路径已成熟；推荐主方向 = **俯视角 8 向 + HD-2D 2.5D 视觉（Godot 2D + Y-sort + 正交像素 + 后处理）**，真 3D 像素（Project Shadowglass 式）为后置选项。

---

## 一、三种方向拆解与工业实现

| 方向 | 视觉特征 | 工业实现（Godot） | 复杂度 |
|---|---|---|---|
| **8 视角俯视 RPG** | 星露谷/口袋妖怪式；8 向移动 + 8 向精灵 | Godot 2D：TileMapLayer + Y-sort（站树前/后正确遮挡）+ 8 向 AnimatedSprite2D | 低（最快出可玩） |
| **八方旅人 HD-2D（2.5D）** | 3D 场景 + 像素角色；正交相机；光照/景深/泛光后处理 | ① Godot **Hybrid2D3D GDExtension**（KavyaJP，2D 像素 + 3D 环境）；② 2.5D = 正交相机 + Y-sort + 分层；③ 2D 平面 + shader 后处理模拟 HD-2D | 中 |
| **垂直/透视像素 3D** | Live A Live 战斗 / 月风魔传；真 3D 场景 + 像素贴图；透视或正交 | Project Shadowglass 式：真 3D + **像素稳定系统**（相机稳定采样）+ 低分辨率渲染（80.lv 访谈，2026-05） | 高（定制渲染） |

**推荐**：先做「8 视角俯视 RPG 最小可玩」落地（复用现有 chibi 资产扩展 8 向 + 俯视瓦片 + Y-sort），再叠加 HD-2D 视觉（光照/后处理），最后按需探索真 3D 像素。三步递进，每步独立验收。

## 二、8 向角色资产生成（AI，2026 主流）

| 方案 | 做法 | 适用 |
|---|---|---|
| **sprute**（sprited-ai，开源） | 单张参考图 → **模板引导**图像模型（Nano Banana Pro）→ 8 向精灵表；一条命令 | 8 向一键生成（需 Gemini key） |
| **perfectpixel-studio**（gykim80） | 文本 → 8 方向 100+ 动作精灵表（Wails+Go+React + CLI） | 8 向多动作 |
| **character-animation-creator-skill**（tachikomared） | 文本/参考图 → 64x64 像素角色 8 向 walk/attack 精灵表 | 8 向动画帧 |
| **我们的锚点法**（已验证） | chibi_v4 front/side/back 为锚点，gpt-image-2 多参考重绘补齐 3/4 视角（front-left/right、back-left/right） | 与现有画风一致（**推荐，无需新 key**） |
| bilibili BV1bSNuzBEfv | 2 张参考图（角色 + 像素风格）→ 8 向图 | 风格转换提示词参考 |

现有资产：`char_ailin_chibi_v4/portrait/`（front_a/front_b/side/back + idle/walk/attack/hurt）→ 已有 4 向（下/侧/背），缺 3/4 中间向，补 4 张即可 8 向。

## 三、HD-2D 渲染实现（Godot）

| 方案 | 说明 |
|---|---|
| **Godot-Hybrid2D3D-Renderer**（KavyaJP，GDExtension） | Godot 4.x 专用：混合 2D 像素与 3D 环境，专为八方旅人式 HD-2D；现成 GDExtension 可集成 |
| 2.5D 标准做法（bilibili BV1He4y1u77n / YouTube A7txKkBkgXg） | 正交相机 + 3D 场景 + 像素贴图 + 景深/模糊后处理（八方旅人/Live A Live/DQ3 重制同款流程） |
| Project Shadowglass（80.lv 2026-05） | 真 3D 像素：稳定透视相机 + 像素稳定系统 + 低分辨率渲染（"走进 2D 像素画"） |
| 2D 平面简化版 | TileMapLayer 俯视地图 + Y-sort + CanvasModulate/WorldEnvironment 光照 + 景深后处理（成本最低，先验证） |

## 四、与现有资产/工具映射

| 现有 | 新方向适配 |
|---|---|
| chibi_v4（front/side/back + 动作） | 补 3/4 向 → 8 向；8 向动作帧（walk/attack）需逐向生成 |
| tiles_ai（v1 俯视 16px 草/土/石/水） | 方向对但 16px 太小 → 重生成俯视 HD-2D 大瓦片（128px） |
| tiles_hd2d（横板 128px） | 废弃（横板方向） |
| ailin_*_side（横板侧视帧） | 保留为横板遗留资产，不用于新方向 |
| Godot 工程 godot-game-base（横板） | 新建 `godot-topdown-demo/`（俯视角 8 向），不复用横板场景 |
| image_backend / vision_review / validate-* | 全部复用（生图/视觉验收/门禁） |
| kenney topdown（env/assets/kenney） | 俯视瓦片/道具官方资产参考（备选） |

## 五、推进路线（H 系列，每步独立验收）

### H1 艾琳 8 向像素精灵（✅ 规划，2026-08-19）
- [ ] H1-1 以 chibi_v4 front_b 为锚点，gpt-image-2 多参考生成 4 张 3/4 向（front-left/front-right/back-left/back-right）
- [ ] H1-2 对齐（核心身体/地面线）+ 统一画布 + 真像素化
- [ ] H1-3 vision 验收：8 向身份一致、方向正确、风格统一（>=7/10）

### H2 Godot 俯视角 8 向移动 demo
- [ ] H2-1 新建 godot-topdown-demo/：8 向移动（A/D/W/S + 斜向）+ 8 向 AnimatedSprite2D 切换
- [ ] H2-2 俯视瓦片地图（AI 生成 128px 俯视草/土/石/水，H1.5）或 kenney topdown 占位
- [ ] H2-3 Y-sort 遮挡（树/建筑前后）+ 碰撞
- [ ] H2-4 验收：headless PASS + vision 截图 >=7/10

### H3 HD-2D 视觉叠加
- [ ] H3-1 WorldEnvironment 光照 + CanvasModulate 昼夜（可选）
- [ ] H3-2 景深/泛光后处理（Godot Post-Process 或 Hybrid2D3D GDExtension 集成）
- [ ] H3-3 验收：视觉达 HD-2D 观感（vision 对比八方旅人风格）

### H4 真 3D 像素（后置，可选）
- [ ] H4-1 评估 Project Shadowglass 式像素稳定渲染（Godot 定制 shader）
- [ ] H4-2 3D 场景 + 像素贴图 POC
- 门槛高，仅在 H1-H3 完成后评估

### H5 战斗/交互（后置）
- [ ] 俯视战斗（接近式或回合制，参考《歧路旅人》回合制教程 BV1jLXnBEExC）
- [ ] 对接 P3 NPC Agent

## 六、决策记录
- 2026-08-19：用户否决横板；推荐主方向 = 俯视角 8 向 + HD-2D 2.5D；横板 G1 归档
- 8 向精灵用「锚点法 + gpt-image-2」（无新 key 成本），不用 sprute（需 Gemini key，先验证锚点法）