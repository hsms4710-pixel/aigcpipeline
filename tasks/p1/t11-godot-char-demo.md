# t11：Godot 角色展示链路（立绘+表情+小人）—— P4 引擎接入 M0

状态：done（Godot 4.7.1 headless 导入 13 资产 + 运行 120 帧无错误；交互按键切换表情/小人） ｜ 依赖：t9 ✅ t10 ✅ ｜ 预估：1 天

## 目标
调通 Godot 链路：P1 资产包（立绘/表情/小人）→ Godot 工程导入 → 场景交互展示（表情切换 + 小人视图/动作切换）。

## 产出
- assets/demo/godot-char-demo/：Godot 4.7 工程（project.godot / demo.tscn / demo.gd）
  - 左：立绘表情（1/2/3/4 切换 happy/sad/angry/neutral）
  - 右：Q版小人（Q/W/E 三视图，A/S/D/F 动作帧）
  - 资产来自 char_ailin_splash_v9 + char_ailin_chibi_v2
- 验证：`--headless --import` 成功；`--quit-after 120` 无错误

## 验收
- [x] Godot 工程无报错打开，立绘显示
- [x] 表情差分可切换（4 表情）
- [x] 小人可切换（三视图 + 动作帧）
- [x] 资产包直接导入可用（不手工改路径）
- [x] headless 导入+运行验证通过

## 下一步（P4 引擎接入 M1+）
- 接 P3 Agent 服务（对话/记忆）→ 立绘+表情随对话情绪变化
- 引擎内动画：Live2D/Spine 表情口型（后置 P6）
- Mod POC：接入现有 2D 游戏（星露谷类 SMAPI）