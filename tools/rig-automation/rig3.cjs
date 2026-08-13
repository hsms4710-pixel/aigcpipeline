const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');
const PSD = 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_v10/layered/char_ailin_v10_layered.psd';
const b64 = fs.readFileSync(PSD).toString('base64');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 250)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message.slice(0, 250)));
  const body = async () => (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 900);

  await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3500);

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

  const nextBtn = page.getByRole('button', { name: /Next: Adjust Joints/i }).first();
  if (await nextBtn.count()) { await nextBtn.click(); console.log('clicked Next: Adjust Joints'); }
  await page.waitForTimeout(2000);
  console.log('STEP adjust:', await body());

  const aiBtn = page.getByRole('button', { name: /AI Auto-Rig/i }).first();
  if (await aiBtn.count()) { await aiBtn.click(); console.log('clicked AI Auto-Rig'); }
  await page.waitForTimeout(2000);
  console.log('STEP dwpose:', await body());

  const dl = page.getByRole('button', { name: /^Download$/i }).first();
  if (await dl.count()) { await dl.click(); console.log('clicked Download (local onnx)'); } else {
    // maybe text is 'Working…' already or button label differs
    const allBtns = await page.getByRole('button').allInnerTexts();
    console.log('ALL BUTTONS:', JSON.stringify(allBtns));
  }
  // Poll rig status
  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(10000);
    const t = await body();
    if (!t.includes('Loading ONNX') && !t.includes('Building rig') && !t.includes('Detecting')) { console.log(`poll ${i}:`, t); }
  }
  console.log('CONSOLE ERRORS:', JSON.stringify(errors, null, 2));
  await page.screenshot({ path: 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/env/runtime/tools/stretchy-studio/smoke/rigged3.png' });
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
