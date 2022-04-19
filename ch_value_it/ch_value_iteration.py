import numpy as np
from scipy.spatial import ConvexHull, QhullError

last_valid = list(range(24, 48))
response_time_1 = list(range(12, 24)) + list(range(36, 48))
response_time_0 = list(range(0, 12)) + list(range(24, 36))

k_t_0 = list(range(0, 6)) + list(range(12, 18)) + list(range(24, 30)) + list(range(36, 42))
k_t_1 = list(range(6, 12)) + list(range(18, 24)) + list(range(30, 36)) + list(range(42, 47))

reward = 1
normative = -2
evaluative = 1
DIMS = 2

max_iter = 5
gamma = 0.7  # discount factor
probs = np.load('transitions.npy')
states = list(range(probs.shape[0]))
actions = (0, 1)

# transition is count, we need to normalize
for s in states:
    for a in actions:
        total = sum([e[a] for e in probs[s]])
        if total != 0:
            for s_next in states:
                probs[s][s_next][a] = probs[s][s_next][a] / total


def convex_hull(Q):
    if len(Q) > 3:
        try:
            hull = ConvexHull(Q)
            return list(np.array(Q)[hull.vertices])
        except QhullError:
            return Q
    return Q


def scaling(b, Q):
    n_Q = []
    for v in Q:
        n_Q.append(np.multiply(v, b))
    return n_Q


def translation(u, Q):
    n_Q = []
    for v in Q:
        n_Q.append(np.add(u, v))
    return n_Q


def summation(Q, U):
    if not Q:
        return U
    if not U:
        return Q
    n_Q = []
    for q in Q:
        for u in U:
            n_Q.append(np.add(q, u))
    return convex_hull(n_Q)


V = [[] for i in range(probs.shape[0])]
for i in range(max_iter):
    for s in states:
        union = []
        for a in actions:

            sum_Sp = []  # summatory on s'
            for s_next in states:

                val = [0, 0]  # build reward vector
                if a == 0:  # 'ASK'
                    if s_next in last_valid:
                        val[0] += reward
                    eth_reward = 0
                    if s_next in response_time_1 or s_next not in last_valid or s in k_t_0:
                        val[1] += normative
                    if s_next in response_time_0 and s_next in last_valid and s in k_t_1:
                        val[1] += evaluative
                else:
                    if s in k_t_1:
                        val[1] += normative

                if probs[s][s_next][a]:
                    res = None
                    if not V[s_next]:
                        res = [val]  # R + gamma * V, but V is 0
                        res = scaling(probs[s][s_next][a], res)  # T * [R + gamma * V]
                    else:
                        scaled_V = scaling(gamma, V[s_next])  # gamma * V
                        trans_V = translation(val, scaled_V)  # R + gamma * V
                        res = scaling(probs[s][s_next][a], trans_V)  # T * [R + gamma * V]
                    sum_Sp = summation(sum_Sp, res)

            union = union + sum_Sp  # add to union
        # remove repeated for the union
        union = [list(l) for l in union]
        n_union = []
        for e in union:
            if e not in n_union:
                n_union.append(e)

        V[s] = [list(e) for e in convex_hull(n_union)]

for s in states:
    print('state ', s, V[s])
