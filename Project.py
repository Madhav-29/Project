import pygame
import random
import sys

pygame.init()

# Window
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)

# Colors
SKY = (135, 206, 235)
GREEN = (0, 200, 0)
BLUE = (50, 80, 255)
BLACK = (0, 0, 0)

# Game settings
GRAVITY = 0.4
JUMP = -8
PIPE_GAP = 180
PIPE_SPEED = 3
PIPE_WIDTH = 70
PIPE_DELAY = 1500


class Bird:

    def __init__(self):
        self.x = 100
        self.y = HEIGHT // 2
        self.vel = 0
        self.radius = 15

    def jump(self):
        self.vel = JUMP

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel

    def draw(self):
        pygame.draw.circle(screen, BLUE, (self.x, int(self.y)), self.radius)

    def rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )


class Pipe:

    def __init__(self):
        self.x = WIDTH
        self.height = random.randint(120, 380)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self):

        # Top pipe
        pygame.draw.rect(
            screen,
            GREEN,
            (self.x, 0, PIPE_WIDTH, self.height)
        )

        # Bottom pipe
        pygame.draw.rect(
            screen,
            GREEN,
            (self.x, self.height + PIPE_GAP, PIPE_WIDTH, HEIGHT)
        )

    def collide(self, bird):

        bird_rect = bird.rect()

        top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)

        bottom_rect = pygame.Rect(
            self.x,
            self.height + PIPE_GAP,
            PIPE_WIDTH,
            HEIGHT
        )

        return bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect)


def draw_score(score):

    text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))


def game():

    bird = Bird()
    pipes = []

    score = 0
    last_pipe = pygame.time.get_ticks()

    while True:

        clock.tick(60)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()

        now = pygame.time.get_ticks()

        if now - last_pipe > PIPE_DELAY:
            pipes.append(Pipe())
            last_pipe = now

        bird.update()

        for pipe in pipes[:]:

            pipe.update()

            if pipe.collide(bird):
                return score

            if pipe.x + PIPE_WIDTH < bird.x and not pipe.passed:
                pipe.passed = True
                score += 1

            if pipe.x < -PIPE_WIDTH:
                pipes.remove(pipe)

        if bird.y > HEIGHT or bird.y < 0:
            return score

        screen.fill(SKY)

        for pipe in pipes:
            pipe.draw()

        bird.draw()
        draw_score(score)

        pygame.display.update()


def game_over(score):

    while True:

        screen.fill(SKY)

        text1 = font.render(f"Game Over! Score: {score}", True, BLACK)
        text2 = font.render("Press R to Restart", True, BLACK)
        text3 = font.render("Press Q to Quit", True, BLACK)

        screen.blit(text1, (WIDTH//2 - text1.get_width()//2, 250))
        screen.blit(text2, (WIDTH//2 - text2.get_width()//2, 300))
        screen.blit(text3, (WIDTH//2 - text3.get_width()//2, 340))

        pygame.display.update()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    return

                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


while True:

    score = game()
    game_over(score)
