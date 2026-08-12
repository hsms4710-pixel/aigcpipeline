import React, { useState } from 'react'

export default function PersonaForm({ onCreate }) {
  const [open, setOpen] = useState(false)
  const [f, setF] = useState({
    name: '', race: '', class: '', personality: '', background: '',
    subject: '', equipment: '', outfit: '', detail: '',
    styleType: 'splash', palette: '', resolution: '1024x1024',
    assets: { three_view: true, actions: true, sprite_sheet: false, directional: false,
              portrait: true, expressions: true, turnaround: false, action: false },
  })
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const setAsset = (k) => (e) => setF({ ...f, assets: { ...f.assets, [k]: e.target.checked } })

  const submit = async (e) => {
    e.preventDefault()
    const persona = {
      name: f.name || '未命名角色',
      race: f.race, class: f.class,
      personality_tags: f.personality.split(/[,，]/).map(s => s.trim()).filter(Boolean),
      background: f.background,
      visual: { subject: f.subject, equipment: f.equipment, outfit: f.outfit, detail: f.detail },
      style: { type: f.styleType, palette: f.palette || undefined, resolution: f.resolution },
      assets: {
        pixel: ['three_view','actions','sprite_sheet','directional'].filter(k => f.assets[k]),
        splash: ['portrait','expressions','turnaround','action'].filter(k => f.assets[k]),
      },
    }
    const blob = new Blob([JSON.stringify(persona, null, 2)], { type: 'application/json' })
    const fd = new FormData()
    fd.append('persona', new File([blob], 'persona.json', { type: 'application/json' }))
    await onCreate(fd)
    setOpen(false)
  }

  if (!open) return <button onClick={() => setOpen(true)} style={{ width: '100%', padding: 8, cursor: 'pointer' }}>✏️ 人设卡编辑器（新建角色）</button>

  const L = ({ children }) => <label style={{ display: 'block', margin: '6px 0 2px', fontSize: 12, color: '#555' }}>{children}</label>
  const I = (props) => <input {...props} style={{ width: '100%', boxSizing: 'border-box', padding: 4 }} />
  return (
    <form onSubmit={submit} style={{ border: '1px solid #4a9eff', borderRadius: 8, padding: 10, background: '#f0f7ff' }}>
      <b>人设卡编辑器</b>
      <L>名字</L><I value={f.name} onChange={set('name')} />
      <L>种族 / 职业</L><I value={f.race} onChange={set('race')} placeholder="种族" /><I value={f.class} onChange={set('class')} placeholder="职业" />
      <L>性格（逗号分隔）</L><I value={f.personality} onChange={set('personality')} />
      <L>背景</L><I value={f.background} onChange={set('background')} />
      <L>主体（性别/年龄/体型）</L><I value={f.subject} onChange={set('subject')} />
      <L>装备 / 服饰 / 细节</L><I value={f.equipment} onChange={set('equipment')} placeholder="装备" /><I value={f.outfit} onChange={set('outfit')} placeholder="服饰" /><I value={f.detail} onChange={set('detail')} placeholder="细节（发型/瞳色等）" />
      <L>风格</L>
      <select value={f.styleType} onChange={set('styleType')} style={{ width: '100%', padding: 4 }}>
        <option value="splash">立绘（高清）</option><option value="pixel">像素</option>
      </select>
      <L>调色板 / 分辨率</L><I value={f.palette} onChange={set('palette')} placeholder="如 16-bit" /><I value={f.resolution} onChange={set('resolution')} />
      <L>需要生成的资产</L>
      <div style={{ fontSize: 12 }}>
        {f.styleType === 'pixel' ? <>
          <label><input type="checkbox" checked={f.assets.three_view} onChange={setAsset('three_view')} /> 三视图</label>{' '}
          <label><input type="checkbox" checked={f.assets.actions} onChange={setAsset('actions')} /> 行为帧</label>{' '}
          <label><input type="checkbox" checked={f.assets.sprite_sheet} onChange={setAsset('sprite_sheet')} /> 精灵表</label>{' '}
          <label><input type="checkbox" checked={f.assets.directional} onChange={setAsset('directional')} /> 方向表</label>
        </> : <>
          <label><input type="checkbox" checked={f.assets.portrait} onChange={setAsset('portrait')} /> 主立绘</label>{' '}
          <label><input type="checkbox" checked={f.assets.expressions} onChange={setAsset('expressions')} /> 表情</label>{' '}
          <label><input type="checkbox" checked={f.assets.turnaround} onChange={setAsset('turnaround')} /> 转面</label>
        </>}
      </div>
      <button type="submit" style={{ marginTop: 8, padding: '6px 14px', cursor: 'pointer' }}>创建角色</button>{' '}
      <button type="button" onClick={() => setOpen(false)} style={{ padding: '6px 10px', cursor: 'pointer' }}>取消</button>
    </form>
  )
}
