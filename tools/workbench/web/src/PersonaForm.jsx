import React, { useState, useEffect } from 'react'

const C = { bg:'#2b2b2b', card:'#3a3a3a', border:'#444', text:'#e0e0e0', sub:'#9a9a9a', accent:'#6ea8fe' }
const input = { background:'#1a1a1a', color:C.text, border:`1px solid ${C.border}`, borderRadius:4, padding:'5px 8px', boxSizing:'border-box', width:'100%' }

export default function PersonaForm({ onCreate, dark, prefill }) {
  const [open, setOpen] = useState(false)
  const empty = {
    name:'', race:'', class:'', personality:'', background:'',
    subject:'', equipment:'', outfit:'', detail:'',
    styleType:'splash', palette:'', resolution:'1024x1024',
    assets:{ three_view:true, actions:true, sprite_sheet:false, directional:false,
             portrait:true, expressions:true, dialogue:true, turnaround:false }
  }
  const [f, setF] = useState(empty)
  useEffect(() => { if (prefill) applyPrefill(prefill) }, [prefill])
  const applyPrefill = (p) => {
    setF({
      name:p.name||'', race:p.race||'', class:p.class||'',
      personality:(p.personality_tags||[]).join(', '), background:p.background||'',
      subject:p.visual?.subject||'', equipment:p.visual?.equipment||'', outfit:p.visual?.outfit||'', detail:p.visual?.detail||'',
      styleType:p.style?.type||'splash', palette:p.style?.palette||'', resolution:p.style?.resolution||'1024x1024',
      assets:{ three_view:(p.assets?.pixel||[]).includes('three_view'), actions:(p.assets?.pixel||[]).includes('actions'),
               sprite_sheet:(p.assets?.pixel||[]).includes('sprite_sheet'), directional:(p.assets?.pixel||[]).includes('directional'),
               portrait:(p.assets?.splash||[]).includes('portrait'), expressions:(p.assets?.splash||[]).includes('expressions'),
               dialogue:(p.assets?.splash||[]).includes('dialogue'), turnaround:(p.assets?.splash||[]).includes('turnaround') }
    })
    setOpen(true)
  }
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const setAsset = (k) => (e) => setF({ ...f, assets: { ...f.assets, [k]: e.target.checked } })
  const submit = async (e) => {
    e.preventDefault()
    const persona = {
      name: f.name || '未命名角色', race: f.race, class: f.class,
      personality_tags: f.personality.split(/[,，]/).map(s=>s.trim()).filter(Boolean),
      background: f.background,
      visual: { subject: f.subject, equipment: f.equipment, outfit: f.outfit, detail: f.detail },
      style: { type: f.styleType, palette: f.palette || undefined, resolution: f.resolution },
      assets: {
        pixel: ['three_view','actions','sprite_sheet','directional'].filter(k=>f.assets[k]),
        splash: ['portrait','expressions','dialogue','turnaround'].filter(k=>f.assets[k]),
      },
    }
    const blob = new Blob([JSON.stringify(persona, null, 2)], { type:'application/json' })
    const fd = new FormData()
    fd.append('persona', new File([blob], 'persona.json', { type:'application/json' }))
    await onCreate(fd); setOpen(false)
  }
  if (!open) return <button onClick={() => setOpen(true)} style={{ width:'100%', padding:8, cursor:'pointer', background:C.card, color:C.text, border:`1px solid ${C.border}`, borderRadius:6 }}>✏️ 人设卡编辑器（新建角色）</button>
  const L = ({children}) => <label style={{ display:'block', margin:'6px 0 2px', fontSize:12, color:C.sub }}>{children}</label>
  return (
    <form onSubmit={submit} style={{ border:`1px solid ${C.accent}`, borderRadius:8, padding:10, background:C.card }}>
      <b style={{ color:C.text }}>人设卡编辑器</b>
      <L>名字</L><input style={input} value={f.name} onChange={set('name')} />
      <L>种族 / 职业</L><input style={input} value={f.race} onChange={set('race')} placeholder="种族" /><input style={{...input,marginTop:4}} value={f.class} onChange={set('class')} placeholder="职业" />
      <L>性格（逗号分隔）</L><input style={input} value={f.personality} onChange={set('personality')} />
      <L>背景</L><input style={input} value={f.background} onChange={set('background')} />
      <L>主体（性别/年龄/体型）</L><input style={input} value={f.subject} onChange={set('subject')} />
      <L>装备 / 服饰 / 细节</L><input style={input} value={f.equipment} onChange={set('equipment')} placeholder="装备" /><input style={{...input,marginTop:4}} value={f.outfit} onChange={set('outfit')} placeholder="服饰" /><input style={{...input,marginTop:4}} value={f.detail} onChange={set('detail')} placeholder="细节（发型/瞳色）" />
      <L>风格</L>
      <select style={input} value={f.styleType} onChange={set('styleType')}><option value="splash">立绘（高清）</option><option value="pixel">像素</option></select>
      <L>调色板 / 分辨率</L><input style={input} value={f.palette} onChange={set('palette')} placeholder="如 16-bit" /><input style={{...input,marginTop:4}} value={f.resolution} onChange={set('resolution')} />
      <L>需要生成的资产</L>
      <div style={{ fontSize:12, color:C.text }}>
        {f.styleType === 'pixel' ? <>
          <label><input type="checkbox" checked={f.assets.three_view} onChange={setAsset('three_view')} /> 三视图</label>{' '}
          <label><input type="checkbox" checked={f.assets.actions} onChange={setAsset('actions')} /> 行为帧</label>{' '}
          <label><input type="checkbox" checked={f.assets.sprite_sheet} onChange={setAsset('sprite_sheet')} /> 精灵表</label>
        </> : <>
          <label><input type="checkbox" checked={f.assets.portrait} onChange={setAsset('portrait')} /> 主立绘</label>{' '}
          <label><input type="checkbox" checked={f.assets.expressions} onChange={setAsset('expressions')} /> 表情</label>{' '}
          <label><input type="checkbox" checked={f.assets.dialogue} onChange={setAsset('dialogue')} /> 对话立绘</label>{' '}
          <label><input type="checkbox" checked={f.assets.turnaround} onChange={setAsset('turnaround')} /> 转面</label>
        </>}
      </div>
      <button type="submit" style={{ marginTop:8, padding:'6px 14px', cursor:'pointer', background:C.accent, color:'#111', border:'none', borderRadius:4 }}>创建角色</button>{' '}
      <button type="button" onClick={() => setOpen(false)} style={{ padding:'6px 10px', cursor:'pointer', background:C.bg, color:C.text, border:`1px solid ${C.border}`, borderRadius:4 }}>取消</button>
    </form>
  )
}