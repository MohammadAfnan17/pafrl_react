const API_BASE = '/api'

async function post(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

async function get(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const api = {
  health: () => get('/health'),
  run: (params) => post('/run', params),
  ablation: (params) => post('/ablation', params),
  burst: (params) => post('/burst', params),
}
