# 审计（audit/AUDIT.md）

> 目的：确保"说完成的都真完成了、仓库与文档一致、没有表面功夫"。
> 时机：每 part 交付强制审计；每周例行；规则/契约/harness 变更后专项审计。

## 审计流程
1. 选清单（5 类，见下）逐项核对，每项给出 ✅ / ⚠️ / ❌ + 证据
2. ⚠️/❌ 项开 fixes（记录到 audit-log），可阻塞 part 交付
3. 输出：`audit/audit-log.md` 追加一条（日期 / 范围 / 结果 / fixes / 审计人）

## 5 类清单
### A. rule 合规
- [ ] 无 P5 评测被提前实现
- [ ] 无大文件/产物入库（git ls-files 抽查）
- [ ] 原则变更均有 decision 记录
### B. spec 一致性
- [ ] 当前 part 的 spec 与实际实现一致（无"文档写 A 代码做 B"）
- [ ] 契约（schema/协议）有实现对应，且实现未偏离契约
### C. harness 可用
- [ ] constrain 红线未被违反
- [ ] verify 门禁被实际执行过（task 有验证输出）
- [ ] skills 与当前 part 的流程一致
### D. task 完成度
- [ ] 当前 part 所有 task 状态与事实一致（done = 验收全过）
- [ ] 无"声称 done 但验收未过"的 task
- [ ] backlog 状态同步
### E. 仓库健康
- [ ] git 状态干净、提交规范符合 rules/REPO.md
- [ ] ROADMAP / README 状态与事实一致
- [ ] memory 沉淀至少 1 条 decision/knowledge（part 交付时）

## 审计工具
- `git status` / `git ls-files`（核对入库内容）
- 逐 task 读验收栏 + verify 输出
- 跑 `tools/validate-*.ps1`（资产/人设校验）
