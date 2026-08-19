import React, { useEffect, useState } from 'react';
import { api, stageName, stageIcon } from '../api.js';

// 🚀 一键流水线：选择起止阶段 → 顺序执行 → 自动把上游产物填入下游输入 → live 进度
const ORDER = ['s0_generate', 's1_decompose', 's2_rig', 's3_animate', 's4_package', 's5_engine'];

export default function ChainRunner({ onGo }) {
  const [schemas, setSchemas] = useState({});
  const [startIdx, setStartIdx] = useState(0);
  const [endIdx, setEndIdx] = useState(5);
  const [configs, setConfigs] = useState({});
  const [expanded, setExpanded] = useState(null);
  const [running, setRunning] = useState(false);
  const [chain, setChain] = useState(null);
  const [msg, setMsg] = useState('');
  const [history, setHistory] = useState([]);
  const [viewChain, setViewChain] = useState(null);

  useEffect(() => {
    const loadHistory = () => api.chains().then(h => setHistory(h.slice(0, 10))).catch(() => {});
    loadHistory();
    const ht = setInterval(loadHistory, 5000);
    return () => clearInterval(ht);
  }, []);
  useEffect(() => {
    api.stages().then(ss => {
      const m = {}; const c = {};
      ss.forEach(s => {
        m[s.id] = s;
        const cf = {};
        (s.config || []).forEach(f => { cf[f.key] = f.type === 'bool' ? (f.default === true || f.default === 'true') : (f.default ?? ''); });
        c[s.id] = cf;
      });
      setSchemas(m); setConfigs(c);
    }).catch(() => {});
  }, []);

  const stages = ORDER.slice(startIdx, endIdx + 1);
  const set = (stage, k, v) => setConfigs(c => ({ ...c, [stage]: { ...c[stage], [k]: v } }));

  const run = async () => {
    setRunning(true); setMsg('');
    try {
      const cfg = {};
      stages.forEach(s => { cfg[s] = configs[s] || {}; });
      const r = await api.chainRun(stages, cfg);
      setChain({ id: r.chain_id, stages: r.stages, jobs: [], status: 'created' });
    } catch (e) { setMsg('启动失败: ' + e.message); setRunning(false); }
  };

  useEffect(() => {
    if (!chain) return;
    const t = setInterval(async () => {
      try {
        const d = await api.chain(chain.id);
        setChain(d);
        if (d.status === 'done' || d.status === 'failed') { clearInterval(t); setRunning(false); }
      } catch (e) { /* ignore */ }
    }, 3000);
    return () => clearInterval(t);
  }, [chain && chain.id]);

  const view = async (id) => {
    try { setViewChain(await api.chain(id)); } catch (e) { setMsg('读取失败'); }
  };
  const resume = async (id) => {
    setRunning(true); setMsg('');
    try {
      const r = await api.chainResume(id);
      setChain({ id: r.chain_id, stages: r.stages, jobs: [], status: 'created' });
      setViewChain(null);
      setMsg(`已从阶段 ${r.stages[0]} 续跑 → ${r.chain_id}`);
    } catch (e) { setMsg('续跑失败: ' + e.message); setRunning(false); }
  };
  const runningJobs = (viewChain || chain || { jobs: [] }).jobs || [];
  const shownChain = viewChain || chain;
  const activeIdx = runningJobs.findIndex(j => j.status === 'running');

  return (
    <div className="card">
      <h3>🚀 一键流水线 <span className="sub">顺序执行 · 上游产物自动填入下游</span></h3>

      <div style={{ display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap', marginBottom: 14 }}>
        <label style={{ fontSize: 12, color: 'var(--text-2)' }}>起始
          <select value={startIdx} onChange={e => setStartIdx(parseInt(e.target.value))} style={{ marginLeft: 6, background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 5, padding: '5px 8px' }}>
            {ORDER.map((s, i) => <option key={s} value={i}>{stageName(s)}</option>)}
          </select>
        </label>
        <label style={{ fontSize: 12, color: 'var(--text-2)' }}>结束
          <select value={endIdx} onChange={e => setEndIdx(parseInt(e.target.value))} style={{ marginLeft: 6, background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 5, padding: '5px 8px' }}>
            {ORDER.map((s, i) => <option key={s} value={i} disabled={i < startIdx}>{stageName(s)}</option>)}
          </select>
        </label>
        <button className="btn" onClick={run} disabled={running}>
          {running ? <><span className="spin" /> 执行中…</> : '▶ 运行流水线'}
        </button>
        {msg && <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{msg}</span>}
      </div>

      {/* 每阶段配置（可展开） */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 10, marginBottom: 14 }}>
        {stages.map(s => {
          const sch = schemas[s];
          if (!sch) return null;
          return (
            <div key={s} style={{ border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden', background: 'var(--bg-2)' }}>
              <button
                onClick={() => setExpanded(expanded === s ? null : s)}
                style={{ width: '100%', textAlign: 'left', background: 'transparent', border: 'none', color: 'var(--text)', padding: '8px 12px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span>{stageIcon(s)} {sch.name}</span>
                <span style={{ color: 'var(--text-3)' }}>{expanded === s ? '▾' : '▸'}</span>
              </button>
              {expanded === s && (
                <div style={{ padding: '0 12px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(sch.config || []).map(f => (
                    <div key={f.key}>
                      <label style={{ fontSize: 11, color: 'var(--text-3)' }}>{f.label}{f.required && <span style={{ color: 'var(--danger)' }}> *</span>}</label>
                      {f.type === 'select' && (
                        <select value={configs[s]?.[f.key] ?? ''} onChange={e => set(s, f.key, e.target.value)} style={{ width: '100%', background: 'var(--panel)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 4, padding: '5px 8px', fontSize: 12 }}>
                          {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                      )}
                      {f.type === 'bool' && (
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                          <input type="checkbox" checked={!!configs[s]?.[f.key]} onChange={e => set(s, f.key, e.target.checked)} /> 开启
                        </label>
                      )}
                      {(f.type === 'text' || f.type === 'int' || f.type === 'file') && (
                        <input type={f.type === 'int' ? 'number' : 'text'} value={configs[s]?.[f.key] ?? ''} onChange={e => set(s, f.key, e.target.value)} placeholder={f.default} style={{ width: '100%', background: 'var(--panel)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 4, padding: '5px 8px', fontSize: 12 }} />
                      )}
                      {f.type === 'textarea' && (
                        <textarea value={configs[s]?.[f.key] ?? ''} onChange={e => set(s, f.key, e.target.value)} placeholder={f.default} style={{ width: '100%', minHeight: 54, background: 'var(--panel)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 4, padding: '5px 8px', fontSize: 12, fontFamily: 'var(--mono)' }} />
                      )}
                    </div>
                  ))}
                  {f => null}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* live 进度 */}
      {shownChain && (
        <div>
          <h4 style={{ fontSize: 12, color: 'var(--text-2)', margin: '6px 0 8px' }}>📈 {shownChain.id} · {shownChain.status}{viewChain && <button className="btn ghost sm" style={{ marginLeft: 8 }} onClick={() => setViewChain(null)}>返回</button>}</h4>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
            {shownChain.stages.map((s, i) => {
              const j = runningJobs.find(x => x.idx === i);
              const st = j ? j.status : 'queued';
              const isActive = i === activeIdx;
              return (
                <div key={s} onClick={() => onGo && onGo(s)} style={{ cursor: 'pointer', border: isActive ? '1px solid var(--accent)' : '1px solid var(--border)', background: 'var(--bg-2)', borderRadius: 6, padding: '6px 10px', fontSize: 12, textAlign: 'center', minWidth: 76 }}>
                  <div>{stageIcon(s)} {stageName(s)}</div>
                  <div><span className={`badge ${st === 'running' ? 'running' : st === 'done' ? 'done' : st === 'failed' ? 'failed' : 'queued'}`}>{st}</span></div>
                  {j && j.fills && j.fills.length > 0 && <div style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 3 }} title={j.fills.join('\n')}>↑ 已自动填入</div>}
                  {j && j.error && <div style={{ fontSize: 10, color: 'var(--danger)', marginTop: 3 }}>✗</div>}
                </div>
              );
            })}
          </div>
          {runningJobs.filter(j => j.fills && j.fills.length).map(j => (
            <div key={j.job_id} style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 2 }}>
              {stageName(j.stage)} 上游自动填入: {j.fills.join('；')}
            </div>
          ))}
        </div>
      )}

      {/* 历史流水线 */}
      {history.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <h4 style={{ fontSize: 12, color: 'var(--text-2)', margin: '6px 0 8px' }}>🕘 历史流水线（最近 {history.length} 条）</h4>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {history.map(h => (
              <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 6, padding: '6px 10px', fontSize: 12, color: 'var(--text-2)' }}>
                <button onClick={() => view(h.id)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-2)', fontSize: 12, padding: 0 }}>{h.id}</button>
                <span className={`badge ${h.status}`}>{h.status}</span>
                <span style={{ color: 'var(--text-3)' }}>{h.stages.length} 阶段</span>
                {h.status === 'failed' && (
                  <button className="btn ghost sm" onClick={() => resume(h.id)} disabled={running}>↻ 断点续跑</button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
