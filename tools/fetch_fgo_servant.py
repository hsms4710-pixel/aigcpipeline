# -*- coding: utf-8 -*-
"""fetch_fgo_servant.py — 从 Atlas Academy API 抓取一个 FGO 从者的全部图档资产
用法: python fetch_fgo_servant.py <collectionNo|servantId> [--out DIR]
数据源: https://apps.atlasacademy.io/db/NA/servant/<id>/assets 页面背后的 API
  nice 接口: https://api.atlasacademy.io/nice/NA/servant/<id>
"""
import os, sys, json, re, argparse, urllib.request

UA = {"User-Agent": "CharacterAIGC-Research/1.0 (research script)"}

def http_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def download(url, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    with open(out, "wb") as f:
        f.write(data)
    return len(data)

def merge_vertical(parts, out):
    from PIL import Image
    ims = [Image.open(p).convert("RGBA") for p in parts]
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for im in ims:
        canvas.paste(im, (0, y))
        y += im.height
    canvas.save(out)
    return os.path.getsize(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("servant", help="collectionNo(如 421) 或 servant id")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    basic = http_json("https://api.atlasacademy.io/export/NA/basic_servant.json")
    hit = None
    for s in basic:
        if str(s.get("collectionNo")) == str(a.servant) or str(s.get("id")) == str(a.servant):
            hit = s
            break
    if not hit:
        print("未找到从者:", a.servant); return 1
    sid = hit["id"]
    j = http_json(f"https://api.atlasacademy.io/nice/NA/servant/{sid}")
    name = j.get("name", str(sid))
    cn = j.get("collectionNo", "")
    outdir = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "reference", "fgo", f"{name}_{cn}")
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    ea = j.get("extraAssets", {})
    manifest = {"servant": name, "id": sid, "collectionNo": cn,
                "source": f"https://apps.atlasacademy.io/db/NA/servant/{sid}/assets", "files": {}}
    total = 0

    def save(cat, fn, url):
        nonlocal total
        out = os.path.join(outdir, cat, fn)
        if not os.path.exists(out):
            try:
                n = download(url, out)
                total += n
                print(f"  ok {cat}/{fn} ({n}B)")
            except Exception as e:
                print(f"  ERR {url}: {e}")
                return None
        manifest["files"][f"{cat}/{fn}"] = url
        return out

    def grab(cat, mapping):
        for asc, url in (mapping or {}).items():
            save(cat, f"{asc}.png", url)

    grab("01_face", ea.get("faces", {}).get("ascension"))
    # charaGraph: a@1/a@2 = 立绘A 上下两半, b@1/b@2 = 立绘B 上下两半
    cg = ea.get("charaGraph", {}).get("ascension", {})
    stage = {}
    for part, url in cg.items():
        m = re.search(r'([ab])@([12])\.png$', url)
        if m:
            stage.setdefault(m.group(1), {})[int(m.group(2))] = url
    for art, halves in stage.items():
        for half, url in sorted(halves.items()):
            save("02_stage_art", f"{art}_half{half}.png", url)
        if len(halves) == 2:
            parts = [os.path.join(outdir, "02_stage_art", f"{art}_half{h}.png") for h in sorted(halves)]
            full = os.path.join(outdir, "02_stage_art", f"full_{art}.png")
            if not os.path.exists(full):
                try:
                    n = merge_vertical(parts, full)
                    total += n
                    print(f"  ok 02_stage_art/full_{art}.png (merged {n}B)")
                except Exception as e:
                    print(f"  ERR merge {art}: {e}")
            manifest["files"][f"02_stage_art/full_{art}"] = "merged:" + ",".join(str(h) for h in sorted(halves))
    grab("03_chibi", ea.get("narrowFigure", {}).get("ascension"))
    grab("04_figure", ea.get("charaFigure", {}).get("ascension"))
    grab("05_commands", ea.get("commands", {}).get("ascension"))
    grab("06_status", ea.get("status", {}).get("ascension"))
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n完成: {name} ({cn}) 新增下载 {total}B -> {outdir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

