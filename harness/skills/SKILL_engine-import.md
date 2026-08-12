# SKILL：引擎接入（P4，Part 3 使用）

## 触发
Godot 场景接入、现有游戏 Mod/注入。

## 流程
1. 导入 P1 资产包（立绘/图集/语音）到引擎工程
2. 接 P3 Agent（HTTP 客户端）：对话 UI + 事件总线
3. 白名单动作执行器：say/emote/face_player/move_to/give_item/set_quest_flag
4. 模式 B：Mod 框架（SMAPI/BepInEx）注入，回归检查不破坏原游戏

## 参考
- noko / godot-AI-Dialog / OpenGameAgent（Godot）
- StardewLivingNPCs / ValleyTalk / SentientValley（Mod）
- Thrall / Sigrid（BepInEx 注入）
