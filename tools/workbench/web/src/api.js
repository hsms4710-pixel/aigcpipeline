// api.js — 后端交互封装
async function jfetch(url, opts = {}) {
  const r = await fetch(url, {
    headers: opts.body ? { 'Content-Type': 'application/json' } : undefined,
    ...opts,
  });
  if (!r.ok) { let t = ''; try { t = (await r.json()).detail || '' } catch {}; throw new Error(t || `${r.status} ${r.statusText}`); }
  return r.json();
}
export const api = {
  health: () => jfetch('/api/health'),
  stages: () => jfetch('/api/pipeline/stages'),
  jobs: (stage) => jfetch(`/api/pipeline/jobs${stage ? `?stage=${stage}` : ''}`),
  job: (id) => jfetch(`/api/pipeline/jobs/${id}`),
  createJob: (stage, config) => jfetch('/api/pipeline/jobs', { method: 'POST', body: JSON.stringify({ stage, config }) }),
  rerun: (id) => jfetch(`/api/pipeline/jobs/${id}/run`, { method: 'POST' }),
  artifacts: () => jfetch('/api/artifacts'),
  config: () => jfetch('/api/config'),
  setConfig: (key, value) => jfetch('/api/config', { method: 'POST', body: JSON.stringify({ key, value }) }),
  status: () => jfetch('/api/pipeline/status'),
};
export function fmtSize(n) { if (n == null) return ''; if (n < 1024) return n + 'B'; if (n < 1048576) return (n / 1024).toFixed(1) + 'KB'; return (n / 1048576).toFixed(1) + 'MB'; }
export function fmtDur(ms) { if (!ms) return '-'; if (ms < 1000) return ms + 'ms'; return (ms / 1000).toFixed(1) + 's'; }
export function stageName(id) { return ({ s0_generate: '生图 S0', s1_decompose: '拆层 S1', s2_rig: '绑骨 S2', s3_animate: '动画 S3', s4_package: '打包 S4', s5_engine: '引擎 S5' })[id] || id; }
export function stageIcon(id) { return ({ s0_generate: '🎨', s1_decompose: '🧩', s2_rig: '🦴', s3_animate: '🎬', s4_package: '📦', s5_engine: '🎮' })[id] || '·'; }
