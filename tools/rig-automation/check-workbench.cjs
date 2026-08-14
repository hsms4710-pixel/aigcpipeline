const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 150)); });
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);
  // S0 tab field count
  await page.locator('.topnav button', { hasText: '生图' }).first().click({ force: true });
  await page.waitForTimeout(1500);
  const s0inputs = await page.locator('.field input, .field select, .field textarea').count();
  const s0dry = await page.locator('body').innerText().then(t => t.includes('仅预览提示词'));
  console.log('S0 inputs:', s0inputs, '| dry_run field present:', s0dry);
  // Dashboard jobs
  await page.locator('.topnav button', { hasText: '总览' }).first().click({ force: true });
  await page.waitForTimeout(2000);
  const dash = await page.locator('body').innerText();
  const jobCount = (dash.match(/job_[0-9a-f]{8}/g) || []).length;
  const dagNodes = await page.locator('.dag-node').count();
  console.log('Dashboard: jobs shown =', jobCount, '| DAG nodes =', dagNodes);
  await page.screenshot({ path: 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/pipeline/_tmp/final_dashboard.png' });
  console.log('CONSOLE ERRORS:', JSON.stringify(errors));
  await browser.close();
})().catch(e => { console.error('SCRIPT ERROR:', e.message); process.exit(1); });
