# GPT-Image2-Skill（vendor 副本）

> 来源：https://github.com/wuyoscar/GPT-Image2-Skill ｜ License: MIT（LICENSE 见本目录）
> 抓取日期：2026-08-21 ｜ 只 vendor 了 `skills/gpt-image/`（SKILL.md + references 参考库 + generate.py），**未包含 docs/ 示例大图**。

## 这是什么
GPT Image 2（gpt-image-2）生成/编辑的 Agent skill：方法论 + 参数参考 + 分类提示词画廊（gallery）+ prompt craft 工艺清单。

## 本仓库如何用它（重要：生图必须遵循，不要盲目生成）
- **方法论文档**：
  - `skills/gpt-image/SKILL.md` — Agent runbook（分类请求→查 gallery→craft 精修→执行）
  - `skills/gpt-image/references/craft.md` — 19 节 prompt 工艺清单（结构优先/场景密度/风格锚点/材质光照调色板分离/编辑保真）
  - `skills/gpt-image/references/openai-cookbook.md` — OpenAI 官方 prompting guide 存档
  - `skills/gpt-image/references/gallery-*.md` — 分类提示词画廊（pixel-art / character-design / isometric / gaming / anime-manga 等）
- **已接入本仓库代码**：
  - `tools/prompt_vision.py` — 视觉提示词设计师的 system prompt 已注入本 skill 的 10 条方法论（结构→目标 / 场景密度 / 风格锚点 / 材质光照调色板分离 / 长宽比先行 / 编辑保真）
  - `tools/image_backend.py` — `_check_size()` 校验 size ≥655k px（16px 倍数），低于 1024x1024 告警
  - `tools/a2-pipeline.py` — 默认 size 由 512x512 改为 **1024x1024**
- **关键参数**（gpt-image-2）：
  - size：16px 倍数，总像素 655k–8.3M；常用 1024x1024 / 1024x1536(portrait) / 1536x1024(landscape)
  - quality：low=草稿 / medium=探索 / high=最终（本项目默认 high）
  - 端点：`/v1/images/generations`（文生图）、`/v1/images/edits`（参考图/多参考/mask 局部重绘：opaque=保留、transparent=重绘）
  - gpt-image-2 不接受 `input_fidelity` 参数

## 使用
- 本仓库不替换生图后端（仍走 `tools/image_backend.py` 中转站），只遵循其**提示词与参数方法论**
- 独立调用 skill CLI（需 OPENAI_API_KEY）：`uv run skills/gpt-image/scripts/generate.py -p "..." -f out.png`
