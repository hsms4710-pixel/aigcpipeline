# pipeline 运行审计（audit/langgraph-runs.md）

> LangGraph pipeline（A1+S0-S5+A6）每次运行追加一行；由 pipeline/langgraph/nodes.py `_audit()` 自动写入。
> 格式：时间 | 资产名 | type | stages | final | manifest 路径

- 2026-08-21 04:18 | final_check | character | ['s0','s1','s2','s3','s4','s5'] | WARN(offline dry-run) | pipeline/langgraph 离线冒烟：整图编译+路由+skill 三级加载通过（未执行外部工具）
