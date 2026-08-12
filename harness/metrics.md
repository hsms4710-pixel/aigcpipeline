# harness/metrics.md —— 任务度量规则

## 每 task 收尾
- 状态：done/blocked + 一句结论
- 验证输出：贴 verify 结果
- 耗时：预估 vs 实际（简单记录）

## 每 part 交付
- gate 清单全过
- 审计记录 1 条
- 生成任务统计（P1）：角色数、图/音数量、平均耗时/显存/成本（喂 P5）

## 仓库健康
- task backlog：done/total 比例
- audit 未关闭项：数量（目标 0）
