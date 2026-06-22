import './ControlPanel.css'

export default function ControlPanel({ params, setParams, onRun, onAblation, onBurst, loading, status }) {
  const upd = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : Number(e.target.value)
    setParams((p) => ({ ...p, [key]: val }))
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">SIMULATION PARAMETERS</div>

      <div className="ctrl-grid">
        <div className="ctrl-item">
          <label>IoT Tasks <span className="val">{params.num_tasks}</span></label>
          <input type="range" min="50" max="500" step="25" value={params.num_tasks} onChange={upd('num_tasks')} />
        </div>
        <div className="ctrl-item">
          <label>Fog Nodes <span className="val">{params.num_fog_nodes}</span></label>
          <input type="range" min="5" max="60" step="5" value={params.num_fog_nodes} onChange={upd('num_fog_nodes')} />
        </div>
        <div className="ctrl-item">
          <label>SARSA Episodes <span className="val">{params.episodes}</span></label>
          <input type="range" min="50" max="600" step="50" value={params.episodes} onChange={upd('episodes')} />
        </div>
        <div className="ctrl-item">
          <label>Random Seed <span className="val">{params.seed}</span></label>
          <input type="range" min="1" max="50" step="1" value={params.seed} onChange={upd('seed')} />
        </div>
        <div className="ctrl-item">
          <label>Base Threshold V<sub>base</sub> <span className="val">{params.v_base.toFixed(2)}</span></label>
          <input type="range" min="0.3" max="0.8" step="0.05" value={params.v_base} onChange={upd('v_base')} />
        </div>
        <div className="ctrl-item">
          <label>Adaptive Sensitivity α <span className="val">{params.alpha_th.toFixed(2)}</span></label>
          <input type="range" min="0.05" max="0.5" step="0.05" value={params.alpha_th} onChange={upd('alpha_th')} />
        </div>
      </div>

      <div className="toggle-row">
        <label className="toggle">
          <input type="checkbox" checked={params.use_priority} onChange={upd('use_priority')} />
          <span>Priority-Aware Reward (Novelty #1)</span>
        </label>
        <label className="toggle">
          <input type="checkbox" checked={params.use_adaptive} onChange={upd('use_adaptive')} />
          <span>Adaptive Threshold (Novelty #2)</span>
        </label>
      </div>

      <div className="btn-row">
        <button className="btn btn-primary" disabled={loading} onClick={onRun}>
          ▶ RUN PIPELINE
        </button>
        <button className="btn btn-secondary" disabled={loading} onClick={onAblation}>
          ⊞ 2×2 ABLATION
        </button>
        <button className="btn btn-secondary" disabled={loading} onClick={onBurst}>
          ⚡ BURST TEST
        </button>
      </div>

      <div className="status-bar">
        <span className="status-dot" style={{ background: loading ? '#ffd700' : '#00ff9d' }} />
        <span>{status}</span>
      </div>
    </div>
  )
}
