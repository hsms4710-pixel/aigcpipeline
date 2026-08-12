import os, sys
from dotenv import load_dotenv
from openai import OpenAI

# env/runtime/tools/test-image.py -> 上三级 = env/
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(root, ".env"), override=True)
key = os.environ.get("GPT_API_KEY", "")
base = os.environ.get("GPT_BASE_URL", "")
print("base_url:", base, "| key:", (key[:8] + "...") if key else "EMPTY")
assert key and base, ".env not loaded"

client = OpenAI(api_key=key, base_url=base)

try:
    models = client.models.list()
    names = sorted(m.id for m in models.data)
    print("=== models (%d) ===" % len(names))
    for n in names:
        print(" ", n)
except Exception as e:
    print("list models failed:", type(e).__name__, str(e)[:300])

prompt = ("Anime game character concept art, young female adventurer with silver long hair and blue eyes, "
          "full body, standing pose, clean lineart, vibrant colors, game splash art style")
outdir = os.path.join(root, "runtime", "logs")
os.makedirs(outdir, exist_ok=True)

candidates = ["gpt-image-1", "gpt-image-2", "gpt-image", "gpt-5.5-image", "dall-e-3", "gpt-5.5"]
for m in candidates:
    try:
        print("trying image model:", m, "...")
        resp = client.images.generate(model=m, prompt=prompt, n=1, size="1024x1024")
        url = resp.data[0].url
        print("  OK ->", (url[:80] if url else "no url"))
        if url:
            import requests
            img = requests.get(url, timeout=60).content
            out = os.path.join(outdir, "test_%s.png" % m.replace("/", "_"))
            open(out, "wb").write(img)
            print("  saved:", out, len(img), "bytes")
            break
    except Exception as e:
        print("  failed:", type(e).__name__, str(e)[:200])
