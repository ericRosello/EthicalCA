from datetime import datetime
import pickle
import sys

import pygame
from pathlib import Path
import thorpy

import pandas as pd
import numpy as np

from chatbot.behaviour import Behaviour
from chatbot.chatbot import Chat
from games.pong import Pong
from sim_user import SimUser
from utils import utils_menu as um
from utils.utils_menu import State

pygame.init()

flags = pygame.DOUBLEBUF
screen = pygame.display.set_mode(um.SCREEN_AREA, flags)
screen.set_alpha(None)
pygame.display.set_caption("Pong")

# experiment settings
SIMULATED_USER = True
BUILD_TRANSITIONS = False
RANDOM_BEHAVIOUR = False
N_REPETITIONS = 1
N_EPISODES = 1000
MAX_EPISODE_TIME = 1000*60*5

# destination folder
folder = ''
if RANDOM_BEHAVIOUR:
    folder = f'random'
else:
    folder = f'rl'

if len(sys.argv) > 2:
    par_code = sys.argv[1] + '_'
    dt = sys.argv[2]
    par_reps = sys.argv[3]
    number = f'EP{N_EPISODES}_R{par_reps}'

else:
    dt = datetime.now().strftime("%m_%d__%H_%M_%S")
    par_code = ''
    number = f'EP{N_EPISODES}_R{N_REPETITIONS}'

folder = f'{folder}_{number}_dt{dt}'
print(folder, dt, par_code)
Path(f'runs/{folder}').mkdir(parents=True, exist_ok=True)


def update_state(new):
    global state, lvl
    # application state, change levels, go from game to menu
    if state == State.LEVEL and new == State.GAME:
        lvl += 1
    state = new


def make_menu(text, button, next_state):
    # build menus for the start, between levels and the end
    text_elem = thorpy.OneLineText(text)
    text_elem.set_font_color((255, 255, 255))
    text_elem.set_font_size(60)
    button = thorpy.make_button(button, func=update_state, params={"new": next_state})
    box = thorpy.make_group([text_elem, button])
    thorpy.store(box, mode="v", x=um.GAME_AREA[0]/2, y=um.GAME_AREA[1]/3)
    menu = thorpy.Menu([box])
    for elem in menu.get_population():
        elem.surface = screen
    return menu


def key_input(event_queue):
    # recognise input for the game
    p_dir = 0
    if SIMULATED_USER:
        for event in event_queue:
            if event.type in [pygame.KEYUP, pygame.KEYDOWN]:
                p_dir += -1 if event.key == pygame.K_UP else 0
                p_dir += 1 if event.key == pygame.K_DOWN else 0
    else:
        keys = pygame.key.get_pressed()
        p_dir += -1 if keys[pygame.K_UP] else 0
        p_dir += 1 if keys[pygame.K_DOWN] else 0
    return p_dir


if SIMULATED_USER:
    # limit input allowed if a simulated user is being used
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP,
                              pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP])

N_LVLS = 3

menus = {
    State.START: make_menu("PONG", "Start", State.GAME),
    State.LEVEL: None,
    State.END: make_menu("THANK YOU FOR PLAYING", "Quit", None),
}

# metrics for the graphs
metrics = pd.DataFrame(index=range(N_REPETITIONS * N_EPISODES),
                       columns=['repetition', 'episode', 'reward',
                                'n_in_game', 'n_in_menu', 'time',
                                'n_valid', 'n_skip', 'n_na',
                                'lvl0', 'lvl1', 'lvl2',
                                'reward_ind', 'reward_eth',])

# transitions for the convex hull
acc_transitions = None
if BUILD_TRANSITIONS:
    acc_transitions = Behaviour(count_transitions=BUILD_TRANSITIONS).transition_count

for rep in range(N_REPETITIONS):
    rl = Behaviour(count_transitions=BUILD_TRANSITIONS)

    for episode in range(N_EPISODES):
        print(f'repetition {rep}    episode {episode}')
        state = State.START
        game = None
        lvl = 0
        screenshot = False
        running = True

        chat = Chat(screen, um.CHAT_AREA, 500, {"bg": (100, 100, 100)}, rl, RANDOM_BEHAVIOUR)  # TODO nice wat to set random
        if SIMULATED_USER:
            s_user = SimUser(chat)

        ticks = pygame.time.get_ticks()
        start_time = ticks

        while running:
            rl.level(lvl)

            event_queue = pygame.event.get()
            for event in event_queue:
                if event.type == pygame.QUIT:
                    running = False

            # update chat
            update = False
            ticks = pygame.time.get_ticks()
            for event in event_queue:
                if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                    chat.update(event, ticks, state != State.GAME)  # get option selected
                    update = True
            if not update:
                chat.update(None, ticks, state != State.GAME)  # get option selected

            # if game
            if state == State.GAME:
                if game:
                    p_dir = key_input(event_queue)
                    rl.game_input(p_dir, True, ticks)
                    res = game.update(p_dir)
                    if res is not None:
                        game = None
                        if lvl + 1 >= N_LVLS:
                            state = State.END
                        else:
                            state = State.LEVEL
                            txt = ["YOU WIN", "YOU LOSE"]
                            menus[state] = make_menu(txt[res], "Next", State.GAME)
                else:
                    game = Pong(lvl, screen, um.GAME_AREA, {"bg": (0, 0, 0), "fg": (255, 255, 255)})
            else:
                rl.game_input(0, False, ticks)
                screen.fill((0, 0, 0), (0, 0, *um.GAME_AREA))

            # if menu
            if state and state != State.GAME:
                for element in menus[state].get_population():
                    element.blit()
                for event in event_queue:
                    if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
                        menus[state].react(event)

            if MAX_EPISODE_TIME < ticks - start_time:
                print('MAX TIME EXTENDED - END EPISODE')
                running = False

            if not state:
                running = False

            if SIMULATED_USER:
                s_user.get_action(game, state, lvl)

            pygame.display.update()
            pygame.time.Clock().tick(100)

        rl.step(ticks)
        metrics.iloc[rep * N_EPISODES + episode] = {
            'repetition': rep,
            'episode': episode,
            'reward': rl.stats['reward'],
            'n_in_game': rl.stats['in_game'],
            'n_in_menu': rl.stats['in_menu'],
            'time': ticks - start_time,
            'n_valid': chat.stats['valid'],
            'n_skip': chat.stats['skip'],
            'n_na': chat.stats['na'],
            'lvl0': rl.stats['lvl0'],
            'lvl1': rl.stats['lvl1'],
            'lvl2': rl.stats['lvl2'],
            'reward_ind': rl.stats['reward_ind'],
            'reward_eth': rl.stats['reward_eth'],
        }
        print(metrics.iloc[rep * N_EPISODES + episode])
        rl.new_episode(episode)

    # save partial results
    with open(f'runs/{folder}/{par_code}behaviour_{rep}.pkl', 'wb') as f:
        pickle.dump(rl, f)
    if rl.count_transitions:
        acc_transitions = acc_transitions + rl.transition_count
        print(rl.transition_count)
    if N_REPETITIONS > 1:
        metrics.to_pickle(f'runs/{folder}/{par_code}metrics_checkpoint_{rep}.pkl')

pygame.quit()

# save final results
metrics.to_pickle(f'runs/{folder}/{par_code}metrics.pkl')
if BUILD_TRANSITIONS:
    np.save(f'runs/{folder}/{par_code}transitions.npy', acc_transitions)
