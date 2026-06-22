"""
PAFRL - Fog Load Monitor (v2, recalibrated)
Module: fog_monitor.py

Lightweight real-time load tracker used by the Adaptive FDA to
compute fog_load_ratio(t) BEFORE the SARSA scheduler has made final
assignments (two-stage pipeline, same as Paper 1: Stage 1 = FDA
classification, Stage 2 = SARSA scheduling).

DESIGN NOTE (v2): the original per-node "always route to the least-
loaded node" design artificially balanced load so well that the
aggregate ratio never rose above ~0.02 regardless of traffic volume,
making the adaptive threshold almost completely insensitive to real
congestion. This version tracks a single aggregate "pending work"
scalar (ms of estimated execution time routed to fog but not yet
drained), which decays each step at a rate representing how much
real time elapses between task arrivals. A faster arrival rate
(burst) is modelled with a SLOWER decay (less time to drain between
arrivals); a normal arrival rate uses a FASTER decay. This keeps the
model simple and transparent while making the load signal properly
responsive to both steady load and burst conditions.
"""
import numpy as np


class FogLoadMonitor:
    def __init__(self, fog_nodes, base_decay=0.90, saturation_ms=8000.0):
        caps = [fn["capacity"] for fn in fog_nodes] or [4000]
        self.avg_capacity = float(np.mean(caps))
        self.base_decay   = base_decay
        self.saturation_ms = saturation_ms
        self.queue   = 0.0     # aggregate pending work (ms), system-wide proxy
        self.history = []

    def current_load_ratio(self):
        """0.0 = idle fog system, 1.0 = fully saturated."""
        return float(min(1.0, self.queue / self.saturation_ms))

    def route_task_to_fog(self, task):
        et_estimate = task["instructions"] / self.avg_capacity * 1000.0  # ms
        self.queue += et_estimate

    def step_decay(self, decay=None):
        d = self.base_decay if decay is None else decay
        self.queue *= d

    def record(self):
        r = self.current_load_ratio()
        self.history.append(r)
        return r

    def get_history(self):
        return self.history
