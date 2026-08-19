"""aigc-toolkit.py — 集成 AIGC 工具统一入口
用法:
  python tools/aigc-toolkit.py --tool pixel-art --action sprite --prompt "..." --size 32 --palette db32 --out <png>
  python tools/aigc-toolkit.py --tool pixel-art --action tileset --prompt "..." --tile-size 32 --count 8 --out-dir <dir>
  python tools/aigc-toolkit.py --tool pixel-art --action animation --prompt "..." --frames 4 --tile-size 32 --out-dir <dir>
  python tools/aigc-toolkit.py --tool pixel-art --action pixelize --input <png> --size 32 --palette db32 --output <png>
  python tools/aigc-toolkit.py --tool pixel-art --action qa --input <png> --kind sprite --palette db32
  python tools/aigc-toolkit.py --tool pixel-art --action export-tiled --input <png> --tile-size 32 --columns 4 --output-dir <dir>
已集成: ai-pixel-art (tools/vendor/ai-pixel-art, 经中转站 gpt-image-2, TLS 补丁)
"""
import os, sys, argparse, subprocess, json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(REPO, "tools", "vendor", "ai-pixel-art", "scripts")
PY = sys.executable

def load_env():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(REPO, "env", ".env"), override=True)
    if os.environ.get("GPT_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["GPT_API_KEY"]
    if os.environ.get("GPT_BASE_URL") and not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = os.environ["GPT_BASE_URL"]

ACTIONS = {
    "sprite": ("generate_sprite.py", ["--prompt", "--size", "--palette", "--transparent-bg", "--qa", "--output"]),
    "tileset": ("generate_tileset.py", ["--prompt", "--tile-size", "--count", "--columns", "--palette", "--seamless", "--name", "--output-dir", "--qa"]),
    "animation": ("generate_animation.py", ["--prompt", "--frames", "--tile-size", "--palette", "--action", "--transparent-bg", "--name", "--output-dir", "--qa"]),
    "pixelize": ("pixelize.py", ["--input", "--output", "--size", "--palette"]),
    "qa": ("qa_report.py", ["--input", "--kind", "--palette", "--tile-size", "--columns", "--tile-count", "--frames", "--output-json"]),
    "export-tiled": ("export_tiled.py", ["--input", "--tile-size", "--columns", "--rows", "--output-dir"]),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", default="pixel-art")
    ap.add_argument("--action", default=None)
    ap.add_argument("--style", default=None, help="style asset name (e.g. px-db32)")
    ap.add_argument("--list", action="store_true", help="列出可用 action")
    args, rest = ap.parse_known_args()
    if args.list:
        print("pixel-art actions:", ", ".join(ACTIONS.keys()))
        return
    if args.action is None:
        print("--action required; available:", ", ".join(ACTIONS))
        sys.exit(1)
    if args.action not in ACTIONS:
        print(f"unknown action {args.action}; available: {', '.join(ACTIONS)}")
        sys.exit(1)
    load_env()
    # style-assets ???--style px-db32 ???? palette + STYLE ? + seamless=edge_match
    style_cfg = None
    cfg_path = os.path.join(REPO, "contracts", "style-assets.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                style_cfg = json.load(f)
        except Exception:
            style_cfg = None
    _style_name = getattr(args, "style", None)
    if _style_name and style_cfg:
        # ????????styles.<name>.{palette,style_block}???????
        _st_cfg = style_cfg.get("styles", {}).get(_style_name) if isinstance(style_cfg.get("styles"), dict) else None
        if _st_cfg is None:
            _st_cfg = style_cfg
        _pal = _st_cfg.get("palette", "")
        _st = _st_cfg.get("style_block", "")
        rest = [rest[i] if (rest[i] != "--palette" or i + 1 >= len(rest)) else (rest[i] if False else rest[i]) for i in range(len(rest))]
        # ??/?? --palette
        has_pal = any(a == "--palette" for a in rest)
        if not has_pal:
            rest = ["--palette", _pal] + rest
        # seamless auto -> edge_match
        rest = [("edge_match" if a == "auto" and i > 0 and rest[i-1] == "--seamless" else a) for i, a in enumerate(rest)]
        # STYLE ???? --prompt
        for i, a in enumerate(rest):
            if a == "--prompt" and i + 1 < len(rest):
                rest[i + 1] = rest[i + 1] + ". " + _st
        print("[style-guard] style=%s palette=%s (STYLE block injected)" % (_style_name, _pal))
    script, _ = ACTIONS[args.action]
    cmd = [PY, os.path.join(VENDOR, script)] + rest
    print(">>", " ".join(cmd[:6]), "...")
    r = subprocess.run(cmd)
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()