# PAFRL — React + Python3 Full-Stack Simulation

Priority-Aware Adaptive Fuzzy Reinforcement Learning for fog-enabled
IoT task scheduling. A real React frontend talking to a real Flask
(Python 3) backend that runs the actual PA-FRL algorithm live —
no canned/precomputed data, every click triggers a fresh simulation
run on the backend.

---

## Project Structure

```
pafrl_react/
├── start.py                    ← one-click launcher (recommended)
├── backend/                     Flask API (Python 3)
│   ├── app.py                     REST endpoints
│   └── simulation/
│       ├── models.py                Task & fog node generation
│       ├── fuzzy_afda.py             Adaptive Fuzzy Decision Algorithm
│       ├── fog_monitor.py            Real-time fog load tracker
│       ├── pipeline.py               Streaming classification
│       └── scheduler.py              Priority-Aware SARSA + baselines
└── frontend/                    React 18 + Vite
    └── src/
        ├── App.jsx                   Main app / state / API calls
        ├── api.js                    Fetch wrapper for backend
        └── components/
            ├── ControlPanel.jsx          Sliders + run buttons
            ├── MetricsCards.jsx           KPI summary cards
            ├── ThresholdChart.jsx         Fuzzy load/threshold charts
            ├── ComparisonChart.jsx        PA-FRL vs FCFS/EDF/GFE bars
            ├── ConvergenceChart.jsx       SARSA training reward curve
            ├── FogNodeMap.jsx             Fog node utilisation bars
            ├── TaskLogTable.jsx           Per-task scheduling log
            ├── AblationHeatmap.jsx        2×2 novelty ablation grid
            └── BurstChart.jsx             Burst-load stress test
```

---

## Quick Start (Recommended)

```bash
cd pafrl_react
python start.py
```

This will:
1. Install missing Python packages (flask, numpy, scikit-learn)
2. Run `npm install` in `frontend/` (first time only)
3. Start the Flask backend on port 5000
4. Start the Vite dev server on port 5173
5. Open your browser automatically

---

## Manual Start (2 terminals)

**Terminal 1 — Backend:**
```bash
cd pafrl_react/backend
pip install flask numpy scikit-learn
python app.py
```

**Terminal 2 — Frontend:**
```bash
cd pafrl_react/frontend
npm install
npm run dev
```

Then open **http://localhost:5173**

---

## Using the App

1. **① PIPELINE tab** — adjust sliders (tasks, fog nodes, episodes,
   threshold sensitivity), toggle the two novelties on/off, click
   **RUN PIPELINE**. Watch metrics, charts, fog node load, and the
   task scheduling log populate live from the Python backend.

2. **② ABLATION tab** — click **2×2 ABLATION** to run all four
   combinations of {Fixed, Adaptive} × {FRL, PA-SARSA} and see the
   heatmap of which combination performs best.

3. **③ BURST TEST tab** — click **BURST TEST** to simulate a
   150-task arrival surge and see how the adaptive threshold reduces
   peak fog congestion compared to a fixed threshold.

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/run` | Full pipeline: classify + train + schedule |
| POST | `/api/ablation` | 2×2 ablation matrix |
| POST | `/api/burst` | Burst-load stress test |

**Example `/api/run` request body:**
```json
{
  "num_tasks": 300,
  "num_fog_nodes": 30,
  "episodes": 300,
  "seed": 7,
  "v_base": 0.55,
  "alpha_th": 0.25,
  "use_priority": true,
  "use_adaptive": true
}
```

---

## How It Works

```
React (port 5173)  --proxy--> Flask (port 5000)
                                   │
                                   ├─ models.py        generate tasks + fog nodes
                                   ├─ fuzzy_afda.py     classify fog vs cloud
                                   ├─ fog_monitor.py    track real-time load
                                   ├─ pipeline.py       streaming classification
                                   └─ scheduler.py      train SARSA, run baselines
                                   │
                              JSON response
                                   │
                                   ▼
                        React state → charts (recharts) + tables
```

Every button click in the UI makes a real HTTP POST to Flask, which
runs the actual NumPy/scikit-learn simulation code and returns fresh
results — there is no mock data anywhere in this project.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "API Offline" badge in header | Backend not running — `cd backend && python app.py` |
| `ModuleNotFoundError: sklearn` | `pip install scikit-learn` |
| `npm: command not found` | Install Node.js from nodejs.org |
| Port 5000 already in use | Edit `backend/app.py` last line, change port |
| Port 5173 already in use | Edit `frontend/vite.config.js`, change `server.port` |
| Charts don't update | Check browser console (F12) for fetch errors |
