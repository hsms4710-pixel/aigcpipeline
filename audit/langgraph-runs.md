# pipeline 运行审计（audit/langgraph-runs.md）

> LangGraph pipeline（A1 + 三路线：骨骼A/关键帧B/3D F + A6）每次运行追加一行；由 pipeline/langgraph/nodes.py `_audit()` 自动写入。
> 格式：时间 | 资产名 | route | type | stages | final | manifest 路径

- 2026-08-21 04:35 | v3 三路线离线冒烟 | skeletal/keyframe/3d | character | s0-s5 / kb1-kb2 / f1-f5 | WARN/SKIP/SKIP(offline) | 整图编译+路由+命令构造通过（未执行外部工具）
