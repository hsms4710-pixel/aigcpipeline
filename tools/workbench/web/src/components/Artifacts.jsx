import React, { useEffect, useState } from 'react';
import { api, fmtSize } from '../api.js';

export default function Artifacts() {
  const [groups, setGroups] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const load = () => api.artifacts().then(setGroups).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  const imgs = [];
  groups.forEach(g => (g.artifacts || []).forEach(a => { if (/\.(png|jpg|jpeg|webp|gif)$/i.test(a.ext)) imgs.push({ ...a, job_id: g.job_id }); }));

  return (
    <div>
      <div className="stage-desc">
        <b>🗂 资产库</b> — 所有流水线任务的产物（按 job 归档），可预览/下载
        <div className="flow-line"><input type="text" style={{ width: 260, background: 'var(--bg-2)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 5, padding: '6px 10px' }} placeholder="过滤文件名…" value={filter} onChange={e => setFilter(e.target.value)} /></div>
      </div>

      <div className="card">
        <h3>🖼 图片预览 <span className="sub">{imgs.length} 张</span></h3>
        {imgs.length === 0 ? <div className="empty">暂无图片产物</div> : (
          <div className="preview-grid">
            {imgs.filter(a => !filter || a.path.includes(filter)).slice(0, 60).map((a, i) => (
              <div className="preview-item" key={i}>
                <img src={a.url} alt={a.path} />
                <div className="pn" title={a.path}>{a.path}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h3>📦 产物树</h3>
        {groups.length === 0 && <div className="empty">暂无产物</div>}
        {groups.map(g => (
          <div key={g.job_id} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', marginBottom: 6 }}>📁 {g.job_id}</div>
            <div className="tree">
              {(g.artifacts || []).filter(a => !filter || a.path.includes(filter)).map((a, i) => (
                <div className="row" key={i}>
                  <span>{a.ext === '.png' ? '🖼' : a.ext === '.json' ? '📄' : a.ext === '.log' ? '📝' : '📎'}</span>
                  <a className="nm" href={a.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)', textDecoration: 'none' }}>{a.path}</a>
                  <span className="sz">{fmtSize(a.size)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
