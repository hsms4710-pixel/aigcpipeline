import React, { useEffect, useState } from 'react';
import { api } from '../api.js';

const FIELDS = [
  { key: 'GPT_API_KEY', label: 'GPT / 中转站 Key', sub: '生图（gpt-image-2）与 LLM，可从 gitub.txt 获取' },
  { key: 'GPT_BASE_URL', label: 'GPT Base URL', sub: '中转站 base_url（如 https://api.sisct2.xyz/v1）' },
  { key: 'GPT_MODEL', label: 'GPT 模型', sub: '默认生图模型（gpt-image-2）' },
  { key: 'DEEPSEEK_API_KEY', label: 'DeepSeek Key', sub: '动画 LLM 导演（deepseek-v4-flash）' },
  { key: 'GEMINI_API_KEY', label: 'Gemini Key', sub: '备用生图后端' },
  { key: 'TRIPO_API_KEY', label: 'Tripo 3D Key', sub: '3D 模型生成' },
  { key: 'VOLC_API_KEY', label: '火山引擎 TTS Key', sub: '语音合成' },
];

export default function Settings({ refreshHealth }) {
  const [cfg, setCfg] = useState({});
  const [personaPrompt, setPersonaPrompt] = useState('');
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => { api.config().then(setCfg).catch(() => {}); }, []);
  const save = async (k, v) => { try { await api.setConfig(k, v); setMsg(`已保存 ${k}`); setTimeout(() => setMsg(''), 2500); } catch (e) { setMsg('保存失败: ' + e.message); } };

  const llmFill = async () => {
    if (!personaPrompt.trim()) { setMsg('先输入人设一句话'); return; }
    setLoading(true); setMsg('');
    try {
      const key = cfg.DEEPSEEK_API_KEY || '';
      const base = 'https://api.deepseek.com/v1';
      const r = await fetch(base + '/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
        body: JSON.stringify({
          model: 'deepseek-v4-flash',
          messages: [{ role: 'user', content: `根据这段人设生成完整 persona.json（含 visual/style/assets 字段），只输出 JSON：${personaPrompt}` }],
          max_tokens: 1200, reasoning_effort: 'none',
        }),
      });
      if (!r.ok) throw new Error('LLM 调用失败 ' + r.status);
      const j = await r.json();
      const content = j.choices?.[0]?.message?.content || '';
      const m = content.match(/\{[\s\S]*\}/);
      if (!m) throw new Error('LLM 未返回 JSON');
      const persona = JSON.parse(m[0]);
      const blob = new Blob([JSON.stringify(persona, null, 2)], { type: 'application/json' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'persona.json'; a.click();
      setMsg('persona.json 已下载，请保存到本地供 S0 使用');
    } catch (e) { setMsg('失败: ' + e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="stage-desc"><b>⚙️ 全局设置</b> — API Key（存于 env/.env，不回显明文）与 LLM 人设填充</div>

      <div className="grid2">
        <div className="left">
          <div className="card">
            <h3>🔑 API Keys <span className="sub">掩码显示</span></h3>
            {FIELDS.map(f => (
              <div className="setting-row" key={f.key}>
                <div className="lbl">{f.label}<small>{f.sub}</small></div>
                <input type="password" value={cfg[f.key] || ''} onChange={e => setCfg(c => ({ ...c, [f.key]: e.target.value }))} />
                <button className="btn sm ghost" onClick={() => save(f.key, cfg[f.key] || '')}>保存</button>
              </div>
            ))}
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-3)' }}>Key 来源：C:\Users\26046\Desktop\gitub.txt（sk- 开头的行）</div>
          </div>

          <div className="card">
            <h3>🤖 LLM 人设填充</h3>
            <div className="field">
              <label>一句话人设</label>
              <textarea value={personaPrompt} onChange={e => setPersonaPrompt(e.target.value)} placeholder="例：艾琳，银发蓝瞳猫耳少女，活泼调皮，赛博朋克风格，擅长机械维修…" />
            </div>
            <div style={{ marginTop: 12 }}>
              <button className="btn" onClick={llmFill} disabled={loading}>{loading ? <><span className="spin" /> 生成中…</> : '生成 persona.json'}</button>
            </div>
          </div>
        </div>

        <div className="right">
          <div className="card">
            <h3>💡 配置说明</h3>
            <ul style={{ fontSize: 13, color: 'var(--text-2)', paddingLeft: 18, lineHeight: 2 }}>
              <li>每个阶段的配置项都在对应 Tab 中，运行后进入 job 队列，可观察日志/产物/耗时</li>
              <li>绑骨 S2 / 动画 S3 需要 StretchyStudio 服务（5173/5174）在线，Dashboard 顶部有服务状态灯</li>
              <li>拆层 S1 使用本地 GPU（See-through），耗时约 20 分钟</li>
              <li>生图 S0 需 OpenAI/中转站 Key；动画 S3 需 DeepSeek Key</li>
              <li>产物统一归档到 pipeline/artifacts/&lt;job_id&gt;/，可在资产库 Tab 预览下载</li>
            </ul>
          </div>
        </div>
      </div>
      {msg && <div className="toast">{msg}</div>}
    </div>
  );
}
