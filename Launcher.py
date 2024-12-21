import heapq
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import ClassVar

import pygame

from src.blood_particle import BloodParticle
from src.chest import Chest
from src.constants import COLORS, LEVEL_THRESHOLDS, PENETRATION_COLORS
from src.cursor import Cursor
from src.energy_orb import EnergyOrb
from src.floating_text import FloatingText
from src.muzzle_flash import MuzzleFlash
from src.weapons import Weapon, WeaponCategory

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

constants = {
    'WIDTH': 1920,
    'HEIGHT': 1080,
    'ZOMBIE_RADIUS': 0.1,
    'PLAYER_SPEED': 0.7,
    'SPAWN_INTERVAL': 450,
    'SMALL_CIRCLE_LIFETIME': 9999,
    'FPS': 60,
    'ZOMBIE_FADE_DURATION': 150,
    'MAX_ALIVE_ZOMBIES': 100,
    'HEALTH_BAR_VISIBLE_DURATION': 120,
    'PLAYER_HEALTH': 7500,
    'ZOMBIE_MIN_SPAWN_DISTANCE': 150,
    'ZOMBIE_AVOIDANCE_RADIUS': 5,
    'WAVE_DELAY': 10000,
    'VIRTUAL_WIDTH': 2020,
    'VIRTUAL_HEIGHT': 1180,
}
upgrade_options = [
    'HP +20%',
    'Bullet SPD 10%',
    'Bullet DMG 5%',
    'Reload SPD +5%',
    'Mag Ammo +5%',
    'Fire Rate +5%',
    'Precision +5%',
    'Increase XP Gain',
    'a Random Weapon',
]


class Camera:
    """Manages the camera's position and movement."""

    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """Applies the camera's offset to an entity's position."""
        if isinstance(entity, pygame.Rect):
            return entity.move(self.rect.topleft)
        return entity.rect.move(self.rect.topleft)

    def update(self, target):
        """Updates the camera's position to follow the target."""
        x = -target.rect.centerx + int(constants['WIDTH'] / 2)
        y = -target.rect.centery + int(constants['HEIGHT'] / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(constants['VIRTUAL_WIDTH'] - constants['WIDTH']), x)
        y = max(-(constants['VIRTUAL_HEIGHT'] - constants['HEIGHT']), y)

        self.rect.topleft = (x, y)


class Player(pygame.sprite.Sprite):
    """Represents the player character."""

    def __init__(self, x, y, image):
        super().__init__()
        self.original_image = image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = player_mask
        self.speed = constants['PLAYER_SPEED']
        self.max_health = constants['PLAYER_HEALTH']
        self.health = self.max_health
        self.level = 1
        self.xp = 0
        self.xp_multiplier = 1.0
        self.score = 0
        self.total_kills = 0
        self.shake_offset = (1, 1)
        self.shake_duration = 0.0
        self.shake_intensity = 0
        self.weapon_categories = weapon_categories
        self.current_category_index = 0
        self.set_initial_weapon()

    def set_initial_weapon(self):
        """Sets the initial weapon for the player."""
        first_pistol = self.weapon_categories[0].weapons[0]
        first_pistol.locked = False
        for category in self.weapon_categories:
            for weapon in category.weapons:
                if weapon != first_pistol:
                    weapon.locked = True
        self.current_weapon = first_pistol

    def find_first_category_with_unlocked_weapon(self):
        """Finds the index of the first category with an unlocked weapon."""
        for i, category in enumerate(self.weapon_categories):
            if category.has_unlocked_weapon():
                return i
        return 0

    def get_current_weapon(self):
        """Returns the player's currently equipped weapon."""
        category = self.weapon_categories[self.current_category_index]
        return category.current_weapon()

    def switch_weapon_category(self, index):
        """Switches to a different weapon category."""
        if 0 <= index < len(self.weapon_categories):
            self.current_category_index = index
            new_weapon = self.weapon_categories[self.current_category_index].current_weapon()
            if new_weapon is not None:
                self.current_weapon = new_weapon

    def cycle_weapon(self, direction):
        """Cycles through weapons within the current category."""
        current_category = self.weapon_categories[self.current_category_index]
        if direction > 0:
            current_category.next_weapon()
        else:
            current_category.previous_weapon()
        new_weapon = current_category.current_weapon()
        if new_weapon is not None:
            self.current_weapon = new_weapon

    def update(self, keys, mouse_pos):
        """Updates the player's position and rotation."""
        self.dx, self.dy = 0, 0
        if keys[pygame.K_w]:
            self.dy -= self.speed
        if keys[pygame.K_s]:
            self.dy += self.speed
        if keys[pygame.K_a]:
            self.dx -= self.speed
        if keys[pygame.K_d]:
            self.dx += self.speed

        new_x = self.rect.x + self.dx
        new_y = self.rect.y + self.dy

        if 0 <= new_x < constants['VIRTUAL_WIDTH'] - self.rect.width:
            self.rect.x = new_x
        if 0 <= new_y < constants['VIRTUAL_HEIGHT'] - self.rect.height:
            self.rect.y = new_y

        angle = math.atan2(mouse_pos[1] - self.rect.centery, mouse_pos[0] - self.rect.centerx)
        self.rotate(angle)

    def rotate(self, angle):
        """Rotates the player's image."""
        self.image = pygame.transform.rotate(self.original_image, -math.degrees(angle))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def take_damage(self, amount):
        """Reduces the player's health."""
        self.health -= amount
        self.health = max(self.health, 0)

    def shake(self):
        """Initiates screen shake effect."""
        self.shake_offset = (
            random.randint(-self.shake_intensity, self.shake_intensity),
            random.randint(-self.shake_intensity, self.shake_intensity),
        )
        self.shake_duration = 1

    def update_shake(self):
        if self.shake_duration > 0:
            self.rect.x += self.shake_offset[0]
            self.rect.y += self.shake_offset[1]
            self.shake_duration -= 1
        else:
            self.shake_offset = (0, 0)

    def update_level_and_xp(self, xp_gained):
        global show_upgrade_panel

        self.xp += xp_gained

        while self.xp >= LEVEL_THRESHOLDS[self.level + 1]:
            self.level += 1
            self.xp -= LEVEL_THRESHOLDS[self.level]
            show_upgrade_panel = True


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, penetration, damage, blast_radius=0):
        super().__init__()
        self.image = pygame.Surface((3, 3))
        self.image.fill(COLORS['YELLOW'])
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.dx = self.speed * math.cos(angle)
        self.dy = self.speed * math.sin(angle)
        self.initial_penetration = penetration
        self.penetration = penetration
        self.initial_damage = damage
        self.damage = damage
        self.zombies_hit = []
        self.blast_radius = blast_radius

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if not pygame.Rect(0, 0, constants['VIRTUAL_WIDTH'], constants['VIRTUAL_HEIGHT']).colliderect(self.rect):
            self.kill()
        else:
            for zombie in zombies:
                distance = math.sqrt(
                    (self.rect.centerx - zombie.rect.centerx) ** 2 + (self.rect.centery - zombie.rect.centery) ** 2
                )
                if distance <= self.blast_radius:
                    current_damage = self.get_current_damage()
                    zombie.take_damage(current_damage)

                    damage_color = self.get_penetration_color()
                    damage_text = FloatingText(
                        zombie.rect.centerx, zombie.rect.top, int(current_damage), damage_color, blood_font
                    )
                    floating_texts.add(damage_text)

                    for _ in range(BloodParticle.PARTICLES_PER_SPRAY):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(0.7, 1.5)
                        blood_particle = BloodParticle(zombie.rect.center, angle, speed)
                        blood_particles.add(blood_particle)

    def get_penetration_color(self):
        hit_count = len(self.zombies_hit)
        color_index = min(hit_count, len(PENETRATION_COLORS) - 1)
        return PENETRATION_COLORS[color_index]

    def reduce_penetration(self, zombie):
        if zombie not in self.zombies_hit:
            self.zombies_hit.append(zombie)
            self.penetration -= 1
            self.damage *= 0.9
        if self.penetration <= 0:
            self.kill()

    def get_current_damage(self):
        return self.damage


class ZombieClass:
    a = {'HEALTH': 50, 'SPEED': 1.0}
    b = {'HEALTH': 66, 'SPEED': 1.1}
    c = {'HEALTH': 99, 'SPEED': 1.2}
    d = {'HEALTH': 133, 'SPEED': 1.3}
    e = {'HEALTH': 166, 'SPEED': 1.4}
    f = {'HEALTH': 199, 'SPEED': 1.5}
    g = {'HEALTH': 233, 'SPEED': 1.6}
    h = {'HEALTH': 266, 'SPEED': 1.7}
    i = {'HEALTH': 299, 'SPEED': 1.8}
    j = {'HEALTH': 333, 'SPEED': 1.9}
    k = {'HEALTH': 444, 'SPEED': 2.0}


class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y, player, zombie_image, zombie_class):
        super().__init__()
        self.original_image = zombie_image
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = zombie_class['SPEED']
        self.player = player
        self.max_health = zombie_class['HEALTH']
        self.health = self.max_health
        self.zombie_class_name = self.get_class_name(zombie_class)
        self.fading = False
        self.fade_start_time = 0
        self.last_damage_time = 0
        self.roaming = True
        self.roaming_target = self.get_new_roaming_target()
        self.detect_radius = 12.5
        self.killed = False
        hitbox_size = int(self.rect.width * 0.5)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = self.rect.center
        self.grid_size = (constants['VIRTUAL_WIDTH'] // 16, constants['VIRTUAL_HEIGHT'] // 16)
        self.path = []
        self.path_update_interval = 1500
        self.path_update_offset = random.randint(0, self.path_update_interval)
        self.last_path_update = pygame.time.get_ticks() - self.path_update_offset
        self.show_health_bar = False
        self.last_damage_time = 0
        self.last_groan_time = pygame.time.get_ticks()
        self.next_groan_interval = random.randint(1000, 30000)

        self.groan_sounds = [
            pygame.mixer.Sound(BASE_DIR / 'sfx/zombie_groan1.mp3'),
            pygame.mixer.Sound(BASE_DIR / 'sfx/zombie_groan2.mp3'),
            pygame.mixer.Sound(BASE_DIR / 'sfx/zombie_groan3.mp3'),
        ]

    def get_class_name(self, zombie_class):
        for name, cls in vars(ZombieClass).items():
            if isinstance(cls, dict) and cls == zombie_class:
                return name
        return 'a'

    def get_new_roaming_target(self):
        return random.randint(0, constants['VIRTUAL_WIDTH']), random.randint(0, constants['VIRTUAL_HEIGHT'])

    def update(self):
        self.last_damage_time = pygame.time.get_ticks()
        self.flash()
        if self.fading:
            self.fade_out()
        elif not self.fading:
            current_time = pygame.time.get_ticks()
            if self.show_health_bar and current_time - self.last_damage_time > constants['HEALTH_BAR_VISIBLE_DURATION']:
                self.show_health_bar = False
            if current_time - self.last_path_update > self.path_update_interval:
                self.update_path()
                self.last_path_update = current_time

            if self.path:
                next_pos = self.path[0]
                direction = pygame.math.Vector2(
                    next_pos[0] * 32 - self.rect.centerx, next_pos[1] * 32 - self.rect.centery
                )
                if direction.length() > 0:
                    direction = direction.normalize() * self.speed
                    self.rect.x += direction.x
                    self.rect.y += direction.y
                if (
                    abs(self.rect.centerx - next_pos[0] * 32) < self.speed
                    and abs(self.rect.centery - next_pos[1] * 32) < self.speed
                ):
                    self.path.pop(0)

        self.avoid_other_zombies()
        self.check_boundaries()
        self.rotate_to_target()
        self.hitbox.center = self.rect.center

        current_time = pygame.time.get_ticks()
        if current_time - self.last_groan_time > self.next_groan_interval:
            self.play_random_groan()

    def play_random_groan(self):
        if not self.killed and not self.fading:
            groan_sound = random.choice(self.groan_sounds)
            groan_sound.play()

            self.last_groan_time = pygame.time.get_ticks()
            self.next_groan_interval = random.randint(1000, 30000)

    def update_path(self):
        start = (self.rect.centerx // 32, self.rect.centery // 32)
        goal = (self.player.rect.centerx // 32, self.player.rect.centery // 32)
        self.path = self.a_star(start, goal)

    def get_neighbors(self, pos):
        x, y = pos
        neighbors = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
            (x + 1, y + 1),
            (x - 1, y - 1),
            (x + 1, y - 1),
            (x - 1, y + 1),
        ]
        return [(nx, ny) for nx, ny in neighbors if 0 <= nx < self.grid_size[0] and 0 <= ny < self.grid_size[1]]

    def manhattan_distance(self, a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def a_star(self, start, goal):
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {}
        cost_so_far = defaultdict(lambda: float('inf'))
        came_from[start] = None
        cost_so_far[start] = 0

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == goal:
                break

            for next in self.get_neighbors(current):
                new_cost = cost_so_far[current] + (1 if (next[0] - current[0]) * (next[1] - current[1]) == 0 else 1.414)
                if new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.manhattan_distance(goal, next)
                    heapq.heappush(frontier, (priority, next))
                    came_from[next] = current

        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from.get(current)
            if current is None:
                break
        path.reverse()
        return path

    def avoid_other_zombies(self):
        avoidance_force = pygame.math.Vector2(0, 0)
        for other_zombie in zombies:
            if other_zombie != self:
                distance = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(other_zombie.rect.center)
                if 0 < distance.length() < constants['ZOMBIE_AVOIDANCE_RADIUS']:
                    avoidance_force += distance.normalize()

        if avoidance_force.length() > 0:
            avoidance_force = avoidance_force.normalize() * self.speed * 0.6
            self.rect.x += avoidance_force.x
            self.rect.y += avoidance_force.y

    def check_boundaries(self):
        self.rect.clamp_ip(pygame.Rect(0, 0, constants['VIRTUAL_WIDTH'], constants['VIRTUAL_HEIGHT']))

    def rotate_to_target(self):
        if self.path:
            target = (self.path[0][0] * 32, self.path[0][1] * 32)
        else:
            target = (self.player.rect.centerx, self.player.rect.centery)

        dx = target[0] - self.rect.centerx
        dy = target[1] - self.rect.centery
        if dx != 0 or dy != 0:
            angle = math.degrees(math.atan2(-dy, dx))
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

    def draw_health_bar(self, camera):
        current_time = pygame.time.get_ticks()
        if self.health < self.max_health and not self.killed:
            time_since_last_damage = current_time - self.last_damage_time
            if time_since_last_damage < constants['HEALTH_BAR_VISIBLE_DURATION']:
                HealthBar(self)

    def take_damage(self, amount):
        if not self.killed:
            self.health -= amount
            self.last_damage_time = pygame.time.get_ticks()
            self.show_health_bar = True
            self.flash()

            damage_text = FloatingText(self.rect.centerx, self.rect.top, int(amount), COLORS['GAMMA'], blood_font)
            floating_texts.add(damage_text)

            if self.health <= 0:
                self.killed = True
                self.start_fading()

    def start_fading(self):
        if not self.fading:
            self.fading = True
            self.fade_start_time = pygame.time.get_ticks()
            self.player.total_kills += 1
            score_gained = self.get_score_value()
            self.player.score += score_gained
            player.update_level_and_xp(score_gained + self.blood())

            energy_orbs.add(
                EnergyOrb(
                    x=self.rect.centerx,
                    y=self.rect.centery,
                    image=orb_image,
                )
            )

    def get_score_value(self):
        score_table = {'a': 5, 'b': 10, 'c': 15, 'd': 20, 'e': 25, 'f': 30, 'g': 35, 'h': 40, 'i': 45, 'j': 50, 'k': 55}
        return score_table.get(self.zombie_class_name, 5)

    def blood(self):
        bloodline_table = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9, 'j': 10, 'k': 11}
        return bloodline_table.get(self.zombie_class_name, 1)

    def flash(self):
        self.image.fill(COLORS['WHITE'], special_flags=pygame.BLEND_ADD)
        self.flash_active = True
        self.flash_start_time = pygame.time.get_ticks()

    def update_flash(self):
        if self.flash_active:
            elapsed_time = pygame.time.get_ticks() - self.flash_start_time
            if elapsed_time > 50:
                self.image = self.original_image.copy()
                self.flash_active = False

    def fade_out(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.fade_start_time
        if elapsed_time < constants['ZOMBIE_FADE_DURATION']:
            alpha = 255 - (elapsed_time / constants['ZOMBIE_FADE_DURATION']) * 255
            self.image.set_alpha(alpha)
        else:
            self.kill()
            pygame.mixer.Sound.play(hit_sound)


class HealthBar(pygame.sprite.Sprite):
    """Draws a health bar for player or zombie."""

    WIDTH: ClassVar = 30
    HEIGHT: ClassVar = 6
    OFFSET_X, OFFSET_Y = -20, -20

    def __init__(self, entity):
        super().__init__()
        outline_rect = pygame.Rect(
            entity.rect.centerx - self.WIDTH / 2,
            entity.rect.y + self.OFFSET_Y,
            self.WIDTH,
            self.HEIGHT,
        )
        fill_width = (entity.health / entity.max_health) * self.WIDTH
        fill_rect = outline_rect.copy()
        fill_rect.width = fill_width
        pygame.draw.rect(
            screen,
            COLORS['NEON'],
            camera.apply(fill_rect),
        )
        pygame.draw.rect(
            screen,
            COLORS['WHITE'],
            camera.apply(outline_rect),
            1,
        )


def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(pos, grid_size):
    x, y = pos
    neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [(nx, ny) for nx, ny in neighbors if 0 <= nx < grid_size[0] and 0 <= ny < grid_size[1]]


def render_upgrade_panel():
    # Create semi-transparent overlay for the whole screen
    overlay = pygame.Surface((constants['WIDTH'], constants['HEIGHT']), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with alpha=180
    screen.blit(overlay, (0, 0))

    panel_width = 900
    panel_height = 450
    panel_x = (constants['WIDTH'] - panel_width) // 2
    panel_y = (constants['HEIGHT'] - panel_height) // 2

    # Create semi-transparent panel surface with alpha channel
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 200))  # Black with alpha=200
    screen.blit(panel, (panel_x, panel_y))

    render_text('Choose an Upgrade', base_font, panel_x + (panel_width // 2) - 100, panel_y - 50)

    option_rects = []
    for i, option in enumerate(upgrade_options):
        x = panel_x + (i % 3) * 300 + 25
        y = panel_y + (i // 3) * 150
        rect = pygame.Rect(x, y, 250, 100)

        # Create semi-transparent option boxes with alpha channel
        option_surface = pygame.Surface((250, 100), pygame.SRCALPHA)
        option_surface.fill((0, 0, 0, 150))  # Black with alpha=150
        screen.blit(option_surface, (x, y))

        pygame.draw.rect(screen, COLORS['WHITE'], rect, 2)
        render_text(option, base_font, x + 10, y + 40)
        option_rects.append(rect)

    return option_rects


def apply_upgrade(index):
    if index == 0:
        player.health *= 1.1
    elif index == 1:
        player.speed *= 1.1
    elif index == 2:
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.damage *= 1.1
    elif index == 3:
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.reload_time *= 0.9
    elif index == 4:
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.max_ammo = int(weapon.max_ammo * 1.2)
                weapon.ammo = weapon.max_ammo
    elif index == 5:
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.fire_rate *= 0.9
    elif index == 6:
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.spread_angle *= 0.9
    elif index == 7:
        player.xp_multiplier *= 100
    elif index == 8:
        unlock_random_weapon()

    print(f'Applied upgrade: {upgrade_options[index]}')


def display_damage_text(damage, position, color):
    damage_text = base_font.render(f'-{int(damage)}', True, color)
    damage_rect = damage_text.get_rect(center=position)
    screen.blit(damage_text, damage_rect)


def line_collision(start, end, zombie):
    return zombie.hitbox.clipline(start, end)


def render_text(text, font, x, y, color=COLORS['WHITE']):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))


def manage_waves():
    global current_wave, zombies_to_spawn, wave_start_time

    current_wave += 1
    print(f'Starting Wave {current_wave}')

    zombie_distribution = calculate_zombies(current_wave)
    random.shuffle(zombie_distribution)

    zombies_to_spawn = []
    for zombie_type, count in zombie_distribution:
        while count > 0:
            spawn_count = min(count, constants['MAX_ALIVE_ZOMBIES'])
            zombies_to_spawn.append((zombie_type, spawn_count))
            count -= spawn_count

    pygame.time.set_timer(SPAWN_ZOMBIE, constants['SPAWN_INTERVAL'])
    wave_start_time = pygame.time.get_ticks() + constants['WAVE_DELAY']

    if current_wave > 1:
        chests.add(
            Chest(
                x=constants['VIRTUAL_WIDTH'] // 2,
                y=constants['VIRTUAL_HEIGHT'] // 2,
                image=chest_image,
            )
        )


def unlock_random_weapon():
    locked_weapons = []
    for category in weapon_categories:
        for weapon in category.weapons:
            if weapon.locked:
                locked_weapons.append((category, weapon))

    if locked_weapons:
        category, weapon_to_unlock = random.choice(locked_weapons)
        weapon_to_unlock.locked = False
        print(f'Unlocked: {weapon_to_unlock.name}')
        category.current_index = category.weapons.index(weapon_to_unlock)
        player.current_weapon = weapon_to_unlock
        player.current_category_index = weapon_categories.index(category)
    else:
        print('All weapons are already unlocked!')


def calculate_zombies(wave):
    base_zombies = 25 * wave
    zombie_types = min(26, wave)
    return [(chr(97 + i), base_zombies // zombie_types) for i in range(zombie_types)]


def spawn_zombie(zombie_type):
    spawn_side = random.choice(['top', 'bottom', 'left', 'right'])
    if spawn_side == 'top':
        x, y = random.randint(50, constants['VIRTUAL_WIDTH']), 50
    elif spawn_side == 'bottom':
        x, y = random.randint(50, constants['VIRTUAL_WIDTH']), constants['VIRTUAL_HEIGHT']
    elif spawn_side == 'left':
        x, y = 0, random.randint(50, constants['VIRTUAL_HEIGHT'])
    else:
        x, y = constants['VIRTUAL_WIDTH'], random.randint(50, constants['VIRTUAL_HEIGHT'])
    zombie_classes = {
        'a': (ZombieClass.a, zombie_images[0]),
        'b': (ZombieClass.b, zombie_images[1]),
        'c': (ZombieClass.c, zombie_images[2]),
        'd': (ZombieClass.d, zombie_images[3]),
        'e': (ZombieClass.e, zombie_images[4]),
        'f': (ZombieClass.f, zombie_images[5]),
        'g': (ZombieClass.g, zombie_images[6]),
        'h': (ZombieClass.h, zombie_images[7]),
        'i': (ZombieClass.i, zombie_images[8]),
        'j': (ZombieClass.j, zombie_images[9]),
        'k': (ZombieClass.k, zombie_images[10]),
    }
    zombie_class, zombie_image = zombie_classes.get(zombie_type, (ZombieClass.a, zombie_images[0]))
    zombie = Zombie(x, y, player, zombie_image, zombie_class)
    zombies.add(zombie)


def restart_game():
    global current_wave
    current_wave = 0
    player.health = constants['PLAYER_HEALTH']
    player.rect.center = (constants['VIRTUAL_WIDTH'] // 2, constants['VIRTUAL_HEIGHT'] // 2)

    for group in all_sprites():
        group.empty()

    players.add(player)
    player.set_initial_weapon()
    player.score = 0
    player.total_kills = 0
    player.xp = 0
    player.level = 1

    for category in weapon_categories:
        for weapon in category.weapons:
            weapon.locked = True
    weapon_categories[0].weapons[0].locked = False
    player.current_weapon = weapon_categories[0].weapons[0]
    player.current_category_index = 0
    for category in weapon_categories:
        category.current_index = category.find_first_unlocked_weapon()


def draw_progress_bar(surface, x, y, width, height, progress, color):
    bar_rect = pygame.Rect(x, y, width, height)
    fill_rect = pygame.Rect(x, y, int(width * progress), height)
    pygame.draw.rect(surface, COLORS['WHITE'], bar_rect, 2)
    pygame.draw.rect(surface, color, fill_rect)
    level_text = base_font.render(f'Brain Power: {player.level}', True, COLORS['WHITE'])
    level_text_rect = level_text.get_rect(midleft=(x + 10, y + height // 2))
    surface.blit(level_text, level_text_rect)
    xp_text = base_font.render(f'{player.xp}/{LEVEL_THRESHOLDS[player.level + 1]}', True, COLORS['WHITE'])
    xp_text_rect = xp_text.get_rect(midright=(x + width - 10, y + height // 2))
    surface.blit(xp_text, xp_text_rect)


def render_text_screen(content):
    max_x, max_y = constants['WIDTH'], constants['HEIGHT']
    center_x, center_y = max_x // 2, max_y // 2
    base_left_margin = 100
    left_margin = base_left_margin
    screen.fill(COLORS['BLACK'])
    if content == 'MAIN_MENU':
        left_margin = center_x - 200
        render_text('The Black Box Project', base_font, left_margin, center_y - 150)
        render_text('Press ENTER to Play', base_font, left_margin, center_y - 50)
        render_text('Press H for How to Play', base_font, left_margin, center_y)
        render_text('Press C for Credits', base_font, left_margin, center_y + 50)
        render_text('Press ESC to Quit', base_font, left_margin, center_y + 100)
    elif content == 'HOW_TO_PLAY':
        render_text('How to Play', base_font, center_x - 100, 25)
        render_text('WASD - Move', base_font, left_margin, 100)
        render_text('Left Mouse Button - Shoot', base_font, left_margin, 150)
        render_text('Right Mouse Button - Auto-fire', base_font, left_margin, 200)
        render_text('R - Reload', base_font, left_margin, 250)
        render_text('1-7 - Switch weapon category', base_font, left_margin, 300)
        render_text('Mouse Wheel - Cycle weapons in category', base_font, left_margin, 350)
        render_text('ESC - Pause game', base_font, left_margin, 400)
        render_text('Press ESC to return to main menu', base_font, center_x - 200, max_y - 100)
    elif content == 'CREDITS':
        render_text('Credits', base_font, center_x, -50, 50)
        render_text("Game Developer: Some dude living in his mom's basement", base_font, left_margin, 150)
        render_text('GraphicSFX: Me', base_font, left_margin, 200)
        render_text('SoundFX: Me', base_font, left_margin, 250)
        render_text('Programming: Me', base_font, left_margin, 300)
        render_text('Special Thanks: Coffee', base_font, left_margin, 350)
        render_text('Press ESC to return to main menu', base_font, center_x - 200, max_y - 100)
    elif content == 'PAUSED':
        render_text('Game Paused', base_font, center_x - 150, center_y - 100)
        render_text('Press ENTER to Resume', base_font, center_x - 250, center_y)
        render_text('Press ESC to Main Menu', base_font, center_x - 250, center_y + 50)


def set_initial_weapon(self):
    first_pistol = self.weapon_categories[0].weapons[0]
    first_pistol.locked = False
    for category in self.weapon_categories:
        for weapon in category.weapons:
            if weapon != first_pistol:
                weapon.locked = True
    self.current_weapon = first_pistol


def get_adjusted_mouse_pos(camera):
    mouse_pos = pygame.mouse.get_pos()
    return (mouse_pos[0] - camera.rect.x, mouse_pos[1] - camera.rect.y)


def create_projectile(pellet_angle):
    return Projectile(
        player.rect.centerx,
        player.rect.centery,
        pellet_angle,
        player.current_weapon.projectile_speed,
        player.current_weapon.penetration,
        player.current_weapon.damage,
        blast_radius=player.current_weapon.blast_radius,
    )


def all_sprites() -> list[pygame.sprite.Group]:
    """Returns a list of all sprite groups."""
    return [energy_orbs, blood_particles, chests, zombies, players, muzzle_flashes, projectiles, floating_texts]


if __name__ == '__main__':
    pistol = WeaponCategory(
        'pistols',
        [
            Weapon('Glock(PDW)', 20, 200, 24, 0.080, 15, 1900, 1, locked=False),
        ],
    )
    smg = WeaponCategory(
        'SMG',
        [
            Weapon('Skorpian(SMG)', 20, 90, 24, 0.080, 30, 1900, 3, locked=True),
        ],
    )
    rifles = WeaponCategory(
        'Rifles',
        [
            Weapon('SVT-40(RIFLE)', 20, 440, 59, 0.068, 10, 2250, 5, locked=True),
        ],
    )
    bolt_action = WeaponCategory(
        'Bolt Action',
        [
            Weapon('Mosin(BOLT)', 20, 2500, 85, 0.002, 5, 2700, 7, locked=True),
        ],
    )
    assault_rifles = WeaponCategory(
        'Assault Rifle',
        [
            Weapon('AK-47(AR)', 20, 100, 35, 0.090, 31, 2000, 3, locked=True),
        ],
    )
    lmgs = WeaponCategory(
        'LMG',
        [
            Weapon('PKM(LMG)', 20, 170, 30, 0.2, 51, 3000, 5, locked=True),
        ],
    )
    shotguns = WeaponCategory(
        'Shotgun',
        [
            Weapon('Mossberg 500(SG)', 20, 1200, 25, 0.6, 5, 2500, 3, locked=False),
            Weapon('Remington 870(SG)', 20, 1100, 28, 0.55, 6, 2600, 3, locked=True),
        ],
    )
    launchers = WeaponCategory(
        'Launchers',
        [
            Weapon('RPG-7(BLAST)', 20, 5000, 100, 0.1, 1, 5000, 0, locked=True, blast_radius=50),
        ],
    )
    weapon_categories = [pistol, smg, bolt_action, assault_rifles, lmgs, shotguns, launchers]

    pygame.init()

    base_font = pygame.font.Font(BASE_DIR / 'fonts/ps2.ttf', 15)
    fps_font = pygame.font.Font(BASE_DIR / 'fonts/ps2.ttf', 20)
    score_font = pygame.font.Font(BASE_DIR / 'fonts/ps2.ttf', 20)
    weapon_font = pygame.font.Font(BASE_DIR / 'fonts/ps2.ttf', 17)
    blood_font = pygame.font.Font(BASE_DIR / 'fonts/bloody.ttf', 20)

    screen = pygame.display.set_mode((constants['WIDTH'], constants['HEIGHT']))
    pygame.display.set_caption('TBBP Game')

    player_image = pygame.image.load(BASE_DIR / 'images/player.png').convert_alpha()
    player_mask = pygame.mask.from_surface(player_image)
    zombie_images = [pygame.image.load(BASE_DIR / f'images/zombie{i}.png').convert_alpha() for i in range(1, 12)]
    background_image = pygame.image.load(BASE_DIR / 'images/zombies.png').convert()
    chest_image = pygame.image.load(BASE_DIR / 'images/chest.png').convert_alpha()
    orb_image = pygame.image.load(BASE_DIR / 'images/orb.png').convert_alpha()
    orb_image = pygame.transform.scale(orb_image, (20, 20))

    pygame.mixer.init()
    fire_sound_ak47 = pygame.mixer.Sound(BASE_DIR / 'sfx/bullet.mp3')
    fire_sound_beretta = pygame.mixer.Sound(BASE_DIR / 'sfx/glock.mp3')
    fire_sound_mossberg = pygame.mixer.Sound(BASE_DIR / 'sfx/mossberg.mp3')
    fire_sound_mosin = pygame.mixer.Sound(BASE_DIR / 'sfx/mosin.mp3')
    firing_sound_mosin = pygame.mixer.Sound(BASE_DIR / 'sfx/mosinshot.mp3')
    fire_sound_PKM = pygame.mixer.Sound(BASE_DIR / 'sfx/pkm.mp3')
    fire_sound_skorpian = pygame.mixer.Sound(BASE_DIR / 'sfx/skorpian.mp3')
    fire_sound_svt = pygame.mixer.Sound(BASE_DIR / 'sfx/bullet.mp3')
    fire_sound_rpg = pygame.mixer.Sound(BASE_DIR / 'sfx/bullet.mp3')
    hit_sound = pygame.mixer.Sound(BASE_DIR / 'sfx/splat.mp3')
    reload_sound = pygame.mixer.Sound(BASE_DIR / 'sfx/reload.mp3')

    blood_particles = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    floating_texts = pygame.sprite.Group()
    energy_orbs = pygame.sprite.Group()
    muzzle_flashes = pygame.sprite.Group()
    chests = pygame.sprite.Group()
    players = pygame.sprite.Group()

    fps_color = COLORS['GAMMA']
    clock = pygame.time.Clock()
    camera = Camera(constants['WIDTH'], constants['HEIGHT'])
    player = Player(
        x=constants['VIRTUAL_WIDTH'] // 2,
        y=constants['VIRTUAL_HEIGHT'] // 2,
        image=player_image,
    )
    players.add(player)

    SPAWN_ZOMBIE = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ZOMBIE, constants['SPAWN_INTERVAL'])
    current_wave = 1
    zombies_to_spawn = []

    cursor = Cursor()
    pygame.mouse.set_visible(False)

    render_upgrade_panel()
    running = True
    game_state = 'main_menu'
    selected_weapon = 'Glock(PDW)'
    all_weapon_names = []
    for category in weapon_categories:
        for weapon in category.weapons:
            all_weapon_names.append(weapon.name)

    last_fired_time = {weapon_name: 0 for weapon_name in all_weapon_names}
    current_ammo = {
        weapon_name: weapon.ammo
        for category in weapon_categories
        for weapon in category.weapons
        for weapon_name in [weapon.name]
    }
    reloading = {weapon_name: False for weapon_name in all_weapon_names}
    reload_start_time = {weapon_name: 0 for weapon_name in all_weapon_names}
    start_time = 0
    last_spawn_time = 0
    wave_start_time = 0
    wave_delay_active = False
    auto_firing = False
    show_upgrade_panel = False

    while running:
        mouse_pos = pygame.mouse.get_pos()
        adjusted_mouse_pos = get_adjusted_mouse_pos(camera)
        keys = pygame.key.get_pressed()
        dt = clock.tick(constants['FPS']) / 1000.0
        current_time = pygame.time.get_ticks()
        time_since_last_shot = current_time - last_fired_time[player.current_weapon.name]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    auto_firing = not auto_firing
                    print('Auto-firing mode enabled' if auto_firing else 'Auto-firing mode disabled')
                elif event.button == 1 and show_upgrade_panel:
                    panel_width = 1600
                    panel_height = 900
                    panel_x = (1920 - panel_width) // 2
                    panel_y = (1080 - panel_height) // 2

                    option_width = 450
                    option_height = 200
                    options_per_row = 3
                    horizontal_padding = 50
                    vertical_padding = 50

                    for i, option in enumerate(upgrade_options):
                        row = i // options_per_row
                        col = i % options_per_row

                        x = panel_x + col * (option_width + horizontal_padding) + horizontal_padding
                        y = panel_y + row * (option_height + vertical_padding) + vertical_padding

                        if pygame.Rect(x, y, option_width, option_height).collidepoint(mouse_pos):
                            apply_upgrade(i)
                            show_upgrade_panel = False
                            break

            elif event.type == pygame.KEYDOWN:
                if game_state == 'main_menu':
                    if event.key == pygame.K_RETURN:
                        game_state = 'running'
                        start_time = pygame.time.get_ticks()
                        current_wave = 0
                        manage_waves()
                    elif event.key == pygame.K_h:
                        game_state = 'how_to_play'
                    elif event.key == pygame.K_c:
                        game_state = 'credits'
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif game_state in ['how_to_play', 'credits']:
                    if event.key == pygame.K_ESCAPE:
                        game_state = 'main_menu'
                elif game_state == 'running':
                    if event.key == pygame.K_ESCAPE:
                        game_state = 'paused'
                    elif event.key in [
                        pygame.K_1,
                        pygame.K_2,
                        pygame.K_3,
                        pygame.K_4,
                        pygame.K_5,
                        pygame.K_6,
                        pygame.K_7,
                    ]:
                        category_index = event.key - pygame.K_1
                        player.switch_weapon_category(category_index)
                    elif event.key == pygame.K_r:
                        if (
                            not reloading[player.current_weapon.name]
                            and player.current_weapon.ammo < player.current_weapon.max_ammo
                        ):
                            reload_start_time[player.current_weapon.name] = current_time
                            reloading[player.current_weapon.name] = True
                            pygame.mixer.Sound.play(reload_sound)
                elif game_state == 'paused':
                    if event.key == pygame.K_RETURN:
                        game_state = 'running'
                    elif event.key == pygame.K_ESCAPE:
                        game_state = 'main_menu'
            elif event.type == pygame.MOUSEWHEEL and game_state == 'running':
                player.cycle_weapon(event.y)
            elif event.type == SPAWN_ZOMBIE and game_state == 'running':
                if current_time >= wave_start_time:
                    if wave_delay_active:
                        wave_delay_active = False
                    if current_time - last_spawn_time >= constants['SPAWN_INTERVAL']:
                        if zombies_to_spawn and len(zombies) < constants['MAX_ALIVE_ZOMBIES']:
                            zombie_type, count = random.choice(zombies_to_spawn)
                            spawn_zombie(zombie_type)
                            count -= 1
                            if count > 0:
                                zombies_to_spawn = [
                                    (t, c) if t != zombie_type else (t, count) for t, c in zombies_to_spawn
                                ]
                            else:
                                zombies_to_spawn = [(t, c) for t, c in zombies_to_spawn if t != zombie_type]
                            last_spawn_time = current_time
                        elif not zombies and not zombies_to_spawn:
                            wave_delay_active = True
                            manage_waves()

        if game_state == 'running':
            player.update(keys, adjusted_mouse_pos)
            camera.update(player)

            if show_upgrade_panel:
                # Draw the game world first
                bg_x = -camera.rect.x
                bg_y = -camera.rect.y
                scaled_background = pygame.transform.scale(
                    background_image, (constants['VIRTUAL_WIDTH'], constants['VIRTUAL_HEIGHT'])
                )
                screen_rect = pygame.Rect(0, 0, constants['VIRTUAL_WIDTH'], constants['VIRTUAL_HEIGHT'])
                image_rect = scaled_background.get_rect()
                image_rect.topleft = (bg_x, bg_y)
                cropped_image = scaled_background.subsurface(screen_rect.clip(image_rect))
                screen.blit(cropped_image, (0, 0))

                # Then render all game elements
                for group in all_sprites():
                    for sprite in group:
                        screen.blit(sprite.image, camera.apply(sprite))

                # Now add the semi-transparent overlay
                overlay = pygame.Surface((constants['WIDTH'], constants['HEIGHT']), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 75))  # Adjust alpha value (128) for desired transparency
                screen.blit(overlay, (0, 0))

                option_rects = render_upgrade_panel()
                cursor.draw(surface=screen, center_pos=mouse_pos)
                pygame.display.flip()
                continue

            for orb in energy_orbs:
                if pygame.sprite.collide_rect(player, orb):
                    orb.kill()
                    player.update_level_and_xp(1)

            for chest in chests:
                if pygame.sprite.collide_rect(player, chest):
                    chest.open()
                    unlock_random_weapon()

            if player.current_weapon.ammo == 0 and not reloading[player.current_weapon.name]:
                reload_start_time[player.current_weapon.name] = current_time
                reloading[player.current_weapon.name] = True
                pygame.mixer.Sound.play(reload_sound)

            if (
                reloading[player.current_weapon.name]
                and current_time - reload_start_time[player.current_weapon.name] >= player.current_weapon.reload_time
            ):
                player.current_weapon.ammo = player.current_weapon.max_ammo
                reloading[player.current_weapon.name] = False

            if not reloading[player.current_weapon.name] and time_since_last_shot >= player.current_weapon.fire_rate:
                mouse_buttons = pygame.mouse.get_pressed()
                if mouse_buttons[0] or auto_firing:
                    if player.current_weapon.ammo > 0:
                        angle = math.atan2(
                            adjusted_mouse_pos[1] - player.rect.centery, adjusted_mouse_pos[0] - player.rect.centerx
                        )
                        flash_pos = (
                            player.rect.centerx + math.cos(angle) * 30,
                            player.rect.centery + math.sin(angle) * 30,
                        )
                        muzzle_flash = MuzzleFlash(flash_pos, angle)
                        muzzle_flashes.add(muzzle_flash)

                        if 'SG' in player.current_weapon.name:
                            for _ in range(10):
                                pellet_angle = angle + random.uniform(
                                    -player.current_weapon.spread_angle, player.current_weapon.spread_angle
                                )
                                projectiles.add(create_projectile(pellet_angle))
                            pygame.mixer.Sound.play(fire_sound_mossberg)
                        else:
                            adjusted_angle = angle + random.uniform(
                                -player.current_weapon.spread_angle, player.current_weapon.spread_angle
                            )
                            projectiles.add(create_projectile(adjusted_angle))

                        weapon_sound = {
                            'Glock(PDW)': fire_sound_beretta,
                            'Mosin(BOLT)': [firing_sound_mosin, fire_sound_mosin],
                            'PKM(LMG)': fire_sound_PKM,
                            'Skorpian(SMG)': fire_sound_skorpian,
                            'AK-47(AR)': fire_sound_ak47,
                            # 'SVT-40(RIFLE)': fire_sound_svt,
                            # 'RPG-7(BLAST)': fire_sound_rpg
                        }.get(player.current_weapon.name, None)

                        if weapon_sound:
                            if isinstance(weapon_sound, list):
                                for sound in weapon_sound:
                                    pygame.mixer.Sound.play(sound)
                            else:
                                pygame.mixer.Sound.play(weapon_sound)

                        player.shake()
                        last_fired_time[player.current_weapon.name] = current_time
                        player.current_weapon.ammo -= 1
                    else:
                        reload_start_time[player.current_weapon.name] = current_time
                        reloading[player.current_weapon.name] = True
                        pygame.mixer.Sound.play(reload_sound)

            energy_orbs.update()
            muzzle_flashes.update()
            player.update(keys, adjusted_mouse_pos)
            player.update_shake()
            blood_particles.update()
            projectiles.update()
            zombies.update()
            floating_texts.update()
            camera.update(player)

            for projectile in projectiles:
                start_pos = projectile.rect.center
                end_pos = (start_pos[0] + projectile.dx, start_pos[1] + projectile.dy)
                for zombie in zombies:
                    if line_collision(start_pos, end_pos, zombie) and zombie not in projectile.zombies_hit:
                        current_damage = projectile.get_current_damage()
                        zombie.take_damage(current_damage)
                        damage_color = projectile.get_penetration_color()
                        damage_text = FloatingText(
                            zombie.rect.centerx, zombie.rect.top, int(current_damage), damage_color, blood_font
                        )
                        floating_texts.add(damage_text)
                        projectile.reduce_penetration(zombie)

                        for _ in range(BloodParticle.PARTICLES_PER_SPRAY):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(0.7, 1.5)
                            blood_particle = BloodParticle(zombie.rect.center, angle, speed)
                            blood_particles.add(blood_particle)

                        if projectile.penetration <= 0:
                            projectile.kill()

            bg_x = -camera.rect.x
            bg_y = -camera.rect.y
            scaled_background = pygame.transform.scale(
                background_image, (constants['VIRTUAL_WIDTH'], constants['VIRTUAL_HEIGHT'])
            )
            screen_rect = pygame.Rect(0, 0, constants['VIRTUAL_WIDTH'], constants['VIRTUAL_HEIGHT'])
            image_rect = scaled_background.get_rect()
            image_rect.topleft = (bg_x, bg_y)
            cropped_image = scaled_background.subsurface(screen_rect.clip(image_rect))
            screen.blit(cropped_image, (0, 0))

            progress = player.xp / LEVEL_THRESHOLDS[player.level + 1]
            draw_progress_bar(
                screen, 10, constants['HEIGHT'] - 30, constants['WIDTH'] - 20, 20, progress, COLORS['RED']
            )

            for group in all_sprites():
                for sprite in group:
                    screen.blit(sprite.image, camera.apply(sprite))

            for zombie in zombies:
                zombie.draw_health_bar(camera)
                if pygame.sprite.collide_mask(player, zombie):
                    player.take_damage(25)
                    if player.health <= 0:
                        start_time = pygame.time.get_ticks()
                        restart_game()
                        game_state = 'main_menu'

            elapsed_time = (current_time - start_time) / 1000
            render_text(f'Time: {elapsed_time:.2f} s', base_font, 475, 10)
            render_text(f'Wave: {current_wave}', base_font, 700, 10)
            render_text(f'Score: {player.score}', score_font, 875, 10)
            render_text(f'FPS: {int(clock.get_fps())}', fps_font, constants['WIDTH'] - 140, 10, COLORS['GAMMA'])
            render_text(f'Total Kills: {player.total_kills} (Remaining: {len(zombies)})', base_font, 10, 10)

            version_text = 'Alpha 1.02'
            version_surface = base_font.render(version_text, True, COLORS['WHITE'])
            version_rect = version_surface.get_rect()
            version_rect.bottomright = (constants['WIDTH'] - 10, constants['HEIGHT'] - 40)
            screen.blit(version_surface, version_rect)

            player_pos = camera.apply(player).topleft
            weapon_text = f'{player.current_weapon.name}'
            ammo_text = f'| {player.current_weapon.ammo} |'
            weapon_text_surface = base_font.render(weapon_text, True, COLORS['WHITE'])
            ammo_text_surface = base_font.render(ammo_text, True, COLORS['YELLOW'])

            weapon_text_pos = (player_pos[0], player_pos[1] - -60)
            ammo_text_pos = (player_pos[0], player_pos[1] - -80)

            screen.blit(weapon_text_surface, weapon_text_pos)
            screen.blit(ammo_text_surface, ammo_text_pos)

            if auto_firing:
                auto_fire_text = base_font.render('Auto-Fire: ON', True, COLORS['YELLOW'])
                auto_fire_text_pos = (player_pos[0], player_pos[1] - -100)
                screen.blit(auto_fire_text, auto_fire_text_pos)

            HealthBar(player)
            if reloading[player.current_weapon.name]:
                reload_text = 'Reloading...'
                reload_text_surface = base_font.render(reload_text, True, COLORS['YELLOW'])
                reload_text_pos = (player_pos[0], player_pos[1] - -120)
                screen.blit(reload_text_surface, reload_text_pos)
        elif game_state == 'main_menu':
            render_text_screen('MAIN_MENU')
        elif game_state == 'paused':
            render_text_screen('PAUSED')
        elif game_state == 'how_to_play':
            render_text_screen('HOW_TO_PLAY')
        elif game_state == 'credits':
            render_text_screen('CREDITS')

        cursor.draw(surface=screen, center_pos=mouse_pos)
        pygame.display.flip()

    pygame.quit()
    sys.exit()
