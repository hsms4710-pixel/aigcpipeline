# -*- coding: utf-8 -*-
"""角色 AIGC 工业级流水线 orchestrator（FastAPI）
阶段：S0 生图 → S1 拆层 → S2 绑骨 → S3 动画 → S4 打包 → S5 引擎
每个 job：配置(契约) → 执行(调用底层工具/agent) → 产物 → 门禁 → 日志/成本记录
前端：多 Tab 工作台（web/），完全覆盖本后端能力边界。
"""
import os, sys, json, uuid, sqlite3, threading, subprocess, datetime, shutil, re, glob

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 仓库根
HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.join(repo, "pipeline")
ARTIFACTS_DIR = os.path.join(PIPELINE_DIR, "artifacts")
JOBS_DB = os.path.join(HERE, "workbench.db")
ENV_FILE = os.path.join(repo, "env", ".env")
TOOLS = os.path.join(repo, "tools")
VENV_PY = r"C:\Users\26046\Desktop\inerview\runtime\.venv\Scripts\python.exe"
SEE_THROUGH_PY = os.path.join(repo, "env", "runtime", "tools", "see-through", "venv", "Scripts", "python.exe")
NODE = "node.exe"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="角色 AIGC 工业流水线")

def now(): return datetime.datetime.now().isoformat(timespec="seconds")

def db():
    c = sqlite3.connect(JOBS_DB)
    cols = [r[1] for r in c.execute("PRAGMA table_info(jobs)").fetchall()]
    want = {"id", "stage", "config", "status", "stage_detail", "log", "artifacts", "error", "created", "started", "finished", "duration_ms", "cost"}
    if cols and not want.issubset(set(cols)):
        c.execute("DROP TABLE jobs"); c.commit()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, stage TEXT, config TEXT, status TEXT,
        stage_detail TEXT, log TEXT, artifacts TEXT, error TEXT,
        created TEXT, started TEXT, finished TEXT, duration_ms INTEGER, cost REAL)""")
    return c

# ── 配置（env/.env，密钥掩码）──────────────────────────────────────────────
def read_env():
    env = {}
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
    return env

def write_env(env):
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        for k in sorted(env):
            if k and env[k] is not None:
                f.write(f"{k}={env[k]}\n")

SECRET_KEYS = {"GPT_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "TRIPO_API_KEY", "VOLC_API_KEY", "GPT_BASE_URL"}
def mask(v):
    if not v: return ""
    return v[:4] + "****" + v[-4:] if len(v) > 10 else "****"

# ── 阶段注册表（前端据此渲染配置表单，保证前端完全覆盖后端能力）──────────
def _f(key, label, type="text", default="", options=None, required=False, help=""):
    return {"key": key, "label": label, "type": type, "default": default, "options": options or [], "required": required, "help": help}

STAGES = {
    "s0_generate": {
        "name": "生图 S0", "icon": "🎨", "desc": "人设卡/参考图 → 立绘/表情/小人（GPT-Image-2 / Gemini / FAL / SD）",
        "next": ["s1_decompose"],
        "config": [
            _f("persona", "人设卡 persona.json", "file", "", required=True, help="上传 persona.json（可用 设置→LLM填充 生成）"),
            _f("scene", "资产意图", "select", "splash", ["splash", "chibi", "pixel"], True, "splash=立绘 chibi=Q版小人 pixel=像素"),
            _f("view", "视图", "select", "full", ["full", "bust", "turnaround", "idle", "walk", "attack", "hurt", "side", "back"]),
            _f("exp", "表情", "select", "neutral", ["neutral", "happy", "sad", "angry"]),
            _f("backend", "生图后端", "select", "openai", ["openai", "gemini", "fal"]),
            _f("model", "模型", "text", "gpt-image-2", help="openai: gpt-image-2 / gemini: gemini-2.0-flash / fal: 按账号"),
            _f("size", "尺寸", "select", "1024x1024", ["1024x1024", "1024x1536", "1536x1024"]),
            _f("ref", "参考图路径", "text", "", help="角色锚点参考图（可留空）"),
            _f("style_ref", "风格参考(逗号分隔)", "text", "", help="风格锚点图，多图逗号分隔"),
            _f("force", "强制重生成", "bool", False),
            _f("dry_run", "仅预览提示词(不调API)", "bool", False, help="调试用：打印将执行的命令，不实际调用生图"),
        ],
        "outputs": "full.png / bust.png / exp_*.png / chibi_*",
    },
    "s1_decompose": {
        "name": "拆层 S1", "icon": "🧩", "desc": "立绘 → Live2D 规范分层 PSD（See-through blockswap，GPU）",
        "prev": ["s0_generate"], "next": ["s2_rig"],
        "config": [
            _f("src", "输入图片", "text", "", required=True, help="立绘 PNG 路径（可用 S0 产物）"),
            _f("save_dir", "输出目录", "text", "", help="留空自动生成 pipeline/artifacts/<job>/layered"),
            _f("resolution", "分辨率", "int", "1280"),
            _f("resolution_depth", "深度分辨率", "int", "768"),
            _f("num_inference_steps", "推理步数", "int", "30"),
            _f("save_to_psd", "导出 PSD", "bool", True),
            _f("tblr_split", "四向拆解", "bool", False),
            _f("seed", "随机种子", "int", "42"),
        ],
        "outputs": "layered/*.png + *.psd + depth",
    },
    "s2_rig": {
        "name": "绑骨 S2", "icon": "🦴", "desc": "分层 PSD → DWPose 自动绑骨 → .stretch + Spine（StretchyStudio）",
        "prev": ["s1_decompose"], "next": ["s3_animate"],
        "config": [
            _f("psd", "分层 PSD", "text", "", required=True, help="S1 产物 PSD 路径"),
            _f("out_dir", "输出目录", "text", "", help="留空自动生成 pipeline/artifacts/<job>"),
            _f("joints", "关节微调", "text", "", help="格式 leftElbow:+14,+6;head:0,-10（可空）"),
        ],
        "outputs": "*.stretch + *_spine.zip + 截图",
        "requires_servers": ["5173", "5174"],
    },
    "s3_animate": {
        "name": "动画 S3", "icon": "🎬", "desc": "LLM 导演生成骨骼动画（idle/walk/attack/hurt + 表情）→ Spine 导出",
        "prev": ["s2_rig"], "next": ["s4_package"],
        "config": [
            _f("psd_or_stretch", "输入工程/PSD", "text", "", required=True, help="S2 产物 .stretch 或 PSD"),
            _f("task", "动画任务描述", "textarea", "为角色制作4个循环动画：idle(待机呼吸)、walk(走路)、attack(攻击)、hurt(受击)，外加4个表情截图(happy/sad/angry/neutral)。首尾关键帧一致保证循环。"),
            _f("max_steps", "LLM 最大步数", "int", "16"),
            _f("model", "LLM 模型", "text", "deepseek-v4-flash", help="deepseek-v4-flash / deepseek-v4-pro"),
            _f("out_dir", "输出目录", "text", ""),
        ],
        "outputs": "*.stretch + *_spine.zip + GIF + 表情截图",
        "requires_servers": ["5173", "5174"],
    },
    "s4_package": {
        "name": "打包 S4", "icon": "📦", "desc": "Spine 资产 → atlas 图集 + 资产清单（manifest）+ 校验",
        "prev": ["s3_animate"], "next": ["s5_engine"],
        "config": [
            _f("input_zip", "Spine ZIP 输入", "text", "", required=True, help="S2/S3 产物 *_spine.zip"),
            _f("out_dir", "输出目录", "text", ""),
            _f("atlas_size", "图集尺寸", "int", "2048"),
        ],
        "outputs": "atlas.png + .atlas + manifest.json",
    },
    "s5_engine": {
        "name": "引擎 S5", "icon": "🎮", "desc": "资产包 → Godot 可玩工程（立绘+骨骼动画+表情）",
        "prev": ["s4_package"],
        "config": [
            _f("package_dir", "资产包目录", "text", "", required=True, help="S4 产物目录（含 manifest.json）"),
            _f("out_dir", "Godot 工程输出目录", "text", ""),
            _f("godot_exe", "Godot 可执行文件", "text", r"C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64.exe"),
        ],
        "outputs": "Godot 工程（project.godot + 场景）",
    },
}
STAGE_ORDER = ["s0_generate", "s1_decompose", "s2_rig", "s3_animate", "s4_package", "s5_engine"]

def stage_schema(stage_id):
    st = STAGES.get(stage_id)
    if not st: raise HTTPException(404, "阶段不存在")
    return {"id": stage_id, **{k: st[k] for k in ("name", "icon", "desc", "prev", "next", "outputs", "requires_servers") if k in st}, "config": st["config"]}

# ── Job 管理 ───────────────────────────────────────────────────────────────
class CreateJobReq(BaseModel):
    stage: str
    config: dict = {}

def _artifact_rel(path):
    try: return os.path.relpath(path, repo).replace("\\", "/")
    except Exception: return path

def _collect_artifacts(job_dir):
    arts = []
    if not os.path.isdir(job_dir): return arts
    for root, dirs, files in os.walk(job_dir):
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, job_dir).replace("\\", "/")
            ext = os.path.splitext(f)[1].lower()
            arts.append({"path": rel, "abs": p, "ext": ext, "size": os.path.getsize(p),
                         "url": f"/api/artifacts/file/{os.path.basename(job_dir)}/{rel}"})
    return arts

def create_job(stage, config):
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job_dir = os.path.join(ARTIFACTS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    c = db()
    c.execute("INSERT INTO jobs (id, stage, config, status, stage_detail, log, artifacts, error, created) VALUES (?,?,?,?,?,?,?,?,?)",
              (job_id, stage, json.dumps(config, ensure_ascii=False), "created", "待运行", "", "[]", "", now()))
    c.commit(); c.close()
    return job_id, job_dir

def update_job(job_id, **kw):
    c = db()
    sets = ", ".join(f"{k}=?" for k in kw)
    c.execute(f"UPDATE jobs SET {sets} WHERE id=?", (*kw.values(), job_id))
    c.commit(); c.close()

def get_job(job_id):
    c = db()
    row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    c.close()
    if not row: return None
    cols = ["id", "stage", "config", "status", "stage_detail", "log", "artifacts", "error", "created", "started", "finished", "duration_ms", "cost"]
    d = dict(zip(cols, row))
    d["config"] = json.loads(d["config"] or "{}")
    d["artifacts"] = json.loads(d["artifacts"] or "[]")
    return d

# ── 各阶段执行器 ───────────────────────────────────────────────────────────
def _run_cmd(cmd, cwd, log_path, timeout=7200, env=None):
    _env = dict(os.environ)
    if env: _env.update(env)
    logf = open(log_path, "a", encoding="utf-8")
    logf.write("$ " + " ".join(str(x) for x in cmd) + "\n"); logf.flush()
    try:
        r = subprocess.run(cmd, cwd=cwd, timeout=timeout, capture_output=True, text=True, encoding="utf-8", errors="replace", env=_env)
        logf.write((r.stdout or "") + "\n" + (r.stderr or "")); logf.flush()
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        logf.write("TIMEOUT\n"); logf.flush()
        return -1, "", "timeout"
    finally:
        logf.close()

def _write_log(job_id, text):
    c = db(); c.execute("UPDATE jobs SET log=? WHERE id=?", (text, job_id)); c.commit(); c.close()

def estimate_cost(stage, duration_ms, cfg):
    """粗粒度成本估算（元人民币）。真实计费后续接入。"""
    try:
        h = (duration_ms or 0) / 3600000.0
        if stage == "s0_generate":
            return 0.0 if str(cfg.get("dry_run", "")).lower() in ("true", "on") else 0.05  # 每张生图约¥0.05
        if stage == "s1_decompose":
            return round(h * 0.5, 4)  # 本地GPU约¥0.5/小时
        if stage == "s3_animate":
            return round(0.05 + h * 0.3, 4)  # LLM token + 少量算力
        return 0.0
    except Exception:
        return 0.0

def run_stage(job_id, stage, config):
    job_dir = os.path.join(ARTIFACTS_DIR, job_id)
    log_path = os.path.join(job_dir, "run.log")
    started = now()
    update_job(job_id, status="running", started=started, stage_detail="启动", log="")
    t0 = datetime.datetime.now()
    try:
        if stage == "s0_generate":
            _exec_s0(job_id, job_dir, config, log_path)
        elif stage == "s1_decompose":
            _exec_s1(job_id, job_dir, config, log_path)
        elif stage == "s2_rig":
            _exec_s2(job_id, job_dir, config, log_path)
        elif stage == "s3_animate":
            _exec_s3(job_id, job_dir, config, log_path)
        elif stage == "s4_package":
            _exec_s4(job_id, job_dir, config, log_path)
        elif stage == "s5_engine":
            _exec_s5(job_id, job_dir, config, log_path)
        else:
            raise ValueError(f"未知阶段 {stage}")
        dur = int((datetime.datetime.now() - t0).total_seconds() * 1000)
        arts = _collect_artifacts(job_dir)
        cost = estimate_cost(stage, dur, config)
        update_job(job_id, status="done", stage_detail="完成", duration_ms=dur, cost=cost,
                   artifacts=json.dumps(arts, ensure_ascii=False),
                   log=_read_log(log_path), finished=now())
    except Exception as e:
        dur = int((datetime.datetime.now() - t0).total_seconds() * 1000)
        update_job(job_id, status="failed", stage_detail=f"失败: {str(e)[:200]}", duration_ms=dur,
                   error=str(e)[:1000], cost=estimate_cost(stage, dur, config),
                   log=_read_log(log_path), finished=now())

def _read_log(log_path):
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f: return f.read()[-8000:]
    except Exception: return ""

def _out_dir(job_dir, cfg, key="out_dir", default="out"):
    v = (cfg.get(key) or "").strip()
    if v:
        d = v if os.path.isabs(v) else os.path.join(repo, v)
        os.makedirs(d, exist_ok=True); return d
    d = os.path.join(job_dir, default); os.makedirs(d, exist_ok=True); return d

def _resolve_path(p):
    if not p: return ""
    return p if os.path.isabs(p) else os.path.join(repo, p)

# S0 生图
def _exec_s0(job_id, job_dir, cfg, log_path):
    persona = cfg.get("persona", "")
    scene = cfg.get("scene", "splash")
    if not persona or not os.path.isfile(persona) and not os.path.isfile(_resolve_path(persona)):
        raise ValueError("persona.json 不存在")
    p = _resolve_path(persona)
    out = _out_dir(job_dir, cfg, "out_dir", "portrait")
    cmd = [VENV_PY, os.path.join(TOOLS, "gen-portrait.py"), p, "--out", out, "--scene", scene]
    for k, flag in [("model", "--model"), ("backend", "--backend")]:
        if cfg.get(k): cmd += [flag, str(cfg[k])]
    if cfg.get("ref"): cmd += ["--ref", _resolve_path(cfg["ref"])]
    if cfg.get("style_ref"):
        refs = [x.strip() for x in str(cfg["style_ref"]).split(",") if x.strip()]
        cmd += ["--style-ref", ",".join(refs)]
    if cfg.get("force") in (True, "true", "on"): cmd.append("--force")
    if cfg.get("dry_run") in (True, "true", "on"): cmd.append("--dry-run")
    open(os.path.join(job_dir, "cmd.txt"), "w", encoding="utf-8").write(" ".join(cmd))
    update_job(job_id, stage_detail="调用生图后端")
    rc, so, se = _run_cmd(cmd, repo, log_path)
    if rc != 0: raise RuntimeError((se or so or "生图失败")[-500:])

# S1 拆层
def _exec_s1(job_id, job_dir, cfg, log_path):
    src = _resolve_path(cfg.get("src", ""))
    if not os.path.isfile(src): raise ValueError("输入图片不存在")
    out = _out_dir(job_dir, cfg, "save_dir", "layered")
    cmd = [SEE_THROUGH_PY, os.path.join(repo, "env", "runtime", "tools", "see-through", "inference", "scripts", "inference_psd_blockswap.py"),
           "--srcp", src, "--save_dir", out]
    if cfg.get("resolution"): cmd += ["--resolution", str(cfg["resolution"])]
    if cfg.get("resolution_depth"): cmd += ["--resolution_depth", str(cfg["resolution_depth"])]
    if cfg.get("num_inference_steps"): cmd += ["--num_inference_steps", str(cfg["num_inference_steps"])]
    if cfg.get("save_to_psd", True) in (True, "true", "on"): cmd.append("--save_to_psd")
    if cfg.get("tblr_split", False) in (True, "true", "on"): cmd.append("--tblr_split")
    if cfg.get("seed"): cmd += ["--seed", str(cfg["seed"])]
    update_job(job_id, stage_detail="See-through 拆层（GPU，约20min）")
    rc, so, se = _run_cmd(cmd, os.path.join(repo, "env", "runtime", "tools", "see-through"), log_path, timeout=7200, env={"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"})
    if rc != 0: raise RuntimeError((se or so or "拆层失败")[-500:])
    # 门禁：层完整性
    val = os.path.join(TOOLS, "validate-layered.py")
    rc2, so2, se2 = _run_cmd([SEE_THROUGH_PY, val, "--dir", out], repo, log_path, timeout=120)
    if rc2 != 0:
        update_job(job_id, stage_detail="拆层完成，层校验告警")
        open(os.path.join(job_dir, "gate_layered.txt"), "w", encoding="utf-8").write((so2 or se2 or "")[:2000])

# S2 绑骨
def _exec_s2(job_id, job_dir, cfg, log_path):
    psd = _resolve_path(cfg.get("psd", ""))
    if not os.path.isfile(psd): raise ValueError("分层 PSD 不存在")
    out = _out_dir(job_dir, cfg, "out_dir", "rig")
    script = os.path.join(TOOLS, "rig-automation", "rig-psd.cjs")
    cmd = [NODE, script, psd, out]
    if cfg.get("joints"): cmd.append(str(cfg["joints"]))
    update_job(job_id, stage_detail="StretchyStudio 绑骨（需 5173/5174 服务）")
    rc, so, se = _run_cmd(cmd, repo, log_path, timeout=3600)
    if rc != 0: raise RuntimeError((se or so or "绑骨失败")[-500:])
    for f in glob.glob(os.path.join(out, "*_spine.zip")):
        shutil.copy(f, os.path.join(job_dir, os.path.basename(f)))

# S3 动画
def _exec_s3(job_id, job_dir, cfg, log_path):
    src = _resolve_path(cfg.get("psd_or_stretch", ""))
    if not os.path.isfile(src): raise ValueError("输入工程/PSD 不存在")
    out = _out_dir(job_dir, cfg, "out_dir", "anim")
    script = os.path.join(TOOLS, "rig-automation", "stretchy-agent.cjs")
    cmd = [NODE, script, "--load", src, "--task", str(cfg.get("task", "")), "--out", out, "--max-steps", str(cfg.get("max_steps", 16))]
    if cfg.get("model"): cmd += ["--model", str(cfg["model"])] if False else []
    env = dict(os.environ)
    if cfg.get("model"): env["AGENT_MODEL"] = str(cfg["model"])
    update_job(job_id, stage_detail="LLM 动画导演（deepseek）")
    logf = open(log_path, "a", encoding="utf-8")
    logf.write("$ " + " ".join(cmd) + "\n"); logf.flush()
    try:
        r = subprocess.run(cmd, cwd=repo, timeout=7200, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        logf.write((r.stdout or "") + "\n" + (r.stderr or "")); logf.flush()
        if r.returncode != 0: raise RuntimeError((r.stderr or r.stdout or "动画失败")[-500:])
    finally:
        logf.close()
    for f in glob.glob(os.path.join(out, "*_spine.zip")) + glob.glob(os.path.join(out, "*.gif")):
        shutil.copy(f, os.path.join(job_dir, os.path.basename(f)))

# S4 打包
def _exec_s4(job_id, job_dir, cfg, log_path):
    zipf = _resolve_path(cfg.get("input_zip", ""))
    if not os.path.isfile(zipf): raise ValueError("Spine ZIP 不存在")
    out = _out_dir(job_dir, cfg, "out_dir", "package")
    script = os.path.join(TOOLS, "package-assets.py")
    cmd = [VENV_PY, script, zipf, "--out", out]
    if cfg.get("atlas_size"): cmd += ["--atlas-size", str(cfg["atlas_size"])]
    update_job(job_id, stage_detail="图集打包 + 校验")
    rc, so, se = _run_cmd(cmd, repo, log_path, timeout=600)
    if rc != 0: raise RuntimeError((se or so or "打包失败")[-500:])

# S5 引擎
def _exec_s5(job_id, job_dir, cfg, log_path):
    pkg = _resolve_path(cfg.get("package_dir", ""))
    if not os.path.isdir(pkg): raise ValueError("资产包目录不存在")
    out = _out_dir(job_dir, cfg, "out_dir", "godot")
    script = os.path.join(TOOLS, "export-godot.py")
    cmd = [VENV_PY, script, pkg, "--out", out]
    if cfg.get("godot_exe"): cmd += ["--godot", str(cfg["godot_exe"])]
    update_job(job_id, stage_detail="生成 Godot 工程")
    rc, so, se = _run_cmd(cmd, repo, log_path, timeout=300)
    if rc != 0: raise RuntimeError((se or so or "引擎导出失败")[-500:])

# ── API ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    servers = {}
    for port in ("5173", "5174"):
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
            servers[port] = "up"
        except Exception:
            servers[port] = "down"
    return {"status": "ok", "servers": servers, "time": now()}

@app.get("/api/pipeline/stages")
def list_stages():
    return [stage_schema(s) for s in STAGE_ORDER]

@app.get("/api/pipeline/stages/{stage_id}")
def get_stage(stage_id: str):
    return stage_schema(stage_id)

@app.post("/api/pipeline/jobs")
def create_and_run(req: CreateJobReq):
    if req.stage not in STAGES: raise HTTPException(400, "阶段不存在")
    job_id, _ = create_job(req.stage, req.config)
    threading.Thread(target=run_stage, args=(job_id, req.stage, req.config), daemon=True).start()
    return {"job_id": job_id, "stage": req.stage}

@app.post("/api/pipeline/jobs/{job_id}/run")
def rerun_job(job_id: str):
    job = get_job(job_id)
    if not job: raise HTTPException(404, "job 不存在")
    shutil.rmtree(os.path.join(ARTIFACTS_DIR, job_id), ignore_errors=True)
    os.makedirs(os.path.join(ARTIFACTS_DIR, job_id), exist_ok=True)
    threading.Thread(target=run_stage, args=(job_id, job["stage"], job["config"]), daemon=True).start()
    return {"ok": True}

@app.get("/api/pipeline/jobs")
def list_jobs(stage: str = None, limit: int = 100):
    c = db()
    if stage:
        rows = c.execute("SELECT * FROM jobs WHERE stage=? ORDER BY created DESC LIMIT ?", (stage, limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    cols = ["id", "stage", "config", "status", "stage_detail", "log", "artifacts", "error", "created", "started", "finished", "duration_ms", "cost"]
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        d["config"] = json.loads(d["config"] or "{}")
        d["artifact_count"] = len(json.loads(d["artifacts"] or "[]"))
        d.pop("log", None)
        out.append(d)
    return out

@app.get("/api/pipeline/jobs/{job_id}")
def job_detail(job_id: str):
    j = get_job(job_id)
    if not j: raise HTTPException(404, "job 不存在")
    return j

@app.get("/api/artifacts")
def list_artifacts():
    out = []
    for jid in sorted(os.listdir(ARTIFACTS_DIR), reverse=True):
        jdir = os.path.join(ARTIFACTS_DIR, jid)
        if not os.path.isdir(jdir): continue
        arts = _collect_artifacts(jdir)
        out.append({"job_id": jid, "artifacts": arts[:200]})
    return out

@app.get("/api/artifacts/file/{job_id}/{path:path}")
def artifact_file(job_id: str, path: str):
    base = os.path.abspath(os.path.join(ARTIFACTS_DIR, job_id))
    fp = os.path.abspath(os.path.join(base, path))
    if not fp.startswith(base) or not os.path.isfile(fp):
        raise HTTPException(404, "文件不存在")
    return FileResponse(fp)

@app.get("/api/config")
def get_config():
    env = read_env()
    return {k: (mask(v) if k in SECRET_KEYS else v) for k, v in env.items()}

class ConfigReq(BaseModel):
    key: str
    value: str = ""

@app.post("/api/config")
def set_config(req: ConfigReq):
    env = read_env()
    env[req.key] = req.value
    write_env(env)
    return {"ok": True}

@app.get("/api/pipeline/status")
def pipeline_status():
    """前端 Dashboard：各阶段最近 job + 产物 + 后端健康"""
    c = db()
    rows = c.execute("SELECT stage, status, COUNT(*) c FROM jobs GROUP BY stage, status").fetchall()
    c.close()
    by_stage = {}
    for stage, status, cnt in rows:
        by_stage.setdefault(stage, {})[status] = cnt
    return {"stages": STAGE_ORDER, "by_stage": by_stage, "stage_meta": {s: {"name": STAGES[s]["name"], "icon": STAGES[s]["icon"]} for s in STAGE_ORDER}}

@app.get("/")
def index():
    web = os.path.join(HERE, "web", "dist")
    if os.path.exists(os.path.join(web, "index.html")):
        return FileResponse(os.path.join(web, "index.html"))
    return JSONResponse({"msg": "前端未构建，请在 web/ 执行 npm run build"}, status_code=200)

# 静态资源（前端产物目录 /api 之外）
if os.path.isdir(os.path.join(HERE, "web", "dist")):
    app.mount("/assets", StaticFiles(directory=os.path.join(HERE, "web", "dist", "assets")), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
