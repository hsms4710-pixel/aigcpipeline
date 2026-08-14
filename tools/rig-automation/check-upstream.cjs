const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 150)); });
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3500);
  // S4 tab: 应有"↑ 上游"下拉（来自 S3 产物）
  await page.locator('.topnav button', { hasText: '打包' }).first().click({ force: true });
  await page.waitForTimeout(2500);
  const upSelect = page.locator('select', { hasText: '↑ 上游' });
  console.log('S4 upstream select count:', await upSelect.count());
  // 打开一个 done job 详情看成本
  const done = page.locator('.job-item').filter({ has: page.locator('.badge.done') }).first();
  if (await done.count()) { await done.click({ force: true }); await page.waitForTimeout(2000); }
  const body = await page.locator('body').innerText();
  console.log('cost shown:', body.includes('成本') ? 'yes' : 'no');
  await page.screenshot({ path: 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/pipeline/_tmp/s4_upstream.png' });
  console.log('CONSOLE ERRORS:', JSON.stringify(errors));
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
