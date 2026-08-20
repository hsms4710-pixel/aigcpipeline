# skills_library — LangGraph 风格 Skill 注册表（运行时按需加载）

> 项目主体是 **agent 驱动的 AIGC pipeline**，Skill 不静态写死，而是按
> **LangGraph / Deep Agents 三级渐进披露**方式在运行时加载：
> **Level 1 元数据（name+description 注入 system prompt）→ Level 2 命中后读完整 SKILL.md → Level 3 按需读 references/scripts/assets**。
> 加载器：`tools/skill_loader.py`（discover / select / load / resource，多根 last-one-wins，路径安全）。

## 目录规范（与 LangGraph skills 一致）

```
skills_library/
└── <skill-name>/
    ├── SKILL.md          # YAML frontmatter(name+description) + 指令正文（Agent Skills 规范）
    ├── references/       # 按需查阅的参考文档（Level 3）
    ├── scripts/          # 可执行脚本（Level 3）
    ├── assets/           # 静态资源（Level 3）
    └── agents/           # 可选：agent 定义
```

## 已注册 skill

| skill | 来源 | 用途 | 状态 |
|---|---|---|---|
| `gpt-image` | vendor `tools/vendor/GPT-Image2-Skill/skills/gpt-image` | GPT Image 2 生图/改图方法论：Operating loop + craft + 162-prompt gallery + openai-cookbook + CLI(scripts/generate.py) | ✅ 已注册（A2 资产生成核心 skill） |

## 同步（vendor → registry）

`gpt-image` 是 `tools/vendor/GPT-Image2-Skill`（上游 wuyoscar/GPT-Image2-Skill）的运行态副本，
上游更新后手动同步（PowerShell）：

```powershell
Copy-Item -Path tools/vendor/GPT-Image2-Skill/skills/gpt-image -Destination skills_library/gpt-image -Recurse -Force
```

## 怎么用

```bash
# Level 1 发现（元数据）
python tools/skill_loader.py --list
# 按任务匹配 skill
python tools/skill_loader.py --select "生成像素角色精灵表"
# Level 2 读完整 SKILL.md
python tools/skill_loader.py --load gpt-image
# Level 3 按需读资源
python tools/skill_loader.py --resource gpt-image references/craft.md
# 一键三级上下文（A2 节点内部用法）
python tools/skill_loader.py --context gpt-image --task "宝可梦像素地图瓦片"
```

A2 流水线接入：`tools/agent_a2_node.py`（LangGraph StateGraph 节点）在 `skill_context`
节点用 `build_skill_context()` 加载 gpt-image skill 三级内容；`tools/prompt_vision.py`
同样走 loader（不再硬编码方法论摘要）。详见 `spec/aigc-tools-integration.md`。
