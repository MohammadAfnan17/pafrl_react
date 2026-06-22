const PRIORITY_COLORS = {
  CRITICAL: '#ff4757', HIGH: '#ff8c42', MEDIUM: '#ffd700', LOW: '#00ff9d',
}

export default function TaskLogTable({ log }) {
  if (!log || !log.length) return null

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">
        TASK SCHEDULING LOG (PA-FRL)
        <span className="badge">{log.length} SHOWN</span>
      </div>
      <div style={{ maxHeight: 280, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
          <thead>
            <tr>
              {['ID', 'TYPE', 'PRIORITY', 'DEADLINE', 'SERVICE TIME', 'FOG NODE', 'MET?'].map((h) => (
                <th key={h} style={{
                  fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--muted)',
                  padding: '8px 10px', borderBottom: '1px solid var(--border)',
                  textAlign: 'left', position: 'sticky', top: 0, background: 'var(--card)',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {log.map((r, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(26,45,69,.4)' }}>
                <td style={{ padding: '7px 10px', fontFamily: 'var(--mono)' }}>#{r.task_id}</td>
                <td style={{ padding: '7px 10px' }}>{r.type}</td>
                <td style={{ padding: '7px 10px' }}>
                  <span style={{
                    fontFamily: 'var(--mono)', fontSize: 9, padding: '2px 8px', borderRadius: 6,
                    color: PRIORITY_COLORS[r.priority], border: `1px solid ${PRIORITY_COLORS[r.priority]}44`,
                    background: `${PRIORITY_COLORS[r.priority]}18`,
                  }}>{r.priority}</span>
                </td>
                <td style={{ padding: '7px 10px', fontFamily: 'var(--mono)' }}>{r.deadline}</td>
                <td style={{
                  padding: '7px 10px', fontFamily: 'var(--mono)',
                  color: r.deadline_met ? 'var(--green)' : 'var(--red)',
                }}>{r.st_ms}</td>
                <td style={{ padding: '7px 10px', fontFamily: 'var(--mono)', color: 'var(--accent)' }}>F{r.fog_node}</td>
                <td style={{ padding: '7px 10px', color: r.deadline_met ? 'var(--green)' : 'var(--red)' }}>
                  {r.deadline_met ? '✓' : '✗'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
