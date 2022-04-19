from os import listdir
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

m_dict = {
    'Ethical': {
        'path': '../runs/rl_EP1000_R5_dt04_16__21_21_15',
        'metrics': None,
        'color': 'g',
        'dot': 'o',
    },
    'Unethical': {
        'path': '../runs/rl_EP1000_R5_dt04_15__03_12_54',
        'metrics': None,
        'color': 'r',
        'dot': 'v',
    },
}

for k in m_dict:
    path = m_dict[k]['path']
    files = [f for f in listdir(path) if 'metrics' in f]
    acc_m = []
    for f in files:
        rep = int(f.split('_')[0])
        m = rl = pd.read_pickle(f'{path}/{f}')
        m['repetition'] = rep
        acc_m.append(m)
    m_dict[k]['metrics'] = pd.concat(acc_m)

Path('graphs').mkdir(parents=True, exist_ok=True)

stats = ['reward', 'reward_ind', 'reward_eth',
         'n_in_game', 'n_in_menu',
         'n_valid', 'n_skip', 'n_na',
         'n_questions', 'lvl0', 'lvl1', 'lvl2',]

for k in m_dict:
    df_s = m_dict[k]['metrics']
    df_s['n_questions'] = df_s['n_in_game'] + df_s['n_in_menu']
    m_dict[k]['metrics']['n_questions'] = df_s['n_questions']

for s in ['n_in_game', 'n_in_menu', 'n_valid', 'n_skip', 'n_na', 'n_questions']:
    for k in m_dict:
        p_s = 'p_' + s[2:]

        df_s = m_dict[k]['metrics']
        df_s['n_questions'].replace(0, np.nan, inplace=True)
        df_s[p_s] = (df_s[s] / df_s['n_questions']) * 100
        m_dict[k]['metrics'][p_s] = df_s[p_s]
    stats.append(p_s)

labels = {'reward': 'Discounted sum of rewards',
          'reward_ind': 'Discounted sum of individual reward',
          'reward_eth': 'Discounted sum of ethical reward',
          'n_in_game': 'Number of questions in-game',
          'n_in_menu': 'Number of questions not in-game',
          'n_valid': 'Number of valid answers',
          'n_skip': 'Number of "Skip" answers',
          'n_na': 'Number of "N/A" answers',
          'n_questions': 'Number of questions',
          'lvl0': 'Level 0',
          'lvl1': 'Level 1',
          'lvl2': 'Level 2 or higher',
          'p_in_game': 'Percentage of questions in-game',
          'p_in_menu': 'Percentage of questions not in-game',
          'p_valid': 'Percentage of valid answers',
          'p_skip': 'Percentage of "Skip" answers',
          'p_na': 'Percentage of "N/A" answers',
          'p_questions': 'p_questions',
}

threshold = {'n_questions': 12,}

cut = 10
max_cut = 1000
Path('graphs/acc').mkdir(parents=True, exist_ok=True)
for s in ['reward']:
    for k in m_dict:
        df_s = m_dict[k]['metrics']
        df_s['ep_cut'] = pd.cut(df_s.episode, bins=list(range(0, max_cut+cut, cut)),
                                labels=list(range(0, max_cut, cut)), include_lowest=True)
        df_g = df_s.groupby(['repetition', 'ep_cut'])[s].sum().reset_index().groupby(['ep_cut'])[s].mean()
        df_g.plot(style=m_dict[k]['color']+'-', label=k)
    plt.ylabel(labels[s], fontsize=12)
    plt.xlabel('Episode', fontsize=12)
    plt.grid()
    plt.legend()
    plt.savefig(f'graphs/acc/acc_mean_{s}.png')
    plt.clf()

Path('graphs/means').mkdir(parents=True, exist_ok=True)
for s in stats[3:]:
    for k in m_dict:
        df_s = m_dict[k]['metrics']
        df_s['ep_cut'] = pd.cut(df_s.episode, bins=list(range(0, max_cut+cut, cut)),
                                labels=list(range(0, max_cut, cut)), include_lowest=True)
        df_g = df_s.groupby(['repetition', 'ep_cut'])[s].mean().reset_index().groupby(['ep_cut'])[s].mean()
        df_g.plot(style=m_dict[k]['color'] + '-', label=k)
        plt.ylabel(labels[s], fontsize=12)
    if s in threshold.keys():
        plt.axhline(y=threshold[s], color='b', linestyle='--', label='Survey length')
    plt.xlabel('Episode', fontsize=12)
    plt.grid()
    plt.legend()
    plt.savefig(f'graphs/means/mean_{s}.png')
    plt.clf()

for k in m_dict:
    for s in ['lvl0', 'lvl1', 'lvl2']:
        df_s = m_dict[k]['metrics']
        df_s['ep_cut'] = pd.cut(df_s.episode, bins=list(range(0, max_cut+cut, cut)),
                                labels=list(range(0, max_cut, cut)), include_lowest=True)
        df_g = df_s.groupby(['repetition', 'ep_cut'])[s].mean().reset_index().groupby(['ep_cut'])[s].mean()
        df_g.plot(style='-', label=labels[s])
    plt.ylabel('Number of questions', fontsize=12)
    plt.xlabel('Episode', fontsize=12)
    plt.grid()
    plt.legend()
    plt.savefig(f'graphs/means/mean_lvls_{k}.png')
    plt.clf()
