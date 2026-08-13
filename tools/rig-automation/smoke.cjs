const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');

const PSD = 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_v10/layered/char_ailin_v10_layered.psd';
const b64 = fs.readFileSync(PSD).toString('base64');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 300)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message.slice(0, 300)));

  await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);
  console.log('PAGE TITLE:', await page.title());

  const fileInputs = await page.locator('input[type=file]').count();
  console.log('FILE INPUTS:', fileInputs);
  if (fileInputs > 0) {
    await page.locator('input[type=file]').first().setInputFiles(PSD);
  } else {
    const canvas = page.locator('canvas').first();
    const box = await canvas.boundingBox();
    console.log('CANVAS BOX:', JSON.stringify(box));
    if (box) {
      await page.evaluate(async ({ b64, box }) => {
        const bin = atob(b64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const dt = new DataTransfer();
        dt.items.add(new File([bytes], 'char_ailin_v10_layered.psd', { type: 'application/octet-stream' }));
        const el = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
        if (!el) throw new Error('no element at canvas center');
        ['dragenter', 'dragover', 'drop'].forEach(type => {
          el.dispatchEvent(new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer: dt }));
        });
      }, { b64, box });
    }
  }
  await page.waitForTimeout(5000);

  const body = (await page.locator('body').innerText()).replace(/\s+/g, ' ').slice(0, 800);
  console.log('BODY:', body);
  console.log('CONSOLE ERRORS:', JSON.stringify(errors, null, 2));

  await page.screenshot({ path: 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/env/runtime/tools/stretchy-studio/smoke/smoke.png', fullPage: false });
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
