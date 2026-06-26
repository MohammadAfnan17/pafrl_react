import './ControlPanel.css'

export default function ControlPanel({ params, setParams, onRun, onAblation, onBurst, loading, status }) {
  const upd = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : Number(e.target.value)
    setParams((p) => ({ ...p, [key]: val }))
  }
  const updPriority = (key) => (e) => {
    const val = Number(e.target.value)
    setParams((p) => ({
      ...p,
      priority_weights: { ...p.priority_weights, [key]: val },
    }))
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-title">SIMULATION PARAMETERS</div>

      <div className="ctrl-section">Workload</div>
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
          <label>Mean Arrival Gap (ms) <span className="val">{params.mean_inter_arrival_ms}</span></label>
          <input type="range" min="10" max="250" step="10" value={params.mean_inter_arrival_ms} onChange={upd('mean_inter_arrival_ms')} />
        </div>
        <div className="ctrl-item">
          <label>Task Log Limit <span className="val">{params.task_log_limit}</span></label>
          <input type="range" min="20" max="200" step="20" value={params.task_log_limit} onChange={upd('task_log_limit')} />
        </div>
      </div>

      <div className="ctrl-section">Fog Network</div>
      <div className="ctrl-grid">
        <div className="ctrl-item">
          <label>Min Capacity (MIPS) <span className="val">{params.fog_cap_min}</span></label>
          <input type="range" min="500" max="5000" step="250" value={params.fog_cap_min} onChange={upd('fog_cap_min')} />
        </div>
        <div className="ctrl-item">
          <label>Max Capacity (MIPS) <span className="val">{params.fog_cap_max}</span></label>
          <input type="range" min="2000" max="10000" step="250" value={params.fog_cap_max} onChange={upd('fog_cap_max')} />
        </div>
        <div className="ctrl-item">
          <label>Bandwidth (Mbps) <span className="val">{params.fog_bandwidth}</span></label>
          <input type="range" min="100" max="5000" step="100" value={params.fog_bandwidth} onChange={upd('fog_bandwidth')} />
        </div>
      </div>

      <div className="ctrl-section">Fuzzy & SARSA</div>
      <div className="ctrl-grid">
        <div className="ctrl-item">
          <label>Base Threshold V<sub>base</sub> <span className="val">{params.v_base.toFixed(2)}</span></label>
          <input type="range" min="0.3" max="0.8" step="0.05" value={params.v_base} onChange={upd('v_base')} />
        </div>
        <div className="ctrl-item">
          <label>Adaptive Sensitivity α <span className="val">{params.alpha_th.toFixed(2)}</span></label>
          <input type="range" min="0.05" max="0.5" step="0.05" value={params.alpha_th} onChange={upd('alpha_th')} />
        </div>
        <div className="ctrl-item">
          <label>SARSA α <span className="val">{params.sarsa_alpha.toFixed(2)}</span></label>
          <input type="range" min="0.05" max="1" step="0.05" value={params.sarsa_alpha} onChange={upd('sarsa_alpha')} />
        </div>
        <div className="ctrl-item">
          <label>SARSA γ <span className="val">{params.sarsa_gamma.toFixed(2)}</span></label>
          <input type="range" min="0.1" max="1" step="0.05" value={params.sarsa_gamma} onChange={upd('sarsa_gamma')} />
        </div>
        <div className="ctrl-item">
          <label>Policy ε <span className="val">{params.sarsa_epsilon.toFixed(2)}</span></label>
          <input type="range" min="0" max="1" step="0.05" value={params.sarsa_epsilon} onChange={upd('sarsa_epsilon')} />
        </div>
        <div className="ctrl-item">
          <label>ε Start <span className="val">{params.epsilon_start.toFixed(2)}</span></label>
          <input type="range" min="0" max="1" step="0.05" value={params.epsilon_start} onChange={upd('epsilon_start')} />
        </div>
        <div className="ctrl-item">
          <label>ε End <span className="val">{params.epsilon_end.toFixed(2)}</span></label>
          <input type="range" min="0" max="1" step="0.05" value={params.epsilon_end} onChange={upd('epsilon_end')} />
        </div>
      </div>

      <div className="ctrl-section">Priority Weights</div>
      <div className="ctrl-grid priority-grid">
        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((priority) => (
          <div className="ctrl-item" key={priority}>
            <label>{priority} <span className="val">{params.priority_weights[priority].toFixed(1)}</span></label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.1"
              value={params.priority_weights[priority]}
              onChange={updPriority(priority)}
            />
          </div>
        ))}
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
