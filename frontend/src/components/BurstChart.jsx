import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend,
} from 'recharts'

export default function BurstChart({ burst }) {
  if (!burst) return null

  const data = burst.fixed_load.map((v, i) => ({
    idx: i,
    fixed_load: v,
    adaptive_load: burst.adaptive_load[i],
    fixed_rate: burst.fixed_rate[i],
    adaptive_rate: burst.adaptive_rate[i],
  }))

  const [b0, b1] = burst.burst_window

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">
        BURST-LOAD STRESS TEST
        <span className="badge badge-g">{burst.reduction_pct}% LOAD REDUCTION</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6, textAlign: 'center' }}>
            Fraction Routed to Fog (rolling)
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
              <ReferenceArea x1={b0} x2={b1} fill="#ff4757" fillOpacity={0.08} />
              <XAxis dataKey="idx" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="fixed_rate" name="Fixed FDA" stroke="#00d4ff" strokeWidth={1.6} dot={false} />
              <Line type="monotone" dataKey="adaptive_rate" name="Adaptive FDA" stroke="#00ff9d" strokeWidth={1.6} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6, textAlign: 'center' }}>
            Resulting Fog Load (lower = healthier)
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
              <ReferenceArea x1={b0} x2={b1} fill="#ff4757" fillOpacity={0.08} />
              <XAxis dataKey="idx" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="fixed_load" name="Fixed FDA" stroke="#00d4ff" strokeWidth={1.6} dot={false} />
              <Line type="monotone" dataKey="adaptive_load" name="Adaptive FDA" stroke="#00ff9d" strokeWidth={1.6} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div style={{ marginTop: 10, fontSize: 11, color: 'var(--muted)', textAlign: 'center' }}>
        Shaded region = simulated 150-task arrival burst (between two 100-task normal phases)
      </div>
    </div>
  )
}
