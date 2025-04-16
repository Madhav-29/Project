import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 30)

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)

# Game settings
GRAVITY = 0.25
BIRD_JUMP = -7
PIPE_SPEED = 3
PIPE_GAP = 200
PIPE_FREQUENCY = 1500  # milliseconds

class Bird:
    def __init__(self):
        self.x = 100
        self.y = HEIGHT // 2
        self.velocity = 0
        self.radius = 15
    
    def jump(self):
        self.velocity = BIRD_JUMP
    
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        if self.y < 0:
            self.y = 0
        if self.y > HEIGHT:
            self.y = HEIGHT
    
    def draw(self):
        pygame.draw.circle(screen, BLUE, (self.x, int(self.y)), self.radius)

class Pipe:
    def __init__(self):
        self.x = WIDTH
        self.top_height = random.randint(50, HEIGHT - 250)
        self.bottom_height = HEIGHT - self.top_height - PIPE_GAP
        self.width = 60
        self.passed = False
    
    def update(self):
        self.x -= PIPE_SPEED
    
    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, 0, self.width, self.top_height))
        pygame.draw.rect(screen, GREEN, (self.x, HEIGHT - self.bottom_height, self.width, self.bottom_height))
    
    def collide(self, bird):
        bird_mask = pygame.Rect(bird.x - bird.radius, bird.y - bird.radius, bird.radius * 2, bird.radius * 2)
        top_pipe = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_pipe = pygame.Rect(self.x, HEIGHT - self.bottom_height, self.width, self.bottom_height)
        return bird_mask.colliderect(top_pipe) or bird_mask.colliderect(bottom_pipe)

def game():
    bird = Bird()
    pipes = []
    score = 0
    last_pipe = pygame.time.get_ticks()
    running = True

    while running:
        clock.tick(60)
        
        # Handle events (keyboard/mouse)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()
        
        # Generate pipes
        current_time = pygame.time.get_ticks()
        if current_time - last_pipe > PIPE_FREQUENCY:
            pipes.append(Pipe())
            last_pipe = current_time
        
        # Update bird
        bird.update()
        
        # Update pipes
        for pipe in pipes[:]:
            pipe.update()
            
            if pipe.collide(bird):
                running = False
            
            if pipe.x + pipe.width < bird.x and not pipe.passed:
                pipe.passed = True
                score += 1
            
            if pipe.x < -pipe.width:
                pipes.remove(pipe)
        
        # Draw everything
        screen.fill(SKY_BLUE)
        for pipe in pipes:
            pipe.draw()
        bird.draw()
        
        # Display score
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        pygame.display.update()
    
    # Game over screen
    screen.fill(SKY_BLUE)
    game_over_text = font.render(f"Game Over! Score: {score}", True, BLACK)
    restart_text = font.render("Press R to restart, Q to quit", True, BLACK)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 50))
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
    pygame.display.update()
    
    # Wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                    game()  # Restart
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    game()