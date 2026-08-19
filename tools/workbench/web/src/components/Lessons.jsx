import React, { useEffect, useState } from 'react';
import { api, stageName } from '../api.js';

// 📚 经验库：门禁失败自动沉淀的教训 + 流水线成本统计
export default function Lessons() {
  const [lessons, setLessons] = useState([]);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const load = () => {
      api.lessons(40).then(setLessons).catch(() => {});
      api.status().then(setStatus).catch(() => {});
    };
    load();
    const t = setInterval(load, 6000);
    return () => clearInterval(t);
  }, []);

  const cost = status?.cost_by_stage || {};
  return (
    <div>
      <div className="stage-desc">
        <b>📚 经验库</b> — 流水线门禁失败自动沉淀的教训（harness/memory/pipeline/lessons-learned.md），用于归因与规避
      </div>

      <div className="card">
        <h3>💰 成本与任务统计 <span className="sub">已完成任务</span></h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 10 }}>
          <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent)' }}>¥{status?.total_cost ?? 0}</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>总成本</div>
          </div>
          <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--ok)' }}>{status?.done_count ?? 0}<span style={{ fontSize: 13, color: 'var(--text-3)' }}>/{status?.job_count ?? 0}</span></div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>完成/任务数</div>
          </div>
          {(status?.stages || []).map(s => (
            <div key={s} style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, padding: 12, textAlign: 'center' }}>
              <div style={{ fontSize: 15, fontWeight: 600 }}>{stageName(s)}</div>
              <div style={{ fontSize: 11, color: 'var(--text-3)' }}>¥{cost[s] ?? 0}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>🧠 门禁教训 <span className="sub">{lessons.length} 条</span></h3>
        {lessons.length === 0 && <div className="empty">暂无沉淀教训（门禁 FAIL 时会自动写入）</div>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {lessons.map((l, i) => (
            <div key={i} style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, padding: 10 }}>
              <div style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 4 }}>{l.header}</div>
              {l.reasons.map((r, j) => (
                <div key={j} style={{ fontSize: 12, color: 'var(--warn)', fontFamily: 'var(--mono)' }}>• {r}</div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
