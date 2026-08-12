# t8：提示词模板实现（gen-prompt.py + 模板文件）

状态：todo ｜ 依赖：t1 场景测试结论 ｜ 预估：1 天

## 目标
把 prompt-templates.md 落成可执行模板：persona.json + 资产场景 + 视图 → 提示词。

## 产出
- `tools/gen-prompt.py`：读 persona.json + 场景参数 → 分层组 prompt（主体/装备/服饰/细节/风格锚点/视图/输出约束）
- `spec/p1/contracts/prompt-templates/pixel.md`、`splash.md`（场景模板 + 视图片段 + 输出约束）

## 验收
- [ ] 三种场景（像素三视图/像素行为帧/立绘表情）各生成 1 条 prompt 合理可读
- [ ] 风格锚点 + 参考图锚点字段自动带上
- [ ] ruff/black 通过
