"""image_backend.py：生图后端统一抽象（openai 中转站 / gemini Nano Banana / fal 聚合）
统一接口 gen_image(prompt, out, ref=None, backend=..., model=...) -> (bytes大小, 用时秒)
"""
import os, time, base64


def _download(url, out):
    import requests
    img = requests.get(url, timeout=180).content
    with open(out, "wb") as f:
        f.write(img)
    return len(img)


def _openai_gen(client, prompt, out, ref, model, size):
    if ref is None:
        resp = client.images.generate(model=model, prompt=prompt, n=1, size=size)
        return _download(resp.data[0].url, out)
    with open(ref, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    resp = client.responses.create(model=model, input=[
        {"type": "image", "image_url": "data:image/png;base64," + b64},
        {"type": "text", "text": prompt},
    ])
    for it in resp.output:
        for part in (getattr(it, "content", None) or []):
            if getattr(part, "type", "") == "image":
                url = getattr(part, "image_url", "")
                if isinstance(url, str) and url.startswith("data:"):
                    data = base64.b64decode(url.split(",", 1)[1])
                    with open(out, "wb") as f:
                        f.write(data)
                    return len(data)
    raise RuntimeError("responses 输出无图片（中转站可能不支持参考图）")


def _gemini_gen(client, prompt, out, ref, model):
    from google.genai import types
    cfg = {"prompt": prompt}
    if ref:
        with open(ref, "rb") as f:
            cfg["image"] = types.Part.from_bytes(data=f.read(), mime_type="image/png")
    resp = client.models.generate_images(model=model, config=types.GenerateImagesConfig(**cfg))
    data = resp.generated_images[0].image.image_bytes
    with open(out, "wb") as f:
        f.write(data)
    return len(data)


def _fal_gen(prompt, out, ref, model):
    import fal_client
    args = {"prompt": prompt}
    if ref:
        args["image"] = fal_client.upload_file(ref)
    result = fal_client.run(model, arguments=args)
    url = result.get("images", [{}])[0].get("url")
    return _download(url, out)


def gen_image(prompt, out, ref=None, backend="openai", model="gpt-image-2", size="1024x1024", client=None):
    """统一生图入口。client 可复用；返回 (bytes大小, 耗时秒)。"""
    t0 = time.time()
    if backend == "openai":
        if client is None:
            from dotenv import load_dotenv
            from openai import OpenAI
            repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            load_dotenv(os.path.join(repo, "env", ".env"), override=True)
            client = OpenAI(api_key=os.environ.get("GPT_API_KEY", ""), base_url=os.environ.get("GPT_BASE_URL", ""))
        n = _openai_gen(client, prompt, out, ref, model, size)
    elif backend == "gemini":
        if client is None:
            from google import genai
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        n = _gemini_gen(client, prompt, out, ref, model)
    elif backend == "fal":
        n = _fal_gen(prompt, out, ref, model)
    else:
        raise ValueError(f"未知 backend: {backend}")
    return n, time.time() - t0
