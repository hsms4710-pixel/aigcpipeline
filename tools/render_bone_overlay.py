# -*- coding: utf-8 -*-
"""render_bone_overlay.py — 骨骼叠加截图：在角色图上画出骨骼/关节，供人工或视觉模型审查
用法: python render_bone_overlay.py <spine.zip> <out_dir>
输出: overlay_rest.png / overlay_walk_050.png / overlay_attack_080.png
"""
import zipfile, json, os, math, sys
import numpy as np
from PIL import Image, ImageDraw

# ---- 与 spine_player.gd 相同的驱动/枢轴/FK 逻辑 ----
DRIVER_PARTS = {
    "torso": ["topwear", "objects"],
    "head": ["back_hair", "front_hair", "headwear", "face", "mouth", "nose",
             "eyebrow-l", "eyebrow-r", "eyewhite-l", "eyewhite-r",
             "eyelash-l", "eyelash-r", "irides-l", "irides-r", "ears-l", "ears-r"],
    "leftLeg": ["legwear-l", "footwear-l"], "rightLeg": ["legwear-r", "footwear-r"],
    "leftArm": ["handwear-l"], "rightArm": ["handwear-r"],
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
        if a['time'] <= t <= b['time']:
            span = b['time'] - a['time']
            u = 0.0 if span <= 0 else (t - a['time']) / span
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
                if isinstance(a, dict) and 'vertices' in a:
                    vs = a['vertices']
                    xs = [v['x'] if isinstance(v, dict) else v for v in vs]
                    ys = [v['y'] if isinstance(v, dict) else float(v) for v in vs]
                    attachments[slot] = [min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)]
    def derive(bbox, mode):
        x0, y0, w, h = bbox
        if mode == 'top_center': return (x0 + w/2, y0)
        if mode == 'bottom_center': return (x0 + w/2, y0 + h)
        return (x0 + w/2, y0 + h/2)
    dp = dict(DRIVER_PARTS)
    if 'legwear-l-shin' in attachments:
        dp['leftLeg'] = ['legwear-l']; dp['leftKnee'] = ['legwear-l-shin']; dp['leftFootTarget'] = ['footwear-l']
    if 'legwear-r-shin' in attachments:
        dp['rightLeg'] = ['legwear-r']; dp['rightKnee'] = ['legwear-r-shin']; dp['rightFootTarget'] = ['footwear-r']
    if 'handwear-l-forearm' in attachments:
        dp['leftArm'] = ['handwear-l']; dp['leftElbow'] = ['handwear-l-forearm']
    if 'handwear-r-forearm' in attachments:
        dp['rightArm'] = ['handwear-r']; dp['rightElbow'] = ['handwear-r-forearm']
    pivots_ov = data.get('_pivots', {})
    drivers = {}
    for d, parts in dp.items():
        bbox = None
        for p in parts:
            if p not in attachments: continue
            b = attachments[p]
            if bbox is None:
                bbox = list(b)
            else:
                bbox = [min(bbox[0], b[0]), min(bbox[1], b[1]),
                        max(bbox[0]+bbox[2], b[0]+b[2])-min(bbox[0], b[0]),
                        max(bbox[1]+bbox[3], b[1]+b[3])-min(bbox[1], b[1])]
        if bbox is None: continue
        pivot = derive(bbox, PIVOT_MODE.get(d, 'center'))
        pov = pivots_ov.get(d)
        if isinstance(pov, (list, tuple)) and len(pov) == 2:
            pivot = (float(pov[0]), float(pov[1]))
        drivers[d] = {'parts': parts, 'pivot': pivot,
                      'parent': bones.get(d, {}).get('parent', '')}
    return drivers, slots, attachments, bones

def depth(drivers, d):
    n = 0; cur = d
    while cur in drivers:
        p = drivers[cur].get('parent', '')
        if p == '' or p not in drivers: break
        cur = p; n += 1
        if n > 32: break
    return n

def compute_world(drivers, anim):
    order = sorted(drivers.keys(), key=lambda d: depth(drivers, d))
    world = {}
    for d in order:
        a = anim.get(d, {'rot': 0.0, 'scale': (1,1), 'translate': (0,0)})
        rest = drivers[d]['pivot']; parent = drivers[d]['parent']
        rot = a['rot']; scale = a['scale']; tr = a['translate']
        if parent == '' or parent not in world:
            joint = (rest[0]+tr[0], rest[1]+tr[1])
        else:
            pw = world[parent]; pj, pr, ps, prest = pw['joint'], pw['rot'], pw['scale'], pw['rest']
            off = (rest[0]-prest[0], rest[1]-prest[1])
            rd = math.radians(pr); c, s = math.cos(rd), math.sin(rd)
            joint = (pj[0] + (off[0]*c - off[1]*s)*ps[0] + tr[0], pj[1] + (off[0]*s + off[1]*c)*ps[1] + tr[1])
            rot = pr + rot; scale = (ps[0]*scale[0], ps[1]*scale[1])
        world[d] = {'joint': joint, 'rot': rot, 'scale': scale, 'rest': rest}
    return world

def sample_clip(drivers, clip, t):
    anim = {}
    for d in drivers:
        tr = clip.get('bones', {}).get(d, {})
        rot = sample(tr.get('rotate', []), t) or 0.0
        s = sample(tr.get('scale', []), t)
        scale = (s[0], s[1]) if isinstance(s, (tuple, list)) else (1.0, 1.0)
        tv = sample(tr.get('translate', []), t)
        translate = (tv[0], tv[1]) if isinstance(tv, (tuple, list)) else (0.0, 0.0)
        anim[d] = {'rot': rot, 'scale': scale, 'translate': translate}
    return anim

def render_with_bones(data, imgs, drivers, slots, clip, t, out_path, W=1280, H=1280):
    anim = sample_clip(drivers, clip, t)
    world = compute_world(drivers, anim)
    driver_of = {}
    for d in drivers:
        for p in drivers[d]['parts']:
            driver_of[p] = d
    canvas = Image.new('RGBA', (W, H), (24, 24, 32, 255))
    for s in slots:
        name = s.get('name', '')
        if name not in imgs: continue
        tex = imgs[name]
        d = driver_of.get(name, '')
        if d == '' or d not in world:
            canvas.alpha_composite(tex); continue
        w = world[d]; joint, rot, scale, rest = w['joint'], w['rot'], w['scale'], w['rest']
        t2 = tex.rotate(-math.degrees(rot), center=rest, resample=Image.BICUBIC, expand=False)
        out = Image.new('RGBA', (W, H), (0,0,0,0))
        out.alpha_composite(t2, (int(round(joint[0]-rest[0])), int(round(joint[1]-rest[1]))))
        canvas.alpha_composite(out)
    # 画骨骼
    draw = ImageDraw.Draw(canvas, 'RGBA')
    for d in drivers:
        w = world[d]; parent = drivers[d]['parent']
        j = w['joint']
        if parent and parent in world:
            pj = world[parent]['joint']
            draw.line([pj, j], fill=(255, 60, 60, 255), width=5)
            # 中间骨段
            mid = ((pj[0]+j[0])/2, (pj[1]+j[1])/2)
            draw.ellipse([mid[0]-5, mid[1]-5, mid[0]+5, mid[1]+5], fill=(255, 180, 60, 255))
        # 关节圆
        r = 9
        draw.ellipse([j[0]-r, j[1]-r, j[0]+r, j[1]+r], fill=(60, 255, 120, 220), outline=(0, 0, 0, 255), width=2)
        draw.text((j[0]+12, j[1]-14), d, fill=(255, 255, 255, 255))
    canvas.save(out_path)
    return canvas, world

if __name__ == '__main__':
    zip_path = sys.argv[1]; out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    data, imgs = load_zip(zip_path)
    drivers, slots, attachments, bones = build_drivers(data, imgs)
    print('drivers:', sorted(drivers.keys()))
    anims = data.get('animations', {})
    # rest
    c, world = render_with_bones(data, imgs, drivers, slots, {}, 0.0, os.path.join(out_dir, 'overlay_rest.png'))
    print('saved overlay_rest.png')
    for clip_name, t, fn in [('walk', 0.5, 'overlay_walk_050.png'), ('attack', 0.8, 'overlay_attack_080.png')]:
        if clip_name in anims:
            render_with_bones(data, imgs, drivers, slots, anims[clip_name], t, os.path.join(out_dir, fn))
            print('saved', fn)
    # 几何校验：关节落在角色身体区域
    alpha = np.asarray(imgs['topwear'])[:, :, 3] > 10
    body_ok = {}
    for jk in ['leftArm','rightArm','leftLeg','rightLeg','leftElbow','rightElbow','leftKnee','rightKnee','leftFootTarget','rightFootTarget']:
        if jk in world:
            x, y = int(world[jk]['joint'][0]), int(world[jk]['joint'][1])
            body_ok[jk] = (x, y, bool(alpha[y, x]) if 0 <= x < 1280 and 0 <= y < 1280 else False)
    print('GEOM:', json.dumps(body_ok, ensure_ascii=False))
    print('OK')