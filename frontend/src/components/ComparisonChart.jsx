import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts'

const COLORS = { 'PA-FRL (Ours)': '#00ff9d', FCFS: '#ff4757', EDF: '#ffd700', GFE: '#a855f7' }

export default function ComparisonChart({ metrics }) {
  if (!metrics) return null

  const data = [
    { name: 'PA-FRL (Ours)', avg_st: metrics.pa_frl.avg_st_ms, pdst: metrics.pa_frl.pdst_pct },
    { name: 'EDF', avg_st: metrics.edf.avg_st_ms, pdst: metrics.edf.pdst_pct },
    { name: 'GFE', avg_st: metrics.gfe.avg_st_ms, pdst: metrics.gfe.pdst_pct },
    { name: 'FCFS', avg_st: metrics.fcfs.avg_st_ms, pdst: metrics.fcfs.pdst_pct },
  ]

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">ALGORITHM COMPARISON</div>
      <div className="chart-grid">
        <div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6, textAlign: 'center' }}>
            Average Service Time (ms)
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
              <Bar dataKey="avg_st" radius={[6, 6, 0, 0]}>
                {data.map((d, i) => <Cell key={i} fill={COLORS[d.name]} />)}
                <LabelList dataKey="avg_st" position="top" fill="#e2e8f0" fontSize={10} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6, textAlign: 'center' }}>
            Deadline Satisfaction (PDST %)
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
              <Bar dataKey="pdst" radius={[6, 6, 0, 0]}>
                {data.map((d, i) => <Cell key={i} fill={COLORS[d.name]} />)}
                <LabelList dataKey="pdst" position="top" fill="#e2e8f0" fontSize={10} formatter={(v) => `${v}%`} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
