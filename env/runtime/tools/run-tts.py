import os, sys, time
import numpy as np
gpt_root = r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路\env\runtime\tools\GPT-SoVITS"
os.chdir(gpt_root)
sys.path.insert(0, gpt_root)
sys.path.insert(0, os.path.join(gpt_root, "GPT_SoVITS"))

import torch, librosa, torchaudio
def _load_fallback(path, out=None, normalization=None, channels_first=True):
    y, sr = librosa.load(path, sr=None, mono=False)
    if y.ndim == 1:
        y = y[None, :]
    return torch.from_numpy(y).float(), sr
torchaudio.load = _load_fallback
print("torchaudio.load patched -> librosa")

from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

cfg = TTS_Config({"custom": {
    "device": "cpu", "is_half": False, "version": "v1",
    "t2s_weights_path": "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
    "vits_weights_path": "GPT_SoVITS/pretrained_models/s2G488k.pth",
    "cnhuhbert_base_path": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
    "bert_base_path": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
}})
print("device:", cfg.device, "is_half:", cfg.is_half, "version:", cfg.version)
tts = TTS(cfg)

params = {
    "text": "我会在这个世界留下我的传说。",
    "text_lang": "zh",
    "ref_audio_path": r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路\env\runtime\logs\ref_voice.wav",
    "prompt_text": "你好，我是来自异世界的旅人。我曾跨越无数山海，只为寻找一个能听懂我故事的人。",
    "prompt_lang": "zh",
    "top_k": 5, "top_p": 1.0, "temperature": 1.0,
    "text_split_method": "cut5", "batch_size": 1, "speed_factor": 1.0,
    "streaming_mode": False, "seed": -1, "media_type": "wav",
}
t0 = time.time()
gen = tts.run(params)
sr, audio = next(gen)
print("inference time: %.1fs, sr=%s" % (time.time()-t0, sr))
out = r"C:\Users\26046\Desktop\inerview\research\角色AIGC与AI-NPC全链路\env\runtime\logs\tts_output_v1.wav"
wav_data = audio[0] if isinstance(audio, (list, tuple)) else audio
import scipy.io.wavfile as wavio
wavio.write(out, sr, np.asarray(wav_data).astype(np.float32))
print("saved:", out, os.path.getsize(out), "bytes")
