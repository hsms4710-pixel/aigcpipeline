import React, { useEffect, useState, useRef } from 'react'
import { Tldraw, useEditor } from '@tldraw/tldraw'
import PersonaForm from './PersonaForm.jsx'
import '@tldraw/tldraw/tldraw.css'

function AddToCanvas({ onAdd }) {
  return <button style={{ margin: 4, padding: '6px 12px', cursor: 'pointer' }} onClick={onAdd}>添加到画布</button>
}

export default function App() {
  const [chars, setChars] = useState([])
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const editorRef = useRef(null)

  const refresh = async () => {
    const r = await fetch('/api/characters')
    setChars(await r.json())
  }
  useEffect(() => { refresh(); const t = setInterval(refresh, 5000); return () => clearInterval(t) }, [])

  const uploadFromForm = async (fd) => {
    setBusy(true)
    const r = await fetch('/api/characters', { method: 'POST', body: fd })
    const j = await r.json()
    setMsg(已创建角色 )
    setBusy(false); refresh()
  }

  const upload = async (e) => {
    e.preventDefault()
    const fd = new FormData()
    const pf = e.target.persona.files[0]
    if (!pf) { setMsg('请选择 persona.json'); return }
    fd.append('persona', pf)
    if (e.target.ref.files[0]) fd.append('ref_image', e.target.ref.files[0])
    setBusy(true)
    const r = await fetch('/api/characters', { method: 'POST', body: fd })
    const j = await r.json()
    setMsg(`已创建角色 ${j.id}`)
    setBusy(false); refresh()
  }

  const generate = async (id, scene) => {
    setMsg('提交生成...')
    const r = await fetch(`/api/characters/${id}/generate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ scene })
    })
    const j = await r.json()
    setMsg(`已提交 job ${j.job_id}（中转站恢复后自动跑通）`)
    poll(j.job_id)
  }

  const poll = async (jobId) => {
    for (let i = 0; i < 120; i++) {
      const r = await fetch(`/api/jobs/${jobId}`); const j = await r.json()
      if (j.status === 'done' || j.status === 'failed') {
        setMsg(`job ${j.status}: ${j.stage} ${(j.message || '').slice(0, 120)}`)
        refresh(); return
      }
      setMsg(`生成中: ${j.stage}/${j.status}`)
      await new Promise(r2 => setTimeout(r2, 3000))
    }
  }

  const addToCanvas = (path) => {
    const ed = editorRef.current
    if (!ed) return
    const url = '/char-assets/' + selected.id + '/' + path
    const c = ed.getViewportPageBounds()
    ed.createShape({
      type: 'image',
      x: c.minX + Math.random() * 200,
      y: c.minY + Math.random() * 200,
      props: { src: url, w: 160, h: 160 }
    })
  }

  const filesOf = (node, out = []) => {
    if (node.type === 'file' && ['.png', '.jpg', '.jpeg', '.webp', '.wav', '.mp3'].includes(node.ext)) out.push(node)
    if (node.children) node.children.forEach(ch => filesOf(ch, out))
    return out
  }

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* 侧栏 */}
      <div style={{ width: 300, borderRight: '1px solid #ddd', padding: 12, overflowY: 'auto', background: '#fafafa' }}>
        <h3 style={{ marginTop: 0 }}>角色 AIGC 工作台</h3>
        <PersonaForm onCreate={uploadFromForm} />
        <hr />
        <h4>或上传 persona.json</h4>
        <form onSubmit={upload}>
          <div style={{ margin: '6px 0' }}><input type="file" name="persona" accept=".json" /></div>
          <div style={{ margin: '6px 0' }}><input type="file" name="ref" accept="image/*" /></div>
          <button disabled={busy} style={{ cursor: 'pointer', padding: '6px 14px' }}>创建角色</button>
        </form>
        <div style={{ fontSize: 12, color: '#666', margin: '6px 0' }}>{msg}</div>
        <h4>角色列表</h4>
        {chars.map(ch => (
          <div key={ch.id} style={{ border: selected === ch.id ? '2px solid #4a9eff' : '1px solid #ddd', borderRadius: 6, padding: 8, marginBottom: 8, cursor: 'pointer', background: '#fff' }}
               onClick={() => setSelected(ch.id)}>
            <b>{ch.id}</b>
            <div style={{ marginTop: 6 }}>
              <button style={{ marginRight: 4 }} onClick={(e) => { e.stopPropagation(); generate(ch.id, 'pixel') }}>像素生成</button>
              <button onClick={(e) => { e.stopPropagation(); generate(ch.id, 'splash') }}>立绘生成</button>
            </div>
          </div>
        ))}
      </div>
      {/* 画布区 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Tldraw onMount={(ed) => { editorRef.current = ed }} />
        {selected && (
          <div style={{ position: 'absolute', right: 12, top: 12, width: 220, background: '#fff', border: '1px solid #ddd', borderRadius: 8, padding: 8, maxHeight: '60vh', overflowY: 'auto', zIndex: 100 }}>
            <b>{selected} 资产</b>
            {chars.find(c => c.id === selected)?.assets.map((node) => (
              <AssetRow key={node.path} node={node} charId={selected} onAdd={addToCanvas} depth={0} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function AssetRow({ node, charId, onAdd, depth }) {
  const pad = { paddingLeft: depth * 12 }
  if (node.type === 'dir')
    return (
      <div style={pad}>
        <div style={{ fontWeight: 600, marginTop: 4 }}>📁 {node.name}</div>
        {node.children.map(ch => <AssetRow key={ch.path} node={ch} charId={charId} onAdd={onAdd} depth={depth + 1} />)}
      </div>
    )
  const isImg = ['.png', '.jpg', '.jpeg', '.webp'].includes(node.ext)
  return (
    <div style={{ ...pad, display: 'flex', alignItems: 'center', gap: 6, margin: '3px 0', fontSize: 12 }}>
      <span>{isImg ? '🖼️' : '🔊'} {node.name}</span>
      <button style={{ marginLeft: 'auto', cursor: 'pointer', fontSize: 11 }} onClick={() => onAdd(node.path)}>+画布</button>
    </div>
  )
}
