import os, requests
from concurrent.futures import ThreadPoolExecutor
BASE = "https://hf-mirror.com/lj1995/GPT-SoVITS/resolve/main/"
DEST = r"C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/env/runtime/tools/GPT-SoVITS/GPT_SoVITS/pretrained_models"
files = [
    "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
    "s2G488k.pth",
    "s2D488k.pth",
    "chinese-hubert-base/config.json",
    "chinese-hubert-base/preprocessor_config.json",
    "chinese-hubert-base/pytorch_model.bin",
    "chinese-roberta-wwm-ext-large/config.json",
    "chinese-roberta-wwm-ext-large/pytorch_model.bin",
    "chinese-roberta-wwm-ext-large/tokenizer.json",
]
def dl(f):
    url = BASE + f
    out = os.path.join(DEST, f.replace("/", os.sep))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        print("skip", f); return
    tmp = out + ".part"
    r = requests.get(url, stream=True, timeout=120)
    if r.status_code != 200:
        print("FAIL", f, r.status_code); return
    n = 0
    with open(tmp, "wb") as fh:
        for chunk in r.iter_content(1 << 20):
            fh.write(chunk); n += len(chunk)
    os.replace(tmp, out)
    print("ok", f, round(n/1e6, 1), "MB")
with ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(dl, files))
print("ALL DONE")
