import os, base64, time
from dotenv import load_dotenv
from openai import OpenAI

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(repo, "env", ".env"), override=True)
client = OpenAI(api_key=os.environ["GPT_API_KEY"], base_url=os.environ["GPT_BASE_URL"])

front = os.path.join(repo, "assets", "demo", "pixel_front_anchor.png")
with open(front, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
data_url = "data:image/png;base64," + b64

prompt = ("side view of the same female elf ranger character as the reference image, "
          "full body, profile facing left, pixel art, 16-bit, limited palette, transparent background")
t0 = time.time()
try:
    resp = client.responses.create(
        model="gpt-image-1",
        input=[
            {"type": "image", "image_url": data_url},
            {"type": "text", "text": prompt},
        ],
    )
    # 解析输出
    out = resp.output
    imgs = []
    for item in out:
        if getattr(item, "type", "") == "image" or "image" in str(getattr(item, "type", "")):
            imgs.append(item)
    print("elapsed %.0fs, output items:" % (time.time()-t0))
    for it in out:
        print("  -", it.type if hasattr(it, "type") else type(it).__name__)
    # 尝试提取图片
    for it in out:
        c = getattr(it, "content", None)
        if c:
            for part in c:
                if getattr(part, "type", "") == "image":
                    b64o = part.image_url  # may be b64 or url
                    print("  image part found:", str(b64o)[:100])
                    if isinstance(b64o, str) and b64o.startswith("data:"):
                        data = b64o.split(",", 1)[1]
                        open(os.path.join(repo, "assets", "demo", "pixel_side_ref.png"), "wb").write(base64.b64decode(data))
                        print("  saved pixel_side_ref.png")
except Exception as e:
    print("FAILED:", type(e).__name__, str(e)[:500])
