# Godot 角色展示 demo（立绘 + 表情差分 + 小人）

> 目的：**调通 Godot 链路**——P1 资产包（立绘/表情/小人）能被 Godot 工程直接导入并在场景中交互展示。
> 前置：Godot 4.7+（本机 lovegaming/Godot_v4.7.1-stable_win64.exe）

## 场景内容
- 左侧：**立绘表情**（bust 半身 + 4 表情差分）——按键 1/2/3/4 切换 happy/sad/angry/neutral
- 右侧：**Q版小人**——按键 Q/W/E 切换 正面/侧/背，A/S/D/F 切换 idle/walk/attack/hurt
- 资产来源：`char_ailin_splash_v9`（立绘/表情）+ `char_ailin_chibi_v2`（小人，方舟小人参考）

## 验证（headless）
```
Godot --headless --path <本目录> --import          # 导入 13 项资产，全部成功
Godot --headless --path <本目录> --quit-after 120  # 运行 120 帧，无脚本/场景错误
```
- 交互验证：用 Godot 打开本目录 → F5 运行 → 按上述按键切换表情/小人

## 资产目录
- assets/portrait_full.png / portrait_bust.png：立绘
- assets/exp_{happy,sad,angry,neutral}.png：表情差分
- assets/chibi_{full,side,back,idle,walk,attack,hurt}.png：小人三视图 + 动作帧

## 状态
- ✅ Godot 链路调通（导入 + 运行 + 交互脚本）
- 下一步：P4 引擎接入——接 P3 Agent（对话/记忆），再加引擎内动画（Live2D/Spine 表情口型）