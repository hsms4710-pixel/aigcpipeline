# -*- coding: utf-8 -*-
"""nodes.py — 完整 pipeline LangGraph 节点（A1 + S0-S5 + A6）

把 tools/workbench（FastAPI S0-S5 编排）的每个 stage 改成 LangGraph 节点，真实接线底层工具：

  A1 a1_plan          需求 -> plan 资产契约
  S0 a2_skill/prompt/generate/a3_gate  demand 驱动生图（LangGraph skill 三级渐进披露）
     s0_gen_portrait   人物卡驱动生图（gen-portrait.py）
  S1 s1_decompose     See-through blockswap 拆层 -> validate-layered 门禁（WARN 非致命）
  S2 s2_rig           StretchyStudio rig-psd.cjs 绑骨 -> fix-rig -> validate-rig 门禁
  S3 s3_animate       LLM 动画导演 stretchy-agent.cjs -> fix-rig -> validate-anim 门禁 + usage 成本
  S4 s4_package       package-assets.py 图集打包 + manifest
  S5 s5_engine        export-godot.py Godot 工程（SpinePlayer）
  A6 a6_archive       manifest v2 + lessons 回填 + audit

诚实原则：工具/服务缺失时 status=FAIL/STUB/SKIP 并给原因，绝不假装 PASS。
dry_run=True 时只校验输入契约 + 构造命令（打印），不执行外部工具（可离线验证整图）。
"""
from __future__ import annotations

import json, os, re, shutil, subprocess, sys, time
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, "tools")
PLG = os.path.join(REPO, "pipeline", "langgraph")
for _p in (TOOLS, PLG):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from skill_loader import DEFAULT_ROOTS, build_skill_context  # noqa: E402
from state import PipelineState  # noqa: E402

# ---- 环境常量（与 tools/workbench/app.py 一致） ----
VENV_PY = os.path.join(REPO, "runtime", ".venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PY):
    VENV_PY = sys.executable
SEE_THROUGH_DIR = os.path.join(REPO, "env", "runtime", "tools", "see-through")
SEE_THROUGH_PY = os.path.join(SEE_THROUGH_DIR, "venv", "Scripts", "python.exe")
if not os.path.exists(SEE_THROUGH_PY):
    SEE_THROUGH_PY = VENV_PY
NODE = "node.exe"
LESSONS_FILE = os.path.join(REPO, "harness", "memory", "pipeline", "lessons-learned.md")

STAGE_ORDER = ["s0", "s1", "s2", "s3", "s4", "s5"]
STAGE_TOOLS = {
    "s0": "gen-portrait.py / prompt_vision + image_backend",
    "s1": "See-through inference_psd_blockswap.py + validate-layered.py",
    "s2": "rig-automation/rig-psd.cjs + fix-rig.py + validate-rig.py",
    "s3": "rig-automation/stretchy-agent.cjs + fix-rig.py + validate-anim.py",
    "s4": "package-assets.py + validate-asset-package.py",
    "s5": "export-godot.py + godot-shot.py",
}


def _log(state: PipelineState, msg: str) -> None:
    state.setdefault("log", []).append(msg)
    print(f"[pipeline] {msg}")


def _dump(state: PipelineState, rel: str, obj: Any) -> str:
    os.makedirs(state["out_dir"], exist_ok=True)
    p = os.path.join(state["out_dir"], rel)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return p


def _resolve(p: str) -> str:
    if not p:
        return ""
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def _stage_dir(state: PipelineState, stage: str, default: str) -> str:
    d = os.path.join(state["out_dir"], stage, default)
    os.makedirs(d, exist_ok=True)
    return d


def _stage_upstream(state: PipelineState, stage: str) -> str:
    """取上游 stage 的主产物路径（按 S0->S5 顺序回退查找）。"""
    for prev in reversed(STAGE_ORDER[:STAGE_ORDER.index(stage) if stage in STAGE_ORDER else len(STAGE_ORDER)]):
        so = (state.get("stage_outputs") or {}).get(prev, {})
        for k in ("image_path", "layered_dir", "rig_zip", "anim_zip", "package_dir", "godot_dir"):
            if so.get(k):
                return so[k]
    return state.get("image_path", "")


def _run_cmd(cmd: list, cwd: str, state: PipelineState, stage: str,
             timeout: int = 7200, env: dict | None = None) -> tuple[int, str, str]:
    """执行命令并记录日志（与 workbench _run_cmd 一致）。dry_run 时只打印不执行。"""
    state.setdefault("stage_logs", {})
    log_tail = state["stage_logs"].setdefault(stage, "")
    log_tail += "$ " + " ".join(str(x) for x in cmd) + "\n"
    if state.get("dry_run"):
        print(f"[pipeline:{stage}] DRY-RUN 命令: {' '.join(str(x) for x in cmd)}")
        state["stage_logs"][stage] = log_tail
        return 0, "dry-run", ""
    _env = dict(os.environ)
    if env:
        _env.update(env)
    try:
        r = subprocess.run(cmd, cwd=cwd, timeout=timeout, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=_env)
        log_tail += (r.stdout or "") + "\n" + (r.stderr or "")
        state["stage_logs"][stage] = log_tail[-12000:]
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        state["stage_logs"][stage] = log_tail + "TIMEOUT\n"
        return -1, "", "timeout"
    except Exception as e:
        state["stage_logs"][stage] = log_tail + f"EXC {type(e).__name__}: {e}\n"
        return -1, "", str(e)


def _set_stage(state: PipelineState, stage: str, status: str, out: dict | None = None,
               gate: dict | None = None, reason: str = "") -> dict:
    """统一写 stage_outputs[stage] = {status, out, gate, reason}。"""
    so = dict(state.get("stage_outputs") or {})
    entry = {"status": status, "out": out or {}, "gate": gate or {}, "reason": reason}
    so[stage] = entry
    state["stage_outputs"] = so
    _log(state, f"{stage} -> {status}" + (f" | {reason}" if reason else ""))
    return {"stage_outputs": so}


def _stage_status(state: PipelineState, stage: str) -> str:
    return (state.get("stage_outputs") or {}).get(stage, {}).get("status", "SKIP")


# ===========================================================================
# A1 需求规划
# ===========================================================================
_TYPE_KEYWORDS = [
    ("map", ["地图", "map", "俯视", "村庄", "城镇", "野外", "overworld", "场景地图"]),
    ("scene", ["场景", "scene", "town", "室内", "酒馆"]),
    ("tileset", ["瓦片", "tileset", "图块", "无缝"]),
    ("animation", ["动画", "animation", "walk", "idle", "攻击动画", "帧动画"]),
    ("character", ["角色", "character", "小人", "立绘", "人物", "chibi", "sprite character"]),
]


def node_a1_plan(state: PipelineState) -> dict:
    demand = state.get("demand", "")
    atype = state.get("atype", "")
    if not atype:
        dl = demand.lower()
        for t, kws in _TYPE_KEYWORDS:
            if any(k in demand or k in dl for k in kws):
                atype = t
                break
        atype = atype or "sprite"
    if atype == "sprite" and state.get("persona"):
        atype = "character"
    style = state.get("style", "pokemon-nds-bw")
    name = state.get("name") or _auto_name(demand, atype)
    transparent = state.get("transparent", atype in ("character", "sprite"))
    size = state.get("size", "1024x1024")
    plan = {
        "schema": "asset.plan.v1",
        "type": atype,
        "style": style,
        "name": name,
        "params": {"size": size, "transparent": transparent,
                   "split": [4, 4] if atype in ("character", "animation") else None,
                   "frame_size": 64 if atype in ("character", "animation") else 0},
        "sub_tasks": _sub_tasks(atype),
        "pipeline": "s0->s1->s2->s3->s4->s5->a6",
        "notes": "A1 规则解析生成；persona 驱动时 atype=character",
    }
    state["plan"] = plan
    state["atype"] = atype
    state["style"] = style
    state["name"] = name
    state["size"] = size
    state["transparent"] = transparent
    _dump(state, "plan.json", plan)
    _log(state, f"A1 规划 -> type={atype} style={style} name={name} pipeline={plan['pipeline']}")
    return {"plan": plan, "atype": atype, "style": style, "name": name, "size": size, "transparent": transparent}


def _auto_name(demand: str, atype: str) -> str:
    m = re.search(r"(艾琳|ailin|阿米娅|amiya|[\u4e00-\u9fff]{2,4})", demand)
    who = (m.group(1) if m else "char").lower()
    return f"{who}_{atype}_{int(time.time()) % 100000}"


def _sub_tasks(atype: str) -> list:
    base = {
        "character": ["S0 立绘/表情/小人", "S1 拆层(PSD)", "S2 绑骨", "S3 动画", "S4 打包", "S5 Godot 引擎"],
        "map": ["S0 瓦片集/地图", "S3 门禁", "S5 Godot TileMap 工程"],
        "tileset": ["S0 瓦片集", "S3 无缝/风格门禁", "S5 瓦片入库"],
        "animation": ["S0 关键帧", "S3 帧间一致性门禁", "S5 Godot AnimatedSprite2D"],
        "scene": ["S0 场景图", "S3 视觉门禁", "S5 Godot 场景骨架"],
        "sprite": ["S0 精灵生成", "S3 视觉门禁", "S5 入库/引擎接入"],
    }
    return base.get(atype, base["sprite"])


# ===========================================================================
# S0 生图（demand 驱动：LangGraph skill 三级渐进披露 + 视觉提示词 + 生图 + 门禁）
# ===========================================================================
def node_a2_skill(state: PipelineState) -> dict:
    task = f"{state.get('style', '')} {state.get('atype', '')} {state.get('demand', '')}"
    ctx = build_skill_context(state.get("skill_name") or "gpt-image", task=task,
                              skills_roots=state.get("skills_roots") or DEFAULT_ROOTS)
    state["skill_ctx"] = ctx
    _log(state, f"S0 skill_context -> activated={ctx['skill']} loaded={ctx['skill_loaded']} "
                f"resources={sorted(ctx['resources'].keys())}")
    return {"skill_ctx": ctx}


def node_a2_prompt(state: PipelineState) -> dict:
    from prompt_vision import design_prompt
    no_vision = bool(state.get("dry_run") or state.get("no_vision"))
    eff_demand = state["demand"]
    if state.get("issues"):
        eff_demand += " 上一轮验收问题（请针对性修订提示词修复）: " + "; ".join(str(x) for x in state["issues"][:6])
    prompt_doc = design_prompt(
        eff_demand, state["style"], state["atype"],
        refs=state.get("refs", []),
        current_prompt=state.get("last_prompt", ""),
        skill_name=state.get("skill_name") or "gpt-image",
        skills_roots=state.get("skills_roots") or DEFAULT_ROOTS,
        max_resource_chars=state.get("max_resource_chars", 8000),
        out_json=os.path.join(state["out_dir"], "prompt.json"),
        no_vision=no_vision,
        skill_ctx=state.get("skill_ctx"),
    )
    state["prompt_doc"] = prompt_doc
    state["last_prompt"] = prompt_doc.get("prompt", "")
    _log(state, f"S0 design_prompt -> {len(state['last_prompt'])} chars (no_vision={no_vision})")
    return {"prompt_doc": prompt_doc, "last_prompt": state["last_prompt"]}


def node_a2_generate(state: PipelineState) -> dict:
    if state.get("dry_run") or state.get("skip_generate") or not state.get("last_prompt"):
        state["image_path"] = ""
        _log(state, "S0 generate -> SKIP（dry-run/skip-generate）")
        return {"image_path": ""}
    from image_backend import gen_image
    raw = os.path.join(state["out_dir"], "s0", "raw.png")
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    n, dt = gen_image(state["last_prompt"], raw, size=state["size"],
                      transparent=state.get("transparent", False), quality="high")
    state["image_path"] = raw
    _log(state, f"S0 generate -> {n/1024:.0f}KB {dt:.1f}s ({raw})")
    return {"image_path": raw}


def node_a3_gate(state: PipelineState) -> dict:
    """S0 视觉门禁（Vision Gate）。dry-run/skip 时 SKIP。"""
    if state.get("dry_run") or state.get("skip_generate") or not state.get("image_path"):
        state["gate_result"] = "SKIP"
        upd = _set_stage(state, "s0", "WARN", out={"image_path": state.get("image_path", "")},
                         gate={"script": "vision_gate.py", "result": "SKIP", "report": {}},
                         reason="dry-run/skip-generate：无图可验")
        return {"gate_result": "SKIP", "attempts": int(state.get("attempts", 0)) + 1, "issues": [], **upd}
    from vision_gate import run_gate
    gate_json = os.path.join(state["out_dir"], "gate.json")
    report, result = run_gate([state["image_path"]], state["atype"], state["name"],
                              state.get("threshold", 7.0), state.get("baseline", []), gate_json, max_size=768)
    attempts = int(state.get("attempts", 0)) + 1
    issues = report.get("issues", []) if isinstance(report, dict) else []
    state["gate_report"] = report
    state["gate_result"] = result
    state["attempts"] = attempts
    state["issues"] = list(issues)
    _log(state, f"S0 gate -> {result} overall={report.get('overall')} issues={len(issues)} (attempt {attempts})")
    # 记录 S0 stage 契约（demand 路径）
    s0_status = "PASS" if result == "PASS" else ("WARN" if result == "SKIP" else "FAIL")
    upd = _set_stage(state, "s0", s0_status, out={"image_path": state.get("image_path", "")},
                     gate={"script": "vision_gate.py", "result": result, "report": report})
    return {"gate_report": report, "gate_result": result, "attempts": attempts, "issues": list(issues), **upd}


def node_s0_gen_portrait(state: PipelineState) -> dict:
    """S0 人物卡驱动生图（gen-portrait.py：persona -> 立绘/表情/小人）。"""
    out = _stage_dir(state, "s0", "portrait")
    persona = _resolve(state.get("persona", ""))
    if not persona or not os.path.isfile(persona):
        return _set_stage(state, "s0", "FAIL", reason=f"persona.json 不存在: {persona}")
    cmd = [VENV_PY, os.path.join(TOOLS, "gen-portrait.py"), persona, "--out", out,
           "--scene", state.get("scene", "splash")]
    for k, flag in (("model", "--model"), ("backend", "--backend")):
        if state.get(k):
            cmd += [flag, str(state[k])]
    if state.get("refs"):
        cmd += ["--ref", _resolve(state["refs"][0])]
    if state.get("style_ref"):
        cmd += ["--style-ref", str(state["style_ref"])]
    rc, so, se = _run_cmd(cmd, REPO, state, "s0", timeout=1800)
    if rc != 0:
        return _set_stage(state, "s0", "FAIL", reason=(se or so or "生图失败")[-300:])
    # 收集产物
    imgs = sorted([os.path.join(dp, f) for dp, _, fns in os.walk(out) for f in fns
                   if f.lower().endswith((".png", ".jpg"))])[:8]
    image_path = imgs[0] if imgs else ""
    state["image_path"] = image_path
    return _set_stage(state, "s0", "PASS", out={"image_path": image_path, "images": imgs})


# ===========================================================================
# S1 拆层（See-through blockswap）
# ===========================================================================
def node_s1_decompose(state: PipelineState) -> dict:
    out = _stage_dir(state, "s1", "layered")
    src = _resolve(state.get("s1_src") or _stage_upstream(state, "s1") or state.get("image_path", ""))
    if not src or not os.path.isfile(src):
        return _set_stage(state, "s1", "SKIP", reason=f"输入图片不存在（src={src}）")
    infer = os.path.join(SEE_THROUGH_DIR, "inference", "scripts", "inference_psd_blockswap.py")
    if not os.path.isfile(infer):
        return _set_stage(state, "s1", "STUB", reason=f"See-through 未安装: {infer}（env/README.md §4.2）")
    cmd = [SEE_THROUGH_PY, infer, "--srcp", src, "--save_dir", out]
    for k, flag in (("resolution", "--resolution"), ("resolution_depth", "--resolution_depth"),
                    ("num_inference_steps", "--num_inference_steps"), ("seed", "--seed")):
        if state.get(k):
            cmd += [flag, str(state[k])]
    if state.get("save_to_psd", True):
        cmd.append("--save_to_psd")
    if state.get("tblr_split"):
        cmd.append("--tblr_split")
    rc, so, se = _run_cmd(cmd, SEE_THROUGH_DIR, state, "s1", timeout=7200,
                          env={"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    if rc != 0:
        return _set_stage(state, "s1", "FAIL", reason=(se or so or "拆层失败")[-300:])
    # 门禁：层完整性（validate-layered）
    gate = {"script": "validate-layered.py", "result": "PASS"}
    rc2, so2, se2 = _run_cmd([SEE_THROUGH_PY, os.path.join(TOOLS, "validate-layered.py"), "--dir", out],
                             REPO, state, "s1", timeout=120, env={"PYTHONIOENCODING": "utf-8"})
    if rc2 != 0:
        gate = {"script": "validate-layered.py", "result": "WARN", "report": (so2 or se2 or "")[:2000]}
        _write_gate_file(state, "s1", gate)
        _append_lesson("s1_decompose", state, so2 or se2 or "")
    psd = next((os.path.join(dp, f) for dp, _, fns in os.walk(out) for f in fns
                if f.lower().endswith(".psd")), "")
    return _set_stage(state, "s1", "PASS" if rc2 == 0 else "WARN",
                      out={"layered_dir": out, "psd": psd}, gate=gate)


# ===========================================================================
# S2 绑骨（StretchyStudio rig-psd.cjs）
# ===========================================================================
def node_s2_rig(state: PipelineState) -> dict:
    out = _stage_dir(state, "s2", "rig")
    psd = _resolve(state.get("s2_psd") or "")
    if not psd:
        layered = (state.get("stage_outputs") or {}).get("s1", {}).get("out", {}).get("layered_dir", "")
        if layered and os.path.isdir(layered):
            psd = next((os.path.join(dp, f) for dp, _, fns in os.walk(layered) for f in fns
                        if f.lower().endswith(".psd")), "")
    if not psd or not os.path.isfile(psd):
        return _set_stage(state, "s2", "SKIP", reason=f"分层 PSD 不存在（psd={psd}）")
    script = os.path.join(TOOLS, "rig-automation", "rig-psd.cjs")
    if not os.path.isfile(script):
        return _set_stage(state, "s2", "STUB", reason=f"rig-psd.cjs 缺失: {script}")
    cmd = [NODE, script, psd, out]
    if state.get("s2_joints"):
        cmd.append(str(state["s2_joints"]))
    rc, so, se = _run_cmd(cmd, REPO, state, "s2", timeout=3600)
    if rc != 0:
        return _set_stage(state, "s2", "FAIL", reason=(se or so or "绑骨失败")[-300:])
    zips = _collect(out, "*_spine.zip") + _collect(state["out_dir"], "*_spine.zip")
    if zips:
        fixed = _fix_rig(state, "s2", zips[0])
        gate = _gate_zip(state, "s2", "validate-rig.py", fixed or zips[0])
        if gate["result"] == "FAIL":
            _append_lesson("s2_rig", state, gate.get("report", ""))
            if state.get("gate_strict"):
                return _set_stage(state, "s2", "FAIL", out={"rig_zip": zips[0]}, gate=gate,
                                  reason="rig 门禁 FAIL（严格模式）")
    else:
        gate = {"script": "validate-rig.py", "result": "SKIP", "report": "无 *_spine.zip"}
    return _set_stage(state, "s2", "PASS", out={"rig_zip": zips[0] if zips else ""}, gate=gate)


# ===========================================================================
# S3 动画（LLM 动画导演 stretchy-agent.cjs）
# ===========================================================================
def node_s3_animate(state: PipelineState) -> dict:
    out = _stage_dir(state, "s3", "anim")
    src = _resolve(state.get("s3_input") or "")
    if not src:
        s2 = (state.get("stage_outputs") or {}).get("s2", {}).get("out", {})
        s1 = (state.get("stage_outputs") or {}).get("s1", {}).get("out", {})
        src = s2.get("rig_zip") or s1.get("psd") or ""
    if not src or not os.path.isfile(src):
        return _set_stage(state, "s3", "SKIP", reason=f"输入工程/PSD 不存在（src={src}）")
    script = os.path.join(TOOLS, "rig-automation", "stretchy-agent.cjs")
    if not os.path.isfile(script):
        return _set_stage(state, "s3", "STUB", reason=f"stretchy-agent.cjs 缺失: {script}")
    task = state.get("s3_task") or ("为角色制作4个循环动画：idle(待机呼吸)、walk(走路)、attack(攻击)、"
                                    "hurt(受击)，外加4个表情截图(happy/sad/angry/neutral)。首尾关键帧一致保证循环。")
    cmd = [NODE, script, "--load", src, "--task", task, "--out", out,
           "--max-steps", str(state.get("s3_max_steps", 16))]
    # 经验库 -> 规避规则注入（反馈闭环）
    rules = _build_anim_rules()
    if rules:
        rpath = os.path.join(out, "rules.txt")
        with open(rpath, "w", encoding="utf-8") as f:
            f.write("\n".join(f"- 已知失败规避：{r}" for r in rules))
        cmd += ["--rules", rpath]
    env = {"AGENT_MODEL": state.get("model", "deepseek-v4-flash")}
    rc, so, se = _run_cmd(cmd, REPO, state, "s3", timeout=7200, env=env)
    if rc != 0:
        return _set_stage(state, "s3", "FAIL", reason=(se or so or "动画失败")[-300:])
    # 真实计费：usage.json
    cost = 0.0
    usage_f = os.path.join(out, "usage.json")
    if os.path.isfile(usage_f):
        try:
            u = json.load(open(usage_f, encoding="utf-8"))
            pt = int(u.get("prompt_tokens", 0)); ct = int(u.get("completion_tokens", 0))
            cost = round(pt * 0.0015 / 1000 + ct * 0.004 / 1000, 4)
        except Exception:
            cost = 0.0
    zips = _collect(out, "*_spine.zip") + _collect(state["out_dir"], "*_spine.zip")
    gate = {"script": "validate-anim.py", "result": "SKIP", "report": "无 *_spine.zip"}
    if zips:
        fixed = _fix_rig(state, "s3", zips[0])
        gate = _gate_zip(state, "s3", "validate-anim.py", fixed or zips[0])
        if gate["result"] == "FAIL":
            _append_lesson("s3_animate", state, gate.get("report", ""))
            if state.get("gate_strict"):
                return _set_stage(state, "s3", "FAIL", out={"anim_zip": zips[0]}, gate=gate,
                                  reason="anim 门禁 FAIL（严格模式）")
    gifs = _collect(out, "*.gif")
    return _set_stage(state, "s3", "PASS",
                      out={"anim_zip": zips[0] if zips else "", "gif": gifs[0] if gifs else "",
                           "usage": os.path.join(out, "usage.json") if os.path.isfile(usage_f) else "",
                           "cost": cost}, gate=gate)


# ===========================================================================
# S4 打包（package-assets.py 图集）
# ===========================================================================
def node_s4_package(state: PipelineState) -> dict:
    out = _stage_dir(state, "s4", "package")
    zipf = _resolve(state.get("s4_input") or "")
    if not zipf:
        s3 = (state.get("stage_outputs") or {}).get("s3", {}).get("out", {})
        s2 = (state.get("stage_outputs") or {}).get("s2", {}).get("out", {})
        zipf = s3.get("anim_zip") or s2.get("rig_zip") or ""
    if not zipf or not os.path.isfile(zipf):
        return _set_stage(state, "s4", "SKIP", reason=f"Spine ZIP 不存在（zip={zipf}）")
    cmd = [VENV_PY, os.path.join(TOOLS, "package-assets.py"), zipf, "--out", out]
    if state.get("atlas_size"):
        cmd += ["--atlas-size", str(state["atlas_size"])]
    rc, so, se = _run_cmd(cmd, REPO, state, "s4", timeout=600)
    if rc != 0:
        return _set_stage(state, "s4", "FAIL", reason=(se or so or "打包失败")[-300:])
    # 校验（validate-asset-package.py 若存在）
    gate = {"script": "validate-asset-package.py", "result": "PASS"}
    vp = os.path.join(TOOLS, "validate-asset-package.py")
    if os.path.isfile(vp):
        rc2, so2, se2 = _run_cmd([VENV_PY, vp, out], REPO, state, "s4", timeout=120)
        if rc2 != 0:
            gate = {"script": "validate-asset-package.py", "result": "WARN", "report": (so2 or se2 or "")[:2000]}
    return _set_stage(state, "s4", "PASS", out={"package_dir": out}, gate=gate)


# ===========================================================================
# S5 引擎（export-godot.py + 可选 godot 验证）
# ===========================================================================
def node_s5_engine(state: PipelineState) -> dict:
    out = _stage_dir(state, "s5", "godot")
    pkg = _resolve(state.get("s5_input") or "")
    if not pkg:
        pkg = (state.get("stage_outputs") or {}).get("s4", {}).get("out", {}).get("package_dir", "")
    if not pkg or not os.path.isdir(pkg):
        return _set_stage(state, "s5", "SKIP", reason=f"资产包目录不存在（pkg={pkg}）")
    cmd = [VENV_PY, os.path.join(TOOLS, "export-godot.py"), pkg, "--out", out]
    if state.get("godot_exe"):
        cmd += ["--godot", str(state["godot_exe"])]
    rc, so, se = _run_cmd(cmd, REPO, state, "s5", timeout=300)
    if rc != 0:
        return _set_stage(state, "s5", "FAIL", reason=(se or so or "引擎导出失败")[-300:])
    return _set_stage(state, "s5", "PASS", out={"godot_dir": out, "project": os.path.join(out, "project.godot")})


# ===========================================================================
# A6 归档反馈
# ===========================================================================
def node_a6_archive(state: PipelineState) -> dict:
    stages = {}
    for s, e in (state.get("stage_outputs") or {}).items():
        stages[s] = {"status": e.get("status"), "gate": e.get("gate", {}), "reason": e.get("reason", "")}
    overall = _overall_status(stages)
    manifest = {
        "schema": "asset.manifest.v2",
        "orchestrator": "langgraph-pipeline",
        "pipeline": "A1->S0->S1->S2->S3->S4->S5->A6",
        "type": state.get("atype"),
        "name": state.get("name"),
        "style": state.get("style"),
        "plan": state.get("plan", {}),
        "stages": stages,
        "artifacts": _artifact_paths(state),
        "meta": {
            "demand": state.get("demand", ""),
            "prompt": state.get("last_prompt", ""),
            "model": state.get("model") or "gpt-image-2",
            "attempts": state.get("attempts", 0),
            "duration_s": round(time.time() - state.get("_t0", time.time()), 1),
            "stage_tools": STAGE_TOOLS,
        },
        "qa": {"vision": state.get("gate_report", {})},
        "skill": state.get("skill_ctx", {}).get("skill"),
        "confirmed": False,
    }
    state["manifest"] = manifest
    mpath = _dump(state, "manifest.json", manifest)
    _audit(state, mpath)
    state["final_status"] = overall
    _log(state, f"A6 归档 -> {mpath} | final_status={overall}")
    return {"manifest": manifest, "final_status": overall}


def _overall_status(stages: dict) -> str:
    if not stages:
        return "SKIP"
    statuses = [s.get("status", "SKIP") for s in stages.values()]
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS" in statuses:
        return "PASS"
    if "WARN" in statuses:
        return "WARN"
    return "SKIP"


def _artifact_paths(state: PipelineState) -> list:
    paths = []
    for s in STAGE_ORDER:
        e = (state.get("stage_outputs") or {}).get(s, {})
        o = e.get("out", {})
        for k in ("image_path", "layered_dir", "rig_zip", "anim_zip", "package_dir", "godot_dir", "gif"):
            if o.get(k):
                paths.append(o[k])
    if state.get("image_path"):
        paths.append(state["image_path"])
    return paths


def _collect(base: str, pat: str) -> list:
    if not base or not os.path.isdir(base):
        return []
    return sorted(os.path.join(base, f) for f in os.listdir(base) if glob_match(f, pat))


def glob_match(name: str, pat: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(name, pat)


def _write_gate_file(state: PipelineState, stage: str, gate: dict) -> None:
    try:
        with open(os.path.join(state["out_dir"], f"gate_{stage}.txt"), "w", encoding="utf-8") as f:
            f.write(gate.get("report", "")[:2000])
    except Exception:
        pass


def _gate_zip(state: PipelineState, stage: str, script: str, zipf: str) -> dict:
    gate_py = os.path.join(TOOLS, script)
    rc, so, se = _run_cmd([VENV_PY, gate_py, zipf], REPO, state, stage, timeout=120,
                          env={"PYTHONIOENCODING": "utf-8"})
    report = (so or se or "")[:2000]
    last = report.strip().split("\n")[-1] if report.strip() else ""
    result = "FAIL" if "FAIL" in last else ("WARN" if ("WARN" in last or "warning" in last.lower()) else "PASS")
    gate = {"script": script, "result": result, "report": report}
    _write_gate_file(state, stage, gate)
    return gate


def _fix_rig(state: PipelineState, stage: str, zipf: str) -> str | None:
    """fix-rig.py 标准骨架修复；失败用原 zip。返回修复后 zip 路径或 None。"""
    fix = os.path.join(TOOLS, "fix-rig.py")
    fixed = zipf.replace("_spine.zip", "_fixed_spine.zip")
    rc, so, se = _run_cmd([VENV_PY, fix, zipf, "--out", fixed], REPO, state, stage, timeout=120,
                          env={"PYTHONIOENCODING": "utf-8"})
    if rc != 0 or not os.path.isfile(fixed):
        return None
    os.remove(zipf)
    os.rename(fixed, zipf)
    return zipf


def _append_lesson(stage: str, state: PipelineState, report: str) -> bool:
    """门禁 FAIL -> 沉淀经验（harness/memory/pipeline/lessons-learned.md），同签名去重。"""
    if not report:
        return False
    lines = [l for l in report.splitlines() if l.startswith("FAIL")]
    if not lines:
        return False
    sig = stage + "|" + "|".join(l.strip() for l in lines)
    entry = (f"## {time.strftime('%Y-%m-%d %H:%M')}  |  stage={stage}  |  job={state.get('name')}\n"
             + "\n".join(f"- {l.strip()}" for l in lines) + "\n\n")
    try:
        os.makedirs(os.path.dirname(LESSONS_FILE), exist_ok=True)
        body = open(LESSONS_FILE, encoding="utf-8").read() if os.path.isfile(LESSONS_FILE) else ""
        if sig in body:
            return False
        with open(LESSONS_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception:
        return False


def _build_anim_rules() -> list:
    rules = []
    try:
        if not os.path.isfile(LESSONS_FILE):
            return rules
        body = open(LESSONS_FILE, encoding="utf-8").read()
        for line in body.splitlines():
            if line.startswith("- ") and "FAIL" in line:
                r = line[2:].replace("FAIL - ", "").strip()
                if r and r not in rules:
                    rules.append(r)
    except Exception:
        pass
    return rules


def _audit(state: PipelineState, manifest_path: str) -> None:
    audit_dir = os.path.join(REPO, "audit")
    os.makedirs(audit_dir, exist_ok=True)
    with open(os.path.join(audit_dir, "langgraph-runs.md"), "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} | {state.get('name')} | "
                f"type={state.get('atype')} | stages={sorted((state.get('stage_outputs') or {}).keys())} | "
                f"final={state.get('final_status')} | manifest={manifest_path}\n")

