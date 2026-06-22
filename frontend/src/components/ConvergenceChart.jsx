import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ConvergenceChart({ rewards }) {
  if (!rewards || !rewards.length) return null

  // Smooth with rolling average
  const w = Math.min(8, rewards.length)
  const data = rewards.map((_, i) => {
    const slice = rewards.slice(Math.max(0, i - w + 1), i + 1)
    const avg = slice.reduce((a, b) => a + b, 0) / slice.length
    return { episode: i + 1, reward: Math.round(avg * 10) / 10 }
  })

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">SARSA TRAINING CONVERGENCE</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2d45" />
          <XAxis dataKey="episode" tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <Tooltip contentStyle={{ background: '#101e30', border: '1px solid #1a2d45' }} />
          <Line type="monotone" dataKey="reward" stroke="#00d4ff" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
