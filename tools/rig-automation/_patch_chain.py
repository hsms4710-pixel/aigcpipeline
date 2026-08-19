# -*- coding: utf-8 -*-
import os
base = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# 1) rig-psd.cjs：rig 完成后保存 .stretch
f = os.path.join(base, "rig-psd.cjs")
src = open(f, encoding="utf-8").read()
anchor = "  console.log('EDITOR READY:', (await page.locator('body').innerText()).includes('PARAMETERS') ? 'yes' : 'no');"
add = anchor + """

  // 保存 .stretch 工程（供 S3 动画直接加载）
  await page.getByTitle('Save project').click({ force: true, timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(2000);
  const dlTab = page.getByRole('tab', { name: /Download File/i }).first();
  if (await dlTab.count()) await dlTab.click({ force: true, timeout: 45000 });
  await page.waitForTimeout(800);
  const nameInput = page.locator('#name');
  if (await nameInput.count()) {
    await nameInput.fill(`${name}_rigged`);
    const sdP = page.waitForEvent('download', { timeout: 60000 }).catch(() => null);
    await page.getByRole('button', { name: /^Save$/i }).first().click({ force: true, timeout: 45000 }).catch(() => {});
    const sd = await sdP;
    if (sd) { const dest = path.join(OUT, `${name}_rigged.stretch`); await sd.saveAs(dest); console.log('STRETCH SAVED:', dest, fs.statSync(dest).size); }
  }
"""
assert anchor in src, "rig-psd anchor not found"
src = src.replace(anchor, add)
open(f, "w", encoding="utf-8").write(src)
print("rig-psd.cjs patched: saves .stretch")

# 2) stretchy-agent.cjs：支持直接加载 .stretch
f2 = os.path.join(base, "stretchy-agent.cjs")
src2 = open(f2, encoding="utf-8").read()
old = "async function loadAndRig(page, psdPath) {"
new = """async function loadStretch(page, stretchPath) {
  await page.goto(APP_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(4000);
  await page.getByTitle('Load project').click({ force: true, timeout: 45000 });
  await page.waitForTimeout(2000);
  await page.locator('input[type=file]').first().setInputFiles(stretchPath);
  for (let i = 0; i < 25; i++) { await page.waitForTimeout(1000); const s = await page.evaluate(() => window.__ss.readState()); if (s.animations.length > 0) break; }
  await page.waitForTimeout(1500);
  console.log('STRETCH LOADED');
}

async function loadAndRig(page, psdPath) {"""
assert old in src2, "agent anchor not found"
src2 = src2.replace(old, new)
old2 = "  if (loadPsd) {\n    await loadAndRig(page, loadPsd);"
if old2 not in src2:
    old2 = "  if (loadPsd) {\r\n    await loadAndRig(page, loadPsd);"
new2 = old2.replace("await loadAndRig(page, loadPsd);", "if (loadPsd.toLowerCase().endsWith('.stretch')) { await loadStretch(page, loadPsd); } else { await loadAndRig(page, loadPsd); }")
assert old2 in src2, "agent dispatch not found"
src2 = src2.replace(old2, new2)
open(f2, "w", encoding="utf-8").write(src2)
print("stretchy-agent.cjs patched: supports .stretch load")
