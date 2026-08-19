# -*- coding: utf-8 -*-
"""validate-anim.py — S3 动画质量门禁
输入：Spine ZIP 或 skeleton.json。检查：
  F1 必需 clip 存在（idle/walk/attack/hurt）
  F2 clip 时长 > 0
  F3 每 clip 有骨骼轨道（非空动画）
  F4 循环闭合：每轨道首尾关键帧值一致（rotate/scale/translate）
  F5 关节幅度：rotation 关键帧在 ±75° 内（生理范围）
  W1 缓动曲线：bezier 曲线关键帧占比（曲线平滑度）
退出码：0=OK(可警告)  1=FAIL
"""
import os, sys, json, zipfile, argparse

REQUIRED_CLIPS = ["idle", "walk", "attack", "hurt"]
MAX_ROT = 75.0

def load_skeleton(src):
    if os.path.isdir(src):
        sk = os.path.join(src, "skeleton.json")
        return json.load(open(sk, encoding="utf-8"))
    if src.lower().endswith(".zip"):
        with zipfile.ZipFile(src) as z:
            names = z.namelist()
            skn = "skeleton.json" if "skeleton.json" in names else next((n for n in names if n.endswith("skeleton.json")), None)
            if not skn:
                raise ValueError("ZIP 内无 skeleton.json")
            return json.loads(z.read(skn).decode("utf-8"))
    return json.load(open(src, encoding="utf-8"))

def _kf_value(kf):
    if "value" in kf:
        return kf["value"]
    if "x" in kf:
        return (kf["x"], kf["y"])
    return None

def _approx(a, b, eps=0.01):
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(_approx(x, y, eps) for x, y in zip(a, b))
    return abs(float(a) - float(b)) <= eps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="spine zip 或 skeleton.json 或目录")
    a = ap.parse_args()
    try:
        data = load_skeleton(a.src)
    except Exception as e:
        print(f"RESULT: FAIL (无法读取: {e})"); return 1

    anims = data.get("animations", {})
    fails, warns, info = [], [], []
    for c in REQUIRED_CLIPS:
        if c not in anims:
            fails.append(f"F1 缺必需 clip: {c}")
    if not anims:
        fails.append("F1 无任何动画 clip")
        print("RESULT: FAIL"); return 1

    total_kf = 0
    curved_kf = 0
    for cname, clip in anims.items():
        bones = clip.get("bones", {})
        dur = 0.0
        track_count = 0
        for bname, tracks in bones.items():
            for prop, kfs in tracks.items():
                if not kfs:
                    continue
                track_count += 1
                dur = max(dur, float(kfs[-1].get("time", 0.0)))
                total_kf += len(kfs)
                curved_kf += sum(1 for k in kfs if isinstance(k.get("curve"), list) and len(k["curve"]) == 4)
                vals = [_kf_value(k) for k in kfs]
                if len(vals) >= 2 and not _approx(vals[0], vals[-1]):
                    fails.append(f"F4 循环未闭合: clip={cname} {bname}.{prop} 首{vals[0]}≠尾{vals[-1]}")
                if prop == "rotate":
                    for k in kfs:
                        v = float(k.get("value", 0.0))
                        if abs(v) > MAX_ROT:
                            fails.append(f"F5 关节幅度过大: clip={cname} {bname} rotation={v}°（>±{MAX_ROT}°）")
        if cname in REQUIRED_CLIPS and dur <= 0:
            fails.append(f"F2 clip 时长无效: {cname}")
        if cname in REQUIRED_CLIPS and track_count == 0:
            fails.append(f"F3 空动画: {cname} 无骨骼轨道")
        info.append(f"{cname}: {dur:.2f}s / {track_count} 轨道")

    for i in info: print(" -", i)
    # M0-6/M0-9：动画应驱动肘/膝（质量提示，不阻断）
    if "attack" in anims:
        at_bones = anims["attack"].get("bones", {})
        if not any(b in at_bones for b in ("leftElbow", "rightElbow")):
            warns.append("W2 attack 未驱动肘骨（leftElbow/rightElbow）→ 整臂刚性挥击；建议 M0-6 肘驱动")
    if "walk" in anims:
        wk = anims["walk"].get("bones", {})
        max_knee = 0.0
        for kn in ("leftKnee", "rightKnee"):
            for k in wk.get(kn, {}).get("rotate", []):
                v = abs(float(k.get("value", 0.0)))
                if v > max_knee:
                    max_knee = v
        if max_knee < 40:
            warns.append(f"W3 walk 膝弯曲幅度不足（最大 {max_knee:.0f}° < 40°）→ 走路无屈膝；建议 M0-9")
        else:
            print(f"walk 膝弯曲最大 {max_knee:.0f}°")
    if total_kf > 0:
        curve_pct = 100.0 * curved_kf / total_kf
        if curve_pct < 30:
            warns.append(f"W1 缓动曲线占比低 {curve_pct:.0f}%（{curved_kf}/{total_kf}），动作可能生硬")
        else:
            print(f"缓动曲线: {curve_pct:.0f}% ({curved_kf}/{total_kf} 关键帧)")
    for f in fails: print("FAIL -", f)
    for w in warns: print("WARN -", w)
    if fails:
        print(f"RESULT: FAIL ({len(fails)} issues)")
        return 1
    print(f"RESULT: OK (warnings: {len(warns)})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
