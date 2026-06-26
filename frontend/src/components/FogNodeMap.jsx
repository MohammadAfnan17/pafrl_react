export default function FogNodeMap({ fogNodes }) {
  if (!fogNodes || !fogNodes.length) return null
  const maxTasks = Math.max(...fogNodes.map((f) => f.tasks), 1)

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">
        FOG NODE UTILISATION
        <span className="badge">{fogNodes.length} NODES</span>
      </div>
      <div style={{
        display: 'flex', flexDirection: 'column', gap: 6,
        maxHeight: 260, overflowY: 'auto', paddingRight: 4,
      }}>
        {fogNodes.map((fn) => (
          <div key={fn.id} className="fog-node-row">
            <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--accent)' }}>
              F{fn.id}
            </span>
            <span style={{ fontSize: 10, color: 'var(--muted)' }}>
              {fn.capacity} MIPS
            </span>
            <div style={{ flex: 1, height: 8, background: 'var(--border)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 4,
                width: `${(fn.tasks / maxTasks) * 100}%`,
                background: 'linear-gradient(90deg, #00d4ff, #00ff9d)',
                transition: 'width .6s ease',
              }} />
            </div>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>
              {fn.tasks} tasks ({fn.utilisation}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
