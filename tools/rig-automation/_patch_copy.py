# -*- coding: utf-8 -*-
import os
f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workbench", "web", "src", "components", "StageTab.jsx")
src = open(f, encoding="utf-8").read()
old = """                      <a href={a.url} target="_blank" rel="noreferrer">{a.path}</a>
                      <span className="asz">{fmtSize(a.size)}</span>
                    </div>"""
new = """                      <a href={a.url} target="_blank" rel="noreferrer">{a.path}</a>
                      <span className="asz">{fmtSize(a.size)}</span>
                      <button className="btn ghost sm" title="复制绝对路径（供下一阶段输入）" onClick={() => { navigator.clipboard.writeText(a.abs); alert('已复制: ' + a.abs); }}>📋</button>
                    </div>"""
assert old in src, "artifact markup not found"
src = src.replace(old, new)
open(f, "w", encoding="utf-8").write(src)
print("copy button patched")
