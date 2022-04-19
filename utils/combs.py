import itertools
import pandas as pd

# script to check state encodings

vals = {
    'last_valid': [0, 1],
    'response_time': [0, 1],
    'k_t': [0, 1],
    'in_game': [0, 1],
    'lvl': [0, 1, 2],
}
_state_encod = {
    'last_valid': 2,
    'response_time': 2,
    'k_t': 2,
    'in_game': 2,
    'lvl': 3,
}

a = [e[1] for e in vals.items()]

data = list(itertools.product(*a))
df = pd.DataFrame(data, columns=vals.keys())


def _state(state):
    res = 0
    keys = list(state.keys())
    for i in range(len(state)):
        k = keys[i]
        obs = state[k]
        obs_factor = _state_encod[k]
        res = obs + obs_factor * res
    return res


for index, row in df.iterrows():
    print([e for e in row.items()], '\t', _state(row.to_dict()))
