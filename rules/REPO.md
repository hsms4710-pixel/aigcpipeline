# 仓库规则（rules/REPO.md）

## 1. 目录与写入权限
| 目录 | 用途 | 谁写 |
|---|---|---|
| rules/ | 课题原则 + 仓库规则 | 仅组长/主 agent，变更需记录 decision |
| spec/ | 每个 part 的规范（范围/契约/借鉴） | spec 评审后写入 |
| harness/ | AI 执行规则层 + skills | 随 part 演进 |
| tasks/ | 任务拆解（backlog + 每 part） | 拆解时写入，状态在 task 文件内维护 |
| audit/ | 审计清单 + 日志 | 审计时写入 |
| reference/ | 调研引用笔记 | 调研时追加 |
| assets/ | 工作产物（不入库，见 .gitignore） | 开发时写入 |
| tools/ | 本地工具脚本 | 开发时写入 |
| 工作流设计.md / 研究计划.md | 调研文档（根） | 调研/规划时更新 |

## 2. 文件命名
- spec：`spec/<part>/spec.md`（主规范）、`design.md`（技术方案，需要时）、`contracts/`（契约，如 persona-schema.json）
- task：`tasks/<part>/t<序号>-<短名>.md`，编号全库唯一（t1, t2, ...）
- skill：`harness/skills/SKILL_<短名>.md`
- 审计：`audit/audit-log.md`（追加）；`audit/checklists/<part>-<日期>.md`

## 3. 状态流转
```
idea → spec（范围+借鉴+契约）→ tasks 拆解（含验收）→ harness/skill 就位 → 开发（逐 task）→ verify → audit → 归档
```
- task 状态：`todo / in_progress / done / blocked`，写在 task 文件头部
- part 状态：`规划中 / 开发中 / 已交付 / 已审计`，写在 `ROADMAP.md`

## 4. git 提交规范
- 前缀：`docs:`（文档/调研）、`spec:`（规范）、`task:`（任务拆解）、`feat:`（功能/工具）、`harness:`（harness/skill）、`audit:`（审计）、`chore:`
- 提交信息：`<前缀> <part>: <一句话>`
- 示例：`spec p1: 人设卡 JSON Schema v0`
- 规则/原则变更必须带 `decision:` 记录（写入 harness/memory/decisions/）

## 5. 审计时机与触发
- 每个 part 交付时强制审计
- 每周一次例行审计（如无变化则跳过）
- 改动规则/契约/harness 后触发专项审计
- 审计流程见 `audit/AUDIT.md`

## 6. 禁止事项
- 不直接改 `rules/PRINCIPLES.md` 而不记录 decision
- 不把大文件/产物提交入库（见 .gitignore：assets/output、wav/mp4、模型权重）
- 不绕过 `harness/verify.md` 的验证门禁声称"完成"
- 评测（P5）在 P1-P4 跑通前不实现
