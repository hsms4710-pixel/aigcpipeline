import os, base64, time, json
from dotenv import load_dotenv
from openai import OpenAI

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(repo, "env", ".env"), override=True)
client = OpenAI(api_key=os.environ["GPT_API_KEY"], base_url=os.environ["GPT_BASE_URL"])

front = os.path.join(repo, "assets", "demo", "pixel_front_anchor.png")
with open(front, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
data_url = "data:image/png;base64," + b64

# 1) 测中转站基础生图是否恢复
print("=== 1) images.generate (无图) ===")
try:
    r = client.images.generate(model="gpt-image-1", prompt="pixel art test, front view", n=1, size="512x512")
    print("  OK, url len:", len(r.data[0].url or ""))
except Exception as e:
    print("  FAIL:", type(e).__name__, str(e)[:150])

# 2) chat completions + image_url（最常见兼容方式）
for m in ["gpt-4o", "gpt-image-1", "gpt-5.5"]:
    print(f"=== 2) chat.completions + image_url ({m}) ===")
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "side view of the same character as the image, pixel art, full body"},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]}],
            max_tokens=1000,
        )
        msg = resp.choices[0].message
        print("  OK. content type:", type(msg.content).__name__)
        c = msg.content
        if isinstance(c, list):
            for item in c:
                t = item.get("type")
                print("    part:", t)
                if t == "image_url":
                    print("    image url:", str(item["image_url"]["url"])[:60])
        else:
            print("    text:", str(c)[:80])
        break
    except Exception as e:
        print("  FAIL:", type(e).__name__, str(e)[:150])
