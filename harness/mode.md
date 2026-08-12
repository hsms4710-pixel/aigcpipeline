# harness/mode.md —— 模式路由 + 阶段路径

按当前目标选择模式，决定读哪些文件、产出什么：

| 模式 | 何时 | 读 | 产出 |
|---|---|---|---|
| 调研 | 开新 part / 选型不确定 | reference/ + 各 spec 借鉴清单 | 借鉴清单更新 / 选型结论入 spec |
| 规划 | 拆 part / 拆 task | spec/<part>/ + tasks/backlog.md | tasks/<part>/ 拆解 |
| 开发 | 执行 task | tasks/<part>/ 当前 task + harness/constrain + verify | 代码/资产/工具，跑 verify |
| 审计 | part 交付 / 每周 | audit/AUDIT.md + 全仓 | audit-log 记录 + fixes |
| 收尾 | 发布/归档 | README + ROADMAP | 状态更新、commit、归档 |

阶段路径（简单任务）：spec → task → 开发 → verify → 归档
阶段路径（复杂任务）：调研 → spec → tasks → harness/skill 就位 → 开发 → 审阅 → verify → audit → 归档
