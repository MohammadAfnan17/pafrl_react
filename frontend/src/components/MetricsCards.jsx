export default function MetricsCards({ metrics }) {
  if (!metrics) return null
  const m = metrics.pa_frl || {}
  const fcfs = metrics.fcfs || {}

  const delta = (a, b) => (a - b).toFixed(1)
  const stDelta = fcfs.avg_st_ms ? delta(fcfs.avg_st_ms, m.avg_st_ms) : null
  const pdstDelta = fcfs.pdst_pct ? delta(m.pdst_pct, fcfs.pdst_pct) : null

  const cards = [
    { label: 'PDST (%)', value: m.pdst_pct, color: 'var(--green)', sub: pdstDelta ? `+${pdstDelta} vs FCFS` : '' },
    { label: 'AVG SERVICE TIME (ms)', value: m.avg_st_ms, color: 'var(--accent)', sub: stDelta ? `-${stDelta}ms vs FCFS` : '' },
    { label: 'CRITICAL PDST (%)', value: m.pdst_critical, color: 'var(--red)', sub: 'urgent tasks' },
    { label: 'AVG PENALTY (ms)', value: m.avg_penalty_ms, color: 'var(--purple)', sub: 'over deadline' },
  ]

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">PA-FRL PERFORMANCE METRICS</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
        {cards.map((c, i) => (
          <div key={i} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 12, padding: 14, textAlign: 'center',
          }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 24, fontWeight: 700, color: c.color }}>
              {c.value ?? '—'}
            </div>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1, marginTop: 4 }}>{c.label}</div>
            {c.sub && (
              <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--muted)', marginTop: 6 }}>{c.sub}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
