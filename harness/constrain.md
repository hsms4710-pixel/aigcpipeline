# harness/constrain.md —— 红线 / 告警 / 约定

## 红线（不可违反）
- ❌ 不实现 P5 评测（P1-P4 跑通前）
- ❌ 不把模型权重/大产物提交入库（.gitignore 已列）
- ❌ 不直接改 rules/PRINCIPLES.md 而不记录 decision
- ❌ 不绕过 verify 声称"完成"；验收不通过 = 未完成
- ❌ 不绑定单一引擎：产出必须资产中立（PNG/WAV/glTF/JSON）

## 告警（需确认）
- ⚠️ 引入重型框架（Temporal、K8s、云服务）前先确认是否必要（MVP 倾向轻量）
- ⚠️ 使用外部 API/模型 key 前确认费用与密钥存放
- ⚠️ 语音克隆/肖像生成涉及版权/肖像权：只用用户自己的参考素材

## 约定
- 每个生成任务落 metadata（模型/参数/耗时/显存/成本/seed）——喂后续评测
- 代码风格：Python 用 ruff/black；Godot 用 gdformat；提交前静态检查
- 新契约（schema/协议）先评审再写实现
