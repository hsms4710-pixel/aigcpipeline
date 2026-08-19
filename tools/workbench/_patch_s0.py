# -*- coding: utf-8 -*-
import os
f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
src = open(f, encoding="utf-8").read()
old1 = '            _f("force", "强制重生成", "bool", False),'
new1 = ('            _f("force", "强制重生成", "bool", False),\n'
        '            _f("dry_run", "仅预览提示词(不调API)", "bool", False, help="调试用：打印将执行的命令，不实际调用生图"),')
assert old1 in src, "s0 field marker not found"
src = src.replace(old1, new1)
old2 = '    if cfg.get("force") in (True, "true", "on"): cmd.append("--force")'
new2 = ('    if cfg.get("force") in (True, "true", "on"): cmd.append("--force")\n'
        '    if cfg.get("dry_run") in (True, "true", "on"): cmd.append("--dry-run")\n'
        '    open(os.path.join(job_dir, "cmd.txt"), "w", encoding="utf-8").write(" ".join(cmd))')
assert old2 in src, "s0 force marker not found"
src = src.replace(old2, new2)
open(f, "w", encoding="utf-8").write(src)
print("S0 dry_run patched")
