# -*- coding: utf-8 -*-
"""fix-rig.py — S2 绑骨后处理：标准骨架模板修复（M0-2 + M0-3 之 IK 部分）
修复项：
  F1 去重骨（保留 DWPose 子树 knee / 小偏移 elbow，elbow 重挂到 leftArm/rightArm）
  F2 补缺失 Warp 骨（槽位引用但不在 bones 数组 → identity 骨）
  F3 加脚部 IK（leftFootTarget/rightFootTarget 挂 knee 下 + ik[]）
用法: python fix-rig.py <spine.zip|skeleton.json|目录> [--out 输出.json]
"""
import os, sys, json, zipfile, argparse

def load(src):
    if os.path.isdir(src):
        return json.load(open(os.path.join(src, "skeleton.json"), encoding="utf-8")), None
    if str(src).lower().endswith(".zip"):
        with zipfile.ZipFile(src) as z:
            names = z.namelist()
            sk = "skeleton.json" if "skeleton.json" in names else next((n for n in names if n.endswith("skeleton.json")), None)
            if not sk:
                raise ValueError("ZIP 内无 skeleton.json")
            return json.loads(z.read(sk).decode("utf-8")), sk
    return json.load(open(src, encoding="utf-8")), None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data, zip_sk_name = load(a.src)
    bones = data.get("bones", [])
    slots = data.get("slots", [])
    anims = data.get("animations", {})
    removed, added = [], []

    # ── F1 去重骨 ──────────────────────────────────────────────────────
    from collections import Counter
    names = [b.get("name", "") for b in bones]
    dup_names = [n for n, c in Counter(names).items() if c > 1]
    slot_bones = {s.get("bone", "") for s in slots if s.get("bone")}
    anim_bones = set()
    for clip in anims.values():
        anim_bones.update(clip.get("bones", {}).keys())
    referenced = slot_bones | anim_bones

    # 对每个重名组选一个保留：优先 DWPose 子树（父在 leftLeg/rightLeg），其次小偏移（elbow）
    chosen_ids = set()
    for n in dup_names:
        group = [b for b in bones if b.get("name") == n]
        pref = next((b for b in group if b.get("parent") in ("leftLeg", "rightLeg")), None)
        if pref is None:
            pref = min(group, key=lambda b: abs(float(b.get("x", 0))) + abs(float(b.get("y", 0))))
        chosen_ids.add(id(pref))
    final = []
    for b in bones:
        if b.get("name") in dup_names and id(b) not in chosen_ids:
            removed.append(b.get("name")); continue
        final.append(b)
    data["bones"] = final
    bone_names = [b.get("name", "") for b in final]

    # ── F2 补缺失 Warp 骨 ─────────────────────────────────────────────
    missing = sorted(sb for sb in slot_bones if sb not in bone_names)
    for mb in missing:
        data["bones"].append({"name": mb, "parent": "root", "x": 0, "y": 0, "rotation": 0})
        added.append(mb)

    # 肘骨重挂到手臂（标准 FK）
    for b in data["bones"]:
        if b.get("name") == "leftElbow" and b.get("parent") != "leftArm":
            b["parent"] = "leftArm"
        elif b.get("name") == "rightElbow" and b.get("parent") != "rightArm":
            b["parent"] = "rightArm"

    # ── F3 脚部 IK ────────────────────────────────────────────────────
    ik = data.get("ik") or []
    have_ik = {i.get("name") for i in ik}
    for leg, knee, target in [("leftLeg", "leftKnee", "leftFootTarget"),
                              ("rightLeg", "rightKnee", "rightFootTarget")]:
        if leg not in bone_names:
            continue
        if target not in have_ik:
            if all(b.get("name") != target for b in data["bones"]):
                data["bones"].append({"name": target, "parent": knee, "x": 0, "y": -140, "rotation": 0})
            ik.append({"name": target, "order": len(ik), "bones": [leg, knee], "target": target,
                       "bendPositive": True, "mix": 1.0, "compress": 1.0, "stretch": 1.0})
            have_ik.add(target)
    data["ik"] = ik

    # ── F4 动画循环闭合（首尾关键帧一致，防脚滑/漂移）────────────────
    closed = 0
    for clip in data.get("animations", {}).values():
        dur = 0.0
        for bname, tracks in clip.get("bones", {}).items():
            for prop, kfs in tracks.items():
                if kfs:
                    dur = max(dur, float(kfs[-1].get("time", 0.0)))
        for bname, tracks in clip.get("bones", {}).items():
            for prop, kfs in tracks.items():
                if len(kfs) < 2:
                    continue
                first = kfs[0]
                last = kfs[-1]
                def _close():
                    if "value" in first and "value" in last:
                        if last["value"] != first["value"]:
                            last["value"] = first["value"]; return True
                    elif "x" in first and "x" in last:
                        if last["x"] != first["x"] or last["y"] != first["y"]:
                            last["x"] = first["x"]; last["y"] = first["y"]; return True
                    return False
                if _close():
                    closed += 1
                # 末帧不在 clip 末尾则补一个闭合帧
                if abs(float(last.get("time", 0.0)) - dur) > 0.001 and dur > 0:
                    kf = dict(first)
                    kf["time"] = dur
                    kfs.append(kf)
                    closed += 1
    if closed:
        print(f"动画循环闭合修正: {closed} 条轨道")

    # ── 输出 ──────────────────────────────────────────────────────────
    is_zip = str(a.src).lower().endswith(".zip")
    if a.out:
        out = a.out
    elif is_zip:
        base = os.path.splitext(os.path.basename(a.src))[0]
        out = os.path.join(os.path.dirname(os.path.abspath(a.src)), base + "_fixed_spine.zip")
    else:
        base = os.path.splitext(os.path.basename(a.src))[0]
        out = os.path.join(os.path.dirname(os.path.abspath(a.src)), base + "_fixed.skeleton.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if is_zip:
        # 重建 zip：保留原文件，替换 skeleton.json 为修复版
        import tempfile
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(a.src) as z:
            z.extractall(tmp)
        sk_path = os.path.join(tmp, zip_sk_name or "skeleton.json")
        with open(sk_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp):
                for fn in files:
                    p = os.path.join(root, fn)
                    z.write(p, os.path.relpath(p, tmp))
    else:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    print(f"去重骨: {removed if removed else '无'}")
    print(f"补缺失骨: {added if added else '无'}")
    print(f"IK 约束: {len(data.get('ik', []))} 条 | 总骨骼: {len(data['bones'])}")
    print(f"输出: {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
