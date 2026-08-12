# harness/verify.md —— 验证命令与门禁

> 门禁：task 声称 done 前必须执行对应验证，并把输出贴进 task 文件。

## 通用
- git 状态干净：`git status` 无未提交变更（或有说明）
- 文档引用路径有效：`inform.md` 提到的文件都存在

## Python（P1 编排/工具）
- 静态检查：`ruff check tools/`、`black --check tools/`
- 测试：`pytest tools/tests/ -q`（有测试时）
- 依赖锁定：`requirements.txt` / `pyproject.toml` 已更新

## 资产
- 资产包校验脚本：`tools/validate-asset-package.ps1 <pkg_dir>` 通过
- 人设卡校验：`tools/validate-persona.ps1 persona.json` 通过

## Godot（P4）
- 工程可打开：无脚本错误（Editor 打开无报错）
- 导出/运行：`godot --headless --path <project> --quit` 无错误

## TTS / 生图（P1）
- 产物存在且非空：立绘 4 表情 + 3 段 wav
- 人工确认：身份一致 / 音色一致（记录在 task 验收栏）

## 强门禁（对账）
- task 验收清单全勾选
- audit/AUDIT.md 清单通过（part 交付时）
