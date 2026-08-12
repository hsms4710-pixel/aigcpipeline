# t6：资产包导出 + Godot 导入验证

状态：done（Godot 4.7.1 headless：import 成功 + 场景无解析错误，立绘/语音导入验证通过） ｜ 依赖：t5 ✅ ｜ 预估：1-2 天

## 目标
证明资产中立：P1 产物能被 Godot 最小工程导入并使用。

## 产出
- `assets/demo/godot-import-demo/`：最小 Godot 4.x 工程（显示立绘 + 播放语音）
- 导入说明（写进 README 或 spec）

## 验收
- [ ] Godot 工程无报错打开，立绘显示、语音播放
- [ ] 用工作台下载的资产包直接导入可用（不手工改路径）
