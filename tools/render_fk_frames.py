# -*- coding: utf-8 -*-
"""render_fk_frames.py — 用与 spine_player.gd 相同的 FK 数学渲染动画帧（验证/预览）
输出: <out_dir>/<clip>_<t>xx.png；并校验肘/膝关节区域内容连续（不撕裂）
"""
import zipfile, json, os, math, sys
import numpy as np
from PIL import Image

DRIVER_PARTS = {
    "torso": ["topwear", "objects"],
    "head": ["back_hair", "front_hair", "headwear", "face", "mouth", "nose",
             "eyebrow-l", "eyebrow-r", "eyewhite-l", "eyewhite-r",
             "eyelash-l", "eyelash-r", "irides-l", "irides-r", "ears-l", "ears-r"],
    "leftLeg": ["legwear-l", "footwear-l"],
    "rightLeg": ["legwear-r", "footwear-r"],
    "leftArm": ["handwear-l"],
    "rightArm": ["handwear-r"],
}
PIVOT_MODE = {
    "torso": "bottom_center", "head": "bottom_center",
    "leftLeg": "top_center", "rightLeg": "top_center",
    "leftArm": "top_center", "rightArm": "top_center",
    "leftElbow": "top_center", "rightElbow": "top_center",
    "leftKnee": "top_center", "rightKnee": "top_center",
    "leftFootTarget": "top_center", "rightFootTarget": "top_center",
}

def load_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        skn = next(n for n in z.namelist() if n.endswith('skeleton.json'))
        data = json.loads(z.read(skn).decode('utf-8'))
        imgs = {}
        for n in z.namelist():
            if n.endswith('.png'):
                imgs[os.path.splitext(os.path.basename(n))[0]] = Image.open(z.open(n)).convert('RGBA')
    return data, imgs

def bezier(u, x1, y1, x2, y2):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(16):
        mid = (lo + hi) / 2
        omt = 1 - mid
        x = 3*omt*omt*mid*x1 + 3*omt*mid*mid*x2 + mid*mid*mid
        if x < u: lo = mid
        else: hi = mid
    tt = (lo + hi) / 2
    omt = 1 - tt
    return 3*omt*omt*tt*y1 + 3*omt*tt*tt*y2 + tt*tt*tt

def sample(track, t):
    if not track: return None
    if t <= track[0]['time']: return track[0].get('value', 0.0)
    if t >= track[-1]['time']: return track[-1].get('value', 0.0)
    for i in range(len(track)-1):
        a, b = track[i], track[i+1]
        ta, tb = a['time'], b['time']
        if ta <= t <= tb:
            span = tb - ta
            u = 0.0 if span <= 0 else (t - ta) / span
            eu = u
            curve = a.get('curve')
            if isinstance(curve, list) and len(curve) == 4:
                eu = bezier(u, curve[0], curve[1], curve[2], curve[3])
            va, vb = a.get('value', 0.0), b.get('value', 0.0)
            return va + (vb - va) * eu
    return track[0].get('value', 0.0)

def build_drivers(data, imgs):
    bones = {b['name']: b for b in data.get('bones', [])}
    slots = data.get('slots', [])
    attachments = {}
    for skin in data.get('skins', []):
        for slot, atts in skin.get('attachments', {}).items():
            for aname, a in atts.items():
                if isinstance(a, dict) and 'bbox' in a:
                    attachments[slot] = a['bbox']
                elif isinstance(a, dict) and 'vertices' in a:
                    vs = a['vertices']
                    xs = [v['x'] if isinstance(v, dict) else v for v in vs]
                    ys = [v['y'] if isinstance(v, dict) else float(v) for v in vs]
                    attachments[slot] = [min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)]
    def derive(bbox, mode):
        x0, y0, w, h = bbox
        if mode == 'top_center': return (x0 + w/2, y0)
        if mode == 'bottom_center': return (x0 + w/2, y0 + h)
        return (x0 + w/2, y0 + h/2)
    driver_parts = dict(DRIVER_PARTS)
    if 'legwear-l-shin' in attachments:
        driver_parts['leftLeg'] = ['legwear-l']
        driver_parts['leftKnee'] = ['legwear-l-shin']
        driver_parts['leftFootTarget'] = ['footwear-l']
    if 'legwear-r-shin' in attachments:
        driver_parts['rightLeg'] = ['legwear-r']
        driver_parts['rightKnee'] = ['legwear-r-shin']
        driver_parts['rightFootTarget'] = ['footwear-r']
    if 'handwear-l-forearm' in attachments:
        driver_parts['leftArm'] = ['handwear-l']
        driver_parts['leftElbow'] = ['handwear-l-forearm']
    if 'handwear-r-forearm' in attachments:
        driver_parts['rightArm'] = ['handwear-r']
        driver_parts['rightElbow'] = ['handwear-r-forearm']
    pivots_ov = data.get('_pivots', {})
    drivers = {}
    for d, parts in driver_parts.items():
        bbox = None
        for p in parts:
            if p in attachments:
                bbox = attachments[p] if bbox is None else [min(bbox[0], attachments[p][0]), min(bbox[1], attachments[p][1]), max(bbox[0]+bbox[2], attachments[p][0]+attachments[p][2])-min(bbox[0], attachments[p][0]), max(bbox[1]+bbox[3], attachments[p][1]+attachments[p][3])-min(bbox[1], attachments[p][1])]
        if bbox is None:
            continue
        pivot = derive(bbox, PIVOT_MODE.get(d, 'center'))
        pov = pivots_ov.get(d)
        if isinstance(pov, (list, tuple)) and len(pov) == 2:
            pivot = (float(pov[0]), float(pov[1]))
        parent = bones.get(d, {}).get('parent', '')
        drivers[d] = {'parts': parts, 'pivot': pivot, 'parent': parent}
    return drivers, slots, attachments

def compute_world(drivers, anim):
    order = sorted(drivers.keys(), key=lambda d: depth(drivers, d))
    world = {}
    for d in order:
        a = anim.get(d, {'rot': 0.0, 'scale': (1, 1), 'translate': (0, 0)})
        rest = drivers[d]['pivot']
        parent = drivers[d]['parent']
        rot = a['rot']; scale = a['scale']; tr = a['translate']
        if parent == '' or parent not in world:
            joint = (rest[0] + tr[0], rest[1] + tr[1])
        else:
            pw = world[parent]
            pj, pr, ps, prest = pw['joint'], pw['rot'], pw['scale'], pw['rest']
            off = (rest[0] - prest[0], rest[1] - prest[1])
            rd = math.radians(pr)
            c, s = math.cos(rd), math.sin(rd)
            rotx = (off[0]*c - off[1]*s) * ps[0]
            roty = (off[0]*s + off[1]*c) * ps[1]
            joint = (pj[0] + rotx + tr[0], pj[1] + roty + tr[1])
            rot = pr + rot
            scale = (ps[0]*scale[0], ps[1]*scale[1])
        world[d] = {'joint': joint, 'rot': rot, 'scale': scale, 'rest': rest}
    return world

def depth(drivers, d):
    n = 0
    cur = d
    while cur in drivers:
        p = drivers[cur].get('parent', '')
        if p == '' or p not in drivers: break
        cur = p; n += 1
        if n > 32: break
    return n

def sample_clip(drivers, clip, t):
    anim = {}
    bones_t = clip.get('bones', {})
    for d in drivers:
        tr = bones_t.get(d, {})
        rot = sample(tr.get('rotate', []), t) or 0.0
        s = sample(tr.get('scale', []), t)
        scale = (s[0], s[1]) if isinstance(s, (tuple, list)) else (1.0, 1.0)
        trv = sample(tr.get('translate', []), t)
        translate = (trv[0], trv[1]) if isinstance(trv, (tuple, list)) else (0.0, 0.0)
        anim[d] = {'rot': rot, 'scale': scale, 'translate': translate}
    return anim

def render_frame(data, imgs, drivers, slots, clip, t, out_path, W=1280, H=1280):
    anim = sample_clip(drivers, clip, t)
    world = compute_world(drivers, anim)
    driver_of = {}
    for d in drivers:
        for p in drivers[d]['parts']:
            driver_of[p] = d
    canvas = Image.new('RGBA', (W, H), (24, 24, 32, 255))  # 深灰底，部件清晰可见（非纯黑）
    for s in slots:
        name = s.get('name', '')
        if name not in imgs:
            continue
        tex = imgs[name]
        d = driver_of.get(name, '')
        if d == '' or d not in world:
            canvas.alpha_composite(tex)
            continue
        w = world[d]
        joint, rot, scale, rest = w['joint'], w['rot'], w['scale'], w['rest']
        ang = math.radians(rot)
        c, s = math.cos(ang), math.sin(ang)
        tex2 = tex
        if scale != (1.0, 1.0):
            tex2 = tex2.resize((int(tex.width*scale[0]), int(tex.height*scale[1])), Image.LANCZOS)
        # 旋转：把 tex2 以 rest 为枢轴旋转 ang，然后平移到 joint
        t2 = tex2.rotate(-math.degrees(ang), center=(rest[0], rest[1]), resample=Image.BICUBIC, expand=False)
        # 平移：joint - rest
        ox = joint[0] - rest[0]
        oy = joint[1] - rest[1]
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.alpha_composite(t2, (int(round(ox)), int(round(oy))))
        canvas.alpha_composite(out)
    canvas.save(out_path)
    return canvas

if __name__ == '__main__':
    zip_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    data, imgs = load_zip(zip_path)
    drivers, slots, attachments = build_drivers(data, imgs)
    print('drivers:', sorted(drivers.keys()))
    anims = data.get('animations', {})
    joints_out = {}
    for clip_name, times in [('walk', [0.0, 0.5, 1.0, 1.5]), ('attack', [0.0, 0.4, 0.8, 1.2])]:
        if clip_name not in anims:
            print('skip', clip_name); continue
        clip = anims[clip_name]
        joints_out[clip_name] = {}
        for t in times:
            p = os.path.join(out_dir, f'{clip_name}_{int(t*100):03d}.png')
            render_frame(data, imgs, drivers, slots, clip, t, p)
            anim = sample_clip(drivers, clip, t)
            world = compute_world(drivers, anim)
            pose = {}
            for jk in ['leftElbow', 'rightElbow', 'leftKnee', 'rightKnee', 'leftFootTarget', 'rightFootTarget']:
                if jk in world:
                    pose[jk] = world[jk]['joint']
            joints_out[clip_name][str(t)] = pose
            print('saved', p)
    with open(os.path.join(out_dir, 'joints.json'), 'w', encoding='utf-8') as f:
        json.dump(joints_out, f, ensure_ascii=False)
    print('OK')