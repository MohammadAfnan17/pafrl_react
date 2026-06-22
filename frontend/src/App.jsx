import { useState, useEffect } from 'react'
import { api } from './api'
import ControlPanel from './components/ControlPanel'
import MetricsCards from './components/MetricsCards'
import ThresholdChart from './components/ThresholdChart'
import ComparisonChart from './components/ComparisonChart'
import ConvergenceChart from './components/ConvergenceChart'
import FogNodeMap from './components/FogNodeMap'
import TaskLogTable from './components/TaskLogTable'
import AblationHeatmap from './components/AblationHeatmap'
import BurstChart from './components/BurstChart'

const DEFAULT_PARAMS = {
  num_tasks: 300,
  num_fog_nodes: 30,
  episodes: 300,
  seed: 7,
  v_base: 0.55,
  alpha_th: 0.25,
  use_priority: true,
  use_adaptive: true,
}

export default function App() {
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('Ready — backend not yet checked')
  const [apiOnline, setApiOnline] = useState(false)

  const [runResult, setRunResult] = useState(null)
  const [ablation, setAblation] = useState(null)
  const [burst, setBurst] = useState(null)
  const [activeTab, setActiveTab] = useState('run')

  useEffect(() => {
    api.health()
      .then(() => { setApiOnline(true); setStatus('Backend connected — configure parameters and click RUN PIPELINE') })
      .catch(() => { setApiOnline(false); setStatus('⚠ Backend offline — start Flask: cd backend && python app.py') })
  }, [])

  async function handleRun() {
    setLoading(true)
    setStatus('Running PA-FRL pipeline (classification + SARSA training)...')
    setActiveTab('run')
    try {
      const data = await api.run(params)
      setRunResult(data)
      setStatus(`✓ Done — PDST: ${data.metrics.pa_frl.pdst_pct}% | Avg ST: ${data.metrics.pa_frl.avg_st_ms}ms | Fog tasks: ${data.metrics.pa_frl.total_tasks}`)
    } catch (e) {
      setStatus(`✗ Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleAblation() {
    setLoading(true)
    setStatus('Running 2×2 ablation matrix (4 SARSA trainings)...')
    setActiveTab('ablation')
    try {
      const data = await api.ablation(params)
      setAblation(data.ablation)
      setStatus('✓ Ablation complete — see heatmap below')
    } catch (e) {
      setStatus(`✗ Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleBurst() {
    setLoading(true)
    setStatus('Running burst-load stress test...')
    setActiveTab('burst')
    try {
      const data = await api.burst({ seed: params.seed })
      setBurst(data)
      setStatus(`✓ Burst test complete — ${data.reduction_pct}% fog load reduction during burst`)
    } catch (e) {
      setStatus(`✗ Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', position: 'relative', zIndex: 1 }}>
      <header style={{
        padding: '18px 28px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(180deg, rgba(0,212,255,.06), transparent)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10, background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
            boxShadow: '0 0 20px rgba(0,212,255,.4)',
          }}>⚡</div>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 18, color: 'var(--accent)', letterSpacing: 3 }}>PA-FRL</div>
            <div style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: 1 }}>
              PRIORITY-AWARE ADAPTIVE FUZZY REINFORCEMENT LEARNING · React + Python3
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: apiOnline ? 'var(--green)' : 'var(--red)',
            boxShadow: apiOnline ? '0 0 8px var(--green)' : 'none',
          }} />
          <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--muted)' }}>
            {apiOnline ? 'Flask API Connected' : 'API Offline'}
          </span>
        </div>
      </header>

      <main style={{ padding: '20px 28px', maxWidth: 1300, margin: '0 auto' }}>
        <ControlPanel
          params={params}
          setParams={setParams}
          onRun={handleRun}
          onAblation={handleAblation}
          onBurst={handleBurst}
          loading={loading}
          status={status}
        />

        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {['run', 'ablation', 'burst'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '8px 18px', borderRadius: 8, border: '1px solid var(--border)',
                background: activeTab === tab ? 'rgba(0,212,255,.12)' : 'transparent',
                color: activeTab === tab ? 'var(--accent)' : 'var(--muted)',
                fontFamily: 'var(--mono)', fontSize: 11, cursor: 'pointer',
                borderColor: activeTab === tab ? 'var(--accent)' : 'var(--border)',
              }}
            >
              {tab === 'run' ? '① PIPELINE' : tab === 'ablation' ? '② ABLATION' : '③ BURST TEST'}
            </button>
          ))}
        </div>

        {activeTab === 'run' && (
          <>
            {!runResult && (
              <div className="card" style={{ textAlign: 'center', color: 'var(--muted)', padding: 40 }}>
                Click <strong style={{ color: 'var(--accent)' }}>RUN PIPELINE</strong> above to execute the
                live PA-FRL simulation (Adaptive Fuzzy FDA + Priority-Aware SARSA) on the Python backend.
              </div>
            )}
            {runResult && (
              <>
                <MetricsCards metrics={runResult.metrics} />
                <ThresholdChart classification={runResult.classification} params={params} />
                <ComparisonChart metrics={runResult.metrics} />
                <ConvergenceChart rewards={runResult.rewards} />
                <FogNodeMap fogNodes={runResult.fog_nodes} />
                <TaskLogTable log={runResult.task_log} />
              </>
            )}
          </>
        )}

        {activeTab === 'ablation' && (
          <>
            {!ablation && (
              <div className="card" style={{ textAlign: 'center', color: 'var(--muted)', padding: 40 }}>
                Click <strong style={{ color: 'var(--accent)' }}>2×2 ABLATION</strong> above to isolate the
                contribution of each novelty (Priority Reward × Adaptive Threshold).
              </div>
            )}
            {ablation && <AblationHeatmap ablation={ablation} />}
          </>
        )}

        {activeTab === 'burst' && (
          <>
            {!burst && (
              <div className="card" style={{ textAlign: 'center', color: 'var(--muted)', padding: 40 }}>
                Click <strong style={{ color: 'var(--accent)' }}>BURST TEST</strong> above to simulate a
                150-task arrival surge and compare fog congestion under Fixed vs Adaptive thresholds.
              </div>
            )}
            {burst && <BurstChart burst={burst} />}
          </>
        )}
      </main>
    </div>
  )
}
