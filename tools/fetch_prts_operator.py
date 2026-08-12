# -*- coding: utf-8 -*-
"""fetch_prts_operator.py — 从 PRTS Wiki(明日方舟) 抓取一个干员的立绘/头像图档
用法: python fetch_prts_operator.py <干员名> [--out DIR]
数据源: https://prts.wiki/w/<干员名> (MediaWiki API: action=query&list=allimages)
文件命名规则参考模板:立绘差分 / 模板:剧情立绘  (立绘_干员名_精英/皮肤.png, 头像_干员名_*.png)
"""
import os, sys, json, argparse, urllib.request, urllib.parse

API = "https://prts.wiki/api.php"
UA = {"User-Agent": "CharacterAIGC-Research/1.0 (research script; contact: local@localhost)"}

def api(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)

def download(url, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    with open(out, "wb") as f:
        f.write(data)
    return len(data)

def list_files(prefix):
    """列出以 prefix 开头的所有文件"""
    out = []
    cont = {}
    while True:
        params = {"action": "query", "list": "allimages", "aiprefix": prefix,
                  "ailimit": "500", "format": "json"}
        params.update(cont)
        j = api(params)
        out.extend(j.get("query", {}).get("allimages", []))
        if "continue" in j:
            cont = j["continue"]
        else:
            break
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="干员名，如 阿米娅")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    name = a.name.strip()
    outdir = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "reference", "arknights", name)
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    total = 0
    manifest = {"operator": name, "source": f"https://prts.wiki/w/{urllib.parse.quote(name)}", "files": {}}
    # 1) 立绘（精英阶段 + 皮肤）
    li = list_files("立绘_" + name)
    # 2) 头像
    tx = list_files("头像_" + name)
    # 过滤掉明显无关的（如 阿米娅的相册 等）
    def is_art(fn):
        return fn.startswith(("立绘_", "头像_")) and not fn.startswith("立绘_临时")
    cats = {"立绘_": ("立绘", li), "头像_": ("头像", tx)}
    for prefix, (cat, flist) in cats.items():
        for f in flist:
            fn = f["name"]
            if not is_art(fn):
                continue
            info = api({"action": "query", "titles": "File:" + fn,
                        "prop": "imageinfo", "iiprop": "url|size", "format": "json"})
            pages = info.get("query", {}).get("pages", {})
            ii = None
            for p in pages.values():
                if "imageinfo" in p:
                    ii = p["imageinfo"][0]
            if not ii:
                continue
            url = ii["url"]
            # 用原始文件名（去前后缀歧义）
            base = fn[len(prefix):].replace("/", "_").replace(":", "_")
            out = os.path.join(outdir, cat, base)
            if not os.path.exists(out):
                try:
                    n = download(url, out)
                    total += n
                    print(f"  ok {cat}/{base} ({ii.get('width','?')}x{ii.get('height','?')}, {n}B)")
                except Exception as e:
                    print(f"  ERR {fn}: {e}")
                    continue
            manifest["files"][f"{cat}/{base}"] = url
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n完成: {name} 新增下载 {total}B -> {outdir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
