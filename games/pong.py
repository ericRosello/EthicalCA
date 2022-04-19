import math
from random import randint, choice

import pygame


class Paddle(pygame.sprite.Sprite):

    def __init__(self, color, width, height, window):
        super().__init__()
        self.image = pygame.Surface([width, height])
        pygame.draw.rect(self.image, color, [0, 0, width, height])
        self.rect = self.image.get_rect()
        self.window = window

    def move(self, pixels):
        self.rect.y += pixels
        if self.rect.y > self.window[1] - self.rect.height:
            self.rect.y = self.window[1] - self.rect.height
        if self.rect.y < 0:
            self.rect.y = 0


class Ball(pygame.sprite.Sprite):

    def __init__(self, color, width, height, vel_range, window):
        super().__init__()
        self.image = pygame.Surface([width, height])
        pygame.draw.rect(self.image, color, [0, 0, width, height])
        self.reset_vel = (lambda: [randint(*vel_range[0]), randint(*vel_range[0])])
        self.velocity = self.reset_vel()
        self.rect = self.image.get_rect()
        self.window = window

    def reset(self):
        self.velocity = self.reset_vel()
        self.rect.x = (self.window[0] + self.rect.width) / 2
        self.rect.y = (self.window[1] + self.rect.height) / 2

    def update(self):
        if abs(self.velocity[1]) < 0.5:
            self.velocity[1] = choice([-1, 1])
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

        if self.rect.x >= self.window[0] - self.rect.width:
            self.velocity[0] *= -1
        if self.rect.x <= 0:
            self.velocity[0] *= -1
        if self.rect.y > self.window[1] - self.rect.height:  # offset not to paint chat
            self.velocity[1] *= -1
        if self.rect.y < 0:
            self.velocity[1] *= -1


class Goal(pygame.sprite.Sprite):

    def __init__(self, color, width, height):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()


class Pong:

    def __init__(self, lvl, screen, window, colors):
        self.screen = screen
        self.WINDOW = window

        self.BG = colors["bg"]
        self.FG = colors["fg"]

        # levels of difficulty
        levels = {
            0: {
                "PADDLE_H": 90,
                "P_VEL": 5,
                "O_VEL": 4,
                "B_VEL": [(4, 7), (-5, 5)],
            },
            1: {
                "PADDLE_H": 70,
                "P_VEL": 6,
                "O_VEL": 5,
                "B_VEL": [(7, 9), (-5, 5)],
            },
            2: {
                "PADDLE_H": 65,
                "P_VEL": 8,
                "O_VEL": 7,
                "B_VEL": [(9, 10), (-5, 5)],
            },
        }

        # if more than available
        lvl = min(lvl, max(levels.keys()))

        self.END = 5

        self.PADDLE_W = 30
        self.PADDLE_H = levels[lvl]["PADDLE_H"]
        self.INITIAL_X = 20
        self.INITIAL_Y = (self.WINDOW[1] - self.PADDLE_H) / 2

        self.BALL_S = 30

        self.VEL_FACT = 1

        self.P_VEL = levels[lvl]["P_VEL"] * self.VEL_FACT
        self.O_VEL = levels[lvl]["O_VEL"] * self.VEL_FACT
        self.B_VEL = [(a * self.VEL_FACT, b * self.VEL_FACT) for a, b in levels[lvl]["B_VEL"]]

        self.O_VIEW = self.WINDOW[0] / 2

        player = Paddle(self.FG, self.PADDLE_W, self.PADDLE_H, self.WINDOW)
        player.rect.x = self.INITIAL_X
        player.rect.y = self.INITIAL_Y
        self.player = player

        opponent = Paddle(self.FG, self.PADDLE_W, self.PADDLE_H, self.WINDOW)
        opponent.rect.x = self.WINDOW[0] - self.PADDLE_W - self.INITIAL_X
        opponent.rect.y = self.INITIAL_Y
        self.opponent = opponent

        ball = Ball(self.FG, self.BALL_S, self.BALL_S, self.B_VEL, self.WINDOW)
        ball.rect.x = (self.WINDOW[0] + self.BALL_S) / 2
        ball.rect.y = (self.WINDOW[1] + self.BALL_S) / 2
        self.ball = ball

        p_goal = Goal(self.BG, 1, self.WINDOW[1])
        p_goal.rect.x = 0
        self.p_goal = p_goal
        o_goal = Goal(self.BG, 1, self.WINDOW[1])
        o_goal.rect.x = self.WINDOW[0] - 1
        self.o_goal = o_goal

        sprites = pygame.sprite.Group()
        sprites.add(player)
        sprites.add(opponent)
        sprites.add(ball)
        sprites.add(p_goal)
        sprites.add(o_goal)

        self.sprites = sprites
        self.score = [0, 0]

    def ai_move(self, entity):
        ball_center = self.ball.rect.y + self.ball.rect.height / 2
        if entity.rect.y > ball_center:
            return -1
        if entity.rect.y + entity.rect.height < ball_center:
            return 1
        return 0

    def dist_to_ball(self, entity):
        return abs(entity.rect.x - self.ball.rect.x)

    def ball_direction(self):
        return math.copysign(1, self.ball.velocity[0])

    def update(self, p_input):
        if p_input != 0:
            self.player.move(p_input * self.P_VEL)

        # opponent movement
        if self.ball.rect.x > self.O_VIEW:
            move_dir = self.ai_move(self.opponent)
            if move_dir != 0:
                self.opponent.move(move_dir * self.O_VEL)

        # ball collision for players
        ball_center = self.ball.rect.y + self.ball.rect.height / 2
        if self.ball.rect.collidelist([self.player.rect, self.opponent.rect]) != -1:
            if self.ball.rect.x > self.WINDOW[0] / 2:
                rect = self.opponent.rect
            else:
                rect = self.player.rect
            center = rect.y + rect.height/2
            diff = (ball_center - center) / (self.PADDLE_H / 2)

            self.ball.velocity[0] *= -1
            self.ball.velocity[1] = diff * 5.0

            if (self.opponent.rect.x + self.PADDLE_W/3) < (self.ball.rect.x + self.BALL_S):
                self.score[0] += 1
                self.ball.reset()
            elif self.ball.rect.x < (self.player.rect.x + 2*self.PADDLE_W/3):
                self.score[1] += 1
                self.ball.reset()

        # ball collision for points
        if self.ball.rect.colliderect(self.o_goal.rect):
            self.score[0] += 1
            self.ball.reset()
        if self.ball.rect.colliderect(self.p_goal.rect):
            self.score[1] += 1
            self.ball.reset()

        self.sprites.update()

        # background
        self.screen.fill(self.BG, (0, 0, self.WINDOW[0], self.WINDOW[1]))
        pygame.draw.line(self.screen, self.FG, [(self.WINDOW[0] - 5) / 2, 0],
                         [(self.WINDOW[0]-5)/2, self.WINDOW[1]], 5)
        # scores
        font = pygame.font.Font(None, 50)
        text = font.render(str(self.score[0]), False, self.FG)
        self.screen.blit(text, (self.WINDOW[0]/2 - 50, 5))
        text = font.render(str(self.score[1]), False, self.FG)
        self.screen.blit(text, (self.WINDOW[0]/2 + 30, 5))

        # elements
        self.sprites.draw(self.screen)

        if sum(self.score) >= self.END or int(self.END/2)+1 in self.score:  # best of END
            return self.score.index(max(self.score))
