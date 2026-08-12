import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from huggingface_hub import snapshot_download
target = r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路\env\runtime\tools\GPT-SoVITS"
out = os.path.join(target, "GPT_SoVITS", "pretrained_models")
os.makedirs(out, exist_ok=True)
print("downloading gsv-v2final-pretrained ->", out)
snapshot_download(
    repo_id="lj1995/GPT-SoVITS",
    allow_patterns=["gsv-v2final-pretrained/**"],
    local_dir=out,
    local_dir_use_symlinks=False,
    max_workers=4,
)
print("done")
