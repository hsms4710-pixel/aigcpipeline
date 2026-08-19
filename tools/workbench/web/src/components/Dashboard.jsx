import React, { useEffect, useState } from 'react';
import { api, stageName, stageIcon } from '../api.js';
import ChainRunner from './ChainRunner.jsx';

export default function Dashboard({ onGo }) {
  const [status, setStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const load = () => {
      api.status().then(setStatus).catch(() => {});
      api.jobs().then(setJobs).catch(() => {});
      api.health().then(setHealth).catch(() => {});
    };
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  const counts = {};
  (jobs || []).forEach(j => { counts[j.status] = (counts[j.status] || 0) + 1; });

  return (
    <div>
      <div className="stage-desc">
        <b>📊 流水线总览</b> — 生图 → 拆层 → 绑骨 → 动画 → 打包 → 引擎 ｜ 每个节点可观察输入/输出/流程/产物，可独立配置与重跑
        <div className="flow-line">
          {health && Object.entries(health.servers || {}).map(([p, s]) => (
            <span key={p} className="sv"><span className={s === 'up' ? 'dotup' : 'dotdown'} /> 服务:{p} {s}</span>
          ))}
          {Object.entries(counts).map(([k, v]) => <span key={k} className={`badge ${k}`}>{k}: {v}</span>)}
          {status?.total_cost != null && <span className="badge done">💰 ¥{status.total_cost}</span>}
          {status?.done_count != null && <span className="badge done">✓ {status.done_count}/{status.job_count}</span>}
        </div>
      </div>

      <ChainRunner onGo={onGo} />

      <div className="dag">
        {(status?.stages || []).map((s, i) => {
          const meta = status.stage_meta?.[s] || {};
          const st = status.by_stage?.[s] || {};
          const ok = st.done > 0;
          const run = st.running > 0;
          return (
            <div className={`dag-node ${ok ? 'ok' : ''}`} key={s} onClick={() => onGo(s)} style={{ cursor: 'pointer' }}>
              {run && <span className="st spin" />}
              <div className="ic">{meta.icon || stageIcon(s)}</div>
              <div className="nm">{meta.name || stageName(s)}</div>
              <div className="cnt">{i === 0 ? '起点' : `← 上一阶段`}{i < 5 ? ' →' : ''}</div>
              <div className="cnt" style={{ marginTop: 6 }}>
                {Object.entries(st).map(([k, v]) => <span key={k} className={`badge ${k}`} style={{ marginRight: 4 }}>{k} {v}</span>)}
                {Object.keys(st).length === 0 && <span className="muted">未运行</span>}
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h3>🕘 最近任务</h3>
        {jobs.length === 0 && <div className="empty">还没有任务，点击上方阶段卡片进入对应阶段配置并运行</div>}
        <div className="job-list">
          {jobs.slice(0, 20).map(j => (
            <div className="job-item" key={j.id} onClick={() => onGo(j.stage)}>
              <span className="jid">{j.id}</span>
              <span>{stageIcon(j.stage)} {stageName(j.stage)}</span>
              <div className="meta"><div className="t">{j.stage_detail}</div><div className="s">{new Date(j.created).toLocaleString()}</div></div>
              <span className={`badge ${j.status}`}>{j.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
