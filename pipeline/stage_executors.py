# -*- coding: utf-8 -*-
"""stage_executors.py — 各 stage 的共享实现层（节点内部实现，与 LangGraph 工作流解耦）

> 原则（用户明确）：**LangGraph workflow（编排）与每个节点的具体实现不冲突**。
> 本文件是"每个节点的具体实现"：纯函数，入参 cfg/job_dir，返回
> {status, out, gate, reason, log_tail}。可被 LangGraph 节点、workbench（tools/workbench/app.py）、
> 脚本等任意调用方复用——图只负责流程，实现只有一份，不重复不冲突。
>
> 覆盖路线：
>   A 骨骼路线：s0_gen_portrait / s1_decompose / s2_rig / s3_animate / s4_package / s5_engine
>   B 关键帧路线：kb1_keyframes（gen-frame-cycle）/ kb2_godot_anim（build-godot-anim-demo，含对齐）
>   F 3D 路线（后续补充）：f1_gen3d / f2_blender / f3_rig / f4_motion / f5_godot3d（契约+桩，如实 STUB）
"""
from __future__ import annotations

import fnmatch, glob, json, os, re, shutil, subprocess, sys, time
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")
VENV_PY = os.path.join(REPO, "runtime", ".venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PY):
    VENV_PY = sys.executable
SEE_THROUGH_DIR = os.path.join(REPO, "env", "runtime", "tools", "see-through")
SEE_THROUGH_PY = os.path.join(SEE_THROUGH_DIR, "venv", "Scripts", "python.exe")
if not os.path.exists(SEE_THROUGH_PY):
    SEE_THROUGH_PY = VENV_PY
NODE = "node.exe"
LESSONS_FILE = os.path.join(REPO, "harness", "memory", "pipeline", "lessons-learned.md")

GODOT_EXE_DEFAULT = r"C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64_console.exe"


def _resolve(p: str) -> str:
    if not p:
        return ""
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def _dir(job_dir: str, stage: str, default: str) -> str:
    d = os.path.join(job_dir, stage, default)
    os.makedirs(d, exist_ok=True)
    return d


def _collect(base: str, pat: str) -> list:
    if not base or not os.path.isdir(base):
        return []
    return sorted(os.path.join(base, f) for f in os.listdir(base) if fnmatch.fnmatch(f, pat))


def _run_cmd(cmd: list, cwd: str, log_tail: str, timeout: int = 7200,
             env: dict | None = None, dry_run: bool = False) -> tuple[int, str, str, str]:
    """执行命令；dry_run 只打印不执行。返回 (rc, stdout, stderr, log_tail)。"""
    log_tail += "$ " + " ".join(str(x) for x in cmd) + "\n"
    if dry_run:
        print(f"[executor] DRY-RUN: {' '.join(str(x) for x in cmd)}")
        return 0, "dry-run", "", log_tail
    _env = dict(os.environ)
    if env:
        _env.update(env)
    try:
        r = subprocess.run(cmd, cwd=cwd, timeout=timeout, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=_env)
        log_tail += (r.stdout or "") + "\n" + (r.stderr or "")
        return r.returncode, r.stdout or "", r.stderr or "", log_tail[-12000:]
    except subprocess.TimeoutExpired:
        log_tail += "TIMEOUT\n"
        return -1, "", "timeout", log_tail
    except Exception as e:
        log_tail += f"EXC {type(e).__name__}: {e}\n"
        return -1, "", str(e), log_tail


def _ok(status: str = "PASS", out: dict | None = None, gate: dict | None = None,
        reason: str = "", log_tail: str = "") -> dict:
    return {"status": status, "out": out or {}, "gate": gate or {}, "reason": reason, "log_tail": log_tail}


# ===========================================================================
# A 骨骼路线（S0-S5）
# ===========================================================================
def exec_s0_gen_portrait(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """S0 人物卡驱动生图：gen-portrait.py（persona -> 立绘/表情/小人）。"""
    out = _dir(job_dir, "s0", "portrait")
    persona = _resolve(cfg.get("persona", ""))
    if not persona or not os.path.isfile(persona):
        return _ok("FAIL", reason=f"persona.json 不存在: {persona}")
    cmd = [VENV_PY, os.path.join(TOOLS, "gen-portrait.py"), persona, "--out", out,
           "--scene", cfg.get("scene", "splash")]
    for k, flag in (("model", "--model"), ("backend", "--backend")):
        if cfg.get(k):
            cmd += [flag, str(cfg[k])]
    if cfg.get("refs"):
        cmd += ["--ref", _resolve(cfg["refs"][0])]
    if cfg.get("style_ref"):
        cmd += ["--style-ref", str(cfg["style_ref"])]
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=1800, dry_run=dry_run)
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "生图失败")[-300:], log_tail=log)
    imgs = sorted(os.path.join(dp, f) for dp, _, fns in os.walk(out) for f in fns
                  if f.lower().endswith((".png", ".jpg")))
    return _ok("PASS", out={"image_path": imgs[0] if imgs else "", "images": imgs[:8]}, log_tail=log)


def exec_s1_decompose(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """S1 拆层：See-through blockswap -> 分层 PSD -> validate-layered 门禁（WARN 非致命）。"""
    out = _dir(job_dir, "s1", "layered")
    src = _resolve(cfg.get("s1_src") or cfg.get("image_path") or "")
    if not src or not os.path.isfile(src):
        return _ok("SKIP", reason=f"输入图片不存在（src={src}）")
    infer = os.path.join(SEE_THROUGH_DIR, "inference", "scripts", "inference_psd_blockswap.py")
    if not os.path.isfile(infer):
        return _ok("STUB", reason=f"See-through 未安装: {infer}（env/README.md §4.2）")
    cmd = [SEE_THROUGH_PY, infer, "--srcp", src, "--save_dir", out]
    for k, flag in (("resolution", "--resolution"), ("resolution_depth", "--resolution_depth"),
                    ("num_inference_steps", "--num_inference_steps"), ("seed", "--seed")):
        if cfg.get(k):
            cmd += [flag, str(cfg[k])]
    if cfg.get("save_to_psd", True):
        cmd.append("--save_to_psd")
    if cfg.get("tblr_split"):
        cmd.append("--tblr_split")
    rc, so, se, log = _run_cmd(cmd, SEE_THROUGH_DIR, "", timeout=7200, dry_run=dry_run,
                               env={"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                                    "PYTHONIOENCODING": "utf-8"})
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "拆层失败")[-300:], log_tail=log)
    gate = {"script": "validate-layered.py", "result": "PASS"}
    rc2, so2, se2, log2 = _run_cmd([SEE_THROUGH_PY, os.path.join(TOOLS, "validate-layered.py"), "--dir", out],
                                   REPO, log, timeout=120, dry_run=dry_run,
                                   env={"PYTHONIOENCODING": "utf-8"})
    if rc2 != 0:
        gate = {"script": "validate-layered.py", "result": "WARN", "report": (so2 or se2 or "")[:2000]}
    psd = next((os.path.join(dp, f) for dp, _, fns in os.walk(out) for f in fns
                if f.lower().endswith(".psd")), "")
    return _ok("PASS" if rc2 == 0 else "WARN", out={"layered_dir": out, "psd": psd},
               gate=gate, log_tail=log2)


def exec_s2_rig(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """S2 绑骨：StretchyStudio rig-psd.cjs -> fix-rig -> validate-rig 门禁。"""
    out = _dir(job_dir, "s2", "rig")
    psd = _resolve(cfg.get("s2_psd") or "")
    if not psd:
        layered = (cfg.get("stage_outputs") or {}).get("s1", {}).get("out", {}).get("layered_dir", "")
        if layered and os.path.isdir(layered):
            psd = next((os.path.join(dp, f) for dp, _, fns in os.walk(layered) for f in fns
                        if f.lower().endswith(".psd")), "")
    if not psd or not os.path.isfile(psd):
        return _ok("SKIP", reason=f"分层 PSD 不存在（psd={psd}）")
    script = os.path.join(TOOLS, "rig-automation", "rig-psd.cjs")
    if not os.path.isfile(script):
        return _ok("STUB", reason=f"rig-psd.cjs 缺失: {script}")
    cmd = [NODE, script, psd, out]
    if cfg.get("s2_joints"):
        cmd.append(str(cfg["s2_joints"]))
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=3600, dry_run=dry_run)
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "绑骨失败")[-300:], log_tail=log)
    zips = _collect(out, "*_spine.zip") + _collect(job_dir, "*_spine.zip")
    gate = {"script": "validate-rig.py", "result": "SKIP", "report": "无 *_spine.zip"}
    if zips:
        fixed = _fix_rig(zips[0], job_dir, log, dry_run)
        gate = _gate_zip("validate-rig.py", fixed or zips[0], job_dir, log, dry_run)
    return _ok("PASS", out={"rig_zip": zips[0] if zips else ""}, gate=gate, log_tail=log)


def exec_s3_animate(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """S3 动画：LLM 动画导演 stretchy-agent.cjs -> fix-rig -> validate-anim 门禁 + usage 成本。"""
    out = _dir(job_dir, "s3", "anim")
    src = _resolve(cfg.get("s3_input") or "")
    if not src:
        s2 = (cfg.get("stage_outputs") or {}).get("s2", {}).get("out", {})
        s1 = (cfg.get("stage_outputs") or {}).get("s1", {}).get("out", {})
        src = s2.get("rig_zip") or s1.get("psd") or ""
    if not src or not os.path.isfile(src):
        return _ok("SKIP", reason=f"输入工程/PSD 不存在（src={src}）")
    script = os.path.join(TOOLS, "rig-automation", "stretchy-agent.cjs")
    if not os.path.isfile(script):
        return _ok("STUB", reason=f"stretchy-agent.cjs 缺失: {script}")
    task = cfg.get("s3_task") or ("为角色制作4个循环动画：idle(待机呼吸)、walk(走路)、attack(攻击)、"
                                  "hurt(受击)，外加4个表情截图(happy/sad/angry/neutral)。首尾关键帧一致保证循环。")
    cmd = [NODE, script, "--load", src, "--task", task, "--out", out,
           "--max-steps", str(cfg.get("s3_max_steps", 16))]
    rules = _build_anim_rules()
    if rules:
        rpath = os.path.join(out, "rules.txt")
        with open(rpath, "w", encoding="utf-8") as f:
            f.write("\n".join(f"- 已知失败规避：{r}" for r in rules))
        cmd += ["--rules", rpath]
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=7200, dry_run=dry_run,
                               env={"AGENT_MODEL": cfg.get("model", "deepseek-v4-flash")})
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "动画失败")[-300:], log_tail=log)
    cost = 0.0
    usage_f = os.path.join(out, "usage.json")
    if os.path.isfile(usage_f):
        try:
            u = json.load(open(usage_f, encoding="utf-8"))
            pt = int(u.get("prompt_tokens", 0)); ct = int(u.get("completion_tokens", 0))
            cost = round(pt * 0.0015 / 1000 + ct * 0.004 / 1000, 4)
        except Exception:
            cost = 0.0
    zips = _collect(out, "*_spine.zip") + _collect(job_dir, "*_spine.zip")
    gate = {"script": "validate-anim.py", "result": "SKIP", "report": "无 *_spine.zip"}
    if zips:
        fixed = _fix_rig(zips[0], job_dir, log, dry_run)
        gate = _gate_zip("validate-anim.py", fixed or zips[0], job_dir, log, dry_run)
    gifs = _collect(out, "*.gif")
    return _ok("PASS", out={"anim_zip": zips[0] if zips else "", "gif": gifs[0] if gifs else "",
                            "usage": usage_f if os.path.isfile(usage_f) else "", "cost": cost},
               gate=gate, log_tail=log)


def exec_s4_package(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """S4 打包：package-assets.py -> atlas 图集 + manifest。"""
    out = _dir(job_dir, "s4", "package")
    zipf = _resolve(cfg.get("s4_input") or "")
    if not zipf:
        s3 = (cfg.get("stage_outputs") or {}).get("s3", {}).get("out", {})
        s2 = (cfg.get("stage_outputs") or {}).get("s2", {}).get("out", {})
        zipf = s3.get("anim_zip") or s2.get("rig_zip") or ""
    if not zipf or not os.path.isfile(zipf):
        return _ok("SKIP", reason=f"Spine ZIP 不存在（zip={zipf}）")
    cmd = [VENV_PY, os.path.join(TOOLS, "package-assets.py"), zipf, "--out", out]
    if cfg.get("atlas_size"):
        cmd += ["--atlas-size", str(cfg["atlas_size"])]
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=600, dry_run=dry_run)
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "打包失败")[-300:], log_tail=log)
    gate = {"script": "validate-asset-package.py", "result": "PASS"}
    vp = os.path.join(TOOLS, "validate-asset-package.py")
    if os.path.isfile(vp):
        rc2, so2, se2, log2 = _run_cmd([VENV_PY, vp, out], REPO, log, timeout=120, dry_run=dry_run)
        if rc2 != 0:
            gate = {"script": "validate-asset-package.py", "result": "WARN",
                    "report": (so2 or se2 or "")[:2000]}
        log = log2
    return _ok("PASS", out={"package_dir": out}, gate=gate, log_tail=log)


def exec_s5_engine(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """S5 引擎：export-godot.py -> Godot 可玩工程（SpinePlayer）。"""
    out = _dir(job_dir, "s5", "godot")
    pkg = _resolve(cfg.get("s5_input") or "")
    if not pkg:
        pkg = (cfg.get("stage_outputs") or {}).get("s4", {}).get("out", {}).get("package_dir", "")
    if not pkg or not os.path.isdir(pkg):
        return _ok("SKIP", reason=f"资产包目录不存在（pkg={pkg}）")
    cmd = [VENV_PY, os.path.join(TOOLS, "export-godot.py"), pkg, "--out", out]
    if cfg.get("godot_exe"):
        cmd += ["--godot", str(cfg["godot_exe"])]
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=300, dry_run=dry_run)
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "引擎导出失败")[-300:], log_tail=log)
    return _ok("PASS", out={"godot_dir": out, "project": os.path.join(out, "project.godot")}, log_tail=log)


# ===========================================================================
# B 关键帧路线（帧动画）
# ===========================================================================
def exec_kb1_keyframes(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """B1 关键帧生成：gen-frame-cycle.py（单锚点 hero + 固定风格块 + 帧动作描述）。"""
    out = _dir(job_dir, "kb", "frames")
    hero = _resolve(cfg.get("kb_hero") or cfg.get("image_path") or "")
    style = cfg.get("kb_style", "pixel")
    if not hero or not os.path.isfile(hero):
        return _ok("SKIP", reason=f"hero/matte 锚点图不存在（hero={hero}）")
    script = os.path.join(TOOLS, "gen-frame-cycle.py")
    if not os.path.isfile(script):
        return _ok("STUB", reason=f"gen-frame-cycle.py 缺失: {script}")
    cmd = [VENV_PY, script, "--style", style, "--hero", hero, "--out", out]
    if cfg.get("kb_only"):
        cmd += ["--only", str(cfg["kb_only"])]
    if cfg.get("kb_force"):
        cmd.append("--force")
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=3600, dry_run=dry_run)
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "关键帧生成失败")[-300:], log_tail=log)
    frames = _collect(out, "*.png")
    return _ok("PASS", out={"frames_dir": out, "frames": frames,
                            "meta": os.path.join(out, "meta.json")}, log_tail=log)


def exec_kb2_godot_anim(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """B2 帧动画 Godot 工程：build-godot-anim-demo.py（核心身体对齐 + AnimatedSprite2D + 状态机）。"""
    out = _dir(job_dir, "kb", "godot_anim")
    frames = _resolve(cfg.get("kb_frames") or "")
    if not frames:
        frames = (cfg.get("stage_outputs") or {}).get("kb1", {}).get("out", {}).get("frames_dir", "")
    if not frames or not os.path.isdir(frames):
        return _ok("SKIP", reason=f"关键帧目录不存在（frames={frames}）")
    cmd = [VENV_PY, os.path.join(TOOLS, "build-godot-anim-demo.py"), "--frames", frames,
           "--out", out, "--name", cfg.get("name", "Ailin Anim Demo")]
    if cfg.get("target_h"):
        cmd += ["--target-h", str(cfg["target_h"])]
    if cfg.get("fps"):
        cmd += ["--fps", str(cfg["fps"])]
    rc, so, se, log = _run_cmd(cmd, REPO, "", timeout=300, dry_run=dry_run)
    if rc != 0:
        return _ok("FAIL", reason=(se or so or "Godot 动画工程生成失败")[-300:], log_tail=log)
    return _ok("PASS", out={"godot_dir": out, "project": os.path.join(out, "project.godot")}, log_tail=log)


# ===========================================================================
# F 3D 路线（后续补充；契约 + 桩，如实 STUB）
# ===========================================================================
_F3D_TOOLS = {
    "f1": "3D 生成：Tripo API / 混元3D / Meshy（text/image -> mesh+贴图）",
    "f2": "Blender 修正：减面/UV/法线/材质（dcc-mcp-creator 或 Blender Python API）",
    "f3": "绑骨：Mixamo / RigNet / Blender Rigify（自动骨骼+蒙皮）",
    "f4": "动作：动作库 / 手K / SCAIL2 动作迁移（spec/生图.md §7）",
    "f5": "Godot 3D 导入：glTF -> 场景 + 动画播放 demo（engine-neutral 资产）",
}


def exec_f1_gen3d(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    """F1 3D 生成（契约已定义，实现待补充）。"""
    return _ok("STUB", out={"tool": _F3D_TOOLS["f1"]},
               reason="F1 3D 生成：契约已定义（text/image -> glTF mesh），实现待 L4 补充（Tripo/Meshy key）")


def exec_f2_blender(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    return _ok("STUB", out={"tool": _F3D_TOOLS["f2"]}, reason="F2 Blender 修正：待补充（dcc-mcp）")


def exec_f3_rig(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    return _ok("STUB", out={"tool": _F3D_TOOLS["f3"]}, reason="F3 绑骨：待补充（Mixamo/RigNet）")


def exec_f4_motion(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    return _ok("STUB", out={"tool": _F3D_TOOLS["f4"]}, reason="F4 动作：待补充（SCAIL2/动作库）")


def exec_f5_godot3d(cfg: dict, job_dir: str, dry_run: bool = False) -> dict:
    return _ok("STUB", out={"tool": _F3D_TOOLS["f5"]}, reason="F5 Godot 3D 导入：待补充（glTF demo）")


# ===========================================================================
# 共享工具（门禁 / 经验库 / 反馈）
# ===========================================================================
def _fix_rig(zipf: str, job_dir: str, log: str, dry_run: bool) -> str | None:
    fix = os.path.join(TOOLS, "fix-rig.py")
    fixed = zipf.replace("_spine.zip", "_fixed_spine.zip")
    rc, so, se, log = _run_cmd([VENV_PY, fix, zipf, "--out", fixed], REPO, log,
                               timeout=120, dry_run=dry_run, env={"PYTHONIOENCODING": "utf-8"})
    if rc != 0 or not os.path.isfile(fixed):
        return None
    os.remove(zipf)
    os.rename(fixed, zipf)
    return zipf


def _gate_zip(script: str, zipf: str, job_dir: str, log: str, dry_run: bool) -> dict:
    rc, so, se, log = _run_cmd([VENV_PY, os.path.join(TOOLS, script), zipf], REPO, log,
                               timeout=120, dry_run=dry_run, env={"PYTHONIOENCODING": "utf-8"})
    report = (so or se or "")[:2000]
    last = report.strip().split("\n")[-1] if report.strip() else ""
    result = "FAIL" if "FAIL" in last else ("WARN" if ("WARN" in last or "warning" in last.lower()) else "PASS")
    return {"script": script, "result": result, "report": report}


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


EXECUTORS = {
    "s0_gen_portrait": exec_s0_gen_portrait,
    "s1_decompose": exec_s1_decompose,
    "s2_rig": exec_s2_rig,
    "s3_animate": exec_s3_animate,
    "s4_package": exec_s4_package,
    "s5_engine": exec_s5_engine,
    "kb1_keyframes": exec_kb1_keyframes,
    "kb2_godot_anim": exec_kb2_godot_anim,
    "f1_gen3d": exec_f1_gen3d,
    "f2_blender": exec_f2_blender,
    "f3_rig": exec_f3_rig,
    "f4_motion": exec_f4_motion,
    "f5_godot3d": exec_f5_godot3d,
}
