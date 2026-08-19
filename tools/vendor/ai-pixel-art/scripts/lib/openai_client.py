"""Direct OpenAI image generation client wrapper."""

from __future__ import annotations

import os
import sys

DEFAULT_MODEL = "gpt-image-2"


def build_client(api_key: str | None = None, organization: str | None = None):
    try:
        from openai import OpenAI
    except ImportError:
        print(
            "ERROR: openai package not installed. Run: pip install openai",
            file=sys.stderr,
        )
        sys.exit(1)

    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "ERROR: OpenAI provider requires OPENAI_API_KEY or --openai-api-key.",
            file=sys.stderr,
        )
        sys.exit(1)

    kwargs = {
        "api_key": api_key,
        "organization": organization or os.environ.get("OPENAI_ORG_ID"),
    }
    # ????????TLS1.2 + ???????api.sisct2.xyz ??? TLS1.2 ????????
    try:
        import ssl, httpx
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        transport = httpx.HTTPTransport(verify=ctx, trust_env=False)
        kwargs["http_client"] = httpx.Client(transport=transport, timeout=httpx.Timeout(300.0))
    except Exception:
        pass
    return OpenAI(**kwargs)


def resolve_model(cli_value: str | None = None) -> str:
    return cli_value or os.environ.get("OPENAI_IMAGE_MODEL", DEFAULT_MODEL)


def generate_image_bytes(
    client,
    *,
    model: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    n: int = 1,
) -> list[bytes]:
    """Generate images and return a list of raw image bytes."""
    import base64
    import urllib.request

    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=n,
    )

    out: list[bytes] = []
    for img in response.data:
        if getattr(img, "b64_json", None):
            out.append(base64.b64decode(img.b64_json))
        elif getattr(img, "url", None):
            with urllib.request.urlopen(img.url) as r:
                out.append(r.read())
        else:
            raise RuntimeError(f"No image data in response item: {img}")
    return out
