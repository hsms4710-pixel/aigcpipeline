const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const STRETCH = process.argv[2] || 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_anim/char_ailin_animated.stretch';
const OUT = process.argv[3] || 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_anim/preview';
const PY = 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/env/runtime/tools/see-through/venv/Scripts/python.exe';
const CLIPS = ['idle', 'walk', 'attack', 'hurt'];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  page.on('pageerror', e => console.log('PAGEERROR:', e.message.slice(0, 200)));
  for (let attempt = 1; attempt <= 3; attempt++) {
    try { await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded', timeout: 45000 }); break; }
    catch (e) { await page.waitForTimeout(4000); }
  }
  await page.waitForTimeout(4000);
  if (!(await page.evaluate(() => !!window.__ss))) throw new Error('bridge missing');

  await page.getByTitle('Load project').click({ force: true, timeout: 45000 });
  await page.waitForTimeout(2000);
  await page.locator('input[type=file]').first().setInputFiles(STRETCH);
  for (let i = 0; i < 25; i++) {
    await page.waitForTimeout(1000);
    const st0 = await page.evaluate(() => window.__ss.readState());
    if (st0.animations.length > 0) break;
  }
  // 适配视图（否则角色渲染在画布外）
  await page.getByTitle('Canvas Properties').click({ force: true, timeout: 45000 });
  await page.waitForTimeout(1200);
  const fitBtn = page.getByRole('button', { name: /Fit to minimum animation area/i });
  if (await fitBtn.count()) { await fitBtn.click({ force: true, timeout: 45000 }); console.log('fitted view'); }
  await page.waitForTimeout(1200);
  const state = await page.evaluate(() => window.__ss.readState());
  console.log('CLIPS:', state.animations.map(a => `${a.name}(${a.duration}ms)`).join(', '));
  const clips = state.animations.filter(a => CLIPS.includes(a.name.toLowerCase()));

  const gifSpecs = [];
  for (const clip of clips) {
    const dur = clip.duration || 2000;
    const frames = 14;
    const tmpDir = path.join(OUT, 'frames_' + clip.name);
    fs.mkdirSync(tmpDir, { recursive: true });
    for (let i = 0; i < frames; i++) {
      const t = Math.round((i / (frames - 1)) * dur);
      await page.evaluate(([n, ms]) => { window.__ss.setActiveClip(n); window.__ss.seek(ms); }, [clip.name, t]);
      await page.waitForTimeout(120);
      await page.screenshot({ path: path.join(tmpDir, `f${String(i).padStart(2, '0')}.png`) });
    }
    gifSpecs.push({
      name: clip.name,
      out: path.join(OUT, clip.name + '.gif'),
      files: Array.from({ length: frames }, (_, i) => path.join(tmpDir, `f${String(i).padStart(2, '0')}.png`)),
      delay: 8,
    });
    console.log('captured', frames, 'frames for', clip.name);
  }

  // Expression frames
  const expDir = path.join(OUT, 'frames_expressions');
  fs.mkdirSync(expDir, { recursive: true });
  const expDefs = [
    { name: 'happy', params: { 'Eye L Smile': 1, 'Eye R Smile': 1, 'Mouth Open': 0.4 } },
    { name: 'sad', params: { 'Brow L Y': 0.5, 'Brow R Y': 0.5, 'Mouth Open': 0.2 } },
    { name: 'angry', params: { 'Brow L Y': -0.5, 'Brow R Y': -0.5, 'Brow L Angle': 0.4, 'Brow R Angle': -0.4, 'Mouth Form': -0.6 } },
    { name: 'neutral', params: {} },
  ];
  const expFiles = [];
  for (const def of expDefs) {
    await page.evaluate((params) => Object.entries(params).forEach(([k, v]) => window.__ss.setParam(k, v)), def.params);
    await page.waitForTimeout(200);
    const p = path.join(expDir, def.name + '.png');
    await page.screenshot({ path: p });
    expFiles.push(p);
  }
  await page.evaluate(() => window.__ss.listParams().forEach(p => window.__ss.setParam(p.name, 0)));
  gifSpecs.push({ name: 'expressions', out: path.join(OUT, 'expressions.gif'), files: expFiles, delay: 900 });

  // Assemble GIFs via python reading a spec file (avoid shell quoting)
  const specFile = path.join(OUT, 'gif_spec.json');
  fs.writeFileSync(specFile, JSON.stringify(gifSpecs));
  const pyCode = `
import json, sys
from PIL import Image
specs = json.load(open(sys.argv[1], encoding='utf-8'))
for s in specs:
    imgs = [Image.open(f) for f in s['files']]
    imgs[0].save(s['out'], save_all=True, append_images=imgs[1:], duration=s['delay'], loop=0)
    print('GIF:', s['out'], imgs[0].size, len(imgs), 'frames')
`;
  const pyFile = path.join(OUT, 'make_gif.py');
  fs.writeFileSync(pyFile, pyCode);
  const r = spawnSync(PY, [pyFile, specFile], { encoding: 'utf8' });
  if (r.status === 0) console.log(r.stdout);
  else console.error('GIF FAILED:', (r.stderr || r.stdout || '').slice(0, 600));

  console.log('PREVIEW OUTPUT:', OUT);
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
