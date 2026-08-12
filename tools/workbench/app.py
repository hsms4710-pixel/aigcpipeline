"""t5 工作台后端：FastAPI + SQLite job 队列 + 云生图集成 + 无限画布前端托管"""
import os, sys, json, uuid, sqlite3, threading, subprocess, datetime, shutil

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 仓库根
sys.path.insert(0, repo)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="角色 AIGC 工作台")
CHAR_DIR = os.path.join(repo, "assets", "characters")
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workbench.db")
VENV_PY = r"C:\Users\26046\Desktop\inerview\runtime\.venv\Scripts\python.exe"
GEN_PORTRAIT = os.path.join(repo, "tools", "gen-portrait.py")
os.makedirs(CHAR_DIR, exist_ok=True)

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, char_id TEXT, scene TEXT, stage TEXT,
        status TEXT, message TEXT, created TEXT, updated TEXT)""")
    return c

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

class GenReq(BaseModel):
    scene: str = "pixel"

@app.get("/")
def index():
    web = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "dist")
    if os.path.exists(os.path.join(web, "index.html")):
        return FileResponse(os.path.join(web, "index.html"))
    return JSONResponse({"msg": "前端未构建，先 npm run build（web/）或直接用 API"}, status_code=200)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/characters")
def list_chars():
    out = []
    for name in sorted(os.listdir(CHAR_DIR)):
        d = os.path.join(CHAR_DIR, name)
        if os.path.isdir(d):
            out.append({"id": name, "assets": _tree(d)})
    return out

def _tree(d, prefix=""):
    res = []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        rel = os.path.join(prefix, n).replace("\\", "/")
        if os.path.isdir(p):
            res.append({"type": "dir", "name": n, "path": rel, "children": _tree(p, rel)})
        else:
            res.append({"type": "file", "name": n, "path": rel, "ext": os.path.splitext(n)[1]})
    return res

@app.post("/api/characters")
async def create_character(persona: UploadFile = File(...), ref_image: UploadFile | None = File(None)):
    char_id = f"char_{uuid.uuid4().hex[:8]}"
    d = os.path.join(CHAR_DIR, char_id)
    os.makedirs(d, exist_ok=True)
    content = await persona.read()
    with open(os.path.join(d, "persona.json"), "wb") as f:
        f.write(content)
    if ref_image and ref_image.filename:
        ext = os.path.splitext(ref_image.filename)[1] or ".png"
        with open(os.path.join(d, f"ref{ext}"), "wb") as f:
            f.write(await ref_image.read())
    return {"id": char_id}

@app.post("/api/characters/{char_id}/generate")
def generate(char_id: str, req: GenReq):
    d = os.path.join(CHAR_DIR, char_id)
    if not os.path.isdir(d):
        raise HTTPException(404, "角色不存在")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    c = db()
    c.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
              (job_id, char_id, req.scene, "queued", "queued", "", now(), now()))
    c.commit()
    threading.Thread(target=_run_job, args=(job_id, char_id, req.scene), daemon=True).start()
    return {"job_id": job_id}

def _run_job(job_id, char_id, scene):
    c = db()
    def set_state(stage, status, msg):
        c.execute("UPDATE jobs SET stage=?, status=?, message=?, updated=? WHERE id=?",
                  (stage, status, msg, now(), job_id))
        c.commit()
    set_state("concept", "running", "生成提示词并调用生图 API")
    try:
        outdir = os.path.join(CHAR_DIR, char_id)
        persona = os.path.join(outdir, "persona.json")
        ref = None
        for n in os.listdir(outdir):
            if n.startswith("ref"):
                ref = os.path.join(outdir, n); break
        cmd = [VENV_PY, GEN_PORTRAIT, persona, "--out", outdir, "--scene", scene]
        if ref: cmd += ["--ref", ref]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run(cmd, cwd=repo, timeout=3600, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        if r.returncode != 0:
            set_state("portrait", "failed", (r.stderr or r.stdout)[-500:])
            return
        set_state("package", "done", "资产包已生成")
    except Exception as e:
        set_state("portrait", "failed", str(e)[-500:])

@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    c = db()
    row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, "job 不存在")
    keys = ["id", "char_id", "scene", "stage", "status", "message", "created", "updated"]
    return dict(zip(keys, row))

@app.post("/api/jobs/{job_id}/retry")
def retry(job_id: str):
    c = db()
    row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    threading.Thread(target=_run_job, args=(row[0], row[1], row[2]), daemon=True).start()
    c.execute("UPDATE jobs SET stage='queued', status='queued', updated=? WHERE id=?", (now(), job_id))
    c.commit()
    return {"ok": True}

# 静态资产
app.mount("/char-assets", StaticFiles(directory=CHAR_DIR), name="char-assets")

# ---- v2 API：参考图 / 模板 / 配置 / persona-llm ----
@app.get("/api/refs")
def list_refs():
    ref_dir = os.path.join(repo, "assets", "reference")
    out = []
    if os.path.isdir(ref_dir):
        for grp in sorted(os.listdir(ref_dir)):
            gd = os.path.join(ref_dir, grp)
            if os.path.isdir(gd):
                files = [f for f in sorted(os.listdir(gd)) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
                out.append({"group": grp, "files": files})
    return out

@app.get("/api/templates")
def list_templates():
    import json as _json
    tdir = os.path.join(repo, "spec", "p1-character-voice", "contracts", "prompt-templates")
    out = {}
    for f in ("pixel.json", "splash.json"):
        p_ = os.path.join(tdir, f)
        if os.path.exists(p_):
            with open(p_, encoding="utf-8-sig") as fh:
                out[f.replace(".json", "")] = _json.load(fh)
    return out

@app.post("/api/config")
async def save_config(payload: dict):
    """保存 API key 到 env/.env（掩码显示；不覆盖已有未知键）。payload: {"GPT_API_KEY": "...", ...}"""
    env_file = os.path.join(repo, "env", ".env")
    lines = []
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            lines = f.readlines()
    keys = {l.split("=", 1)[0].strip(): l for l in lines if "=" in l and not l.strip().startswith("#")}
    for k, v in payload.items():
        if v and not v.startswith("***"):
            keys[k] = f"{k}={v}\n"
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(keys.values())
    return {"ok": True, "saved": list(payload.keys())}

@app.get("/api/config")
def get_config():
    env_file = os.path.join(repo, "env", ".env")
    keys = ("GPT_API_KEY", "GPT_BASE_URL", "GEMINI_API_KEY", "FAL_KEY", "VOLC_API_KEY", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
    out = {}
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    if k in keys:
                        out[k] = ("***" + v[-4:]) if v else ""
    return out

@app.post("/api/persona/llm")
async def persona_llm(payload: dict):
    """一句话人设 → LLM 生成完整 persona（需配置 LLM key）。"""
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "缺少人设描述")
    env_file = os.path.join(repo, "env", ".env")
    lk = lb = lm = None
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("LLM_API_KEY="): lk = line.split("=",1)[1].strip()
                elif line.startswith("LLM_BASE_URL="): lb = line.split("=",1)[1].strip()
                elif line.startswith("LLM_MODEL="): lm = line.split("=",1)[1].strip()
    if not lk:
        raise HTTPException(400, "未配置 LLM key（配置 → LLM）")
    from openai import OpenAI
    client = OpenAI(api_key=lk, base_url=lb or "https://api.sisct2.xyz/v1")
    sys_prompt = (
        "你是一个游戏角色设定师。根据用户的一句话人设，生成严格的 JSON（不要 markdown），字段："
        '{"name","race","class","personality_tags":[],"background","visual":{"subject","equipment","outfit","detail"},'
        '"style":{"type":"pixel 或 splash","palette","resolution"},"assets":{"pixel":["three_view","actions"],"splash":["portrait","expressions","dialogue"]}}'
    )
    r = client.chat.completions.create(model=lm or "gpt-4o-mini",
        messages=[{"role":"system","content":sys_prompt},{"role":"user","content":text}], temperature=0.7)
    import json as _json
    content = r.choices[0].message.content
    # 提取 JSON
    start = content.find("{"); end = content.rfind("}") + 1
    try:
        persona = _json.loads(content[start:end])
    except Exception:
        raise HTTPException(500, "LLM 返回非 JSON: " + content[:200])
    return persona
# 前端构建产物（web/dist）兜底托管 —— 放在所有 API 之后
_web_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "dist")
if os.path.exists(os.path.join(_web_dist, "index.html")):
    app.mount("/", StaticFiles(directory=_web_dist, html=True), name="web")
