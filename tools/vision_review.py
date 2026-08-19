# -*- coding: utf-8 -*-
"""vision_review.py — 用 GPT 视觉模型审查图片（骨骼截图/动画帧）
用法: python vision_review.py <img1> [img2 ...] [--prompt "问什么"] [--model gpt-5.4] [--max-size 768]
"""
import argparse, base64, io, json, os, sys
import urllib.request
from PIL import Image

def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'env', '.env'), override=True)
    except Exception:
        pass

API = 'https://api.sisct2.xyz/v1/chat/completions'
KEY = os.environ.get('VISION_KEY', '')  # 从 env/.env 读取，勿硬编码

def img_to_dataurl(path, max_size):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    scale = max_size / max(w, h)
    if scale < 1.0:
        im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format='JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'data:image/jpeg;base64,{b64}', im.size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('imgs', nargs='+')
    ap.add_argument('--prompt', default='请描述这张图片的内容，重点检查：角色姿态、四肢位置、关节是否断裂/穿模、画面是否正常。')
    ap.add_argument('--model', default='gpt-5.5')
    ap.add_argument('--max-size', type=int, default=768)
    ap.add_argument('--api', default=API)
    ap.add_argument('--key', default=KEY)
    a = ap.parse_args()
    content = [{'type': 'text', 'text': a.prompt}]
    for p in a.imgs:
        url, size = img_to_dataurl(p, a.max_size)
        print(f'  img {p} -> {size}', file=sys.stderr)
        content.append({'type': 'image_url', 'image_url': {'url': url}})
    body = {'model': a.model, 'messages': [{'role': 'user', 'content': content}], 'max_tokens': 1200}
    req = urllib.request.Request(a.api, data=json.dumps(body).encode('utf-8'),
                                 headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {a.key}'})
    import time
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                j = json.loads(r.read().decode('utf-8'))
            print(j['choices'][0]['message']['content'])
            if j.get('usage'):
                print(f"\n[usage] prompt={j['usage'].get('prompt_tokens')} completion={j['usage'].get('completion_tokens')} model={j.get('model')}", file=sys.stderr)
            return
        except urllib.error.HTTPError as e:
            print('HTTP', e.code, e.read().decode('utf-8')[:300], file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            last = e
            print(f'  retry {attempt+1}: {e}', file=sys.stderr)
            time.sleep(4 * (attempt + 1))
    print('FAILED:', last, file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    main()