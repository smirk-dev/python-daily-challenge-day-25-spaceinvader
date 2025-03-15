import pygame
import random
import sys
import os
import time
import math
from pygame import mixer

# Initialize pygame
pygame.init()
mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 64
ENEMY_SIZE = 64
BULLET_SIZE = (16, 32)
POWERUP_SIZE = 40
SCORE_FILE = "high_scores.txt"
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Create asset directories if they don't exist
os.makedirs("assets/images", exist_ok=True)
os.makedirs("assets/sounds", exist_ok=True)

# Load images
def load_image(name, size, color_key=None):
    # Try to load image from assets directory
    try:
        image_path = os.path.join("assets", "images", f"{name}.png")
        if os.path.exists(image_path):
            img = pygame.image.load(image_path)
            img = pygame.transform.scale(img, size)
            if color_key is not None:
                img.set_colorkey(color_key)
            return img
    except:
        pass
    
    # Create a placeholder if image can't be found
    surface = pygame.Surface(size)
    if name == "player":
        surface.fill(GREEN)
        # Draw a simple spaceship shape
        pygame.draw.polygon(surface, WHITE, [(32, 10), (10, 50), (54, 50)])
    elif name == "enemy1":
        surface.fill(RED)
        # Draw a simple enemy shape
        pygame.draw.circle(surface, WHITE, (32, 32), 20, 3)
    elif name == "enemy2":
        surface.fill(PURPLE)
        # Draw a simple enemy shape
        pygame.draw.polygon(surface, WHITE, [(20, 20), (44, 20), (32, 44)], 3)
    elif name == "enemy3":
        surface.fill(YELLOW)
        # Draw a simple enemy shape
        pygame.draw.rect(surface, WHITE, (12, 12, 40, 40), 3)
    elif name == "bullet":
        surface.fill(WHITE)
        # Add some detail to the bullet
        pygame.draw.line(surface, YELLOW, (BULLET_SIZE[0]//2, 0), (BULLET_SIZE[0]//2, BULLET_SIZE[1]), 2)
    elif name == "background":
        surface.fill(BLACK)
    elif name == "shield":
        surface.fill(GREEN)
        # Add some detail to the shield
        pygame.draw.rect(surface, BLACK, (10, 10, 80, 30), 2)
    elif name == "powerup":
        surface.fill(BLUE)
        # Add a nice glow to the powerup
        pygame.draw.circle(surface, WHITE, (POWERUP_SIZE//2, POWERUP_SIZE//2), POWERUP_SIZE//3, 3)
    elif name.startswith("explosion"):
        surface.fill(BLACK)
        surface.set_colorkey(BLACK)  # Make black transparent
        # Create an explosion effect based on the stage
        stage = int(name[-1]) if name[-1].isdigit() else 1
        radius = 10 + (stage * 10)
        pygame.draw.circle(surface, YELLOW, (ENEMY_SIZE//2, ENEMY_SIZE//2), radius)
        pygame.draw.circle(surface, RED, (ENEMY_SIZE//2, ENEMY_SIZE//2), radius - 5)
    else:
        surface.fill(color_key if color_key else (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))
    
    if color_key:
        surface.set_colorkey(color_key)
    return surface

# Load sounds
def load_sound(name):
    # Try to load the sound from a few different potential paths
    sound_paths = [
        os.path.join("assets", "sounds", f"{name}.wav"),
        os.path.join("assets", "sounds", f"{name}.mp3"),
        os.path.join("sounds", f"{name}.wav"),
        os.path.join("sounds", f"{name}.mp3")
    ]
    
    for path in sound_paths:
        try:
            if os.path.exists(path):
                sound = mixer.Sound(path)
                return sound
        except:
            pass
    
    # Return a dummy sound object that does nothing
    class DummySound:
        def play(self, loops=0):
            pass
        def set_volume(self, vol):
            pass
        def stop(self):
            pass

    return DummySound()

# Load assets
player_img = load_image("player", (PLAYER_SIZE, PLAYER_SIZE), BLACK)
enemy_img = load_image("enemy1", (ENEMY_SIZE, ENEMY_SIZE), BLACK)
enemy2_img = load_image("enemy2", (ENEMY_SIZE, ENEMY_SIZE), BLACK)
enemy3_img = load_image("enemy3", (ENEMY_SIZE, ENEMY_SIZE), BLACK)
bullet_img = load_image("bullet", BULLET_SIZE, BLACK)
background_img = load_image("background", (SCREEN_WIDTH, SCREEN_HEIGHT), BLACK)
shield_img = load_image("shield", (100, 50), BLACK)
powerup_img = load_image("powerup", (POWERUP_SIZE, POWERUP_SIZE), BLACK)
explosion_imgs = [
    load_image(f"explosion{i}", (ENEMY_SIZE, ENEMY_SIZE), BLACK) for i in range(1, 4)
]

# Load sounds
shoot_sound = load_sound("shoot")
explosion_sound = load_sound("explosion")
powerup_sound = load_sound("powerup")
game_over_sound = load_sound("game_over")
background_music = load_sound("background_music")

# Adjust sound volumes
shoot_sound.set_volume(0.3)
explosion_sound.set_volume(0.4)
powerup_sound.set_volume(0.5)
game_over_sound.set_volume(0.2)
background_music.set_volume(0.2)


class Player:
    def __init__(self):
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH // 2 - PLAYER_SIZE // 2
        self.rect.y = SCREEN_HEIGHT - 100
        self.speed = 5
        self.lives = 3
        self.shoot_cooldown = 0
        self.cooldown_time = 30  # Frames between shots
        self.power_level = 1
        self.power_timer = 0
        self.shield = False
        self.shield_timer = 0
        self.invincible = False
        self.invincible_timer = 0
        self.flicker_timer = 0
        self.visible = True
        self.dash_cooldown = 0
        self.dash_duration = 0
        self.dash_direction = 0

    def move(self, direction):
        # Apply dash if active
        if self.dash_duration > 0:
            self.rect.x += self.dash_direction * self.speed * 3
            self.dash_duration -= 1
        else:
            self.rect.x += direction * self.speed
        
        # Keep player within screen bounds
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - PLAYER_SIZE))

    def dash(self, direction):
        if self.dash_cooldown <= 0:
            self.dash_duration = 10  # Dash for 10 frames
            self.dash_direction = direction
            self.dash_cooldown = FPS * 2  # 2 second cooldown

    def update(self):
        # Handle cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Handle power-up timer
        if self.power_timer > 0:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.power_level = 1

        # Handle shield timer
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield = False

        # Handle invincibility timer
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            # Make player flicker
            self.flicker_timer += 1
            if self.flicker_timer > 5:
                self.visible = not self.visible
                self.flicker_timer = 0
            if self.invincible_timer <= 0:
                self.invincible = False
                self.visible = True

    def hit(self):
        if self.shield:
            self.shield = False
            self.shield_timer = 0
            return False
        if self.invincible:
            return False
        self.lives -= 1
        if self.lives > 0:
            self.invincible = True
            self.invincible_timer = FPS * 2  # 2 seconds of invincibility
        return self.lives <= 0

    def power_up(self, power_type):
        if power_type == "weapon":
            self.power_level = min(3, self.power_level + 1)
            self.power_timer = FPS * 15  # 15 seconds for power-up
        elif power_type == "shield":
            self.shield = True
            self.shield_timer = FPS * 10  # 10 seconds for shield
        elif power_type == "life":
            self.lives = min(5, self.lives + 1)
        elif power_type == "speed":
            self.speed = min(8, self.speed + 1)  # New speed power-up
        powerup_sound.play()


class Enemy:
    def __init__(self, x, y, enemy_type=0):
        self.enemy_type = enemy_type
        if enemy_type == 0:
            self.image = enemy_img
            self.health = 1
            self.score_value = 100
            self.speed = 1
        elif enemy_type == 1:
            self.image = enemy2_img
            self.health = 2
            self.score_value = 200
            self.speed = 1.5
        else:
            self.image = enemy3_img
            self.health = 3
            self.score_value = 300
            self.speed = 2

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1
        self.shoot_chance = 0.001 * (enemy_type + 1)
        self.explosion_index = 0
        self.exploding = False
        self.explosion_timer = 0
        # Add a float position for smoother movement
        self.float_x = float(x)
        self.float_y = float(y)
        # Add a target y-position for smooth downward movement
        self.target_y = float(y)
        # Add entrance animation
        self.entering = True
        self.entrance_y = -ENEMY_SIZE
        self.final_y = float(y)
        self.entrance_speed = random.uniform(1.0, 2.0)

    def move(self, speed_multiplier=1.0):
        if self.entering:
            # Entrance animation
            if self.float_y < self.final_y:
                self.float_y += self.entrance_speed
                self.rect.y = int(self.float_y)
            else:
                self.entering = False
                self.float_y = self.final_y
                self.rect.y = int(self.float_y)
        else:
            # Normal movement
            self.float_x += self.speed * self.direction * speed_multiplier
            self.rect.x = int(self.float_x)
            
            # Smooth downward movement if there's a target y-position
            if self.float_y < self.target_y:
                # Move down smoothly
                downward_speed = min(2.0, (self.target_y - self.float_y) / 10)
                self.float_y += downward_speed
                self.rect.y = int(self.float_y)

    def set_target_y(self, y):
        # Set a new target y-position
        self.target_y = float(y)

    def should_shoot(self):
        return random.random() < self.shoot_chance

    def hit(self):
        self.health -= 1
        return self.health <= 0

    def explode(self):
        if not self.exploding:
            self.exploding = True
            explosion_sound.play()

        self.explosion_timer += 1
        if self.explosion_timer > 5:
            self.explosion_index += 1
            self.explosion_timer = 0

        if self.explosion_index < len(explosion_imgs):
            return explosion_imgs[self.explosion_index]
        return None


class Bullet:
    def __init__(self, x, y, speed=7, enemy_bullet=False):
        self.enemy_bullet = enemy_bullet
        if enemy_bullet:
            self.image = pygame.transform.rotate(bullet_img, 180)
            self.image.fill(RED)
        else:
            self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed

    def move(self):
        if self.enemy_bullet:
            self.rect.y += self.speed
        else:
            self.rect.y -= self.speed


class Powerup:
    def __init__(self, x, y):
        self.types = ["weapon", "shield", "life", "speed"]  # Added speed power-up
        self.type = random.choice(self.types)

        # Create a new image based on the powerup type
        self.image = powerup_img.copy()
        if self.type == "weapon":
            self.image.fill(BLUE)
            pygame.draw.circle(self.image, WHITE, (POWERUP_SIZE//2, POWERUP_SIZE//2), POWERUP_SIZE//4)
        elif self.type == "shield":
            self.image.fill(GREEN)
            pygame.draw.rect(self.image, WHITE, (POWERUP_SIZE//4, POWERUP_SIZE//4, POWERUP_SIZE//2, POWERUP_SIZE//2), 2)
        elif self.type == "speed":
            self.image.fill(PURPLE)
            # Draw a lightning bolt symbol
            points = [(POWERUP_SIZE//2, 10), (20, 25), (30, 25), (20, 40)]
            pygame.draw.lines(self.image, WHITE, False, points, 3)
        else:  # life
            self.image.fill(RED)
            # Draw a heart symbol
            pygame.draw.circle(self.image, WHITE, (POWERUP_SIZE//3 * 2, POWERUP_SIZE//3), POWERUP_SIZE//6)
            pygame.draw.polygon(self.image, WHITE, [(POWERUP_SIZE//2, POWERUP_SIZE//3 * 2), 
                                                  (10, POWERUP_SIZE//3), 
                                                  (POWERUP_SIZE-10, POWERUP_SIZE//3)])

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        
    def move(self):
        self.rect.y += self.speed


class Shield:
    def __init__(self, x, y):
        self.image = shield_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = 5
        
    def hit(self):
        self.health -= 1
        # Change the shield transparency based on health
        alpha = int((self.health / 5) * 255)
        temp_shield = self.image.copy()
        temp_shield.fill((255, 255, 255, alpha), None, pygame.BLEND_RGBA_MULT)
        self.image = temp_shield
        return self.health <= 0


class Game:
    def __init__(self):
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.shields = []
        self.score = 0
        self.level = 1
        self.wave_size = 5
        self.enemy_speed_multiplier = 1.0
        self.game_over = False
        self.pause = False
        self.explosion_particles = []
        self.stars = self.create_starfield()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.high_scores = self.load_high_scores()
        self.create_shields()
        
        # Start the game music
        background_music.play(-1)  # Loop indefinitely
        
    def create_shields(self):
        # Create 3 shields
        shield_positions = [
            (SCREEN_WIDTH // 4 - 50, SCREEN_HEIGHT - 170),
            (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 170),
            (SCREEN_WIDTH * 3 // 4 - 50, SCREEN_HEIGHT - 170)
        ]
        self.shields = [Shield(x, y) for x, y in shield_positions]
    
    def create_starfield(self):
        # Create a starfield for the background
        stars = []
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            speed = random.uniform(0.1, 0.5)
            brightness = random.randint(150, 255)
            color = (brightness, brightness, brightness)
            stars.append([x, y, size, speed, color])
        return stars
    
    def update_starfield(self):
        # Move the stars down to create parallax scrolling effect
        for star in self.stars:
            star[1] += star[3]  # Move by speed
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)
    
    def spawn_enemies(self):
        # Only spawn enemies if there are none left
        if not self.enemies:
            # Increase difficulty with each wave
            self.wave_size = min(40, 5 + self.level * 2)
            self.enemy_speed_multiplier = 1.0 + (self.level * 0.1)
            
            # Calculate grid size for enemies
            cols = min(10, self.wave_size)
            rows = (self.wave_size + cols - 1) // cols  # Ceiling division
            
            # Calculate spacing
            x_spacing = (SCREEN_WIDTH - 100) // cols
            y_spacing = 50
            
            # Create enemies in a grid formation
            for i in range(self.wave_size):
                row = i // cols
                col = i % cols
                x = 50 + col * x_spacing
                y = 50 + row * y_spacing
                
                # Determine enemy type based on row
                enemy_type = 0  # Default type
                if row >= 2:
                    enemy_type = 2
                elif row >= 1:
                    enemy_type = 1
                
                self.enemies.append(Enemy(x, y, enemy_type))
            
            # Increase level
            self.level += 1
    
    def spawn_powerup(self, x, y):
        if random.random() < 0.2:  # 20% chance to spawn a power-up
            self.powerups.append(Powerup(x, y))
    
    def check_collisions(self):
        # Check player bullet collisions with enemies
        for bullet in self.bullets[:]:
            hit = False
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    if enemy.hit():
                        # Check if the enemy should drop a power-up
                        self.spawn_powerup(enemy.rect.x, enemy.rect.y)
                        # Add to score
                        self.score += enemy.score_value
                        # Start enemy explosion animation
                        enemy.explode()
                    # Remove bullet regardless
                    self.bullets.remove(bullet)
                    hit = True
                    break
            
            # Check for shield collisions
            if not hit:
                for shield in self.shields[:]:
                    if bullet.rect.colliderect(shield.rect):
                        if shield.hit():
                            self.shields.remove(shield)
                        self.bullets.remove(bullet)
                        hit = True
                        break
            
            # Remove bullets that leave the screen
            if not hit and bullet.rect.y < -BULLET_SIZE[1]:
                self.bullets.remove(bullet)
        
        # Check enemy bullet collisions with player and shields
        for bullet in self.enemy_bullets[:]:
            # Check for player collision
            if bullet.rect.colliderect(self.player.rect) and self.player.visible:
                if self.player.hit():
                    self.game_over = True
                    game_over_sound.play()
                self.enemy_bullets.remove(bullet)
                continue
            
            # Check for shield collisions
            hit_shield = False
            for shield in self.shields[:]:
                if bullet.rect.colliderect(shield.rect):
                    if shield.hit():
                        self.shields.remove(shield)
                    self.enemy_bullets.remove(bullet)
                    hit_shield = True
                    break
            
            if hit_shield:
                continue
            
            # Remove bullets that leave the screen
            if bullet.rect.y > SCREEN_HEIGHT:
                self.enemy_bullets.remove(bullet)
        
        # Check player collisions with powerups
        for powerup in self.powerups[:]:
            if self.player.rect.colliderect(powerup.rect):
                self.player.power_up(powerup.type)
                self.powerups.remove(powerup)
        
        # Check player collisions with enemies
        if not self.player.invincible:
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    if self.player.hit():
                        self.game_over = True
                        game_over_sound.play()
                    enemy.hit()  # Enemy is also damaged when hitting the player
    
    def check_enemy_movement(self):
        # Check if any enemy has reached the edge of the screen
        change_direction = False
        move_down = False
        
        for enemy in self.enemies:
            if enemy.entering:
                continue  # Skip enemies that are still in entrance animation
                
            if enemy.rect.x < 10 and enemy.direction < 0:
                change_direction = True
                move_down = True
                break
            if enemy.rect.x > SCREEN_WIDTH - ENEMY_SIZE - 10 and enemy.direction > 0:
                change_direction = True
                move_down = True
                break
        
        if change_direction:
            for enemy in self.enemies:
                if enemy.entering:
                    continue
                enemy.direction *= -1
                if move_down:
                    # Set a new target y-position instead of immediately moving down
                    enemy.set_target_y(enemy.float_y + 20)
        
        # Check if any enemy has reached the bottom of the screen
        for enemy in self.enemies:
            if enemy.rect.y > SCREEN_HEIGHT - 100:
                self.game_over = True
                game_over_sound.play()
                break
    
    def process_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-1)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(1)
        
        # Space to shoot
        if keys[pygame.K_SPACE] and self.player.shoot_cooldown <= 0:
            self.shoot()
        
        # Dash ability (double tap)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.dash(-1)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.dash(1)
    
    def shoot(self):
        # Different shooting patterns based on power level
        if self.player.power_level == 1:
            # Single bullet
            x = self.player.rect.x + PLAYER_SIZE // 2 - BULLET_SIZE[0] // 2
            y = self.player.rect.y
            self.bullets.append(Bullet(x, y))
            self.player.shoot_cooldown = self.player.cooldown_time
        elif self.player.power_level == 2:
            # Double bullets
            x1 = self.player.rect.x + PLAYER_SIZE // 4 - BULLET_SIZE[0] // 2
            x2 = self.player.rect.x + PLAYER_SIZE * 3 // 4 - BULLET_SIZE[0] // 2
            y = self.player.rect.y
            self.bullets.append(Bullet(x1, y))
            self.bullets.append(Bullet(x2, y))
            self.player.shoot_cooldown = self.player.cooldown_time
        else:  # power_level >= 3
            # Triple bullets
            x1 = self.player.rect.x + PLAYER_SIZE // 2 - BULLET_SIZE[0] // 2
            x2 = self.player.rect.x + PLAYER_SIZE // 4 - BULLET_SIZE[0] // 2
            x3 = self.player.rect.x + PLAYER_SIZE * 3 // 4 - BULLET_SIZE[0] // 2
            y = self.player.rect.y
            self.bullets.append(Bullet(x1, y))
            self.bullets.append(Bullet(x2, y))
            self.bullets.append(Bullet(x3, y))
            self.player.shoot_cooldown = self.player.cooldown_time - 10  # Faster shooting
        
        shoot_sound.play()
    
    def enemy_shoot(self):
        # Allow enemies to shoot randomly
        for enemy in self.enemies:
            if not enemy.entering and enemy.should_shoot():
                x = enemy.rect.x + ENEMY_SIZE // 2 - BULLET_SIZE[0] // 2
                y = enemy.rect.y + ENEMY_SIZE
                self.enemy_bullets.append(Bullet(x, y, 3, True))
    
    def update(self):
        if self.game_over or self.pause:
            return
        
        # Update player
        self.player.update()
        
        # Spawn enemies if needed
        self.spawn_enemies()
        
        # Update all game objects
        for bullet in self.bullets:
            bullet.move()
        
        for bullet in self.enemy_bullets:
            bullet.move()
        
        # Update enemies and handle explosions
        for enemy in self.enemies[:]:
            if enemy.exploding:
                # Update explosion animation
                explosion_img = enemy.explode()
                if explosion_img is None:
                    self.enemies.remove(enemy)
            else:
                enemy.move(self.enemy_speed_multiplier)
        
        # Allow enemies to shoot
        self.enemy_shoot()
        
        # Check enemy movement patterns
        self.check_enemy_movement()
        
        # Update powerups
        for powerup in self.powerups[:]:
            powerup.move()
            # Remove powerups that leave the screen
            if powerup.rect.y > SCREEN_HEIGHT:
                self.powerups.remove(powerup)
        
        # Update starfield
        self.update_starfield()
        
        # Check for collisions
        self.check_collisions()
    
    def render(self):
        # Draw background
        screen.blit(background_img, (0, 0))
        
        # Draw starfield
        for star in self.stars:
            pygame.draw.circle(screen, star[4], (int(star[0]), int(star[1])), star[2])
        
        # Draw shields
        for shield in self.shields:
            screen.blit(shield.image, shield.rect)
        
        # Draw player if visible
        if self.player.visible:
            screen.blit(self.player.image, self.player.rect)
            
            # Draw shield effect if active
            if self.player.shield:
                # Draw a translucent shield effect
                shield_surface = pygame.Surface((PLAYER_SIZE + 20, PLAYER_SIZE + 20), pygame.SRCALPHA)
                pygame.draw.circle(shield_surface, (0, 255, 255, 100), 
                                  (PLAYER_SIZE // 2 + 10, PLAYER_SIZE // 2 + 10), 
                                  PLAYER_SIZE // 2 + 10, 3)
                screen.blit(shield_surface, (self.player.rect.x - 10, self.player.rect.y - 10))
        
        # Draw enemies
        for enemy in self.enemies:
            if enemy.exploding:
                # Draw the current explosion frame
                if enemy.explosion_index < len(explosion_imgs):
                    screen.blit(explosion_imgs[enemy.explosion_index], enemy.rect)
            else:
                screen.blit(enemy.image, enemy.rect)
        
        # Draw bullets
        for bullet in self.bullets:
            screen.blit(bullet.image, bullet.rect)
        
        for bullet in self.enemy_bullets:
            screen.blit(bullet.image, bullet.rect)
        
        # Draw powerups
        for powerup in self.powerups:
            screen.blit(powerup.image, powerup.rect)
        
        # Draw HUD
        self.render_hud()
        
        # Draw game over screen
        if self.game_over:
            self.render_game_over()
        
        # Draw pause screen
        if self.pause:
            self.render_pause()
    def render_hud(self):
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Draw level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        screen.blit(level_text, (10, 50))
        
        # Draw lives
        lives_text = self.font.render(f"Lives: {self.player.lives}", True, WHITE)
        screen.blit(lives_text, (SCREEN_WIDTH - 150, 10))
        
        # Draw power level indicator
        power_text = self.small_font.render(f"Power: {self.player.power_level}", True, BLUE)
        screen.blit(power_text, (SCREEN_WIDTH - 150, 50))
        
        # Draw power timer
        if self.player.power_timer > 0:
            timer_width = int((self.player.power_timer / (FPS * 15)) * 100)
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 150, 75, 100, 10), 1)
            pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH - 150, 75, timer_width, 10))
        
        # Draw shield indicator
        if self.player.shield:
            shield_text = self.small_font.render("Shield Active", True, GREEN)
            screen.blit(shield_text, (SCREEN_WIDTH - 150, 90))
            
            # Draw shield timer
            timer_width = int((self.player.shield_timer / (FPS * 10)) * 100)
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 150, 110, 100, 10), 1)
            pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 150, 110, timer_width, 10))
        
        # Draw dash cooldown
        if self.player.dash_cooldown > 0:
            dash_text = self.small_font.render("Dash", True, YELLOW)
            screen.blit(dash_text, (SCREEN_WIDTH - 150, 130))
            
            timer_width = int((1 - (self.player.dash_cooldown / (FPS * 2))) * 100)
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 150, 150, 100, 10), 1)
            pygame.draw.rect(screen, YELLOW, (SCREEN_WIDTH - 150, 150, timer_width, 10))
    
    def render_game_over(self):
        # Darken the screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(game_over_text, text_rect)
        
        # Score display
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(score_text, text_rect)
        
        # High score check
        is_high_score = self.check_high_score()
        if is_high_score:
            high_score_text = self.font.render("NEW HIGH SCORE!", True, YELLOW)
            text_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            screen.blit(high_score_text, text_rect)
        
        # Restart instructions
        restart_text = self.small_font.render("Press R to restart or Q to quit", True, WHITE)
        text_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        screen.blit(restart_text, text_rect)
    
    def render_pause(self):
        # Darken the screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(120)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.font.render("PAUSED", True, WHITE)
        text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(pause_text, text_rect)
        
        # Resume instructions
        resume_text = self.small_font.render("Press P to resume", True, WHITE)
        text_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(resume_text, text_rect)
    
    def check_high_score(self):
        if not self.high_scores or self.score > self.high_scores[0]:
            self.high_scores.insert(0, self.score)
            self.high_scores = sorted(self.high_scores, reverse=True)[:5]  # Keep only top 5
            self.save_high_scores()
            return True
        return False
    
    def load_high_scores(self):
        try:
            if os.path.exists(SCORE_FILE):
                with open(SCORE_FILE, "r") as file:
                    scores = [int(score.strip()) for score in file.readlines() if score.strip()]
                return sorted(scores, reverse=True)[:5]  # Keep only top 5
        except:
            pass
        return []
    
    def save_high_scores(self):
        try:
            with open(SCORE_FILE, "w") as file:
                for score in self.high_scores:
                    file.write(f"{score}\n")
        except:
            pass
    
    def start_new_game(self):
        self.__init__()


def show_menu():
    # Create menu font
    menu_font = pygame.font.Font(None, 50)
    small_font = pygame.font.Font(None, 30)
    
    # Create title
    title_text = menu_font.render("SPACE INVADERS", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
    
    # Create buttons
    start_text = small_font.render("Press ENTER to Start", True, WHITE)
    start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    
    quit_text = small_font.render("Press ESC to Quit", True, WHITE)
    quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    
    # Load high scores
    high_scores = []
    try:
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, "r") as file:
                high_scores = [int(score.strip()) for score in file.readlines() if score.strip()]
                high_scores = sorted(high_scores, reverse=True)[:5]  # Keep only top 5
    except:
        pass
    
    # Create a simple animation effect
    stars = []
    for _ in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.randint(1, 3)
        speed = random.uniform(0.1, 1.0)
        brightness = random.randint(150, 255)
        color = (brightness, brightness, brightness)
        stars.append([x, y, size, speed, color])
    
    # Create an animated title
    title_color = [255, 255, 255]
    title_dir = -1
    
    # Load menu music if available
    menu_music = load_sound("menu_music")
    menu_music.play(-1)
    
    clock = pygame.time.Clock()
    menu_running = True
    
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    menu_music.stop()
                    return True  # Start the game
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Update animated elements
        # Update stars
        for star in stars:
            star[1] += star[3]  # Move by speed
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)
        
        # Update title color
        title_color[2] += title_dir * 2  # Change blue component
        if title_color[2] <= 100 or title_color[2] >= 255:
            title_dir *= -1
        
        # Draw everything
        screen.fill(BLACK)
        
        # Draw stars
        for star in stars:
            pygame.draw.circle(screen, star[4], (int(star[0]), int(star[1])), star[2])
        
        # Draw title with animated color
        animated_title = menu_font.render("SPACE INVADERS", True, tuple(title_color))
        screen.blit(animated_title, title_rect)
        
        # Draw buttons with pulsing effect
        alpha = 128 + int(127 * math.sin(time.time() * 3))
        start_surface = pygame.Surface(start_text.get_size(), pygame.SRCALPHA)
        start_surface.fill((255, 255, 255, alpha))
        start_surface.blit(start_text, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(start_surface, start_rect)
        
        screen.blit(quit_text, quit_rect)
        
        # Draw high scores
        high_score_text = small_font.render("HIGH SCORES", True, YELLOW)
        screen.blit(high_score_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 100))
        
        for i, score in enumerate(high_scores):
            text = small_font.render(f"{i+1}. {score}", True, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 130 + i * 30))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return False


def main():
    # Show menu first
    if not show_menu():
        pygame.quit()
        sys.exit()
    
    # Start the game
    game = Game()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    game.pause = not game.pause
                
                if game.game_over:
                    if event.key == pygame.K_r:
                        game = Game()  # Start a new game
                    elif event.key == pygame.K_q:
                        running = False
        
        # Process input (outside of event loop to get smooth movement)
        if not game.game_over and not game.pause:
            game.process_input()
        
        # Update game state
        game.update()
        
        # Render everything
        game.render()
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        game.clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()