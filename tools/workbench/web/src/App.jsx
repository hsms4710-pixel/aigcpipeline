import React, { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard.jsx';
import StageTab from './components/StageTab.jsx';
import Artifacts from './components/Artifacts.jsx';
import Settings from './components/Settings.jsx';
import { api } from './api.js';
import './styles.css';

const TABS = [
  { id: 'dashboard', label: '📊 总览' },
  { id: 's0_generate', label: '🎨 生图' },
  { id: 's1_decompose', label: '🧩 拆层' },
  { id: 's2_rig', label: '🦴 绑骨' },
  { id: 's3_animate', label: '🎬 动画' },
  { id: 's4_package', label: '📦 打包' },
  { id: 's5_engine', label: '🎮 引擎' },
  { id: 'artifacts', label: '🗂 资产库' },
  { id: 'settings', label: '⚙️ 设置' },
];

export default function App() {
  const [tab, setTab] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [toast, setToast] = useState('');

  const refreshHealth = () => api.health().then(setHealth).catch(() => {});
  useEffect(() => {
    refreshHealth();
    const t = setInterval(refreshHealth, 6000);
    return () => clearInterval(t);
  }, []);

  const notify = (m) => { setToast(m); setTimeout(() => setToast(''), 3000); };

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          <span className="dot" />
          <div>角色 AIGC 流水线<small>Character AIGC Pipeline Console</small></div>
        </div>
        <nav className="topnav">
          {TABS.map(t => (
            <button key={t.id} className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>{t.label}</button>
          ))}
        </nav>
        <div className="health">
          <span>API</span>
          <span className="sv"><span className={health ? 'dotup' : 'dotdown'} /> 8000</span>
          {health && Object.entries(health.servers || {}).map(([p, s]) => (
            <span className="sv" key={p}><span className={s === 'up' ? 'dotup' : 'dotdown'} /> {p}</span>
          ))}
        </div>
      </div>

      <div className="content">
        <div className="page">
          {tab === 'dashboard' && <Dashboard onGo={setTab} />}
          {['s0_generate', 's1_decompose', 's2_rig', 's3_animate', 's4_package', 's5_engine'].includes(tab) && (
            <StageTab key={tab} stage={tab} refreshHealth={refreshHealth} />
          )}
          {tab === 'artifacts' && <Artifacts />}
          {tab === 'settings' && <Settings />}
        </div>
      </div>
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
