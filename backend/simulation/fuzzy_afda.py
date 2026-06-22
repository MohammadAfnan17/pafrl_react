"""
PAFRL - Adaptive Fuzzy Decision Algorithm (A-FDA)
Module: fuzzy_afda.py

NOVEL CONTRIBUTION #2: Adaptive Threshold
Paper 1 uses FIXED V_th = 0.55
We make V_th DYNAMIC based on real-time fog load:

    V_th(t) = V_base - alpha * fog_load_ratio(t)

Classification rule is: destination = CLOUD if weight > V_th else FOG.
When fog is busy   -> V_th DECREASES -> easier for weight to exceed it
                       -> more tasks routed to CLOUD (relieves fog)
When fog is idle    -> V_th INCREASES -> harder to exceed
                       -> more tasks stay on FOG (uses spare capacity)

This prevents fog overload while maximizing fog utilization
when resources are available.
"""
import numpy as np


# ── Triangular membership function (Paper 1 Eq. 21) ─────
# FIXED: handles "shoulder" cases where u==w (left shoulder, e.g. "Short")
# or w==v (right shoulder, e.g. "Long"). Naive (x-u)/(w-u) divides by
# zero in these cases and silently returns 0 -- this was a critical bug
# that caused "Short"/"Long" membership to always evaluate to 0.
def tri_mf(x, u, w, v):
    if w == u:                     # left-shoulder (e.g. Short/Small/Less)
        if x <= w:  return 1.0
        if x >= v:  return 0.0
        return (v - x) / (v - w)
    if w == v:                     # right-shoulder (e.g. Long/Huge/More)
        if x >= w:  return 1.0
        if x <= u:  return 0.0
        return (x - u) / (w - u)
    l = (x - u) / (w - u)
    r = (v - x) / (v - w)
    return float(max(min(l, r), 0.0))


def mf_deadline(x):
    return {"Short": tri_mf(x,0,0,0.5), "Medium": tri_mf(x,0,0.5,1), "Long": tri_mf(x,0.5,1,1)}

def mf_datasize(x):
    return {"Small": tri_mf(x,0,0,0.5), "Medium": tri_mf(x,0,0.5,1), "Huge": tri_mf(x,0.5,1,1)}

def mf_instructions(x):
    return {"Less": tri_mf(x,0,0,0.5), "Moderate": tri_mf(x,0,0.5,1), "More": tri_mf(x,0.5,1,1)}


OUT_MF = {
    "EL": (0.00, 0.00, 0.20), "L":  (0.00, 0.20, 0.40),
    "LM": (0.20, 0.40, 0.60), "HM": (0.40, 0.60, 0.80),
    "H":  (0.60, 0.80, 1.00), "EH": (0.80, 1.00, 1.00),
}

# 27-rule base (Paper 1 Table 4, unchanged — we extend usage, not rules)
RULES = [
    ("Short","Small","Less","EL"),    ("Short","Small","Moderate","L"),
    ("Short","Small","More","LM"),    ("Short","Medium","Less","L"),
    ("Short","Medium","Moderate","LM"),("Short","Medium","More","HM"),
    ("Short","Huge","Less","L"),      ("Short","Huge","Moderate","LM"),
    ("Short","Huge","More","HM"),     ("Medium","Small","Less","L"),
    ("Medium","Small","Moderate","HM"),("Medium","Small","More","H"),
    ("Medium","Medium","Less","LM"),  ("Medium","Medium","Moderate","HM"),
    ("Medium","Medium","More","H"),   ("Medium","Huge","Less","LM"),
    ("Medium","Huge","Moderate","HM"),("Medium","Huge","More","H"),
    ("Long","Small","Less","L"),      ("Long","Small","Moderate","LM"),
    ("Long","Small","More","H"),      ("Long","Medium","Less","LM"),
    ("Long","Medium","Moderate","HM"),("Long","Medium","More","EH"),
    ("Long","Huge","Less","LM"),      ("Long","Huge","Moderate","H"),
    ("Long","Huge","More","EH"),
]


def normalize(v, mn, mx):
    if mx == mn: return 0.5
    return float(max(0.0, min(1.0, (v - mn) / (mx - mn))))


def defuzzify_cog(activated):
    xs = np.linspace(0, 1, 101)
    num = den = 0.0
    for x in xs:
        mx = 0.0
        for lbl, strength in activated.items():
            u, w, v = OUT_MF[lbl]
            mx = max(mx, min(tri_mf(x, u, w, v), strength))
        num += x * mx
        den += mx
    return float(num / den) if den else 0.3


class AdaptiveFuzzyFDA:
    """
    NOVEL: Adaptive threshold V_th(t) = V_base + alpha * fog_load_ratio(t)

    Also accepts task priority: CRITICAL priority tasks get a
    threshold bonus (harder to push to cloud) since they need
    fog-level low latency regardless of load.
    """
    def __init__(self, dl_min=300, dl_max=3500,
                 ds_min=20,  ds_max=1100,
                 in_min=200, in_max=5000,
                 v_base=0.55, alpha=0.25,
                 priority_bonus=None):
        self.dl_min, self.dl_max = dl_min, dl_max
        self.ds_min, self.ds_max = ds_min, ds_max
        self.in_min, self.in_max = in_min, in_max
        self.v_base = v_base
        self.alpha  = alpha
        # Critical tasks get threshold raised by this amount
        # (harder to classify as cloud -> stays in fog)
        self.priority_bonus = priority_bonus or {
            "CRITICAL": 0.20, "HIGH": 0.10, "MEDIUM": 0.0, "LOW": -0.05
        }
        self.threshold_history = []   # for plotting V_th(t) over time

    def compute_threshold(self, fog_load_ratio, priority="MEDIUM"):
        """
        Core adaptive formula (Novel Contribution #2)

        Classification rule: destination = CLOUD if weight > V_th else FOG.
        Therefore, to relieve fog congestion under high load we must
        LOWER the threshold (making it easier for weight to exceed it,
        i.e. easier to qualify for cloud) -- NOT raise it. Raising V_th
        would do the opposite (harder to reach cloud => MORE tasks
        forced into an already-congested fog layer).

            V_th(t) = v_base - alpha * fog_load_ratio + priority_bonus

        Priority bonus still ADDS for CRITICAL tasks: this raises their
        effective threshold so they remain harder to push to cloud even
        under load, preserving low-latency fog access for urgent tasks.
        """
        base_th = self.v_base - self.alpha * fog_load_ratio
        bonus   = self.priority_bonus.get(priority, 0.0)
        load_only_th = float(np.clip(base_th, 0.05, 0.95))
        final_th     = float(np.clip(base_th + bonus, 0.05, 0.95))
        return load_only_th, final_th

    def classify_one(self, task, fog_load_ratio):
        dl_n = normalize(task["deadline"],     self.dl_min, self.dl_max)
        ds_n = normalize(task["data_size"],    self.ds_min, self.ds_max)
        in_n = normalize(task["instructions"], self.in_min, self.in_max)

        dl_m = mf_deadline(dl_n)
        ds_m = mf_datasize(ds_n)
        in_m = mf_instructions(in_n)

        activated = {}
        for (d, s, i, o) in RULES:
            strength = min(dl_m[d], ds_m[s], in_m[i])
            if strength > 0:
                activated[o] = max(activated.get(o, 0.0), strength)

        weight = defuzzify_cog(activated)

        # NOVEL: dynamic threshold depends on CURRENT fog load + task priority
        load_only_th, v_th = self.compute_threshold(fog_load_ratio, task.get("priority", "MEDIUM"))
        self.threshold_history.append(v_th)

        dest = "cloud" if weight > v_th else "fog"

        return {
            "task_id":      task["id"],
            "type":         task["type"],
            "priority":     task.get("priority", "MEDIUM"),
            "deadline":     task["deadline"],
            "weight":       round(weight, 4),
            "threshold_used":     round(v_th, 4),
            "threshold_load_only": round(load_only_th, 4),
            "fog_load_at_decision": round(fog_load_ratio, 3),
            "destination":  dest,
        }

    def classify_all(self, tasks, fog_load_tracker=None):
        """
        fog_load_tracker: callable that returns current fog_load_ratio in [0,1]
        If None, uses a static load of 0.5 (Paper 1 baseline-equivalent mode).
        """
        fog_tasks, cloud_tasks, results = [], [], []
        for t in tasks:
            load = fog_load_tracker() if fog_load_tracker else 0.5
            r = self.classify_one(t, load)
            results.append(r)
            dest_task = {**t, "fuzzy_weight": r["weight"],
                         "threshold_used": r["threshold_used"],
                         "destination": r["destination"]}
            (fog_tasks if r["destination"]=="fog" else cloud_tasks).append(dest_task)

        return {
            "fog_tasks": fog_tasks, "cloud_tasks": cloud_tasks,
            "results": results,
            "fog_count": len(fog_tasks), "cloud_count": len(cloud_tasks),
            "total": len(tasks),
            "fog_pct": round(len(fog_tasks)/max(len(tasks),1)*100,1),
            "cloud_pct": round(len(cloud_tasks)/max(len(tasks),1)*100,1),
            "avg_threshold": round(np.mean([r["threshold_used"] for r in results]),4),
            "threshold_history": self.threshold_history,
        }


class FixedFuzzyFDA(AdaptiveFuzzyFDA):
    """Baseline: Paper 1's ORIGINAL fixed-threshold FDA (alpha=0, no adaptation)"""
    def __init__(self, **kwargs):
        kwargs["alpha"] = 0.0
        kwargs["priority_bonus"] = {"CRITICAL":0,"HIGH":0,"MEDIUM":0,"LOW":0}
        super().__init__(**kwargs)
