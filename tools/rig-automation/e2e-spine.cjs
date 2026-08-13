const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const PSD = 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_v10/layered/char_ailin_v10_layered.psd';
const OUT = 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_rigged';
const b64 = fs.readFileSync(PSD).toString('base64');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1680, height: 1050 }, acceptDownloads: true });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message.slice(0, 200)));
  const body = async () => (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 600);

  await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3500);

  // Drop PSD
  const canvas = page.locator('canvas').first();
  const box = await canvas.boundingBox();
  await page.evaluate(async ({ b64, box }) => {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const dt = new DataTransfer();
    dt.items.add(new File([bytes], 'char_ailin_v10_layered.psd', { type: 'application/octet-stream' }));
    const el = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
    ['dragenter', 'dragover', 'drop'].forEach(t => el.dispatchEvent(new DragEvent(t, { bubbles: true, cancelable: true, dataTransfer: dt })));
  }, { b64, box });
  await page.waitForTimeout(2500);

  await page.getByRole('button', { name: /Continue/i }).first().click();
  await page.waitForTimeout(2000);
  await page.getByRole('button', { name: /Next: Adjust Joints/i }).first().click();
  await page.waitForTimeout(2000);
  await page.getByRole('button', { name: /AI Auto-Rig/i }).first().click();
  await page.waitForTimeout(2000);
  await page.getByRole('button', { name: /^Download$/i }).first().click();
  console.log('DWPose downloading…');
  // Wait for rig to complete (dialog closes, back to adjust step)
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(8000);
    const t = await page.locator('body').innerText();
    if (!t.includes('Load DWPose model') && !t.includes('Working…')) { console.log(`rig done after ~${(i+1)*8}s`); break; }
  }

  const paramsBtn = page.getByRole('button', { name: /Next: Setup Parameters/i }).first();
  if (await paramsBtn.count()) { await paramsBtn.click(); console.log('clicked Next: Setup Parameters'); }
  await page.waitForTimeout(6000);
  console.log('LIVERIG STEP:', (await body()).includes('Step 4') ? 'OK Step4 visible' : await body());

  const doneBtn = page.getByRole('button', { name: /Done/i }).first();
  if (await doneBtn.count()) { await doneBtn.click(); console.log('clicked Done'); }
  // Wait for mesh generation / editor
  await page.waitForTimeout(20000);
  console.log('AFTER DONE:', await body());

  // Open Export
  const exportBtn = page.getByTitle('Export frames');
  if (await exportBtn.count()) { await exportBtn.click(); console.log('opened Export modal'); }
  await page.waitForTimeout(2500);

  // Select Spine from type dropdown
  const typeTrigger = page.locator('[role="combobox"]').first();
  if (await typeTrigger.count()) {
    await typeTrigger.click();
    await page.waitForTimeout(1000);
    const spineOpt = page.locator('[role="option"]', { hasText: 'Spine' }).first();
    if (await spineOpt.count()) { await spineOpt.click(); console.log('selected Spine'); }
    await page.waitForTimeout(1000);
  }

  // Click Export (capture download)
  const dlPromise = page.waitForEvent('download', { timeout: 60000 }).catch(() => null);
  const expBtn = page.getByRole('button', { name: /^Export$/i }).first();
  if (await expBtn.count()) { await expBtn.click(); console.log('clicked Export'); }
  const dl = await dlPromise;
  if (dl) {
    const dest = path.join(OUT, 'spine_export.zip');
    await dl.saveAs(dest);
    console.log('DOWNLOADED:', dest, fs.statSync(dest).size, 'bytes');
  } else {
    console.log('NO DOWNLOAD captured');
  }
  console.log('CONSOLE ERRORS:', JSON.stringify(errors, null, 2));
  await page.screenshot({ path: path.join(OUT, 'rigged_view.png') });
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
