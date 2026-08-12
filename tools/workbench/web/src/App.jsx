import React, { useEffect, useState } from 'react'
import { Tldraw } from '@tldraw/tldraw'
import '@tldraw/tldraw/tldraw.css'
import PersonaForm from './PersonaForm.jsx'

const C = {
  bg: '#1e1e1e', panel: '#2b2b2b', card: '#333333', border: '#444', text: '#e0e0e0',
  sub: '#9a9a9a', accent: '#6ea8fe', danger: '#f08080', ok: '#7bc96f'
}
const btn = { background: C.accent, color: '#111', border: 'none', padding: '6px 12px', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }
const input = { background: '#1a1a1a', color: C.text, border: `1px solid ${C.border}`, borderRadius: 4, padding: '5px 8px', boxSizing: 'border-box', width: '100%' }
const label = { display: 'block', fontSize: 12, color: C.sub, margin: '8px 0 3px' }

function TabBtn({ active, onClick, children }) {
  return <button onClick={onClick} style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px 14px', cursor: 'pointer', background: active ? C.card : 'transparent', color: active ? C.accent : C.text, border: 'none', borderLeft: active ? `3px solid ${C.accent}` : '3px solid transparent', fontSize: 14 }}>{children}</button>
}

export default function App() {
  const [tab, setTab] = useState('persona')
  const [chars, setChars] = useState([])
  const [msg, setMsg] = useState('')
  const [editor, setEditor] = useState(null)

  const refresh = async () => { try { const r = await fetch('/api/characters'); setChars(await r.json()) } catch {} }
  useEffect(() => { refresh(); const t = setInterval(refresh, 6000); return () => clearInterval(t) }, [])

  const addToCanvas = (charId, path) => {
    if (!editor) return
    const c = editor.getViewportPageBounds()
    editor.createShape({ type: 'image', x: c.minX + 100 + Math.random()*150, y: c.minY + 100 + Math.random()*150, props: { src: `/char-assets/${charId}/${path}`, w: 180, h: 180 } })
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: C.bg, color: C.text }}>
      {/* 左侧导航 */}
      <div style={{ width: 320, borderRight: `1px solid ${C.border}`, background: C.panel, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '14px 16px', borderBottom: `1px solid ${C.border}`, fontWeight: 700, fontSize: 15 }}>
          ⚙️ 角色 AIGC 工作台
          <div style={{ fontSize: 11, color: C.sub, fontWeight: 400, marginTop: 2 }}>AIGC 流水线入口 v2</div>
        </div>
        <nav style={{ borderBottom: `1px solid ${C.border}` }}>
          <TabBtn active={tab==='persona'} onClick={() => setTab('persona')}>👤 人设（导入/创建/LLM）</TabBtn>
          <TabBtn active={tab==='create'} onClick={() => setTab('create')}>🖼️ 资产创建</TabBtn>
          <TabBtn active={tab==='refs'} onClick={() => setTab('refs')}>📚 参考图</TabBtn>
          <TabBtn active={tab==='config'} onClick={() => setTab('config')}>🔑 配置</TabBtn>
        </nav>
        <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
          {msg && <div style={{ background: '#3a3a3a', color: C.sub, fontSize: 12, padding: '6px 8px', borderRadius: 4, marginBottom: 8 }}>{msg}</div>}
          {tab === 'persona' && <PersonaTab chars={chars} refresh={refresh} setMsg={setMsg} />}
          {tab === 'create' && <CreateTab chars={chars} setMsg={setMsg} />}
          {tab === 'refs' && <RefsTab />}
          {tab === 'config' && <ConfigTab setMsg={setMsg} />}
        </div>
      </div>
      {/* 主区画布 */}
      <div style={{ flex: 1, position: 'relative', background: C.bg }}>
        <Tldraw onMount={(ed) => setEditor(ed)} />
        {chars.length > 0 && (
          <div style={{ position: 'absolute', right: 12, top: 12, width: 230, background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, padding: 8, maxHeight: '65vh', overflowY: 'auto', zIndex: 100, fontSize: 12 }}>
            <b style={{ color: C.text }}>角色资产</b>
            {chars.map(ch => (
              <div key={ch.id} style={{ marginTop: 8 }}>
                <div style={{ color: C.accent, fontWeight: 600 }}>{ch.id}</div>
                <AssetTree nodes={ch.assets} charId={ch.id} onAdd={addToCanvas} depth={0} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function AssetTree({ nodes, charId, onAdd, depth }) {
  const pad = { paddingLeft: depth * 10 }
  if (!nodes || !nodes.length) return <div style={{...pad, color: C.sub}}>（空）</div>
  return <div>
    {nodes.map(node => {
      if (node.type === 'dir') return <div key={node.path} style={pad}><div style={{ color: C.sub, marginTop: 3 }}>📁 {node.name}</div><AssetTree nodes={node.children} charId={charId} onAdd={onAdd} depth={depth+1} /></div>
      const img = ['.png','.jpg','.jpeg','.webp'].includes(node.ext)
      return <div key={node.path} style={{...pad, display:'flex', alignItems:'center', gap:4, margin:'2px 0'}}>
        <span style={{ color: C.text }}>{img?'🖼️':'🔊'} {node.name}</span>
        <button style={{ marginLeft:'auto', fontSize:11, cursor:'pointer' }} onClick={() => onAdd(charId, node.path)}>+画布</button>
      </div>
    })}
  </div>
}

// ---- 人设面板 ----
function PersonaTab({ chars, refresh, setMsg }) {
  const [llmText, setLlmText] = useState('')
  const [llmBusy, setLlmBusy] = useState(false)
  const [formKey, setFormKey] = useState(0)
  const [prefill, setPrefill] = useState(null)

  const upload = async (fd) => {
    const r = await fetch('/api/characters', { method: 'POST', body: fd })
    const j = await r.json(); setMsg(`已创建角色 ${j.id}`); refresh()
  }
  const llmFill = async () => {
    if (!llmText.trim()) { setMsg('先输入人设描述'); return }
    setLlmBusy(true); setMsg('LLM 生成人设中...')
    try {
      const r = await fetch('/api/persona/llm', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ text: llmText }) })
      const j = await r.json()
      if (!r.ok) { setMsg('LLM 失败: ' + (j.detail || '')); return }
      setPrefill(j); setFormKey(k => k+1); setMsg('LLM 人设已生成，可编辑后创建')
    } catch(e) { setMsg('LLM 调用失败') }
    finally { setLlmBusy(false) }
  }
  return <div>
    <h4 style={{ color: C.text, margin: '4px 0' }}>导入 persona.json</h4>
    <form onSubmit={(e) => { e.preventDefault(); const fd = new FormData(); const f = e.target.persona.files[0]; if (!f) { setMsg('选文件'); return } fd.append('persona', f); if (e.target.ref.files[0]) fd.append('ref_image', e.target.ref.files[0]); upload(fd) }}>
      <input type="file" name="persona" accept=".json" style={input} /><div style={{height:6}}/>
      <input type="file" name="ref" accept="image/*" style={input} /><div style={{height:8}}/>
      <button style={btn}>导入角色</button>
    </form>
    <hr style={{ borderColor: C.border, margin: '12px 0' }} />
    <h4 style={{ color: C.text, margin: '4px 0' }}>LLM 填充人设</h4>
    <textarea value={llmText} onChange={e => setLlmText(e.target.value)} placeholder="例：一个来自北方森林的精灵游侠，冷静敏锐，绿色皮甲配复合弓，银白长发翠瞳，像素风格" style={{...input, height: 70 }} />
    <div style={{ height: 8 }} />
    <button onClick={llmFill} disabled={llmBusy} style={btn}>{llmBusy ? '生成中...' : 'LLM 生成人设'}</button>
    <hr style={{ borderColor: C.border, margin: '12px 0' }} />
    <h4 style={{ color: C.text, margin: '4px 0' }}>在线实时创建</h4>
    <PersonaForm key={formKey} prefill={prefill} onCreate={upload} dark />
    <hr style={{ borderColor: C.border, margin: '12px 0' }} />
    <h4 style={{ color: C.text, margin: '4px 0' }}>已有角色（{chars.length}）</h4>
    {chars.map(ch => <div key={ch.id} style={{ background: C.card, borderRadius: 6, padding: 8, marginBottom: 6, fontSize: 13 }}>{ch.id}</div>)}
  </div>
}

// ---- 资产创建面板 ----
function CreateTab({ chars, setMsg }) {
  const [charId, setCharId] = useState('')
  const [scene, setScene] = useState('splash')
  const [refs, setRefs] = useState([])
  const [ref, setRef] = useState('')
  const [backend, setBackend] = useState('openai')
  const [busy, setBusy] = useState(false)
  useEffect(() => { fetch('/api/refs').then(r => r.json()).then(setRefs).catch(()=>{}) }, [])
  const run = async () => {
    if (!charId) { setMsg('先选择角色'); return }
    setBusy(true); setMsg('提交生成...')
    const r = await fetch(`/api/characters/${charId}/generate`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ scene }) })
    const j = await r.json(); setMsg(`已提交 ${j.job_id}`); setBusy(false)
  }
  return <div>
    <label style={label}>角色</label>
    <select style={input} value={charId} onChange={e => setCharId(e.target.value)}>
      <option value="">选择角色</option>
      {chars.map(ch => <option key={ch.id} value={ch.id}>{ch.id}</option>)}
    </select>
    <label style={label}>资产意图（风格）</label>
    <select style={input} value={scene} onChange={e => setScene(e.target.value)}>
      <option value="splash">立绘（高清 2D，含表情拼图）</option>
      <option value="pixel">像素（三视图+行为帧）</option>
    </select>
    <label style={label}>风格参考图（可选）</label>
    <select style={input} value={ref} onChange={e => setRef(e.target.value)}>
      <option value="">无（默认画风）</option>
      {refs.map(g => g.files.map(f => <option key={g.group+'/'+f} value={`assets/reference/${g.group}/${f}`}>{g.group}/{f}</option>))}
    </select>
    <label style={label}>生图后端</label>
    <select style={input} value={backend} onChange={e => setBackend(e.target.value)}>
      <option value="openai">openai（中转站 gpt-image-2）</option>
      <option value="gemini">gemini（Nano Banana，需 key）</option>
      <option value="fal">fal（需 key）</option>
    </select>
    <div style={{ height: 12 }} />
    <button onClick={run} disabled={busy} style={btn}>{busy ? '提交中...' : '开始生成'}</button>
    <div style={{ fontSize: 11, color: C.sub, marginTop: 8 }}>生成进度见右上角 Job（后续版本加状态栏）；产物在右侧"角色资产"。</div>
  </div>
}

// ---- 参考图面板 ----
function RefsTab() {
  const [refs, setRefs] = useState([])
  useEffect(() => { fetch('/api/refs').then(r => r.json()).then(setRefs).catch(()=>{}) }, [])
  return <div>
    <h4 style={{ color: C.text, margin: '4px 0' }}>参考图库</h4>
    {refs.map(g => (
      <div key={g.group} style={{ marginBottom: 12 }}>
        <div style={{ color: C.accent, fontWeight: 600, fontSize: 13 }}>{g.group}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
          {g.files.map(f => (
            <div key={f} title={f} style={{ width: 60, height: 60, overflow: 'hidden', borderRadius: 4, border: `1px solid ${C.border}`, background: '#111' }}>
              <img src={`/char-assets/../reference/${g.group}/${f}`.replace('/char-assets/..', '')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => { e.target.style.display='none' }} />
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
}

// ---- 配置面板 ----
function ConfigTab({ setMsg }) {
  const [cfg, setCfg] = useState({})
  useEffect(() => { fetch('/api/config').then(r => r.json()).then(setCfg).catch(()=>{}) }, [])
  const fields = [
    ['GPT_API_KEY','GPT 生图 key'], ['GPT_BASE_URL','GPT base_url'],
    ['GEMINI_API_KEY','Gemini（Nano Banana）key'], ['FAL_KEY','fal key'],
    ['VOLC_API_KEY','火山 TTS key'], ['LLM_API_KEY','LLM key（人设填充）'], ['LLM_BASE_URL','LLM base_url'], ['LLM_MODEL','LLM model']
  ]
  const save = async () => {
    const r = await fetch('/api/config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(cfg) })
    setMsg((await r.json()).ok ? '配置已保存' : '保存失败')
  }
  return <div>
    <h4 style={{ color: C.text, margin: '4px 0' }}>API Keys / 配置</h4>
    {fields.map(([k, lab]) => (
      <div key={k}>
        <label style={label}>{lab}</label>
        <input style={input} value={cfg[k] || ''} onChange={e => setCfg({...cfg, [k]: e.target.value})} placeholder={cfg[k] && cfg[k].startsWith('***') ? '已配置（留空不变）' : ''} />
      </div>
    ))}
    <div style={{ height: 10 }} />
    <button onClick={save} style={btn}>保存配置</button>
    <div style={{ fontSize: 11, color: C.sub, marginTop: 8 }}>key 保存在本地 env/.env，掩码显示不回显。</div>
  </div>
}