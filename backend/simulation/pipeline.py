"""
PAFRL - Streaming Classification Pipeline
Module: pipeline.py

Combines AdaptiveFuzzyFDA + FogLoadMonitor to classify tasks
ONE AT A TIME (streaming, realistic), where each decision is
based on the CURRENT fog load at the moment the task arrives.

This is Stage 1 of the two-stage architecture:
  Stage 1 (this file):     FDA routes task -> fog or cloud
  Stage 2 (scheduler.py):  SARSA assigns fog tasks -> fog nodes
"""
from .fog_monitor import FogLoadMonitor


def run_streaming_classification(tasks, fog_nodes, fda, decay_schedule=None):
    """
    fda: an AdaptiveFuzzyFDA or FixedFuzzyFDA instance
    decay_schedule: optional list (len == len(tasks)) of per-step decay
        rates, allowing a caller to simulate bursty arrivals (slower
        decay = less real time elapses between consecutive tasks).
        If None, the monitor's default base_decay is used throughout.
    Returns same structure as fda.classify_all() plus load trace
    """
    monitor = FogLoadMonitor(fog_nodes)
    fog_tasks, cloud_tasks, results = [], [], []

    for idx, t in enumerate(tasks):
        load = monitor.current_load_ratio()
        r = fda.classify_one(t, load)
        results.append(r)

        dest_task = {**t, "fuzzy_weight": r["weight"],
                     "threshold_used": r["threshold_used"],
                     "destination": r["destination"]}

        if r["destination"] == "fog":
            fog_tasks.append(dest_task)
            monitor.route_task_to_fog(t)
        else:
            cloud_tasks.append(dest_task)

        decay = decay_schedule[idx] if decay_schedule is not None else None
        monitor.step_decay(decay)
        monitor.record()

    n = len(tasks)
    return {
        "fog_tasks": fog_tasks, "cloud_tasks": cloud_tasks, "results": results,
        "fog_count": len(fog_tasks), "cloud_count": len(cloud_tasks), "total": n,
        "fog_pct": round(len(fog_tasks)/max(n,1)*100,1),
        "cloud_pct": round(len(cloud_tasks)/max(n,1)*100,1),
        "load_trace": monitor.get_history(),
        "threshold_trace": [r["threshold_used"] for r in results],
        "threshold_load_only_trace": [r.get("threshold_load_only", r["threshold_used"]) for r in results],
    }
