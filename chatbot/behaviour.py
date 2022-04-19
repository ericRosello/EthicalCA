from functools import reduce
import numpy as np


class Behaviour:
    def __init__(self, count_transitions=False):
        # Q-learning params
        self.epsilon = 1
        self.alpha = 0.7
        self.disc_fact = 0.7

        self.max_epsilon = 1
        self.min_epsilon = 0.01

        self.decay = 0.006  # 1000 episodes

        # variables used for the graphs
        self.stats = {
            'reward': 0,
            'reward_ind': 0,
            'reward_eth': 0,
            'in_game': 0,
            'in_menu': 0,
            'lvl0': 0,
            'lvl1': 0,
            'lvl2': 0,
        }

        self.actions = ['ASK', 'WAIT']
        self._last_action = 0
        n_actions = len(self.actions)

        # state, and auxiliary values for the encoding
        self.state = {
            'last_valid': False,
            'response_time': 0,
            'k_t': 0,
            'in_game': False,
            'lvl': 0,
        }
        self.state_aux = {
            'response_time': -1,
            'k_t': 0,
        }
        self._state_encod = {
            'last_valid': 2,
            'response_time': 2,
            'k_t': 2,
            'in_game': 2,
            'lvl': 3,
        }
        n_states = reduce(lambda x, y: x * y, self._state_encod.values())

        self.Q = np.zeros((n_states, n_actions))

        self._last_state = 0
        self._last_state_dict = self.state.copy()

        # threshold for time variables
        self.time_ranges = {
            'response_time': [3000],
            'k_t': [1000],
        }

        # if needed for convex hull
        self.count_transitions = count_transitions
        if count_transitions:
            self.transition_count = np.zeros((n_states, n_states, n_actions))

        # rewards
        self.reward = 0
        self.rewards = {
            'reward': 1,
            # # unethical
            # 'normative': -0,
            # 'evaluative': 0,
            # 'We': 0.0,
            # # ethical
            'normative': -2,
            'evaluative': 1,
            'We': 0.55,
        }
        self.first_iter = True

    def new_episode(self, episode):
        self.epsilon = self.min_epsilon + (self.max_epsilon - self.min_epsilon) * np.exp(-self.decay * episode)
        self.state = {
            'last_valid': False,
            'response_time': 0,
            'k_t': 0,
            'in_game': False,
            'lvl': 0,
        }
        self.state_aux = {
            'response_time': -1,
            'k_t': 0,
        }
        self.reward = 0
        self.stats = {
            'reward': 0,
            'reward_ind': 0,
            'reward_eth': 0,
            'in_game': 0,
            'in_menu': 0,
            'lvl0': 0,
            'lvl1': 0,
            'lvl2': 0,
        }
        self._last_action = 0
        self._last_state = 0
        self.first_iter = True

    def chat_input(self, valid, time):
        self.state['last_valid'] = valid
        self.state_aux['response_time'] = time

    def level(self, lvl):
        self.state['lvl'] = min(lvl, 2)

    def game_input(self, direction, ingame, time):
        if direction != 0:
            self.state_aux['k_t'] = time
        self.state['in_game'] = ingame

    def _update_times(self, time):
        # transform times to categories
        time_vars = self.state_aux.keys()
        for k in time_vars:
            ranges = self.time_ranges[k]
            if self.state_aux[k] != -1:
                found = False
                for i, time_threshold in enumerate(ranges):
                    if time - self.state_aux[k] < time_threshold:
                        self.state[k] = i
                        found = True
                if not found:
                    self.state[k] = len(ranges)
            else:
                self.state[k] = 0

    def _state(self):
        # encode state
        state = 0
        keys = list(self.state.keys())
        for i in range(len(self.state)):
            k = keys[i]
            obs = self.state[k]
            obs_factor = self._state_encod[k]
            state = obs + obs_factor * state
        return state

    def step(self, time, asking=False):
        self._update_times(time)

        if self.state_aux['response_time'] != -1:
            self.state_aux['response_time'] = -1

        state = self._state()

        if self.count_transitions:
            self.transition_count[self._last_state, state, self._last_action] += 1

        # choose action
        if np.random.uniform(0, 1) < self.epsilon:
            action = np.random.choice(self.actions)  # exploration
            ac_i = self.actions.index(action)
        else:
            ac_i = np.argmax(self.Q[state, :])  # explotation
            action = self.actions[ac_i]

        reward = 0  # build reward vector
        eth_reward = 0

        if self._last_action == 0:  # 'ASK'
            if self.state['last_valid']:
                reward += self.rewards['reward']
            if self.state['response_time'] == 1 or not self.state['last_valid'] or self._last_state_dict['k_t'] == 0:
                eth_reward += self.rewards['normative']
            if self.state['response_time'] == 0 and self.state['last_valid'] and self._last_state_dict['k_t'] == 1:
                eth_reward += self.rewards['evaluative']
        else:
            if self._last_state_dict['k_t'] == 1:
                eth_reward += self.rewards['normative']

        self.stats['reward_ind'] += reward
        self.stats['reward_eth'] += self.rewards['We'] * eth_reward

        reward = reward + self.rewards['We'] * eth_reward

        self.reward = reward

        if self.first_iter:
            self.first_iter = False
            self.reward = 0

        self.Q[self._last_state, self._last_action] = self.Q[self._last_state, self._last_action] + self.alpha * (self.reward + self.disc_fact * np.max(self.Q[state, :]) - self.Q[self._last_state, self._last_action])

        if self._last_action == 0:
            print(self.state, state, action, time, self.reward, '<-', self._last_state_dict['in_game'])
        else:
            print(self.state, state, action, time, self.reward)

        self._last_state = state
        self._last_state_dict = self.state.copy()
        self._last_action = ac_i

        self.stats['reward'] += self.reward
        self.reward = 0

        ask = action == self.actions[0]
        if asking:
            ask = True

        self.state['last_valid'] = False
        self.state['response_time'] = False

        if ask and not asking:
            self.stats['lvl'+str(self.state['lvl'])] += 1
            if self.state['in_game']:
                self.stats['in_game'] += 1
            else:
                self.stats['in_menu'] += 1

        return ask
