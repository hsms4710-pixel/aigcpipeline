# -*- coding: utf-8 -*-
"""skill_loader.py — LangGraph 风格 Skill 加载器（progressive disclosure）

项目主体是 agent 驱动的 AIGC pipeline，Skill 按 LangGraph / Deep Agents
SkillsMiddleware 的三级渐进披露方式在运行时加载，而不是静态写死在脚本里：

  Level 1 Discovery : 启动时扫描 skills_library/*/SKILL.md 的 YAML frontmatter，
                      把每个 skill 的 name + description 注入 system prompt（元数据）
  Level 2 Read      : 任务命中某 skill 的 description 时，读取该 skill 完整 SKILL.md 指令正文
  Level 3 Execute   : 按 SKILL.md 指令，按需读取 references/ scripts/ assets/ 资源文件

约定（与 LangGraph skills 规范一致，见 docs.langchain.com/oss/python/deepagents/skills）：
  - 一个 skill = 一个目录，内含 SKILL.md（YAML frontmatter: name / description）+ 指令正文，
    可选 references/（按需查阅）、scripts/（可执行）、assets/（静态资源）
  - 默认根 = <repo>/skills_library（LangGraph 约定：backend root 下的顶层 skills 目录）；
    可传额外根，多根同名 skill 时后列出的覆盖（last one wins，LangGraph 语义）
  - 路径安全：load_skill_resource() 做 realpath 校验，不允许越出 skill 根目录
  - 本项目已按此规范落地的 skill：skills_library/gpt-image/（GPT-Image2-Skill，vendor 自
    tools/vendor/GPT-Image2-Skill，同步命令见 skills_library/README.md）

用法（CLI）:
  python tools/skill_loader.py --list                 # Level 1：列出全部 skill 元数据
  python tools/skill_loader.py --select "像素角色生成"  # 按任务描述匹配 skill
  python tools/skill_loader.py --load gpt-image       # Level 2：打印完整 SKILL.md
  python tools/skill_loader.py --resource gpt-image references/craft.md   # Level 3：按需读资源
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ROOTS = [os.path.join(REPO, "skills_library")]
SKILL_MARKER = "SKILL.md"
# 允许的 skill 资源子目录（LangGraph Agent Skills 规范）
RESOURCE_DIRS = ("references", "scripts", "assets", "agents")


@dataclass
class SkillMeta:
    """Level 1：skill 元数据（name + description，注入 system prompt 用）"""
    name: str
    description: str
    root: str
    path: str  # skill 目录绝对路径

    def to_dict(self) -> dict:
        return {"name": self.name, "description": self.description}


@dataclass
class Skill:
    """Level 2+3：完整 skill（SKILL.md 正文 + 可用的资源文件清单）"""
    meta: SkillMeta
    body: str
    resources: dict = field(default_factory=dict)  # rel_path -> abs_path


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 SKILL.md 头部的 YAML frontmatter（--- ... ---），返回 (meta, body)。"""
    meta: dict = {}
    body = text
    m = re.match(r"^\ufeff?---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        raw = m.group(1)
        if yaml is not None:
            try:
                meta = yaml.safe_load(raw) or {}
            except Exception:
                meta = {}
        if not isinstance(meta, dict):
            meta = {}
        body = text[m.end():]
    return meta, body


def _skill_dirs(root: str) -> list[str]:
    """root 下所有含 SKILL.md 的一级 skill 目录（LangGraph：skills/<skill>/SKILL.md）。"""
    out = []
    if not os.path.isdir(root):
        return out
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return out
    for name in entries:
        d = os.path.join(root, name)
        if os.path.isfile(os.path.join(d, SKILL_MARKER)):
            out.append(d)
    return out


def _safe_join(skill_root: str, rel_path: str) -> str:
    """把 rel_path 限定在 skill 根目录内（防路径穿越），返回绝对路径。"""
    base = os.path.realpath(skill_root)
    target = os.path.realpath(os.path.join(skill_root, rel_path))
    if not (target == base or target.startswith(base + os.sep)):
        raise ValueError(f"resource 路径越界: {rel_path!r} (skill={os.path.basename(base)})")
    return target


def _resolve_root(name: str, skills_roots: list[str] | None) -> str | None:
    """在多根中定位名为 name 的 skill 目录；同名时取最后一个（LangGraph last-one-wins）。"""
    found = None
    for root in (skills_roots or DEFAULT_ROOTS):
        d = os.path.join(root, name)
        if os.path.isfile(os.path.join(d, SKILL_MARKER)):
            found = d
    return found


def discover_skills(skills_roots: list[str] | None = None) -> list[SkillMeta]:
    """Level 1 Discovery：扫描所有根，解析每个 SKILL.md frontmatter，返回元数据列表。

    多根同名 skill 时，后列出的根覆盖（last one wins）。
    """
    metas: dict[str, SkillMeta] = {}
    for root in (skills_roots or DEFAULT_ROOTS):
        for d in _skill_dirs(root):
            name = os.path.basename(d)
            try:
                text = open(os.path.join(d, SKILL_MARKER), "r", encoding="utf-8").read()
            except OSError:
                continue
            meta, _ = _parse_frontmatter(text)
            metas[name] = SkillMeta(
                name=str(meta.get("name", name)),
                description=str(meta.get("description", "")).strip(),
                root=os.path.realpath(d),
                path=os.path.realpath(d),
            )
    return list(metas.values())


def select_skill_for_task(task: str, skills_roots: list[str] | None = None,
                          top_k: int = 3) -> list[SkillMeta]:
    """按任务描述匹配 skill：description 关键词命中打分，返回 top_k 个候选。

    模拟 LangGraph agent 的"任务命中 description 就激活该 skill"行为。
    """
    metas = discover_skills(skills_roots)
    if not task:
        return metas[:top_k]
    task_l = task.lower()
    scored = []
    for m in metas:
        desc = m.description.lower()
        # 描述里的关键词词元（去掉停用词/弱词）在任务文本里出现即加分
        toks = re.findall(r"[a-z][a-z0-9\-]{2,}", desc)
        stop = {"use", "the", "this", "when", "skill", "image", "generation", "for", "with", "and", "you", "your", "any"}
        hits = sum(1 for t in set(toks) - stop if t in task_l)
        # 中文：描述中的中文片段命中任务
        cn = re.findall(r"[\u4e00-\u9fff]{2,}", desc)
        cn_hits = sum(1 for t in set(cn) if t in task)
        score = hits * 2 + cn_hits
        if m.name.lower() in task_l:
            score += 5
        scored.append((score, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:top_k]]


def load_skill(name: str, skills_roots: list[str] | None = None) -> Skill:
    """Level 2 Read：读取完整 SKILL.md 正文 + 列出可用资源文件。"""
    d = _resolve_root(name, skills_roots)
    if d is None:
        raise FileNotFoundError(f"skill 不存在: {name!r}（根={skills_roots or DEFAULT_ROOTS}）")
    text = open(os.path.join(d, SKILL_MARKER), "r", encoding="utf-8").read()
    meta, body = _parse_frontmatter(text)
    smeta = SkillMeta(
        name=str(meta.get("name", name)),
        description=str(meta.get("description", "")).strip(),
        root=os.path.realpath(d),
        path=os.path.realpath(d),
    )
    resources: dict[str, str] = {}
    for sub in RESOURCE_DIRS:
        sdir = os.path.join(d, sub)
        if not os.path.isdir(sdir):
            continue
        for dp, _, fns in os.walk(sdir):
            for fn in fns:
                fp = os.path.join(dp, fn)
                rel = os.path.relpath(fp, d).replace("\\", "/")
                resources[rel] = os.path.realpath(fp)
    return Skill(meta=smeta, body=body.strip(), resources=resources)


def load_skill_resource(name: str, rel_path: str,
                        skills_roots: list[str] | None = None) -> str:
    """Level 3 Execute：按需读取 skill 的 references/scripts/assets 资源（路径安全）。"""
    d = _resolve_root(name, skills_roots)
    if d is None:
        raise FileNotFoundError(f"skill 不存在: {name!r}")
    target = _safe_join(d, rel_path)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"skill 资源不存在: {name}/{rel_path}")
    try:
        return open(target, "r", encoding="utf-8").read()
    except UnicodeDecodeError:
        return f"[binary resource {rel_path}: {os.path.getsize(target)} bytes]"


def render_metadata_block(metas: list[SkillMeta] | None = None,
                          skills_roots: list[str] | None = None) -> str:
    """Level 1：把 skill 元数据渲染成 system prompt 片段（SkillsMiddleware 行为）。"""
    metas = metas if metas is not None else discover_skills(skills_roots)
    if not metas:
        return ""
    lines = ["## Available Skills (loaded via LangGraph progressive disclosure)",
             "At startup you only see metadata below (Level 1). When a task matches a skill's description,",
             "load its full SKILL.md (Level 2) and then read only the referenced resources (Level 3)."]
    for m in metas:
        lines.append(f"- `{m.name}`: {m.description}")
    return "\n".join(lines)


def build_skill_context(skill_name: str | None, task: str = "",
                        auto_resources: list[str] | None = None,
                        skills_roots: list[str] | None = None) -> dict:
    """一键组装某 skill 的三级上下文（供一次性脚本/节点使用）。

    - metadata: 全部 skill 的 Level 1 元数据块
    - skill: Level 2 完整 SKILL.md
    - resources: Level 3 按需资源 {rel_path: content}（auto_resources 指定；缺省按任务自动选 gallery）
    返回 dict，字段均含"_loaded": true 便于 agent 判断是否已加载。
    """
    metas = discover_skills(skills_roots)
    if skill_name is None and task:
        cand = select_skill_for_task(task, skills_roots, top_k=1)
        skill_name = cand[0].name if cand else None
    skill = load_skill(skill_name, skills_roots) if skill_name else None
    resources: dict[str, str] = {}
    if skill and skill.resources:
        picks = list(auto_resources or [])
        if not picks:
            picks = auto_pick_resources(skill, task)
        for rel in picks:
            if rel in skill.resources:
                resources[rel] = load_skill_resource(skill_name, rel, skills_roots)
    return {
        "metadata": render_metadata_block(metas),
        "metadata_loaded": bool(metas),
        "skill": skill_name,
        "skill_body": skill.body if skill else "",
        "skill_loaded": skill is not None,
        "resources": resources,
        "resources_loaded": bool(resources),
    }


def auto_pick_resources(skill: Skill, task: str = "") -> list[str]:
    """按任务/资产类型自动挑选该读哪些 references（Level 3 的最小切片原则）。

    gpt-image 参考库规则（SKILL.md 原文）：先 gallery.md 路由索引，再按类别取 1 个 gallery，
    craft.md 用于修 prompt / 文字 / UI / 图表 / 多面板一致性。
    """
    refs = sorted(r for r in skill.resources if r.startswith("references/"))
    if not refs:
        return []
    index = [r for r in refs if r.endswith("gallery.md")]
    craft = [r for r in refs if r.endswith("craft.md")]
    picks = list(index)  # 路由索引优先
    # 按任务关键词匹配 gallery 类别（只取 1 个，避免上下文膨胀）
    kw = (task or "").lower()
    gallery_map = [
        ("pixel", "gallery-pixel-art.md"),
        ("game", "gallery-gaming.md"),
        ("character", "gallery-character-design.md"),
        ("anime", "gallery-anime-and-manga.md"),
        ("isometric", "gallery-isometric.md"),
        ("illustration", "gallery-illustration.md"),
        ("ui", "gallery-ui-ux-mockups.md"),
        ("poster", "gallery-typography-and-posters.md"),
        ("map", "gallery-gaming.md"),
        ("sprite", "gallery-pixel-art.md"),
    ]
    for k, fn in gallery_map:
        if k in kw:
            for r in refs:
                if r.endswith(fn):
                    picks.append(r)
                    break
            break
    if not any(r.endswith("craft.md") for r in picks) and craft:
        picks.append(craft[0])  # 生图必备：prompt 工艺清单
    # 去重保序
    seen, out = set(), []
    for r in picks:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="LangGraph 风格 skill 加载器（progressive disclosure）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="Level 1: 列出所有 skill 元数据")
    g.add_argument("--select", metavar="TASK", help="按任务描述匹配 skill（返回候选）")
    g.add_argument("--load", metavar="NAME", help="Level 2: 打印完整 SKILL.md")
    g.add_argument("--resource", nargs=2, metavar=("NAME", "REL_PATH"), help="Level 3: 按需读资源")
    g.add_argument("--context", metavar="NAME", help="一键输出三级上下文（含 auto 选资源）")
    ap.add_argument("--root", action="append", default=[], help="额外 skill 根（可多次）")
    ap.add_argument("--task", default="", help="--context 的任务描述（自动选资源）")
    a = ap.parse_args()
    roots = DEFAULT_ROOTS + a.root
    if a.list:
        for m in discover_skills(roots):
            print(f"- {m.name}: {m.description[:120]}")
        return 0
    if a.select:
        for m in select_skill_for_task(a.select, roots):
            print(f"[{m.name}] score-matched: {m.description[:120]}")
        return 0
    if a.load:
        s = load_skill(a.load, roots)
        print(f"# SKILL: {s.meta.name}\n# root: {s.meta.root}\n")
        print(s.body)
        if s.resources:
            print(f"\n# resources ({len(s.resources)}):")
            for rel in sorted(s.resources):
                print(f"  {rel}")
        return 0
    if a.resource:
        name, rel = a.resource
        print(load_skill_resource(name, rel, roots))
        return 0
    if a.context:
        ctx = build_skill_context(a.context, task=a.task, skills_roots=roots)
        print(f"# metadata_loaded={ctx['metadata_loaded']} skill={ctx['skill']} skill_loaded={ctx['skill_loaded']}")
        print(ctx["metadata"])
        print("\n" + "#" * 20 + " SKILL.md " + "#" * 20)
        print(ctx["skill_body"][:4000])
        for rel, content in ctx["resources"].items():
            print(f"\n# resource: {rel} ({len(content)} chars)")
            print(content[:1500])
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
