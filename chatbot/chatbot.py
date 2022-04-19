import random

import pygame
import thorpy


class Img(pygame.sprite.Sprite):

    def __init__(self, pos, img, scale=None):
        super().__init__()
        self.image = pygame.image.load(img).convert_alpha()
        if scale:
            self.image = pygame.transform.smoothscale(self.image, scale)
        self.rect = self.image.get_rect(center=pos)


class Chat:

    def __init__(self, screen, window, offset, colors, rl, rand=False):
        self.screen = screen
        self.WINDOW = window
        self.offset = offset

        self.rl = rl
        self.random_ask = rand

        self.stats = {
            'valid': 0,
            'skip': 0,
            'na': 0,
        }

        self.tick = 0
        self.rl_inteval = 1000  # check every 1 seg

        self.BG = colors["bg"]

        self.question_intro = "How much do you relate to the following statement?\n"
        self.questions = [
            "I find the controls of the game to be straightforward.",
            "I find the game's interface to be easy to navigate.",
            "I feel detached from the outside world while playing the game.",
            "I do not care to check events that are happening in the real world during the game.",
            "I think the game is fun.",
            "I feel bored while playing the game.",
            "I feel the game allows me to be imaginative.",
            "I feel creative while playing the game.",
            "I am very focused on my own performance while playing the game.",
            "I want to do as well as possible during the game.",
            "I enjoy the game's graphics.",
            "I think the game is visually appealing.",
        ]
        self.question_prob = random.uniform(0.01, 0.6)
        self.current_dialogue = ""

        sprites = pygame.sprite.Group()

        bubble = Img((400, 560), './chatbot/sprites/bubble.png', (600, 100))
        sprites.add(bubble)

        bot = Img((600, 645), './chatbot/sprites/bot.png', (100, 100))
        sprites.add(bot)

        self.sprites = sprites

        labels = ["Strongly Disagree",
                  "Disagree",
                  "Somewhat Disagree",
                  "Neither Agree nor Disagree",
                  "Somewhat Agree",
                  "Agree",
                  "Strongly Agree",
                  "Skip", "N/A"
                  ]

        self.answered = True

        self.answer = None
        self.last_answer = None
        self.last_question = None
        self.question_time = None

        self.ask_counter = 0
        self.MAX_ASK = 5
        self.WAIT_ASK = 5000
        self.last_answer_time = None

        def response(button):
            # triggered on answer
            question = self.current_dialogue.split("\n")[-1]
            if button != 'N/A':
                self.questions.remove(question)
            self.rl.chat_input(button not in ['Skip', 'N/A'], self.question_time)
            self.stats['valid'] += button not in ['Skip', 'N/A']
            self.stats['skip'] += button == 'Skip'
            self.stats['na'] += button == 'N/A'

            self.last_answer_time = self.question_time
            self.question_time = None

            self.last_answer = button
            self.last_question = question
            self.answered = True
            if not self.questions:
                self.current_dialogue = "Thank you for answering!"

        elements = [thorpy.make_button(l, func=response, params={"button": l}) for l in labels]
        for element in elements:
            element.set_font_size(10)
            element.scale_to_title()

        boxes = []
        for i in range(2):
            box = thorpy.Box(elements[i*4:i*4+4+i])
            thorpy.store(box, mode="h")
            box.fit_children()
            boxes.append(box)

        boxes = thorpy.make_group(boxes)
        thorpy.store(boxes, mode="v", align="left", x=110, y=600)
        boxes.fit_children()

        self.dialogue = thorpy.MultilineText("")

        menu = thorpy.Menu([boxes, self.dialogue])

        for element in menu.get_population():
            element.surface = screen
        self.menu = menu

    def asking(self):
        return not self.answered

    def get_qa(self):
        a = None
        q = self.last_question
        if self.last_answer:
            a = self.last_answer
            self.last_answer = None
            self.last_question = None
        return q, a

    def update(self, event, tick, menu):
        self.screen.fill(self.BG, (0, self.offset, self.WINDOW[0], 10))
        change = False
        if self.answered and self.questions:
            ask = False
            if self.tick + self.rl_inteval < tick:  # allow agent action only in interval
                self.tick = tick
                if self.ask_counter < self.MAX_ASK:  # limit consecutive questions
                    ask = self.rl.step(tick)
                    if self.random_ask:
                        ask = random.uniform(0, 1) < self.question_prob
                    # ask = True
                else:
                    if tick - self.last_answer_time > self.WAIT_ASK:
                        self.ask_counter = 0

            # ask for question to model
            if ask:
                self.ask_counter += 1
                self.current_dialogue = self.question_intro + random.choice(self.questions)
                self.last_question = self.current_dialogue.split("\n")[1]
                self.question_time = tick
                self.answered = False
                change = True
            else:
                self.ask_counter = 0
                default_dialogue = "..."
                if self.current_dialogue != default_dialogue:
                    self.current_dialogue = "..."
                    change = True

        if change or event:
            self.screen.fill(self.BG, (0, self.offset, self.WINDOW[0], self.WINDOW[1] + self.offset))
            self.sprites.draw(self.screen)

            self.menu.remove_from_population(self.dialogue)
            self.dialogue = thorpy.MultilineText(text=self.current_dialogue, size=(600, 100))
            thorpy.store(self.dialogue, mode="v", align="left", x=150, y=525)
            self.menu.add_to_population(self.dialogue)
            if not self.answered:
                for element in self.menu.get_population():
                    if not isinstance(element, thorpy.MultilineText):
                        element.blit()
            for element in self.menu.get_population():
                if isinstance(element, thorpy.MultilineText):
                    element.blit()
            if event:
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                    self.menu.react(event)
