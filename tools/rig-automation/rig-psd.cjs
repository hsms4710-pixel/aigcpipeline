const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const PSD = process.argv[2];
const OUT = process.argv[3] || 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_rigged';
if (!PSD || !fs.existsSync(PSD)) { console.error('USAGE: node rig-psd.cjs <psd> [outdir]'); process.exit(1); }
const b64 = fs.readFileSync(PSD).toString('base64');
const name = path.basename(PSD).replace(/\.psd$/i, '');

async function dropPsd(page) {
  const canvas = page.locator('canvas').first();
  await canvas.waitFor({ state: 'attached', timeout: 30000 }).catch(() => {});
  const box = await canvas.boundingBox();
  if (!box) throw new Error('canvas boundingBox null');
  await page.evaluate(async ({ b64, box }) => {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const dt = new DataTransfer();
    dt.items.add(new File([bytes], 'import.psd', { type: 'application/octet-stream' }));
    const el = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
    if (!el) throw new Error('no element at center');
    ['dragenter', 'dragover', 'drop'].forEach(t => el.dispatchEvent(new DragEvent(t, { bubbles: true, cancelable: true, dataTransfer: dt })));
  }, { b64, box });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1680, height: 1050 }, acceptDownloads: true });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message.slice(0, 200)));

  // Import with retry
  let imported = false;
  for (let attempt = 1; attempt <= 4; attempt++) {
    try {
      await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(4000);
      await dropPsd(page);
      // wait for review modal
      for (let i = 0; i < 15; i++) {
        await page.waitForTimeout(1500);
        const t = (await page.locator('body').innerText()) || '';
        if (t.includes('layers matched')) { imported = true; break; }
      }
      if (imported) break;
      console.log(`import attempt ${attempt}: no review modal, retry`);
    } catch (e) {
      console.log(`import attempt ${attempt} error: ${e.message.split('\n')[0]}`);
      await page.waitForTimeout(3000);
    }
  }
  if (!imported) { console.log('IMPORT FAILED after retries'); await browser.close(); process.exit(1); }

  const match = ((await page.locator('body').innerText()) || '').match(/(\d+) of (\d+) layers matched/);
  console.log('LAYER MATCH:', match ? match[0] : 'unknown');

  await page.getByRole('button', { name: /Continue/i }).first().click({ force: true, timeout: 45000 });
  await page.waitForTimeout(3000);
  const nextBtn = page.getByRole('button', { name: /Next: Adjust Joints/i }).first();
  if (!(await nextBtn.count())) {
    // maybe split dialog or different step — dump and skip if needed
    console.log('NOTE: no Next:AdjustJoints; body:', (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 300));
  } else {
    await nextBtn.click({ force: true, timeout: 45000 });
  }
  await page.waitForTimeout(2500);

  const aiBtn = page.getByRole('button', { name: /AI Auto-Rig/i }).first();
  if (await aiBtn.count()) { await aiBtn.click({ force: true, timeout: 45000 }); }
  await page.waitForTimeout(2000);
  const dl = page.getByRole('button', { name: /^Download$/i }).first();
  if (await dl.count()) { await dl.click({ force: true, timeout: 45000 }); }
  console.log('DWPose running…');
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(8000);
    const t = (await page.locator('body').innerText()) || '';
    if (!t.includes('Load DWPose model') && !t.includes('Working…')) { console.log(`rig done ~${(i + 1) * 8}s`); break; }
  }

  const sp = page.getByRole('button', { name: /Next: Setup Parameters/i }).first();
  if (await sp.count()) { await sp.click({ force: true, timeout: 45000 }); }
  await page.waitForTimeout(6000);
  await page.getByRole('button', { name: /Done/i }).first().click({ force: true, timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(15000);
  console.log('EDITOR READY:', (await page.locator('body').innerText()).includes('PARAMETERS') ? 'yes' : 'no');
  await page.screenshot({ path: path.join(OUT, `${name}_rigged.png`) });

  await page.getByTitle('Export frames').click({ force: true, timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(2000);
  const typeTrigger = page.locator('[role="combobox"]').first();
  if (await typeTrigger.count()) {
    await typeTrigger.click({ force: true, timeout: 45000 });
    await page.waitForTimeout(1200);
    const spineOpt = page.locator('[role="option"]', { hasText: 'Spine' }).first();
    if (await spineOpt.count()) { await spineOpt.click({ force: true, timeout: 45000 }); }
    await page.waitForTimeout(1200);
  }
  const dlPromise = page.waitForEvent('download', { timeout: 90000 }).catch(() => null);
  await page.getByRole('button', { name: /^Export$/i }).first().click({ force: true, timeout: 45000 }).catch(() => {});
  const dled = await dlPromise;
  if (dled) {
    const dest = path.join(OUT, `${name}_spine.zip`);
    await dled.saveAs(dest);
    console.log('SPINE ZIP:', dest, fs.statSync(dest).size, 'bytes');
  } else {
    console.log('NO DOWNLOAD');
  }
  console.log('ERRORS:', JSON.stringify(errors));
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
