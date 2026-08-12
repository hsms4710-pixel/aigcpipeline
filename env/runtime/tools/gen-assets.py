import os, time
from dotenv import load_dotenv
from openai import OpenAI

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(repo, "env", ".env"), override=True)
client = OpenAI(api_key=os.environ["GPT_API_KEY"], base_url=os.environ["GPT_BASE_URL"])
outdir = os.path.join(repo, "assets", "demo")
os.makedirs(outdir, exist_ok=True)

STYLE = ("pixel art, 16-bit style, limited color palette, hard edges, no anti-aliasing, "
         "grid-aligned pixels, sprite-sheet ready, transparent background")
CHAR = ("a female elf ranger, green leather armor, composite bow on back, long silver hair, "
        "emerald eyes, slender build")

def gen(name, extra, n=3):
    prompt = f"{CHAR}, {STYLE}, {extra}"
    t0 = time.time()
    resp = client.images.generate(model="gpt-image-1", prompt=prompt, n=n, size="1024x1024")
    import requests
    for i, d in enumerate(resp.data):
        img = requests.get(d.url, timeout=120).content
        out = os.path.join(outdir, name.replace(".png", f"_{i+1}.png"))
        open(out, "wb").write(img)
        print(f"[{time.time()-t0:.0f}s] {os.path.basename(out)} ({len(img)}B)")

print("== side (3 candidates) ==")
gen("pixel_side.png", "side view, full body, profile facing left, same character design as front view")
print("== back ==")
gen("pixel_back.png", "back view, full body, seen from behind, same character design, bow visible on back")
print("DONE")
