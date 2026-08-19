/**
 * stretchy-agent.cjs — LLM 驱动的 StretchyStudio 动画 agent
 * 用 DeepSeek 作为"动画导演"，通过 window.__ss 桥接编程控制 StretchyStudio：
 * 读角色状态 → LLM 决策（骨骼关键帧/表情参数）→ 执行 → 反馈 → 迭代 → 导出。
 *
 * 用法:
 *   node stretchy-agent.cjs --load <psd> --task "<任务描述>" --out <输出目录> [--max-steps N]
 *   # 若已在浏览器里导入好角色，可省略 --load
 */
const { chromium } = require('C:/Users/26046/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const APP_URL = 'http://localhost:5173/';
const KEY_FILE = 'C:/Users/26046/Desktop/gitub.txt';
const API_BASE = 'https://api.deepseek.com/v1';
const MODEL = process.env.AGENT_MODEL || 'deepseek-v4-flash';
const PW_BIN = 'C:/Users/26046/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
const usageTotals = { prompt_tokens: 0, completion_tokens: 0, calls: 0 };

function readKey() {
  if (process.env.DEEPSEEK_API_KEY) return process.env.DEEPSEEK_API_KEY;
  const txt = fs.readFileSync(KEY_FILE, 'utf8');
  const lines = txt.split(/\r?\n/).map(l => l.trim()).filter(l => /^sk-/.test(l));
  return lines[lines.length - 1];
}

async function llm(messages, { maxTokens = 4000, temperature = 0.6 } = {}) {
  const lastErr = [];
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const body = { model: MODEL, messages, max_tokens: maxTokens, temperature, reasoning_effort: 'none', response_format: { type: 'json_object' } };
      const r = await fetch(`${API_BASE}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${readKey()}` },
        body: JSON.stringify(body),
      });
      if (!r.ok) { const t = await r.text(); throw new Error(`LLM API ${r.status}: ${t.slice(0, 300)}`); }
      const j = await r.json();
      if (j.usage) {
        usageTotals.prompt_tokens += (j.usage.prompt_tokens || 0);
        usageTotals.completion_tokens += (j.usage.completion_tokens || 0);
        usageTotals.calls += 1;
      }
      const content = j.choices?.[0]?.message?.content || '';
      if (content.trim()) return content;
      lastErr.push('empty content; reasoning=' + (j.choices?.[0]?.message?.reasoning_content || '').slice(-200));
    } catch (e) { lastErr.push(e.message); }
    await new Promise(res => setTimeout(res, 3000 * attempt));
  }
  throw new Error('LLM 连续失败: ' + lastErr.join(' | '));
}
async function parseJsonLoose(s) {
  const m = s.match(/\{[\s\S]*\}/);
  if (!m) throw new Error('LLM 返回不是 JSON');
  return JSON.parse(m[0]);
}

// ── 页面工具 ──────────────────────────────────────────────────────────────
async function dropPsd(page, b64) {
  const canvas = page.locator('canvas').first();
  await canvas.waitFor({ state: 'attached', timeout: 30000 }).catch(() => {});
  const box = await canvas.boundingBox();
  if (!box) throw new Error('canvas boundingBox null');
  await page.evaluate(async ({ b64, box }) => {
    const bin = atob(b64); const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const dt = new DataTransfer();
    dt.items.add(new File([bytes], 'import.psd', { type: 'application/octet-stream' }));
    const el = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
    if (!el) throw new Error('no element at center');
    ['dragenter', 'dragover', 'drop'].forEach(t => el.dispatchEvent(new DragEvent(t, { bubbles: true, cancelable: true, dataTransfer: dt })));
  }, { b64, box });
}

async function loadStretch(page, stretchPath) {
  await page.goto(APP_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(4000);
  await page.getByTitle('Load project').click({ force: true, timeout: 45000 });
  await page.waitForTimeout(2000);
  await page.locator('input[type=file]').first().setInputFiles(stretchPath);
  for (let i = 0; i < 25; i++) { await page.waitForTimeout(1000); const s = await page.evaluate(() => window.__ss.readState()); if (s.animations.length > 0) break; }
  await page.waitForTimeout(1500);
  console.log('STRETCH LOADED');
}

async function loadAndRig(page, psdPath) {
  const b64 = fs.readFileSync(psdPath).toString('base64');
  let imported = false;
  for (let attempt = 1; attempt <= 4; attempt++) {
    try {
      await page.goto(APP_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(4000);
      await dropPsd(page, b64);
      for (let i = 0; i < 15; i++) {
        await page.waitForTimeout(1500);
        if (((await page.locator('body').innerText()) || '').includes('layers matched')) { imported = true; break; }
      }
      if (imported) break;
    } catch (e) { console.log(`import attempt ${attempt}: ${e.message.split('\n')[0]}`); await page.waitForTimeout(3000); }
  }
  if (!imported) throw new Error('PSD 导入失败');
  const match = ((await page.locator('body').innerText()) || '').match(/(\d+) of (\d+) layers matched/);
  console.log('LAYER MATCH:', match ? match[0] : 'unknown');

  await page.getByRole('button', { name: /Continue/i }).first().click({ force: true, timeout: 45000 });
  await page.waitForTimeout(3000);
  const nextBtn = page.getByRole('button', { name: /Next: Adjust Joints/i }).first();
  if (await nextBtn.count()) await nextBtn.click({ force: true, timeout: 45000 });
  await page.waitForTimeout(2500);
  const aiBtn = page.getByRole('button', { name: /AI Auto-Rig/i }).first();
  if (await aiBtn.count()) await aiBtn.click({ force: true, timeout: 45000 });
  await page.waitForTimeout(2000);
  const dl = page.getByRole('button', { name: /^Download$/i }).first();
  if (await dl.count()) await dl.click({ force: true, timeout: 45000 });
  console.log('DWPose rigging…');
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(8000);
    const t = (await page.locator('body').innerText()) || '';
    if (!t.includes('Load DWPose model') && !t.includes('Working…')) { console.log(`rig done ~${(i + 1) * 8}s`); break; }
  }
  const sp = page.getByRole('button', { name: /Next: Setup Parameters/i }).first();
  if (await sp.count()) await sp.click({ force: true, timeout: 45000 });
  await page.waitForTimeout(6000);
  await page.getByRole('button', { name: /Done/i }).first().click({ force: true, timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(12000);
  console.log('EDITOR READY:', (await page.locator('body').innerText()).includes('PARAMETERS') ? 'yes' : 'no');
}

async function evalBridge(page, fnName, args) {
  return page.evaluate(([f, a]) => window.__ss[f](...a), [fnName, args]);
}

// ── 执行 LLM 动作 ─────────────────────────────────────────────────────────
async function executeAction(page, act, outDir, notes) {
  const { op, args = {} } = act;
  try {
    switch (op) {
      case 'create_clip':   return await evalBridge(page, 'createClip', [args.name, args.duration_ms ?? 2000, args.fps ?? 24]);
      case 'delete_clip':   return await evalBridge(page, 'deleteClip', [args.name]);
      case 'clear_clip':    return await evalBridge(page, 'clearClip', [args.name]);
      case 'rename_clip':   return await evalBridge(page, 'renameClip', [args.old, args.name]);
      case 'keyframe':      return await evalBridge(page, 'keyframe', [args.clip, args.node, args.property, args.time_ms, args.value, args.easing || 'ease-both']);
      case 'set_param':     return await evalBridge(page, 'setParam', [args.param, args.value]);
      case 'set_transform': return await evalBridge(page, 'setNodeTransform', [args.node, args.props]);
      case 'set_active':    return await evalBridge(page, 'setActiveClip', [args.clip]);
      case 'seek':          return await evalBridge(page, 'seek', [args.time_ms ?? 0]);
      case 'end_frame':     return await evalBridge(page, 'setEndFrame', [args.frame]);
      case 'play':          return await evalBridge(page, 'play', []);
      case 'pause':         return await evalBridge(page, 'pause', []);
      case 'screenshot': {
        await evalBridge(page, 'pause', []);
        await page.waitForTimeout(400);
        const name = (args.name || 'frame').replace(/[\\/:*?"<>|]/g, '_');
        const p = path.join(outDir, name);
        await page.screenshot({ path: p });
        return { ok: true, saved: p };
      }
      case 'note': notes.push(String(args.text || '')); return { ok: true };
      default: return { ok: false, reason: `未知操作 ${op}` };
    }
  } catch (e) {
    return { ok: false, reason: e.message.split('\n')[0] };
  }
}

function buildStatePrompt(state) {
  const lines = ['角色节点层级（name | type | boneRole | children）：'];
  const byId = new Map(state.nodes.map(n => [n.id, n]));
  const roots = state.nodes.filter(n => !n.parent);
  const walk = (n, depth) => {
    const role = n.boneRole ? ` [${n.boneRole}]` : '';
    lines.push(`${'  '.repeat(depth)}- ${n.name} (${n.type})${role}`);
    const kids = state.nodes.filter(c => c.parent === n.id);
    kids.forEach(k => walk(k, depth + 1));
  };
  roots.forEach(r => walk(r, 0));
  lines.push('');
  lines.push('可动画参数：' + state.parameters.map(p => `${p.name}(${p.min}~${p.max})`).join(', '));
  lines.push('现有动画 clip：' + (state.animations.length ? state.animations.map(a => `${a.name}(${a.duration}ms/${a.fps}fps)`) : '无'));
  return lines.join('\n');
}

const SYSTEM_PROMPT = `你是 StretchyStudio 的动画导演 Agent。你可以通过 JSON 动作编程控制一个 2D 骨骼动画编辑器（类 Spine/Live2D）。

动作 schema（每次输出一个 JSON 对象，含 "actions": [...]，可含多个动作；做完后 "done": true 结束）：
- {"op":"create_clip","args":{"name":"idle","duration_ms":2000,"fps":24}}  创建/复用动画 clip
- {"op":"keyframe","args":{"clip":"idle","node":"leftArm","property":"rotation","time_ms":0,"value":0,"easing":"ease-both"}}  在 clip 的某节点某属性某时刻打关键帧
  - 节点名用上面状态里的 name 或 boneRole（root/torso/bothLegs/leftLeg/leftKnee/rightLeg/rightKnee/leftArm/leftElbow/rightArm/rightElbow/leftFootTarget/rightFootTarget/neck/head/eyes/...）；只驱动状态里真实存在的骨（旧 rig 可能无 leftElbow/leftKnee/leftFootTarget，没有就不驱动）
  - 属性：rotation(度) / x / y / scaleX / scaleY / opacity(0-1)
  - 时间单位毫秒。循环动画请首尾关键帧数值一致（time 0 == time duration）
  - easing：linear / ease-in / ease-out / ease-both / ease-in-out
- {"op":"clear_clip","args":{"name":"idle"}} / {"op":"delete_clip","args":{"name":"idle"}}
- {"op":"set_param","args":{"param":"Mouth Open","value":0.6}}  设置表情参数（用于表情截图，参数名见状态）
- {"op":"set_active","args":{"clip":"idle"}} / {"op":"seek","args":{"time_ms":500}} / {"op":"end_frame","args":{"frame":48}}
- {"op":"screenshot","args":{"name":"idle_t500.png"}}  截图当前画面到输出目录
- {"op":"note","args":{"text":"..."}}  记录你的思路

工作方法（严格分阶段，不要一次只做一个动画）：
阶段1（1-2步）：delete_clip 删除向导默认的 Idle；create_clip 一次性创建全部4个新clip：idle/walk/attack/hurt（各自 duration_ms 800~2000，fps 24）。这一步先不打卡关键帧。
阶段2（2-6步）：逐个 clip 打关键帧（可在一步里对一个 clip 打 8~30 个 keyframe 动作）。每个 clip 首尾关键帧一致以形成循环。**严格按工业动画方法论（12 原则）**：
- **walk（最重要，优先做对）**：4 个关键姿态循环——① Contact 左脚前脚跟触地（左腿前摆、右臂前摆）② Down 承重下沉（torso.y 最低点 -6~-10）③ Passing 重心过支撑腿（双腿交叉瞬间）④ Up 最高点（torso.y 抬到 +4~+8）。**髋肩反向**：左腿在前时右臂在前、左臂在后；**支撑脚固定不滑动**；摆动腿沿弧线（rotation 关键帧用 bezier 缓动 [0.42,0,0.58,1] 而非线性）。每 0.5s 一个姿态，2s 循环共 4 姿态。
- **walk 膝与脚（M0-9）**：**支撑腿（触地）膝接近伸直**（leftKnee/rightKnee ≈ 0~10°），**摆动腿过重心时膝弯曲 55~70°**（如 Passing 相 leftKnee +55~+70）；**脚贴地不翘**——摆动腿抬脚瞬间用 leftFootTarget.rotate 反向补偿（≈ -leftKnee.rotate），支撑腿 leftFootTarget ≈ 0；左右腿对称（同一套相位差半周期）。所有值保持 ±75° 内。
- **idle**：呼吸用 torso.scaleY 1→1.03 缓慢 + torso.rotation ±2 微摆 + head.rotation ±3 轻微摇头（不是整体 scale）。
- **attack（M0-6 肘驱动）**：三段式、总时长 0.85~1.0s——① anticipation 蓄力（~0.25s）：上臂 rightArm 后拉 -15~-25 + **前臂 rightElbow 收肘 -50~-70** + torso 后仰 +8；② strike 挥击（~0.3s）：**前臂快速甩直（rightElbow → 0 附近）** + 上臂前送 +30~+45 + torso 前倾 -10；③ follow-through 跟随（~0.3s）：手臂惯性继续前伸再弹性回位（rightElbow +10→0、rightArm +10→0）。**挥击主幅度给 rightElbow（屈肘→甩直），不是整条手臂刚体大摆**；左臂做对称辅助（幅度约右臂 40%）。bezier 缓动制造慢→快→停节奏；所有值保持 ±75° 内。
- **hurt**：受击后仰（torso.rotation +15~+20）+ 头部滞后 follow-through（head 比 torso 晚 0.1s 达到最大）+ 弹性回位（回弹一次小过冲）。
rotation 单位是度，合理范围 -70~70；所有关键帧尽量给 curve:[0.42,0,0.58,1]（bezier 缓动），首尾关键帧数值一致保证循环闭合。
阶段3（1-2步）：精修 FAIL 反馈中的关键帧错误。
阶段4（1-2步）：set_param + screenshot 表情预览：happy(眼睛眯 Eye L/R Smile=1 + 嘴开 Mouth Open=0.4)/sad(眉毛上挑 Brow L/R Y=0.5 + 嘴微开 Mouth Open=0.2)/angry(眉毛下压 Brow L/R Y=-0.5 + 嘴紧 Mouth Open=0)/neutral(全部归零)，各截图一张。
最后 done:true 并给 note 总结。
每次你会收到"当前状态 + 上轮动作执行结果"。请基于反馈迭代，不要重复已成功的动作。`;

// ── 主流程 ────────────────────────────────────────────────────────────────
(async () => {
  const argv = process.argv.slice(2);
  const getArg = (name) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : null; };
  const loadPsd = getArg('--load');
  const task = getArg('--task') || '为角色制作一套循环动画：idle(待机呼吸)、walk(走路)、attack(攻击)、hurt(受击)，以及表情过渡(happy/sad/angry/neutral)预览';
  const outDir = getArg('--out') || 'C:/Users/26046/Desktop/inerview/research/角色AIGC与AI-NPC全链路/assets/demo/char_ailin_anim';
  const maxSteps = parseInt(getArg('--max-steps') || '14', 10);
  const rulesFile = getArg('--rules') || '';
  let systemPrompt = SYSTEM_PROMPT;
  if (rulesFile && fs.existsSync(rulesFile)) {
    const rules = fs.readFileSync(rulesFile, 'utf8').trim();
    if (rules) {
      systemPrompt += '\n\n## 流水线自动注入规则（规避已知失败，必须遵守）\n' + rules;
      console.log('RULES_INJECTED: ' + rules.length + ' chars');
    }
  }
  if (getArg('--print-prompt')) {
    console.log('=====COMPOSED_SYSTEM_PROMPT=====');
    console.log(systemPrompt);
    console.log('=====END=====');
    process.exit(0);
  }
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({ headless: true, executablePath: PW_BIN });
  const page = await browser.newPage({ viewport: { width: 1680, height: 1050 }, acceptDownloads: true });

  if (loadPsd) {
    if (loadPsd.toLowerCase().endsWith('.stretch')) { await loadStretch(page, loadPsd); } else { await loadAndRig(page, loadPsd); }
  } else {
    await page.goto(APP_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(4000);
  }

  // 确认桥接
  const bridgeOk = await page.evaluate(() => !!window.__ss);
  if (!bridgeOk) throw new Error('window.__ss 桥接未加载，请重启 dev server');

  const state = await evalBridge(page, 'readState', []);
  console.log('NODES:', state.nodes.length, '| PARAMS:', state.parameters.length, '| CLIPS:', state.animations.map(a => a.name).join(', '));
  console.log('---角色层级---');
  console.log(buildStatePrompt(state));

  const history = [];
  let done = false;
  for (let step = 0; step < maxSteps && !done; step++) {
    console.log(`\n=== LLM 步骤 ${step + 1}/${maxSteps} ===`);
    const stateNow = await evalBridge(page, 'readState', []);
    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: `任务：${task}\n\n当前角色状态：\n${buildStatePrompt(stateNow)}\n\n${history.length ? '历史与反馈：\n' + history.slice(-6).join('\n') : ''}\n\n请输出 JSON 动作（可多步）。` },
    ];
    let raw;
    try { raw = await llm(messages); } catch (e) { console.error('LLM 调用失败:', e.message); break; }
    let plan;
    try { plan = await parseJsonLoose(raw); } catch (e) { console.error('JSON 解析失败:', e.message, '\nRAW:', raw.slice(0, 200)); break; }
    const actions = plan.actions || [];
    console.log('LLM 计划:', JSON.stringify(actions.map(a => a.op + (a.args?.name ? ':' + a.args.name : '')), null, 0));

    const results = [];
    for (const act of actions) {
      const r = await executeAction(page, act, outDir, history);
      results.push(`${act.op}(${act.args?.name || act.args?.clip || ''}): ${r.ok ? 'OK' : 'FAIL ' + (r.reason || '')}`);
      console.log('  ', results[results.length - 1]);
      if (!r.ok && act.op === 'keyframe') break; // 关键帧失败通常是名字错，停下让 LLM 修正
    }
    history.push(`[step ${step + 1}] actions: ${results.join(' | ')}` + (plan.note ? ` | note: ${plan.note}` : ''));
    if (plan.done) { done = true; console.log('LLM 报告完成'); }
  }

  // 导出
  console.log('\n=== 导出 ===');
  // 保存 .stretch
  await page.getByTitle('Save project').click({ force: true, timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(2500);
  const dlTab = page.getByRole('tab', { name: /Download File/i }).first();
  if (await dlTab.count()) await dlTab.click({ force: true, timeout: 45000 });
  await page.waitForTimeout(1000);
  const nameInput = page.locator('#name');
  if (await nameInput.count()) {
    await nameInput.fill('char_ailin_animated');
    const sdP = page.waitForEvent('download', { timeout: 60000 }).catch(() => null);
    await page.getByRole('button', { name: /^Save$/i }).first().click({ force: true, timeout: 45000 }).catch(() => {});
    const sd = await sdP;
    if (sd) { const dest = path.join(outDir, 'char_ailin_animated.stretch'); await sd.saveAs(dest); console.log('STRETCH:', dest, fs.statSync(dest).size); }
  }
  // 导出 Spine（带重试）
  for (let r = 0; r < 3; r++) {
    await page.getByTitle('Export frames').click({ force: true, timeout: 45000 }).catch(() => {});
    await page.waitForTimeout(2500);
    if (await page.locator('[role=combobox]').count() > 0) break;
  }
  const typeTrigger = page.locator('[role="combobox"]').first();
  if (await typeTrigger.count()) {
    await typeTrigger.click({ force: true, timeout: 45000 });
    await page.waitForTimeout(1200);
    const spineOpt = page.locator('[role="option"]', { hasText: 'Spine' }).first();
    if (await spineOpt.count()) await spineOpt.click({ force: true, timeout: 45000 });
    await page.waitForTimeout(1200);
  }
  const dlPromise = page.waitForEvent('download', { timeout: 90000 }).catch(() => null);
  await page.getByRole('button', { name: /^Export$/i }).first().click({ force: true, timeout: 45000 }).catch(() => {});
  const dled = await dlPromise;
  if (dled) { const dest = path.join(outDir, 'char_ailin_animated_spine.zip'); await dled.saveAs(dest); console.log('SPINE:', dest, fs.statSync(dest).size); }
  else console.log('SPINE 导出未触发下载');

  // 最终状态摘要
  const finalState = await evalBridge(page, 'readState', []);
  console.log('\n=== 最终动画 clip ===');
  for (const a of finalState.animations) {
    console.log(`- ${a.name}: ${a.duration}ms, ${a.trackCount} tracks`);
    for (const t of a.tracks.slice(0, 8)) console.log(`    ${t.nodeName}.${t.property}: ${t.keyframeCount} kf`);
    if (a.tracks.length > 8) console.log(`    ... 共 ${a.tracks.length} tracks`);
  }
  await page.screenshot({ path: path.join(outDir, 'final_view.png') });
  fs.writeFileSync(path.join(outDir, 'usage.json'), JSON.stringify({ ...usageTotals, model: MODEL }, null, 2));
  console.log('USAGE:', JSON.stringify(usageTotals));
  await browser.close();
  console.log('\n完成。产物在:', outDir);
})().catch(e => { console.error('AGENT ERROR:', e.message); process.exit(1); });
