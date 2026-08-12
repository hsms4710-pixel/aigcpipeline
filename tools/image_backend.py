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


def _openai_gen(client, prompt, out, ref, model, size, seed=None, transparent=False, mask=None):
    if ref is None:
        kwargs = {"model": model, "prompt": prompt, "n": 1, "size": size}
        if transparent:
            kwargs["background"] = "transparent"
        if seed is not None:
            kwargs["extra_body"] = {"seed": seed}
        resp = client.images.generate(**kwargs)
        return _download(resp.data[0].url, out)
    # 参考图锚点：images.edit（保持角色）；mask 存在时只编辑透明区域（表情连贯）
    with open(ref, "rb") as f:
        kwargs = {"model": model, "image": f, "prompt": prompt, "size": size}
        if transparent:
            kwargs["background"] = "transparent"
        if mask is not None:
            kwargs["mask"] = open(mask, "rb")
        if seed is not None:
            kwargs["extra_body"] = {"seed": seed}
        resp = client.images.edit(**kwargs)
        return _download(resp.data[0].url, out)


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


def gen_image(prompt, out, ref=None, backend="openai", model="gpt-image-2", size="1024x1024", client=None, seed=None, transparent=False, mask=None, style_ref=None):
    """统一生图入口。client 可复用；style_ref=风格参考图（重绘为新角色，同画风）。返回 (bytes大小, 耗时秒)。"""
    t0 = time.time()
    if backend == "openai":
        if client is None:
            from dotenv import load_dotenv
            from openai import OpenAI
            repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            load_dotenv(os.path.join(repo, "env", ".env"), override=True)
            client = OpenAI(api_key=os.environ.get("GPT_API_KEY", ""), base_url=os.environ.get("GPT_BASE_URL", ""))
        # 风格参考：用一张或多张参考图做"画风迁移"（官方 images.edit 支持 image 数组）
        if style_ref is not None and ref is None:
            refs = style_ref if isinstance(style_ref, (list, tuple)) else [style_ref]
            sp = ("Use the reference image(s) ONLY as art-style references (their lineart, coloring, shading, "
                  "painterly rendering and finish quality). Draw a NEW original character in exactly this art style. "
                  "Do NOT copy the reference character(s), face, pose or outfit: " + prompt)
            files = [open(rf, "rb") for rf in refs]
            try:
                img_arg = files[0] if len(files) == 1 else files
                r = client.images.edit(model=model, image=img_arg, prompt=sp, size=size,
                                       **({"background": "transparent"} if transparent else {}))
            finally:
                for f in files:
                    f.close()
            return _download(r.data[0].url, out), time.time() - t0
        n = _openai_gen(client, prompt, out, ref, model, size, seed=seed, transparent=transparent, mask=mask)
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


def face_mask(ref_img, out_mask, cy=0.40, rx=0.20, ry=0.24):
    """生成脸部近似 mask（二次元立绘表情切换：只改脸，构图不变）。
    mask 中透明区域=要编辑的部位。cy/rx/ry 为脸部椭圆参数（比例）。"""
    from PIL import Image, ImageDraw
    im = Image.open(ref_img).convert("RGBA")
    w, h = im.size
    m = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(m)
    cx = w * 0.5
    d.ellipse([cx - w*rx, h*cy - h*ry, cx + w*rx, h*cy + h*ry], fill=(0, 0, 0, 0))
    m.save(out_mask)
    return out_mask

