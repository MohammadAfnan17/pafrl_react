"""
PAFRL React Demo - Flask Backend API
Exposes the validated PA-FRL simulation (priority-aware SARSA +
adaptive fuzzy threshold) over a REST API for the React frontend.

Run:  python app.py
Serves on http://localhost:5000
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys, os, random
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from simulation.models import generate_task_batch, generate_fog_nodes, generate_task
from simulation.fuzzy_afda import FixedFuzzyFDA, AdaptiveFuzzyFDA
from simulation.pipeline import run_streaming_classification
from simulation.scheduler import (
    PrioritySARSAScheduler, fcfs, edf, gfe, calc_metrics
)

app = Flask(__name__)
CORS(app)

# ── CORS (manual, since flask-cors isn't installed) ──────
# @app.after_request
# def add_cors(resp):
#     resp.headers["Access-Control-Allow-Origin"] = "*"
#     resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
#     resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
#     return resp

# @app.route("/api/<path:path>", methods=["OPTIONS"])
# def options_handler(path):
#     return jsonify({})


# ════════════════════════════════════════════════════════
# /api/health
# ════════════════════════════════════════════════════════
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "system": "PAFRL"})


# ════════════════════════════════════════════════════════
# /api/run  -- Full pipeline in one call
# Params: num_tasks, num_fog_nodes, episodes, seed,
#         v_base, alpha_th, use_priority, use_adaptive
# ════════════════════════════════════════════════════════
@app.route("/api/run", methods=["POST"])
def run_pipeline():
    p = request.get_json(force=True) or {}

    num_tasks     = int(p.get("num_tasks", 300))
    num_fog_nodes = int(p.get("num_fog_nodes", 30))
    episodes      = int(p.get("episodes", 300))
    seed          = int(p.get("seed", 7))
    v_base        = float(p.get("v_base", 0.55))
    alpha_th      = float(p.get("alpha_th", 0.25))
    use_priority  = bool(p.get("use_priority", True))
    use_adaptive  = bool(p.get("use_adaptive", True))

    random.seed(seed); np.random.seed(seed)

    tasks     = generate_task_batch(num_tasks)
    fog_nodes = generate_fog_nodes(num_fog_nodes)

    # ── Stage 1: Classification ──────────────────────────
    if use_adaptive:
        fda = AdaptiveFuzzyFDA(v_base=v_base, alpha=alpha_th)
    else:
        fda = FixedFuzzyFDA(v_base=v_base)

    cls = run_streaming_classification(tasks, fog_nodes, fda)
    fog_tasks_sorted = sorted(cls["fog_tasks"], key=lambda t: t["fuzzy_weight"])

    # ── Stage 2: Scheduling ───────────────────────────────
    random.seed(seed); np.random.seed(seed)
    sarsa = PrioritySARSAScheduler(fog_nodes, episodes=episodes, use_priority=use_priority)
    rewards = sarsa.train(fog_tasks_sorted)
    log = sarsa.schedule(fog_tasks_sorted)
    metrics = calc_metrics(log)

    # ── Baselines (same fog task set, fresh seed) ────────
    random.seed(seed); np.random.seed(seed)
    fcfs_log = fcfs(fog_tasks_sorted, fog_nodes)
    edf_log  = edf(fog_tasks_sorted, fog_nodes)
    gfe_log  = gfe(fog_tasks_sorted, fog_nodes)
    fcfs_m, edf_m, gfe_m = calc_metrics(fcfs_log), calc_metrics(edf_log), calc_metrics(gfe_log)

    # ── Fog node utilisation ──────────────────────────────
    counts = {}
    for r in log:
        counts[r["fog_node"]] = counts.get(r["fog_node"], 0) + 1
    fog_node_stats = [{
        "id": fn["id"], "capacity": fn["capacity"],
        "tasks": counts.get(fn["id"], 0),
        "utilisation": round(counts.get(fn["id"], 0) / max(len(fog_tasks_sorted), 1) * 100, 1),
    } for fn in fog_nodes]

    # ── Threshold trace (down-sampled for transport) ──────
    th_trace = cls.get("threshold_load_only_trace", cls["threshold_trace"])
    load_trace = cls["load_trace"]
    step = max(1, len(th_trace) // 150)

    return jsonify({
        "status": "ok",
        "config": {
            "num_tasks": num_tasks, "num_fog_nodes": num_fog_nodes,
            "episodes": episodes, "seed": seed, "v_base": v_base,
            "alpha_th": alpha_th, "use_priority": use_priority,
            "use_adaptive": use_adaptive,
        },
        "classification": {
            "fog_count": cls["fog_count"], "cloud_count": cls["cloud_count"],
            "total": cls["total"], "fog_pct": cls["fog_pct"], "cloud_pct": cls["cloud_pct"],
            "threshold_trace": th_trace[::step],
            "load_trace": load_trace[::step],
        },
        "metrics": {
            "pa_frl": metrics, "fcfs": fcfs_m, "edf": edf_m, "gfe": gfe_m,
        },
        "rewards": rewards[::max(1, len(rewards)//150)],
        "fog_nodes": fog_node_stats,
        "task_log": log[:40],
    })


# ════════════════════════════════════════════════════════
# /api/ablation -- 2x2 ablation matrix
# ════════════════════════════════════════════════════════
@app.route("/api/ablation", methods=["POST"])
def run_ablation():
    p = request.get_json(force=True) or {}
    num_tasks     = int(p.get("num_tasks", 300))
    num_fog_nodes = int(p.get("num_fog_nodes", 30))
    episodes      = int(p.get("episodes", 300))
    seed          = int(p.get("seed", 7))
    v_base        = float(p.get("v_base", 0.55))
    alpha_th      = float(p.get("alpha_th", 0.25))

    random.seed(seed); np.random.seed(seed)
    tasks     = generate_task_batch(num_tasks)
    fog_nodes = generate_fog_nodes(num_fog_nodes)

    fixed_fda    = FixedFuzzyFDA()
    adaptive_fda = AdaptiveFuzzyFDA(v_base=v_base, alpha=alpha_th)
    fixed_cls    = run_streaming_classification(tasks, fog_nodes, fixed_fda)
    adaptive_cls = run_streaming_classification(tasks, fog_nodes, adaptive_fda)
    fixed_sorted    = sorted(fixed_cls["fog_tasks"], key=lambda t: t["fuzzy_weight"])
    adaptive_sorted = sorted(adaptive_cls["fog_tasks"], key=lambda t: t["fuzzy_weight"])

    def run_combo(fog_tasks, use_priority, combo_seed):
        random.seed(combo_seed); np.random.seed(combo_seed)
        sch = PrioritySARSAScheduler(fog_nodes, episodes=episodes, use_priority=use_priority)
        sch.train(fog_tasks)
        log = sch.schedule(fog_tasks)
        return calc_metrics(log)

    results = {
        "PA-SARSA+Adaptive":  run_combo(adaptive_sorted, True,  seed),
        "FRL-SARSA+Fixed":    run_combo(fixed_sorted,    False, seed),
        "PA-SARSA+Fixed":     run_combo(fixed_sorted,    True,  seed),
        "FRL-SARSA+Adaptive": run_combo(adaptive_sorted, False, seed),
    }

    return jsonify({"status": "ok", "ablation": results})


# ════════════════════════════════════════════════════════
# /api/burst -- burst-load stress test
# ════════════════════════════════════════════════════════
@app.route("/api/burst", methods=["POST"])
def run_burst():
    p = request.get_json(force=True) or {}
    seed = int(p.get("seed", 99))
    num_fog_nodes = int(p.get("num_fog_nodes", 30))
    v_base        = float(p.get("v_base", 0.55))
    alpha_th      = float(p.get("alpha_th", 0.30))
    num_tasks     = int(p.get("num_tasks", 300))
    random.seed(seed); np.random.seed(seed)
    p1 = int(num_tasks * 0.28) # ~28% base
    p2 = int(num_tasks * 0.44) # ~44% burst spike
    p3 = num_tasks - (p1 + p2)

    tasks, tid = [], 0
    for _ in range(p1): tasks.append(generate_task(tid)); tid += 1
    for _ in range(p2): tasks.append(generate_task(tid)); tid += 1
    for _ in range(p3): tasks.append(generate_task(tid)); tid += 1

    fog_nodes = generate_fog_nodes(num_fog_nodes)

    NORMAL_DECAY, BURST_DECAY = 0.80, 0.975
    decay_schedule = [NORMAL_DECAY]*p1 + [BURST_DECAY]*p2 + [NORMAL_DECAY]*p3

    fixed_fda    = FixedFuzzyFDA()
    adaptive_fda = AdaptiveFuzzyFDA(v_base=v_base, alpha=alpha_th)

    fixed_cls    = run_streaming_classification(tasks, fog_nodes, fixed_fda, decay_schedule)
    adaptive_cls = run_streaming_classification(tasks, fog_nodes, adaptive_fda, decay_schedule)

    def windowed_fog_rate(results_list, w=25):
        dests = [1 if r["destination"] == "fog" else 0 for r in results_list]
        return [round(float(np.mean(dests[max(0, i-w):i+1])), 3) for i in range(len(dests))]

    fixed_rate    = windowed_fog_rate(fixed_cls["results"])
    adaptive_rate = windowed_fog_rate(adaptive_cls["results"])
    fixed_load    = [round(v, 3) for v in fixed_cls["load_trace"]]
    adaptive_load = [round(v, 3) for v in adaptive_cls["load_trace"]]

    burst_fixed_avg    = float(np.mean(fixed_load[p1:p1+p2]))
    burst_adaptive_avg = float(np.mean(adaptive_load[p1:p1+p2]))
    reduction_pct = (1 - burst_adaptive_avg / max(burst_fixed_avg, 1e-9)) * 100

    return jsonify({
        "status": "ok",
        "fixed_rate": fixed_rate, "adaptive_rate": adaptive_rate,
        "fixed_load": fixed_load, "adaptive_load": adaptive_load,
        "burst_window": [p1, p1+p2],
        "burst_fixed_avg": round(burst_fixed_avg, 4),
        "burst_adaptive_avg": round(burst_adaptive_avg, 4),
        "reduction_pct": round(reduction_pct, 1),
    })


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  PAFRL Backend API")
    print("  http://localhost:5000/api/health")
    print("="*50 + "\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
