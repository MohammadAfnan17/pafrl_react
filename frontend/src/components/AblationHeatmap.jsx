export default function AblationHeatmap({ ablation }) {
  if (!ablation) return null

  const cells = [
    { key: 'FRL-SARSA+Fixed', row: 0, col: 0, label: 'FRL-SARSA / Fixed' },
    { key: 'FRL-SARSA+Adaptive', row: 0, col: 1, label: 'FRL-SARSA / Adaptive' },
    { key: 'PA-SARSA+Fixed', row: 1, col: 0, label: 'PA-SARSA / Fixed' },
    { key: 'PA-SARSA+Adaptive', row: 1, col: 1, label: 'PA-SARSA / Adaptive' },
  ]

  const values = cells.map((c) => ablation[c.key]?.pdst_pct ?? 0)
  const min = Math.min(...values)
  const max = Math.max(...values)

  const colorFor = (v) => {
    const t = max === min ? 0.5 : (v - min) / (max - min)
    const r = Math.round(251 - t * (251 - 34))
    const g = Math.round(191 + t * (197 - 191))
    const b = Math.round(36 + t * (94 - 36))
    return `rgb(${r},${g},${b})`
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">2×2 ABLATION — PDST (%)</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, maxWidth: 420, margin: '0 auto' }}>
        {cells.map((c) => {
          const v = ablation[c.key]?.pdst_pct
          return (
            <div key={c.key} style={{
              background: colorFor(v ?? 0), borderRadius: 10, padding: '20px 12px',
              textAlign: 'center', color: '#0a0a0a',
            }}>
              <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--mono)' }}>
                {v ?? '—'}%
              </div>
              <div style={{ fontSize: 10, marginTop: 6, fontWeight: 600 }}>{c.label}</div>
            </div>
          )
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, fontSize: 10, color: 'var(--muted)', maxWidth: 420, margin: '12px auto 0' }}>
        <span>← FDA Type: Fixed | Adaptive →</span>
      </div>
    </div>
  )
}
