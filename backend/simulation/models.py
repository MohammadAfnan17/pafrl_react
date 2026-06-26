"""
PAFRL - Priority-Aware Adaptive Fuzzy Reinforcement Learning
Module: models.py

Defines:
  - Task model with PRIORITY LEVELS (our novel addition #1)
  - Fog Node model (heterogeneous, from Paper 1)
  - Priority weight mapping
"""
import random

# ─────────────────────────────────────────────────────────
# NOVEL CONTRIBUTION #1: Priority Levels
# ─────────────────────────────────────────────────────────
# Paper 1 treats all tasks equally. We add 4 priority classes.
PRIORITY_LEVELS = {
    "CRITICAL": {"weight": 8.0, "color": "#ff4757"},
    "HIGH":     {"weight": 3.0, "color": "#ff8c42"},
    "MEDIUM":   {"weight": 1.0, "color": "#ffd700"},
    "LOW":      {"weight": 0.3, "color": "#00ff9d"},
}

# Task types mapped to priority (extends Paper 1 Table 5)
# CALIBRATED so that worst-case execution time on the FASTEST fog
# node (6500 MIPS) stays comfortably below the minimum deadline,
# leaving headroom for queueing/transmission delay. Without this,
# some task instances are structurally impossible to meet (ET alone
# exceeds the deadline even with zero queue), which collapses PDST
# for every algorithm equally and hides any real comparison.
TASK_TYPES = [
    # name,              deadline(ms),   data(KB),    instr(MI),     priority
    {"name": "Emergency Alert",   "dl": (300, 600),   "ds": (20, 60),    "ins": (200, 600),   "priority": "CRITICAL"},
    {"name": "Health Monitor",    "dl": (400, 800),   "ds": (30, 100),   "ins": (300, 900),   "priority": "CRITICAL"},
    {"name": "Object Recognition","dl": (700, 1200),  "ds": (100, 250),  "ins": (800, 2000),  "priority": "HIGH"},
    {"name": "Traffic Control",   "dl": (600, 1000),  "ds": (80, 200),   "ins": (600, 1500),  "priority": "HIGH"},
    {"name": "Smart City Sensor", "dl": (1000, 1800), "ds": (150, 400),  "ins": (1200, 2800), "priority": "MEDIUM"},
    {"name": "Infotainment",      "dl": (1200, 2200), "ds": (250, 550),  "ins": (1500, 3200), "priority": "MEDIUM"},
    {"name": "Large Update",      "dl": (2200, 3200), "ds": (600, 1100), "ins": (3000, 5000), "priority": "LOW"},
    {"name": "Backup Sync",       "dl": (2500, 3500), "ds": (500, 1000), "ins": (2800, 4500), "priority": "LOW"},
]


def generate_task(task_id, arrival_time=0.0, priority_weights=None):
    """Generate one random task with priority (Novel Contribution #1)"""
    t = random.choice(TASK_TYPES)
    weights = priority_weights or {
        name: cfg["weight"] for name, cfg in PRIORITY_LEVELS.items()
    }
    return {
        "id":           task_id,
        "type":         t["name"],
        "deadline":     random.randint(*t["dl"]),
        "data_size":    round(random.uniform(*t["ds"]), 2),
        "instructions": random.randint(*t["ins"]),
        "priority":     t["priority"],
        "priority_weight": float(weights.get(t["priority"], PRIORITY_LEVELS[t["priority"]]["weight"])),
        "arrival_time": round(arrival_time, 2),   # ms, simulation clock
        "destination":  None,
        "fog_node_id":  None,
    }


def generate_task_batch(n, mean_inter_arrival_ms=60.0, priority_weights=None):
    """
    Generate a stream of tasks with realistic Poisson-process arrivals.
    Tasks do NOT all appear at t=0 -- they arrive over time, so fog
    queues naturally drain between arrivals instead of growing without
    bound (critical for realistic wait-time / PDST results).
    """
    tasks = []
    t_now = 0.0
    for i in range(n):
        tasks.append(generate_task(i, arrival_time=t_now, priority_weights=priority_weights))
        # Exponential inter-arrival time (Poisson process)
        t_now += random.expovariate(1.0 / mean_inter_arrival_ms)
    return tasks


def generate_fog_nodes(n, cap_min=1500, cap_max=6500, bandwidth=1000):
    """Heterogeneous fog nodes (Paper 1 Section 3.1)"""
    nodes = []
    for j in range(n):
        nodes.append({
            "id":        j,
            "capacity":  random.randint(cap_min, cap_max),  # MIPS
            "bandwidth": bandwidth,                          # Mbps
            "queue":     0.0,                                # current queue time (s)
        })
    return nodes
