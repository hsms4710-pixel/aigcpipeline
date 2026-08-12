# Godot 导入验证（t6）

目的：证明 P1 资产（立绘 PNG + 语音 WAV）可被 Godot 直接导入使用（资产中立）。

## 验证步骤（Godot 4.4+）
1. 安装 Godot：https://godotengine.org/download（Windows 版）
2. 用 Godot 打开本目录（import demo）→ 打开 demo.tscn
3. 预期：立绘显示（左上角 40,40）+ 语音自动播放
4. Headless 检查（无 UI）：`godot --headless --path <本目录> --quit` 无错误输出

## 资产
- assets/full.png：角色立绘（透明背景，来自场景 B v6）
- assets/voice.wav：台词语音（GPT-SoVITS 零样本克隆）

## 状态
- 工程骨架已建；headless 验证待 Godot 可用（本机/隔离机安装后执行）
