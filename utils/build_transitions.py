from os import listdir
import numpy as np

# script to build transition table from parallel executions

path = '../runs/random_EP10_R50_dt04_15__02_10_12'
files = [f for f in listdir(path) if 'transitions' in f]

acc_t = None
for f in files:
    t = np.load(f'{path}/{f}')
    if acc_t is None:
        acc_t = t
    else:
        acc_t = acc_t + t

print(acc_t)
np.save(f'{path}/transitions.npy', acc_t)
