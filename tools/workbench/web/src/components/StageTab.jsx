import React, { useEffect, useRef, useState } from 'react';
import { api, fmtSize, fmtDur, stageName } from '../api.js';

// 通用阶段 Tab：左侧配置表单（由后端 schema 动态渲染，保证覆盖全部后端能力）+ 右侧 Job 列表/详情/日志/产物
export default function StageTab({ stage, refreshHealth }) {
  const [schema, setSchema] = useState(null);
  const [config, setConfig] = useState({});
  const [jobs, setJobs] = useState([]);
  const [sel, setSel] = useState(null);
  const [detail, setDetail] = useState(null);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState('');
  const timer = useRef(null);

  useEffect(() => { api.stages().then(ss => {
    const s = ss.find(x => x.id === stage);
    setSchema(s);
    const c = {};
    (s?.config || []).forEach(f => { c[f.key] = f.type === 'bool' ? (f.default === true || f.default === 'true') : (f.default ?? ''); });
    setConfig(c);
  }).catch(e => setMsg(e.message)); }, [stage]);

  useEffect(() => {
    const load = () => api.jobs(stage).then(setJobs).catch(() => {});
    load();
    timer.current = setInterval(load, 3000);
    return () => clearInterval(timer.current);
  }, [stage]);

  useEffect(() => { if (!sel) return; api.job(sel).then(setDetail).catch(() => {}); }, [sel]);
  useEffect(() => {
    if (!sel) return;
    const t = setInterval(() => api.job(sel).then(d => { setDetail(d); if (d.status === 'done' || d.status === 'failed') { clearInterval(t); refreshHealth && refreshHealth(); } }).catch(() => {}), 2500);
    return () => clearInterval(t);
  }, [sel]);

  const set = (k, v) => setConfig(c => ({ ...c, [k]: v }));
  const run = async () => {
    setRunning(true); setMsg('');
    try { const r = await api.createJob(stage, config); setSel(r.job_id); setMsg(`已提交 ${r.job_id}`); refreshHealth && refreshHealth(); }
    catch (e) { setMsg('提交失败: ' + e.message); }
    finally { setRunning(false); }
  };
  if (!schema) return <div className="empty">加载阶段配置…</div>;

  const previews = (detail?.artifacts || []).filter(a => /\.(png|jpg|jpeg|webp|gif)$/i.test(a.ext)).slice(0, 12);

  return (
    <div>
      <div className="stage-desc">
        <b>{schema.icon} {schema.name}</b> — {schema.desc}
        <div className="flow-line">
          {schema.prev?.length > 0 && <span>← 上游: {schema.prev.map(stageName).join(', ')}</span>}
          {schema.next?.length > 0 && <span>→ 下游: {schema.next.map(stageName).join(', ')}</span>}
          {schema.outputs && <span>· 产物: {schema.outputs}</span>}
          {schema.requires_servers && <span className="badge warn">需服务 {schema.requires_servers.map(p => ':' + p).join(' ')}</span>}
        </div>
      </div>

      <div className="grid2">
        {/* 左：配置表单 */}
        <div className="left">
          <div className="card">
            <h3>⚙️ 阶段配置 <span className="sub">输入契约</span></h3>
            <div className="form-grid">
              {schema.config.map(f => (
                <div className={`field ${f.type === 'textarea' || f.type === 'file' ? 'full' : ''}`} key={f.key}>
                  <label>{f.label}{f.required && <span className="req"> *</span>}</label>
                  {f.type === 'select' && (
                    <select value={config[f.key] ?? ''} onChange={e => set(f.key, e.target.value)}>
                      {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  )}
                  {f.type === 'bool' && (
                    <div className="bool"><input type="checkbox" checked={!!config[f.key]} onChange={e => set(f.key, e.target.checked)} /><span>{config[f.key] ? '是' : '否'}</span></div>
                  )}
                  {f.type === 'textarea' && (
                    <textarea value={config[f.key] ?? ''} onChange={e => set(f.key, e.target.value)} placeholder={f.default} />
                  )}
                  {(f.type === 'text' || f.type === 'int' || f.type === 'number') && (
                    <input type={f.type === 'int' || f.type === 'number' ? 'number' : 'text'}
                           value={config[f.key] ?? ''} onChange={e => set(f.key, e.target.value)} placeholder={f.default} />
                  )}
                  {f.type === 'file' && (
                    <>
                      <input type="text" value={config[f.key] ?? ''} onChange={e => set(f.key, e.target.value)} placeholder="路径或从上游产物选择" />
                      <div className="file-hint">可填写绝对路径，或参考资产库中的路径</div>
                    </>
                  )}
                  {f.help && <div className="help">{f.help}</div>}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn" onClick={run} disabled={running}>
                {running ? <><span className="spin" /> 提交中…</> : '▶ 运行阶段'}
              </button>
              {msg && <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{msg}</span>}
            </div>
          </div>
        </div>

        {/* 右：Job 列表 + 详情 */}
        <div className="right">
          <div className="card">
            <h3>📋 本阶段任务 <span className="sub">{jobs.length} 个</span></h3>
            {jobs.length === 0 && <div className="empty">还没有任务，配置左侧参数后点击运行</div>}
            <div className="job-list">
              {jobs.slice(0, 30).map(j => (
                <div className={`job-item ${sel === j.id ? 'selected' : ''}`} key={j.id} onClick={() => setSel(j.id)}>
                  <span className="jid">{j.id}</span>
                  <div className="meta">
                    <div className="t">{j.stage_detail}</div>
                    <div className="s">{new Date(j.created).toLocaleString()} · {fmtDur(j.duration_ms)}</div>
                  </div>
                  <span className={`badge ${j.status}`}>{j.status}</span>
                  <span className="muted" style={{ fontSize: 11 }}>{j.artifact_count} 产物</span>
                </div>
              ))}
            </div>
          </div>

          {detail && (
            <div className="detail" style={{ marginTop: 16 }}>
              <div className="head">
                <h3 style={{ margin: 0 }}>🔎 {detail.id} <span className={`badge ${detail.status}`}>{detail.status}</span></h3>
                <button className="btn ghost sm" onClick={() => api.rerun(detail.id).then(() => setMsg('已重新运行')).catch(e => setMsg(e.message))}>↻ 重跑</button>
              </div>
              <dl className="kv">
                <dt>阶段</dt><dd>{stageName(detail.stage)}</dd>
                <dt>创建</dt><dd>{new Date(detail.created).toLocaleString()}</dd>
                <dt>耗时</dt><dd>{fmtDur(detail.duration_ms)}</dd>
                {detail.error && <><dt>错误</dt><dd style={{ color: 'var(--danger)' }}>{detail.error}</dd></>}
              </dl>
              <h4 style={{ fontSize: 12, color: 'var(--text-2)', margin: '10px 0 6px' }}>运行配置</h4>
              <pre className="log" style={{ maxHeight: 140 }}>{JSON.stringify(detail.config, null, 2)}</pre>
              <h4 style={{ fontSize: 12, color: 'var(--text-2)', margin: '10px 0 6px' }}>产物</h4>
              {detail.artifacts.length === 0 ? <div className="muted" style={{ fontSize: 12 }}>暂无产物</div> : (
                <div className="arts">
                  {detail.artifacts.map((a, i) => (
                    <div className="art" key={i}>
                      <span className="aext">{a.ext.replace('.', '')}</span>
                      <a href={a.url} target="_blank" rel="noreferrer">{a.path}</a>
                      <span className="asz">{fmtSize(a.size)}</span>
                      <button className="btn ghost sm" title="复制绝对路径（供下一阶段输入）" onClick={() => { navigator.clipboard.writeText(a.abs); alert('已复制: ' + a.abs); }}>📋</button>
                    </div>
                  ))}
                </div>
              )}
              {previews.length > 0 && (
                <>
                  <h4 style={{ fontSize: 12, color: 'var(--text-2)', margin: '10px 0 6px' }}>图片预览</h4>
                  <div className="preview-grid">
                    {previews.map((a, i) => <div className="preview-item" key={i}><img src={a.url} alt={a.path} /><div className="pn">{a.path}</div></div>)}
                  </div>
                </>
              )}
              <h4 style={{ fontSize: 12, color: 'var(--text-2)', margin: '10px 0 6px' }}>日志</h4>
              <pre className="log">{detail.log || <span className="dim">（无日志）</span>}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
