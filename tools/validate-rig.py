# -*- coding: utf-8 -*-
"""validate-rig.py — S2 绑骨质量门禁
输入：Spine ZIP 或 skeleton.json。检查：
  F1 骨骼可解析（bones 非空）
  F2 无重复骨名
  F3 标准骨架层级关键骨存在（pelvis/spine/chest/neck/head 或 rig_root/torso 等）
  F4 槽位引用的骨骼都在 bones 数组中（抓 StretchyStudio Warp 骨缺失缺陷）
  F5 IK 约束数量 > 0（脚部 ground-lock / 肘膝自然弯曲的工业要求）
  W1 weighted mesh（weights[]）是否存在（可变形部件弯曲不撕裂）
  W2 骨骼枢轴坐标有效（x/y 存在）
退出码：0=OK(可警告)  1=FAIL
"""
import os, sys, json, zipfile, argparse, tempfile

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="spine zip 或 skeleton.json 或含 skeleton.json 的目录")
    a = ap.parse_args()
    try:
        data = load_skeleton(a.src)
    except Exception as e:
        print(f"RESULT: FAIL (无法读取: {e})"); return 1

    fails, warns = [], []
    bones = data.get("bones", [])
    slots = data.get("slots", [])
    ik = data.get("ik", [])
    if not bones:
        fails.append("F1 无骨骼（bones 空）")
    else:
        names = [b.get("name", "") for b in bones]
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:
            fails.append(f"F2 重复骨名: {dup}")
        # F3 标准层级关键骨
        key_bones = ["pelvis", "spine", "chest", "neck", "head", "torso", "rig_root", "leftArm", "rightArm", "leftLeg", "rightLeg"]
        have = [k for k in key_bones if k in names]
        missing = [k for k in key_bones if k not in names]
        if len(have) < 4:
            fails.append(f"F3 标准骨架关键骨不足（有 {have}，缺 {missing}）")
        # F4 槽位引用的骨存在
        if slots:
            slot_bones = set(s.get("bone", "") for s in slots)
            missing_bones = sorted(sb for sb in slot_bones if sb and sb not in names)
            if missing_bones:
                fails.append(f"F4 槽位引用不存在的骨骼: {missing_bones[:10]}（StretchyStudio Warp 骨未导出）")
        # F6 死骨检查：关节骨（elbow/knee/footTarget）必须被槽位引用，否则无法驱动弯曲
        joint_bones = ["leftElbow", "rightElbow", "leftKnee", "rightKnee", "leftFootTarget", "rightFootTarget"]
        refd = set(s.get("bone", "") for s in slots)
        dead = [jb for jb in joint_bones if jb in names and jb not in refd]
        if dead:
            fails.append(f"F6 关节骨未被槽位引用（死骨，无法驱动弯曲）: {dead}")
    if not ik:
        fails.append("F5 无 IK 约束（脚会滑、膝肘不自然）")
    else:
        print(f"IK 约束: {len(ik)} 条")
    # W1 weighted mesh
    weighted = 0
    for skin in data.get("skins", []):
        for slot in skin.get("attachments", {}).values():
            for att in slot.values():
                if att.get("type") == "mesh" and att.get("weights"):
                    weighted += 1
    if weighted == 0:
        warns.append("W1 无 weighted mesh（弯曲处易撕裂；建议 M0-3 加权重）")
    # W2 骨骼枢轴
    no_pivot = [b.get("name") for b in bones if "x" not in b and "y" not in b]
    if no_pivot:
        warns.append(f"W2 {len(no_pivot)} 个骨骼无枢轴坐标: {no_pivot[:6]}")
    # W3 手臂拆分完整性：有 handwear 但无 forearm → 刚性手臂（肘不能弯曲）
    arm_slots = [s.get("name", "") for s in slots if "handwear" in s.get("name", "")]
    has_forearm = any("forearm" in s for s in arm_slots)
    if arm_slots and not has_forearm:
        warns.append("W3 手臂未拆分（无 forearm 部件）→ 肘不能弯曲；建议跑 split-spine-arm.py")

    print(f"骨骼 {len(bones)} | 槽位 {len(slots)} | IK {len(ik)} | weighted mesh {weighted}")
    for f in fails: print("FAIL -", f)
    for w in warns: print("WARN -", w)
    if fails:
        print(f"RESULT: FAIL ({len(fails)} issues)")
        return 1
    print(f"RESULT: OK (warnings: {len(warns)})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
