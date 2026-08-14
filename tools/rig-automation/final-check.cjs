const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 150)); });
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3500);
  // S3 tab: verify done job + artifact with copy button
  await page.locator('.topnav button', { hasText: '动画' }).first().click({ force: true });
  await page.waitForTimeout(2000);
  const jobs = await page.locator('.job-item').count();
  const done = await page.locator('.job-item .badge.done').count();
  console.log('S3 tab: jobs =', jobs, '| done badges =', done);
  // click first done job
  const firstDone = page.locator('.job-item').filter({ has: page.locator('.badge.done') }).first();
  if (await firstDone.count()) { await firstDone.click({ force: true }); await page.waitForTimeout(2000); }
  const copyBtns = await page.locator('button[title*="复制绝对路径"]').count();
  const logVisible = await page.locator('.log').count();
  console.log('job detail: copy buttons =', copyBtns, '| log visible =', logVisible);
  await page.screenshot({ path: 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/pipeline/_tmp/s3_detail.png' });
  console.log('CONSOLE ERRORS:', JSON.stringify(errors));
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
