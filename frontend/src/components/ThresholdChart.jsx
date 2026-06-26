import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'

export default function ThresholdChart({ classification, params }) {
  if (!classification) return null
  const { threshold_trace, load_trace } = classification

  const data = threshold_trace.map((th, i) => ({
    idx: i,
    threshold: Math.round(th * 1000) / 1000,
    load: Math.round((load_trace[i] ?? 0) * 1000) / 1000,
  }))

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">
        FUZZY CLASSIFICATION
        <span className="badge badge-g">
          FOG {classification.fog_pct}% / CLOUD {classification.cloud_pct}%
        </span>
      </div>
      <div className="chart-grid">
        <div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6, textAlign: 'center' }}>
            Real-Time Fog Load Signal
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
              <XAxis dataKey="idx" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
              <Area type="monotone" dataKey="load" stroke="#fb923c" fill="#fb923c" fillOpacity={0.2} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6, textAlign: 'center' }}>
            {params.use_adaptive ? 'Adaptive vs Fixed Threshold' : 'Fixed Threshold (adaptive OFF)'}
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
              <XAxis dataKey="idx" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
              <ReferenceLine y={params.v_base} stroke="#00d4ff" strokeDasharray="5 5" />
              <Line type="monotone" dataKey="threshold" stroke="#00ff9d" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
