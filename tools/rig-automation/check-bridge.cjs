const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage();
  await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(4000);
  const info = await page.evaluate(() => {
    const b = window.__ss;
    if (!b) return { bridge: false };
    return { bridge: true, version: b.version, nodes: b.listNodes().length, params: b.listParams().length, clips: b.listClips().map(c => c.name), hasSetMode: typeof b.setMode === 'function' };
  });
  console.log('BRIDGE:', JSON.stringify(info));
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
