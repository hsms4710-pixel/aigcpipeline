# -*- coding: utf-8 -*-
import io, os
f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
src = open(f, encoding="utf-8").read()
old = '''def db():
    c = sqlite3.connect(JOBS_DB)
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, stage TEXT, config TEXT, status TEXT,
        stage_detail TEXT, log TEXT, artifacts TEXT, error TEXT,
        created TEXT, started TEXT, finished TEXT, duration_ms INTEGER, cost REAL)""")
    return c'''
new = '''def db():
    c = sqlite3.connect(JOBS_DB)
    cols = [r[1] for r in c.execute("PRAGMA table_info(jobs)").fetchall()]
    want = {"id", "stage", "config", "status", "stage_detail", "log", "artifacts", "error", "created", "started", "finished", "duration_ms", "cost"}
    if cols and not want.issubset(set(cols)):
        c.execute("DROP TABLE jobs"); c.commit()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, stage TEXT, config TEXT, status TEXT,
        stage_detail TEXT, log TEXT, artifacts TEXT, error TEXT,
        created TEXT, started TEXT, finished TEXT, duration_ms INTEGER, cost REAL)""")
    return c'''
assert old in src, "db() block not found"
src = src.replace(old, new)
open(f, "w", encoding="utf-8").write(src)
print("db() patched")
