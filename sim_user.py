import random as rnd

import pygame
from pygame.event import Event

from utils.utils_menu import State
from utils import utils_menu as um


class SimUser:

    def __init__(self, chat):
        self.chat = chat

        self.chat_probs = {
            'start': {
                'later': 0.0,
                'skip': 0.60,
                'na': 1.0,
            },
            'game': {
                'later': 0.10,
                'skip': 0.30,
                'na': 0.40,
            },
            'menu': {
                'later': 0.0,
                'skip': 0.05,
                'na': 0.30,
            },
        }

        self.mouse_positions = {
            'answer': (155, 620),
            'skip': (355, 660),
            'na': (400, 660),
            'menu': (um.GAME_AREA[0]/2, um.GAME_AREA[1]/2),
        }

        self.timer = None
        self.resp_time = (2500, 3500)
        self.answ_time = (2000, 3000)
        self.answer_later = False
        self.next_event = None
        self.valid_event = True
        self.ingame_answer = None

    def _create_click(self, pos):
        # simulate a click in the screen on the given position
        event = [Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': 1,
                                                'touch': False, 'window': None}),
                 Event(pygame.MOUSEBUTTONUP, {'pos': pos, 'button': 1,
                                              'touch': False, 'window': None})
                 ]
        return event

    def _check_time(self, time):
        return pygame.time.get_ticks() - self.timer > rnd.uniform(*time)

    def _answer(self, prob_set, lvl):
        prob = self.chat_probs[prob_set]
        if rnd.uniform(0, 1) < prob['later']:  # answer later
            self.answer_later = True
            event = []
            valid_event = True
        else:
            if rnd.uniform(0, 1) < prob['skip']:  # skip answer
                event = self._create_click(self.mouse_positions['skip'])
                valid_event = False
            else:
                if rnd.uniform(0, 1) < prob['na'] * (1-0.5) ** lvl:  # na answer
                    event = self._create_click(self.mouse_positions['na'])
                    valid_event = False
                else:
                    event = self._create_click(self.mouse_positions['answer'])
                    valid_event = True
        return event, valid_event

    def get_action(self, game, state, lvl):
        chat_asking = self.chat.asking()
        question, answer = self.chat.get_qa()

        event = []
        if self.next_event:
            # generate event stored
            time = self.resp_time
            if self.valid_event:
                time = self.answ_time
            if self._check_time(time):
                event = self.next_event
                self.next_event = None
                self.timer = None
        else:
            if chat_asking and not answer:
                # focus on chat
                if state and state != State.GAME:
                    # in menu
                    if self.answer_later:
                        self.answer_later = False
                    prob_set = 'menu'
                    if state == State.START:
                        prob_set = 'start'
                    self.next_event, self.valid_event = self._answer(prob_set, lvl)
                    if self.next_event:
                        self.timer = pygame.time.get_ticks()
                elif game:
                    # in game
                    avoid = False
                    if self.ingame_answer:
                        # help avoiding keeping still for several answers
                        avoid = pygame.time.get_ticks() - self.ingame_answer < 6000
                        self.answer_later = avoid
                    if not self.answer_later:
                        if not avoid:
                            self.ingame_answer = None
                            self.next_event, self.valid_event = self._answer('game', lvl)
                            if self.next_event:
                                self.ingame_answer = pygame.time.get_ticks()
                            if self.next_event:
                                self.timer = pygame.time.get_ticks()

            if not chat_asking or self.answer_later:
                # continue playing
                if state and state != State.GAME:
                    # in menu, advance to next level
                    if self.timer is None:
                        self.timer = pygame.time.get_ticks()
                    elif self._check_time(self.resp_time):
                        event = self._create_click(self.mouse_positions['menu'])
                        self.timer = None
                elif game:
                    # in game, play by moving the paddle
                    if game.ball_direction() > 0 and game.dist_to_ball(game.player) < um.GAME_AREA[0]/2:
                        event = None
                    else:
                        p_dir = game.ai_move(game.player)
                        if p_dir == -1:
                            event = [Event(pygame.KEYDOWN, {'key': pygame.K_UP})]
                        elif p_dir == 1:
                            event = [Event(pygame.KEYDOWN, {'key': pygame.K_DOWN})]
        if event:
            # post the event to generate the behaviour, either keys or clicks
            for e in event:
                pygame.event.post(e)
            return event
        return None
