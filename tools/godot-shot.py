# -*- coding: utf-8 -*-
"""godot-shot.py — 用 godot-assistant MCP（stdio, 新行分隔 JSON-RPC）渲染 Godot 场景截图
用途: A3 视觉门禁直接验收「游戏内实际画面」（人物比例/相机/地图观感），而不是只看源 PNG。

用法:
  python tools/godot-shot.py --scene res://main.tscn --out <png> [--project <demo>] [--timeout 240]
  python tools/godot-shot.py --tools   # 只列出 godot-assistant 工具 schema（调试）
"""
import argparse, json, os, subprocess, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROJECT = os.path.join(REPO, "assets", "demo", "godot-pokemon-demo")
DEFAULT_GODOT = r"C:\Users\26046\Documents\lovegaming\Godot_v4.7.1-stable_win64.exe\Godot_v4.7.1-stable_win64_console.exe"

import queue, threading

class MCPStdio:
    def __init__(self, cmd, cwd, env):
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, cwd=cwd, env=env)
        self.q = queue.Queue()
        self._buf = b""
        self._th = threading.Thread(target=self._reader, daemon=True)
        self._th.start()
    def _reader(self):
        # Windows 管道 read(n) 会阻塞等满 n 字节；用 readline() 按行读取（MCP stdio = 换行分隔）
        while True:
            line = self.p.stdout.readline()
            if not line:
                self.q.put(None)
                break
            line = line.strip()
            if line:
                try:
                    self.q.put(json.loads(line.decode("utf-8")))
                except Exception:
                    pass
    def send(self, obj):
        self.p.stdin.write(json.dumps(obj).encode("utf-8") + b"\n")
        self.p.stdin.flush()
    def read_line(self, timeout):
        try:
            item = self.q.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f"no response in {timeout}s")
        if item is None:
            raise RuntimeError("server exited")
        return item
    def wait_ready(self, timeout=120):
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.read_line(15)
            except TimeoutError:
                continue
            if isinstance(line, dict) and line.get("id") == 0:
                return line
        raise TimeoutError("initialize not acked")

def build_cmd(project):
    return ["npx.cmd", "-y", "godot-assistant", "--project", project]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="res://main.tscn")
    ap.add_argument("--out", default=None)
    ap.add_argument("--project", default=DEFAULT_PROJECT)
    ap.add_argument("--tools", action="store_true")
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--height", type=int, default=600)
    a = ap.parse_args()
    env = dict(os.environ)
    env["GODOT_PATH"] = DEFAULT_GODOT
    if not os.path.exists(a.project):
        print("project not found:", a.project); sys.exit(2)
    m = MCPStdio(build_cmd(a.project), cwd=a.project, env=env)
    try:
        m.send({"jsonrpc":"2.0","id":0,"method":"initialize",
                "params":{"protocolVersion":"2025-03-26","capabilities":{},
                          "clientInfo":{"name":"godot-shot","version":"1.0"}}})
        m.wait_ready(120)
        m.send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        if a.tools:
            m.send({"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}})
            r = m.read_line(60)
            tools = r.get("result", {}).get("tools", [])
            print(f"tools: {len(tools)}")
            for t in tools:
                if t["name"] in ("screenshot", "run_project"):
                    print(f"- {t['name']}: {t.get('description','')}")
                    print("  schema:", json.dumps(t.get("inputSchema", {}), ensure_ascii=False)[:1200])
                else:
                    print(f"- {t['name']}: {t.get('description','')[:70]}")
            return
        # call screenshot (scene offscreen render, 无需 bridge)
        import base64 as _b64
        def _call_screenshot(args, tag):
            m.send({"jsonrpc":"2.0","id":99,"method":"tools/call",
                    "params":{"name":"screenshot","arguments":args}})
            r = m.read_line(a.timeout)
            res = r.get("result", {})
            out_texts = []
            img_data = None
            for c in res.get("content", []):
                if c.get("type") == "text":
                    out_texts.append(c.get("text",""))
                elif c.get("type") == "image":
                    data = c.get("data") or c.get("image") or ""
                    if data and "base64," in data:
                        data = data.split("base64,",1)[1]
                    img_data = data
                elif c.get("type") == "resource":
                    out_texts.append(str(c.get("resource",{}))[:200])
            print(f"[godot-shot] {tag}: isError={res.get('isError')} texts={len(out_texts)} img_data={'yes' if img_data else 'no'}")
            for x in out_texts:
                print(x[:600])
            return img_data, out_texts
        out = a.out or os.path.join(a.project, "shot_main.png")
        # 第一次：不带输出参数，探测返回
        img1, texts1 = _call_screenshot({"source":"scene","scene":a.scene,"width":a.width,"height":a.height,"frames":12}, "try1")
        if img1:
            data = _b64.b64decode(img1)
            with open(out, "wb") as f:
                f.write(data)
            print(f"[godot-shot] saved image -> {out} ({len(data)} bytes)")
        elif texts1:
            # 尝试从文本找路径
            for ln in texts1:
                for kw in ("saved","-> ","png","PNG"):
                    pass
        # 若未保存且无输出参数，尝试把输出路径写进 project 下再找
        if not os.path.exists(out):
            print("[godot-shot] no image content returned; response above is authoritative")
    finally:
        try: m.p.kill()
        except Exception: pass

if __name__ == "__main__":
    main()
