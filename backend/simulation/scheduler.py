"""
PAFRL - Priority-Aware SARSA Scheduler
Module: scheduler.py

NOVEL CONTRIBUTION #1: Priority-Weighted Reward
Paper 1 reward:        r(s,a) = 1 / ST_ij
Our PA-SARSA reward:    r(s,a) = priority_weight(task) / ST_ij

This makes the RL agent learn to prioritize CRITICAL/HIGH
priority tasks during training, directly reducing their
deadline-miss rate without sacrificing overall throughput.

Also implements baselines:
  - FRL-SARSA   (Paper 1 original, priority-agnostic)
  - FCFS, EDF, GFE (Paper 1 baselines)
"""
import numpy as np
import random


# ── Delay model (Paper 1 Eq. 1-6), offline batch queueing ──
# Paper 1 Eq. 2 defines waiting time as the cumulative execution
# time of tasks already assigned to the same fog node ahead of
# this one in processing order (priority/arrival/EDF/RL order,
# depending on the algorithm) -- NOT a real-time wall-clock queue.
# `wait_ms` is therefore simply the running ms-total of ET already
# committed to this node before the current task is considered.
def service_time(task, node, wait_ms=0.0):
    et = (task["instructions"] / node["capacity"]) * 1000.0   # ms
    tt = (task["data_size"] * 0.008 / node["bandwidth"]) * 1000.0
    pt = 2.0 * random.uniform(1.0, 3.0)
    wt = wait_ms                                               # ms (already)
    st = wt + et + tt + pt
    return {"st": st, "et": et, "tt": tt, "pt": pt, "wt": wt}


# ── Energy model (Paper 1 Eq. 7-12) ─────────────────────
def node_energy(node, assigned_tasks, makespan_ms=0.0):
    C = node["capacity"]
    d = 1e-8 * C**2
    b = 0.6e-8 * C**2
    et_s = sum(t.get("instructions",1000)/C for t in assigned_tasks)
    ms_s = makespan_ms/1000.0
    ec_a = d * et_s * C
    ec_i = b * max(0.0, ms_s - et_s) * C
    return {"active": ec_a*1e9, "idle": ec_i*1e9, "total": (ec_a+ec_i)*1e9}


# ── Metrics (extended w/ priority breakdown) ────────────
def calc_metrics(log):
    if not log:
        return {}
    sts  = [r["st_ms"] for r in log]
    mets = [r["deadline_met"] for r in log]
    pens = [max(0.0, r["st_ms"]-r["deadline"]) for r in log]
    ens  = [r.get("energy",0.0) for r in log]

    metrics = {
        "avg_st_ms":   round(float(np.mean(sts)),2),
        "avg_wait_ms": round(float(np.mean([r["wt_ms"] for r in log])),2),
        "avg_exec_ms": round(float(np.mean([r["et_ms"] for r in log])),2),
        "pdst_pct":    round(sum(mets)/len(mets)*100,1),
        "tasks_met":   int(sum(mets)),
        "total_tasks": len(log),
        "avg_penalty_ms": round(float(np.mean(pens)),2),
        "total_energy": round(float(sum(ens)),4),
    }

    # Priority-level breakdown (Novel metric)
    for pr in ["CRITICAL","HIGH","MEDIUM","LOW"]:
        pr_log = [r for r in log if r.get("priority")==pr]
        if pr_log:
            pr_met = [r["deadline_met"] for r in pr_log]
            metrics[f"pdst_{pr.lower()}"] = round(sum(pr_met)/len(pr_met)*100,1)
            metrics[f"avg_st_{pr.lower()}"] = round(
                float(np.mean([r["st_ms"] for r in pr_log])),2)
        else:
            metrics[f"pdst_{pr.lower()}"] = None
            metrics[f"avg_st_{pr.lower()}"] = None
    return metrics


def calc_fog_overload(node_loads_history, threshold=0.8):
    """
    NOVEL METRIC: Fog Overload Rate
    % of time fog nodes operated above `threshold` capacity utilisation
    """
    if not node_loads_history:
        return 0.0
    overloaded = sum(1 for l in node_loads_history if l > threshold)
    return round(overloaded/len(node_loads_history)*100, 1)


# ════════════════════════════════════════════════════════
# PRIORITY-AWARE SARSA (PA-SARSA) — Our main contribution
# ════════════════════════════════════════════════════════
class PrioritySARSAScheduler:
    def __init__(self, fog_nodes, alpha=0.7, gamma=0.95,
                 epsilon=0.5, episodes=300, use_priority=True,
                 epsilon_start=0.9, epsilon_end=0.05):
        self.nodes        = fog_nodes
        self.alpha        = alpha
        self.gamma        = gamma
        self.epsilon      = epsilon
        self.episodes     = episodes
        self.use_priority = use_priority   # toggle for ablation study
        self.epsilon_start = epsilon_start
        self.epsilon_end   = epsilon_end
        self.Q            = {}
        self.rewards      = []
        self.load_history = []   # tracks fog load over time (for overload metric)

    def _policy(self, task, queues):
        """Paper 1 Algorithm 2: pick min-CURRENT-energy node meeting deadline"""
        best, best_e = 0, float("inf")
        for j, nd in enumerate(self.nodes):
            st = service_time(task, nd, queues.get(j, 0.0))
            if st["st"] <= task["deadline"]:
                C = nd["capacity"]
                delta = 1e-8 * C**2
                e = delta * (queues.get(j, 0.0)/1000.0) * C   # current accumulated energy
                if e < best_e: best_e, best = e, j
        return best

    def _eps_greedy(self, s, task, queues, eps=None):
        e = self.epsilon if eps is None else eps
        if random.random() < e:
            return random.randint(0, len(self.nodes)-1)
        if s in self.Q:
            return int(np.argmax(self.Q[s]))
        return self._policy(task, queues)

    def train(self, tasks):
        nS, nA = len(tasks), len(self.nodes)
        self.Q = {s: [0.0]*nA for s in range(nS)}
        self.rewards = []
        if nS == 0 or nA == 0:
            return self.rewards
        eps_start, eps_end = self.epsilon_start, self.epsilon_end

        for ep in range(self.episodes):
            # Linear epsilon decay: explore early, exploit later
            eps = eps_start - (eps_start-eps_end) * (ep/max(self.episodes-1,1))

            queues = {j: 0.0 for j in range(nA)}   # cumulative ET per node (ms)
            total_r = 0.0
            s = 0
            a = self._eps_greedy(s, tasks[s], queues, eps)

            while s < nS - 1:
                t, nd = tasks[s], self.nodes[a]
                st = service_time(t, nd, queues.get(a, 0.0))

                # ═══ NOVEL REWARD FUNCTION ═══
                # Paper 1:        r = 1000 / ST
                # PA-SARSA (ours): r = priority_weight * 1000 / ST
                base_r = 1000.0 / max(st["st"], 0.1)
                if self.use_priority:
                    pw = t.get("priority_weight", 1.0)
                    r = pw * base_r
                else:
                    r = base_r   # ablation: priority OFF (= original FRL)

                total_r += r
                queues[a] = queues.get(a, 0.0) + st["et"]

                sn = s+1
                an = self._eps_greedy(sn, tasks[sn], queues, eps)
                qn = self.Q[sn][an] if sn < nS else 0.0
                self.Q[s][a] += self.alpha*(r + self.gamma*qn - self.Q[s][a])
                s, a = sn, an

            self.rewards.append(round(total_r,2))
            max_q = max(queues.values()) if queues else 1.0
            util = [q/max(max_q,1.0) for q in queues.values()]
            self.load_history.append(float(np.mean(util)) if util else 0.0)

        return self.rewards

    def schedule(self, tasks):
        log = []
        queues     = {j: 0.0 for j in range(len(self.nodes))}
        node_tasks = {j: [] for j in range(len(self.nodes))}

        for s, t in enumerate(tasks):
            a  = int(np.argmax(self.Q[s])) if s in self.Q else self._policy(t, queues)
            nd = self.nodes[a]
            st = service_time(t, nd, queues.get(a, 0.0))
            queues[a] = queues.get(a, 0.0) + st["et"]
            node_tasks[a].append(t)
            en = node_energy(nd, node_tasks[a], queues[a])

            log.append({
                "task_id": t["id"], "type": t["type"],
                "priority": t.get("priority","MEDIUM"),
                "fog_node": a, "capacity": nd["capacity"],
                "deadline": t["deadline"],
                "st_ms": round(st["st"],2), "et_ms": round(st["et"],2),
                "wt_ms": round(st["wt"],2), "tt_ms": round(st["tt"],2),
                "energy": en["total"],
                "deadline_met": st["st"] <= t["deadline"],
                "algo": "PA-SARSA" if self.use_priority else "FRL-SARSA",
            })
        return log

    def fog_load_ratio(self):
        """Returns current average fog load (used by Adaptive FDA)"""
        if not self.load_history:
            return 0.5
        return self.load_history[-1]


# ── Baselines (Paper 1), offline batch queueing ─────────
def fcfs(tasks, nodes):
    log, queues = [], {j: 0.0 for j in range(len(nodes))}
    for t in tasks:
        j = random.randint(0, len(nodes)-1)
        nd = nodes[j]
        st = service_time(t, nd, queues[j])
        queues[j] += st["et"]
        log.append(_row(t, j, nd, st, "FCFS"))
    return log

def edf(tasks, nodes):
    s_tasks = sorted(tasks, key=lambda t: t["deadline"])
    log, queues = [], {j: 0.0 for j in range(len(nodes))}
    for t in s_tasks:
        j = random.randint(0, len(nodes)-1)
        nd = nodes[j]
        st = service_time(t, nd, queues[j])
        queues[j] += st["et"]
        log.append(_row(t, j, nd, st, "EDF"))
    return log

def gfe(tasks, nodes):
    """
    Greedy For Energy (Paper 1): assign each task to the fog node
    with the LEAST current accumulated active energy. FIXED: this
    must be evaluated dynamically (energy grows as a node accumulates
    queued execution time, Eq. 7) -- not via a static per-node
    coefficient, which would always select the same (slowest) node
    and collapse the whole baseline onto a single fog node.
    """
    log, queues = [], {j: 0.0 for j in range(len(nodes))}

    def current_energy(j):
        C = nodes[j]["capacity"]
        delta = 1e-8 * C**2
        return delta * (queues[j] / 1000.0) * C   # active energy so far

    for t in tasks:
        j = min(range(len(nodes)), key=current_energy)
        nd = nodes[j]
        st = service_time(t, nd, queues[j])
        queues[j] += st["et"]
        log.append(_row(t, j, nd, st, "GFE"))
    return log

def _row(t, j, nd, st, algo):
    return {
        "task_id": t["id"], "type": t["type"],
        "priority": t.get("priority","MEDIUM"),
        "fog_node": j, "capacity": nd["capacity"],
        "deadline": t["deadline"],
        "st_ms": round(st["st"],2), "et_ms": round(st["et"],2),
        "wt_ms": round(st["wt"],2), "tt_ms": round(st["tt"],2),
        "energy": 0.0,
        "deadline_met": st["st"] <= t["deadline"],
        "algo": algo,
    }
