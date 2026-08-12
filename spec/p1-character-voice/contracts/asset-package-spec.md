# 资产包规范（asset-package-spec.md）

> 所有生成模块的输出必须符合本规范；校验脚本 tools/validate-asset-package.py。

## 目录结构
```
<character_id>/
├── persona.json            # 人设卡（校验后副本，见 persona-schema.json）
├── metadata.json           # 生成记录：引擎/模型/参数/耗时/显存/成本/seed（每次生成追加）
├── portrait/               # 形象（2D 立绘/分层）
│   ├── full.png            # 主立绘
│   ├── layered/            # 分层输出（Live2D/Spine 预留）
│   ├── expressions/        # 表情差分（可选，非主路径）
│   └── sheet.png           # 表情图集（可选）
├── pixel/                  # 场景 A：2D 像素角色资产
│   ├── front_anchor.png    # front 锚点（必须，后续资产生成基准）
│   ├── views/              # 三视图 front/side/back
│   ├── actions/            # 行为帧 idle/walk/attack/hurt
│   └── sprite_sheet.png    # 精灵表（统一画布/网格）
├── splash/                 # 场景 B：高清立绘资产
│   ├── portrait.png        # 主立绘
│   ├── expressions/        # 表情差分
│   └── turnaround/         # 转面/多视图
├── voice/                  # 语音（V1 独立 part）
│   ├── line_1.wav + line_1.txt
│   └── ...
└── preview.html            # 本地预览页（看图/听音）
```

## 命名与格式
- 图：PNG；透明背景（像素场景必须）；像素场景建议 32/64px 档，立绘 1024+
- 音：WAV 32k mono（GPT-SoVITS 输出）；字幕 txt 与 wav 同名
- metadata.json 结构：
  `{"character_id": "...", "generated_at": "...", "assets": [{"type": "pixel/three_view", "file": "pixel/views/side.png", "engine": "gpt-image-1", "prompt": "...", "params": {...}, "cost": "..."}]}`

## 必需文件（校验门槛）
- persona.json 必须存在且通过 validate-persona
- metadata.json 必须存在且为合法 JSON 数组/对象
- 至少一个资产目录有产物（portrait/ 或 pixel/ 或 splash/）
- 像素场景：front_anchor.png 必须存在
