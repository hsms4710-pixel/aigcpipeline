# Godot 可玩 demo（艾琳 · 定稿资产 chibi_v4 + v10）

> 目的：把**定稿资产**接入 Godot 做成可玩 demo：Q版小人可移动/攻击/受伤，立绘可切换表情。
> 前置：Godot 4.7.1（`C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\`）

## 运行
- **双击 `start-demo.cmd`** 直接运行游戏窗口（无需打开编辑器）
- 或手动：Godot 打开 `project.godot` → F5

## 操作
| 按键 | 动作 |
|---|---|
| WASD / 方向键 | 移动（向下=正面 / 向上=背面 / 左右=翻转；移动中显示走路帧） |
| 空格 | 攻击 |
| H | 受伤 |
| 1/2/3/4 | 立绘表情 快乐/悲伤/愤怒/平静 |

## 资产（定稿）
- Q版小人：`char_ailin_chibi_v4`（front_b 为 hero，7 姿势全部从 front_b 派生，画风一致）
- 立绘/表情：`char_ailin_v10`（full + bust + 4 表情差分）

## 验证
```
Godot --headless --path <本目录> --import          # 导入资产
Godot --headless --path <本目录> --quit-after 120  # 运行 120 帧无错误
```

## 踩坑记录（start-demo.cmd 闪退修复）
- 根因：`start "" "godot.exe" --path "%~dp0"` 中 `%~dp0` 带**结尾反斜杠**，导致 cmd `start` 解析 `--path` 失败 → Godot 闪退。
- 修复：先 `cd /d "%~dp0"`，再用 `--path "%cd%"`（无结尾反斜杠）；去掉 `chcp 65001`（避免代码页切换乱码）；全英文+CRLF。

## 小人大小一致性（2026-08-14）
- chibi 各帧角色主体占画布比例不同（站立 76%，动作帧 91-96%）→ 切帧会"变大"。
- demo.gd `_fit_height()` 按非透明 bbox 统一角色显示高度（547px），所有帧大小一致。
