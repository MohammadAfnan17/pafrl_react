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
# Enable CORS globally across endpoints to prevent preflight errors on render/vercel
CORS(app, resources={r"/*": {"origins": "*"}})

DEFAULT_CONFIG = {
    "num_tasks": 300,
    "num_fog_nodes": 30,
    "episodes": 300,
    "seed": 7,
    "v_base": 0.55,
    "alpha_th": 0.25,
    "use_priority": True,
    "use_adaptive": True,
    "mean_inter_arrival_ms": 60.0,
    "fog_cap_min": 1500,
    "fog_cap_max": 6500,
    "fog_bandwidth": 1000,
    "sarsa_alpha": 0.7,
    "sarsa_gamma": 0.95,
    "sarsa_epsilon": 0.5,
    "epsilon_start": 0.9,
    "epsilon_end": 0.05,
    "task_log_limit": 40,
    "priority_weights": {
        "CRITICAL": 8.0,
        "HIGH": 3.0,
        "MEDIUM": 1.0,
        "LOW": 0.3,
    },
}

def _bool_param(value, default):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default if value is None else bool(value)

def _int_param(payload, key, minimum, maximum):
    try:
        value = int(payload.get(key, DEFAULT_CONFIG[key]))
        return max(minimum, min(maximum, value))
    except (ValueError, TypeError):
        return DEFAULT_CONFIG[key]

def _float_param(payload, key, minimum, maximum):
    try:
        value = float(payload.get(key, DEFAULT_CONFIG[key]))
        return max(minimum, min(maximum, value))
    except (ValueError, TypeError):
        return DEFAULT_CONFIG[key]

def parse_config(payload):
    payload = payload or {}
    priority_payload = payload.get("priority_weights") or {}
    priority_weights = {}
    for name, default in DEFAULT_CONFIG["priority_weights"].items():
        try:
            priority_weights[name] = max(0.0, float(priority_payload.get(name, default)))
        except (ValueError, TypeError):
            priority_weights[name] = default

    cap_min = _int_param(payload, "fog_cap_min", 100, 20000)
    cap_max = _int_param(payload, "fog_cap_max", 100, 30000)
    if cap_min > cap_max:
        cap_min, cap_max = cap_max, cap_min

    epsilon_start = _float_param(payload, "epsilon_start", 0.0, 1.0)
    epsilon_end = _float_param(payload, "epsilon_end", 0.0, 1.0)

    return {
        "num_tasks": _int_param(payload, "num_tasks", 1, 2000),
        "num_fog_nodes": _int_param(payload, "num_fog_nodes", 1, 200),
        "episodes": _int_param(payload, "episodes", 1, 3000),
        "seed": _int_param(payload, "seed", 1, 100000),
        "v_base": _float_param(payload, "v_base", 0.05, 0.95),
        "alpha_th": _float_param(payload, "alpha_th", 0.0, 1.0),
        "use_priority": _bool_param(payload.get("use_priority"), DEFAULT_CONFIG["use_priority"]),
        "use_adaptive": _bool_param(payload.get("use_adaptive"), DEFAULT_CONFIG["use_adaptive"]),
        "mean_inter_arrival_ms": _float_param(payload, "mean_inter_arrival_ms", 1.0, 10000.0),
        "fog_cap_min": cap_min,
        "fog_cap_max": cap_max,
        "fog_bandwidth": _float_param(payload, "fog_bandwidth", 1.0, 100000.0),
        "sarsa_alpha": _float_param(payload, "sarsa_alpha", 0.0, 1.0),
        "sarsa_gamma": _float_param(payload, "sarsa_gamma", 0.0, 1.0),
        "sarsa_epsilon": _float_param(payload, "sarsa_epsilon", 0.0, 1.0),
        "epsilon_start": epsilon_start,
        "epsilon_end": epsilon_end,
        "task_log_limit": _int_param(payload, "task_log_limit", 1, 2000), # Increased ceiling for logs
        "priority_weights": priority_weights,
    }

def make_tasks_and_nodes(config):
    tasks = generate_task_batch(
        config["num_tasks"],
        mean_inter_arrival_ms=config["mean_inter_arrival_ms"],
        priority_weights=config["priority_weights"],
    )
    fog_nodes = generate_fog_nodes(
        config["num_fog_nodes"],
        cap_min=config["fog_cap_min"],
        cap_max=config["fog_cap_max"],
        bandwidth=config["fog_bandwidth"],
    )
    return tasks, fog_nodes

def make_scheduler(fog_nodes, config, use_priority=None):
    return PrioritySARSAScheduler(
        fog_nodes,
        alpha=config["sarsa_alpha"],
        gamma=config["sarsa_gamma"],
        epsilon=config["sarsa_epsilon"],
        episodes=config["episodes"],
        use_priority=config["use_priority"] if use_priority is None else use_priority,
        epsilon_start=config["epsilon_start"],
        epsilon_end=config["epsilon_end"],
    )

# Cache storage placeholder to support post-simulation paginated log indexing
SIMULATION_CACHE = {
    "last_log": []
}

# ════════════════════════════════════════════════════════
# HEALTH ENDPOINTS (Fixed prefix rules to map frontend calls)
# ════════════════════════════════════════════════════════
@app.route("/health")
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "system": "PAFRL", "message": "Server routing sync successful"})


# ════════════════════════════════════════════════════════
# /run -- Full pipeline in one call
# ════════════════════════════════════════════════════════
@app.route("/run", methods=["POST"])
@app.route("/api/run", methods=["POST"])
def run_pipeline():
    config = parse_config(request.get_json(silent=True))

    random.seed(config["seed"]); np.random.seed(config["seed"])
    tasks, fog_nodes = make_tasks_and_nodes(config)

    if config["use_adaptive"]:
        fda = AdaptiveFuzzyFDA(v_base=config["v_base"], alpha=config["alpha_th"])
    else:
        fda = FixedFuzzyFDA(v_base=config["v_base"])

    cls = run_streaming_classification(tasks, fog_nodes, fda)
    fog_tasks_sorted = sorted(cls["fog_tasks"], key=lambda t: t["fuzzy_weight"])

    random.seed(config["seed"]); np.random.seed(config["seed"])
    sarsa = make_scheduler(fog_nodes, config)
    rewards = sarsa.train(fog_tasks_sorted)
    log = sarsa.schedule(fog_tasks_sorted)
    
    # Store complete trace in memory context to support dynamic window slicing
    SIMULATION_CACHE["last_log"] = log
    metrics = calc_metrics(log)

    random.seed(config["seed"]); np.random.seed(config["seed"])
    fcfs_log = fcfs(fog_tasks_sorted, fog_nodes)
    edf_log  = edf(fog_tasks_sorted, fog_nodes)
    gfe_log  = gfe(fog_tasks_sorted, fog_nodes)
    fcfs_m, edf_m, gfe_m = calc_metrics(fcfs_log), calc_metrics(edf_log), calc_metrics(gfe_log)

    counts = {}
    for r in log:
        counts[r["fog_node"]] = counts.get(r["fog_node"], 0) + 1
    fog_node_stats = [{
        "id": fn["id"], "capacity": fn["capacity"],
        "tasks": counts.get(fn["id"], 0),
        "utilisation": round(counts.get(fn["id"], 0) / max(len(fog_tasks_sorted), 1) * 100, 1),
    } for fn in fog_nodes]

    th_trace = cls.get("threshold_load_only_trace", cls["threshold_trace"])
    load_trace = cls["load_trace"]
    step = max(1, len(th_trace) // 150)

    # Clean default return uses task_log_limit ceiling passed from client state UI
    limit = config["task_log_limit"]

    return jsonify({
        "status": "ok",
        "config": config,
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
        "task_log": log[:limit],
        "total_fog_tasks": len(log)
    })


# ════════════════════════════════════════════════════════
# DYNAMIC TASK LOGS PAGINATION (Sprint 2 Execution Niche)
# ════════════════════════════════════════════════════════
@app.route("/logs", methods=["GET"])
@app.route("/api/logs", methods=["GET"])
def get_paginated_logs():
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = max(1, min(100, int(request.args.get("limit", 20))))
    except ValueError:
        page, limit = 1, 20

    all_logs = SIMULATION_CACHE["last_log"]
    total = len(all_logs)
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    return jsonify({
        "status": "ok",
        "page": page,
        "limit": limit,
        "total_records": total,
        "task_log": all_logs[start_idx:end_idx]
    })


# ════════════════════════════════════════════════════════
# /api/ablation
# ════════════════════════════════════════════════════════
@app.route("/ablation", methods=["POST"])
@app.route("/api/ablation", methods=["POST"])
def run_ablation():
    config = parse_config(request.get_json(silent=True))

    random.seed(config["seed"]); np.random.seed(config["seed"])
    tasks, fog_nodes = make_tasks_and_nodes(config)

    fixed_fda    = FixedFuzzyFDA(v_base=config["v_base"])
    adaptive_fda = AdaptiveFuzzyFDA(v_base=config["v_base"], alpha=config["alpha_th"])
    fixed_cls    = run_streaming_classification(tasks, fog_nodes, fixed_fda)
    adaptive_cls = run_streaming_classification(tasks, fog_nodes, adaptive_fda)
    fixed_sorted    = sorted(fixed_cls["fog_tasks"], key=lambda t: t["fuzzy_weight"])
    adaptive_sorted = sorted(adaptive_cls["fog_tasks"], key=lambda t: t["fuzzy_weight"])

    def run_combo(fog_tasks, use_priority, combo_seed):
        random.seed(combo_seed); np.random.seed(combo_seed)
        sch = make_scheduler(fog_nodes, config, use_priority=use_priority)
        sch.train(fog_tasks)
        log = sch.schedule(fog_tasks)
        return calc_metrics(log)

    results = {
        "PA-SARSA+Adaptive":  run_combo(adaptive_sorted, True,  config["seed"]),
        "FRL-SARSA+Fixed":    run_combo(fixed_sorted,    False, config["seed"]),
        "PA-SARSA+Fixed":     run_combo(fixed_sorted,    True,  config["seed"]),
        "FRL-SARSA+Adaptive": run_combo(adaptive_sorted, False, config["seed"]),
    }

    return jsonify({"status": "ok", "config": config, "ablation": results})


# ════════════════════════════════════════════════════════
# /api/burst
# ════════════════════════════════════════════════════════
@app.route("/burst", methods=["POST"])
@app.route("/api/burst", methods=["POST"])
def run_burst():
    payload = request.get_json(silent=True) or {}
    config = parse_config(payload)
    random.seed(config["seed"]); np.random.seed(config["seed"])

    pre_tasks = int(payload.get("burst_pre_tasks", 100))
    burst_tasks = int(payload.get("burst_tasks", 150))
    post_tasks = int(payload.get("burst_post_tasks", 100))

    tasks, tid = [], 0
    for _ in range(pre_tasks): tasks.append(generate_task(tid, priority_weights=config["priority_weights"])); tid += 1
    for _ in range(burst_tasks): tasks.append(generate_task(tid, priority_weights=config["priority_weights"])); tid += 1
    for _ in range(post_tasks): tasks.append(generate_task(tid, priority_weights=config["priority_weights"])); tid += 1

    fog_nodes = generate_fog_nodes(
        config["num_fog_nodes"],
        cap_min=config["fog_cap_min"],
        cap_max=config["fog_cap_max"],
        bandwidth=config["fog_bandwidth"],
    )

    normal_decay = float(payload.get("normal_decay", 0.80))
    burst_decay = float(payload.get("burst_decay", 0.975))
    decay_schedule = [normal_decay]*pre_tasks + [burst_decay]*burst_tasks + [normal_decay]*post_tasks

    fixed_fda    = FixedFuzzyFDA(v_base=config["v_base"])
    adaptive_fda = AdaptiveFuzzyFDA(v_base=config["v_base"], alpha=config["alpha_th"])

    fixed_cls    = run_streaming_classification(tasks, fog_nodes, fixed_fda, decay_schedule)
    adaptive_cls = run_streaming_classification(tasks, fog_nodes, adaptive_fda, decay_schedule)

    def windowed_fog_rate(results_list, w=25):
        dests = [1 if r["destination"] == "fog" else 0 for r in results_list]
        return [round(float(np.mean(dests[max(0, i-w):i+1])), 3) for i in range(len(dests))]

    fixed_rate    = windowed_fog_rate(fixed_cls["results"])
    adaptive_rate = windowed_fog_rate(adaptive_cls["results"])
    fixed_load    = [round(v, 3) for v in fixed_cls["load_trace"]]
    adaptive_load = [round(v, 3) for v in adaptive_cls["load_trace"]]

    burst_start = pre_tasks
    burst_end = pre_tasks + burst_tasks
    burst_fixed_avg    = float(np.mean(fixed_load[burst_start:burst_end]))
    burst_adaptive_avg = float(np.mean(adaptive_load[burst_start:burst_end]))
    reduction_pct = (1 - burst_adaptive_avg / max(burst_fixed_avg, 1e-9)) * 100

    return jsonify({
        "status": "ok",
        "fixed_rate": fixed_rate, "adaptive_rate": adaptive_rate,
        "fixed_load": fixed_load, "adaptive_load": adaptive_load,
        "burst_window": [burst_start, burst_end],
        "config": config,
        "burst_fixed_avg": round(burst_fixed_avg, 4),
        "burst_adaptive_avg": round(burst_adaptive_avg, 4),
        "reduction_pct": round(reduction_pct, 1),
    })

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  PAFRL Backend Engine Online")
    print("  Listening locally at: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
