import heapq
import math
import random
import sys
from collections import defaultdict

import pygame

LEVEL_THRESHOLDS = {
    1: 0,
    2: 90,
    3: 180,
    4: 280,
    5: 390,
    6: 515,
    7: 655,
    8: 810,
    9: 980,
    10: 1170,
    11: 1380,
    12: 1615,
    13: 1875,
    14: 2155,
    15: 2465,
    16: 2805,
    17: 3175,
    18: 3580,
    19: 4020,
    20: 4500,
    21: 5025,
    22: 5600,
    23: 6225,
    24: 6905,
    25: 7645,
    26: 8450,
    27: 9325,
    28: 10275,
    29: 11305,
    30: 12425,
}

CONSTANTS = {
    'MOUSE_BUTTON_LEFT': 1,
    'MOUSE_BUTTON_RIGHT': 3,
    'WIDTH': 1920,
    'HEIGHT': 1080,
    'VIRTUAL_WIDTH': 2020,
    'VIRTUAL_HEIGHT': 1180,
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'BLACK': (0, 0, 0),
    'GREEN': (96, 144, 120),
    'NEON': (57, 255, 20),
    'YELLOW': (255, 255, 0),
    'GAMMA': (74, 254, 2),
    'PENETRATION_COLORS': [
        (255, 0, 0),
        (255, 128, 0),
        (255, 255, 0),
        (0, 255, 0),
    ],
    'PLAYER_SPEED': 0.7,
    'PLAYER_HEALTH': 7500,
    'SPAWN_INTERVAL': 450,
    'SMALL_CIRCLE_LIFETIME': 9999,
    'FPS': 60,
    'ZOMBIE_FLASH_DURATION': 50,
    'ZOMBIE_FADE_DURATION': 150,
    'MAX_ALIVE_ZOMBIES': 100,
    'HEALTH_BAR_VISIBLE_DURATION': 120,
    'ZOMBIE_AVOIDANCE_RADIUS': 5,
    'WAVE_DELAY': 10000,
    'BLOOD_SPRAY_PARTICLES': 5,
    'BLOOD_SPRAY_LIFETIME': 100000,
}
UPGRADE_OPTIONS = [
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


class EnergyOrb(pygame.sprite.Sprite):
    IMAGE_FILE = 'orb.png'

    def __init__(self, x, y):
        super().__init__()
        image = pygame.image.load(EnergyOrb.IMAGE_FILE).convert_alpha()
        self.image = pygame.transform.scale(image, (20, 20))

        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 10000000
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()


class Chest(pygame.sprite.Sprite):
    IMAGE_FILE = 'chest.png'

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load(Chest.IMAGE_FILE).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.opened = False

    def open(self):
        self.opened = True
        self.kill()


class Weapon:
    def __init__(
        self,
        name,
        projectile_speed,
        fire_rate,
        damage,
        spread_angle,
        ammo,
        reload_time,
        penetration,
        locked,
        blast_radius=0,
    ):
        self.name = name
        self.projectile_speed = projectile_speed
        self.fire_rate = fire_rate
        self.damage = damage
        self.spread_angle = spread_angle
        self.ammo = ammo
        self.max_ammo = ammo
        self.reload_time = reload_time
        self.penetration = penetration
        self.locked = locked
        self.blast_radius = blast_radius


class WeaponCategory:
    def __init__(self, name, weapons):
        self.name = name
        self.weapons = weapons
        self.current_index = self.find_first_unlocked_weapon()

    def find_first_unlocked_weapon(self):
        for i, weapon in enumerate(self.weapons):
            if not weapon.locked:
                return i
        return None

    def current_weapon(self):
        if self.current_index is not None:
            return self.weapons[self.current_index]
        return None

    def next_weapon(self):
        if self.current_index is None:
            return
        start_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.weapons)
            if not self.weapons[self.current_index].locked:
                return
            if self.current_index == start_index:
                return

    def previous_weapon(self):
        if self.current_index is None:
            return
        start_index = self.current_index
        while True:
            self.current_index = (self.current_index - 1) % len(self.weapons)
            if not self.weapons[self.current_index].locked:
                return
            if self.current_index == start_index:
                return

    def has_unlocked_weapon(self):
        return any(not weapon.locked for weapon in self.weapons)


class Camera:
    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        if isinstance(entity, pygame.Rect):
            return entity.move(self.rect.topleft)
        return entity.rect.move(self.rect.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(CONSTANTS['WIDTH'] / 2)
        y = -target.rect.centery + int(CONSTANTS['HEIGHT'] / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(CONSTANTS['VIRTUAL_WIDTH'] - CONSTANTS['WIDTH']), x)
        y = max(-(CONSTANTS['VIRTUAL_HEIGHT'] - CONSTANTS['HEIGHT']), y)

        self.rect.topleft = (x, y)


class MuzzleFlash(pygame.sprite.Sprite):
    def __init__(self, pos, angle):
        super().__init__()
        self.original_image = pygame.Surface((10, 10), pygame.SRCALPHA)

        base_red = random.randint(220, 255)
        base_green = random.randint(100, 180)
        base_blue = random.randint(0, 50)
        pygame.draw.circle(self.original_image, (base_red, base_green, base_blue, 230), (10, 10), 6)

        pygame.draw.circle(self.original_image, (base_red, base_green + 20, base_blue, 180), (20, 10), 9)
        pygame.draw.circle(
            self.original_image,
            (min(base_red + 20, 255), min(base_green + 40, 255), min(base_blue + 20, 255), 130),
            (30, 10),
            12,
        )

        self.image = pygame.transform.rotate(self.original_image, math.degrees(-angle))
        self.rect = self.image.get_rect(center=pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = random.randint(1, 4)

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()

        self.weapon_categories = weapon_categories
        self.current_category_index = self.find_first_category_with_unlocked_weapon()
        self.current_weapon = self.get_current_weapon()

    def find_first_category_with_unlocked_weapon(self):
        for i, category in enumerate(self.weapon_categories):
            if category.has_unlocked_weapon():
                return i
        return 0

    def get_current_weapon(self):
        category = self.weapon_categories[self.current_category_index]
        return category.current_weapon()


class Player(pygame.sprite.Sprite):
    IMAGE_FILE = 'player.png'

    def __init__(self, x, y):
        super().__init__()
        self.original_image = pygame.image.load(Player.IMAGE_FILE).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = CONSTANTS['PLAYER_SPEED']
        self.health = CONSTANTS['PLAYER_HEALTH']
        self.shake_offset = (1, 1)
        self.shake_duration = 0.0
        self.shake_intensity = 0
        self.weapon_categories = weapon_categories
        self.current_category_index = 0
        self.set_initial_weapon()

    def set_initial_weapon(self):
        first_pistol = self.weapon_categories[0].weapons[0]
        first_pistol.locked = False
        for category in self.weapon_categories:
            for weapon in category.weapons:
                if weapon != first_pistol:
                    weapon.locked = True
        self.current_weapon = first_pistol

    def find_first_category_with_unlocked_weapon(self):
        for i, category in enumerate(self.weapon_categories):
            if category.has_unlocked_weapon():
                return i
        return 0

    def get_current_weapon(self):
        category = self.weapon_categories[self.current_category_index]
        return category.current_weapon()

    def switch_weapon_category(self, index):
        if 0 <= index < len(self.weapon_categories):
            self.current_category_index = index
            new_weapon = self.weapon_categories[self.current_category_index].current_weapon()
            if new_weapon is not None:
                self.current_weapon = new_weapon

    def cycle_weapon(self, direction):
        current_category = self.weapon_categories[self.current_category_index]
        if direction > 0:
            current_category.next_weapon()
        else:
            current_category.previous_weapon()
        new_weapon = current_category.current_weapon()
        if new_weapon is not None:
            self.current_weapon = new_weapon

    def update(self, keys, mouse_pos):
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

        if 0 <= new_x < CONSTANTS['VIRTUAL_WIDTH'] - self.rect.width:
            self.rect.x = new_x
        if 0 <= new_y < CONSTANTS['VIRTUAL_HEIGHT'] - self.rect.height:
            self.rect.y = new_y

        angle = math.atan2(mouse_pos[1] - self.rect.centery, mouse_pos[0] - self.rect.centerx)
        self.rotate(angle)

        # Debug print
        print(f'dx: {self.dx}, dy: {self.dy}')

    def rotate(self, angle):
        self.image = pygame.transform.rotate(self.original_image, -math.degrees(angle))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def draw_health_bar(self, camera):
        bar_length = 30
        bar_height = 6
        fill = (self.health / CONSTANTS['PLAYER_HEALTH']) * bar_length
        outline_rect = pygame.Rect(self.rect.centerx - bar_length / 2, self.rect.y - 20, bar_length, bar_height)
        fill_rect = pygame.Rect(self.rect.centerx - bar_length / 2, self.rect.y - 20, fill, bar_height)

        camera_outline_rect = camera.apply(pygame.Rect(outline_rect))
        camera_fill_rect = camera.apply(pygame.Rect(fill_rect))

        pygame.draw.rect(screen, CONSTANTS['NEON'], camera_fill_rect)
        pygame.draw.rect(screen, CONSTANTS['WHITE'], camera_outline_rect, 1)

    def take_damage(self, amount):
        self.health -= amount
        self.health = max(self.health, 0)

    def shake(self):
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


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, penetration, damage, blast_radius=0):
        super().__init__()
        self.image = pygame.Surface((3, 3))
        self.image.fill(CONSTANTS['YELLOW'])
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
        if not pygame.Rect(0, 0, CONSTANTS['VIRTUAL_WIDTH'], CONSTANTS['VIRTUAL_HEIGHT']).colliderect(self.rect):
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
                    damage_text = FloatingText(zombie.rect.centerx, zombie.rect.top, int(current_damage), damage_color)
                    floating_texts.add(damage_text)

                    for _ in range(CONSTANTS['BLOOD_SPRAY_PARTICLES']):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(0.7, 1.5)
                        blood_particle = BloodParticle(zombie.rect.center, angle, speed)
                        blood_particles.add(blood_particle)

    def get_penetration_color(self):
        hit_count = len(self.zombies_hit)
        color_index = min(hit_count, len(CONSTANTS['PENETRATION_COLORS']) - 1)
        return CONSTANTS['PENETRATION_COLORS'][color_index]

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
        self.grid_size = (CONSTANTS['VIRTUAL_WIDTH'] // 16, CONSTANTS['VIRTUAL_HEIGHT'] // 16)
        self.path = []
        self.path_update_interval = 1500
        self.path_update_offset = random.randint(0, self.path_update_interval)
        self.last_path_update = pygame.time.get_ticks() - self.path_update_offset
        self.show_health_bar = False
        self.last_damage_time = 0

    def get_class_name(self, zombie_class):
        for name, cls in vars(ZombieClass).items():
            if isinstance(cls, dict) and cls == zombie_class:
                return name
        return 'a'

    def get_new_roaming_target(self):
        return random.randint(0, CONSTANTS['VIRTUAL_WIDTH']), random.randint(0, CONSTANTS['VIRTUAL_HEIGHT'])

    def update(self):
        self.last_damage_time = pygame.time.get_ticks()
        self.flash()
        if self.fading:
            self.fade_out()
        elif not self.fading:
            current_time = pygame.time.get_ticks()
            if self.show_health_bar and current_time - self.last_damage_time > CONSTANTS['HEALTH_BAR_VISIBLE_DURATION']:
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
                if 0 < distance.length() < CONSTANTS['ZOMBIE_AVOIDANCE_RADIUS']:
                    avoidance_force += distance.normalize()

        if avoidance_force.length() > 0:
            avoidance_force = avoidance_force.normalize() * self.speed * 0.6
            self.rect.x += avoidance_force.x
            self.rect.y += avoidance_force.y

    def check_boundaries(self):
        self.rect.clamp_ip(pygame.Rect(0, 0, CONSTANTS['VIRTUAL_WIDTH'], CONSTANTS['VIRTUAL_HEIGHT']))

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
            if time_since_last_damage < CONSTANTS['HEALTH_BAR_VISIBLE_DURATION']:
                bar_length = 30
                bar_height = 6
                fill = (self.health / self.max_health) * bar_length
                outline_rect = pygame.Rect(self.rect.centerx - bar_length / 2, self.rect.y - 10, bar_length, bar_height)
                fill_rect = pygame.Rect(self.rect.centerx - bar_length / 2, self.rect.y - 10, fill, bar_height)
                pygame.draw.rect(screen, CONSTANTS['NEON'], camera.apply(fill_rect))
                pygame.draw.rect(screen, CONSTANTS['WHITE'], camera.apply(outline_rect), 1)

    def take_damage(self, amount):
        if not self.killed:
            self.health -= amount
            self.last_damage_time = pygame.time.get_ticks()
            self.show_health_bar = True
            self.flash()

            damage_text = FloatingText(self.rect.centerx, self.rect.top, int(amount), CONSTANTS['GAMMA'])
            floating_texts.add(damage_text)

            if self.health <= 0:
                self.killed = True
                self.start_fading()

    def start_fading(self):
        if not self.fading:
            self.fading = True
            self.fade_start_time = pygame.time.get_ticks()
            CONSTANTS['SCORE'] += self.get_score_value()
            bloodline_xp_gained = self.blood()
            CONSTANTS['TOTAL_KILLS'] += 1
            energy_orb = EnergyOrb(self.rect.centerx, self.rect.centery)
            energy_orbs.add(energy_orb)
            total_xp_gained = self.get_score_value() + bloodline_xp_gained
            update_player_level_and_xp(total_xp_gained)

    def get_score_value(self):
        score_table = {'a': 5, 'b': 10, 'c': 15, 'd': 20, 'e': 25, 'f': 30, 'g': 35, 'h': 40, 'i': 45, 'j': 50, 'k': 55}
        return score_table.get(self.zombie_class_name, 5)

    def blood(self):
        bloodline_table = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9, 'j': 10, 'k': 11}
        return bloodline_table.get(self.zombie_class_name, 1)

    def flash(self):
        self.image.fill(CONSTANTS['WHITE'], special_flags=pygame.BLEND_ADD)
        self.flash_active = True
        self.flash_start_time = pygame.time.get_ticks()

    def update_flash(self):
        if self.flash_active:
            elapsed_time = pygame.time.get_ticks() - self.flash_start_time
            if elapsed_time > CONSTANTS['ZOMBIE_FLASH_DURATION']:
                self.image = self.original_image.copy()
                self.flash_active = False

    def fade_out(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.fade_start_time
        if elapsed_time < CONSTANTS['ZOMBIE_FADE_DURATION']:
            alpha = 255 - (elapsed_time / CONSTANTS['ZOMBIE_FADE_DURATION']) * 255
            self.image.set_alpha(alpha)
        else:
            self.kill()
            pygame.mixer.Sound.play(hit_sound)


class BloodParticle(pygame.sprite.Sprite):
    def __init__(self, pos, angle, speed):
        super().__init__()
        self.image = pygame.Surface((random.randint(1, 5), random.randint(1, 5)))
        self.image.fill(CONSTANTS['RED'])
        self.rect = self.image.get_rect(center=pos)
        self.dx = speed * math.cos(angle) * -1
        self.dy = speed * math.sin(angle) * -1
        self.gravity = 0.0
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = CONSTANTS['BLOOD_SPRAY_LIFETIME']
        self.alpha = 255

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.dy += self.gravity
        self.dx *= 0.98
        self.dy *= 0.98

        elapsed_time = pygame.time.get_ticks() - self.spawn_time
        if elapsed_time < self.lifetime:
            self.alpha = int(255 * (1 - elapsed_time / self.lifetime))
            self.image.set_alpha(self.alpha)
        else:
            self.kill()


class SmallCircle(pygame.sprite.Sprite):
    def __init__(self, pos, angle, speed):
        super().__init__()
        self.image = pygame.Surface((0.1, 2.0))
        self.image.fill(CONSTANTS['RED'])
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        self.dx = self.speed * math.cos(angle)
        self.dy = self.speed * math.sin(angle)
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if pygame.time.get_ticks() - self.spawn_time > CONSTANTS['SMALL_CIRCLE_LIFETIME']:
            self.kill()


class FloatingText(pygame.sprite.Sprite):
    def __init__(self, x, y, text, color):
        super().__init__()
        self.font = pygame.font.Font('bloody.ttf', 20)
        self.text = str(text)
        self.color = color
        self.outline_color = CONSTANTS['BLACK']
        self.outline_width = 0.1
        self.create_image()
        self.rect = self.image.get_rect(center=(x, y))
        self.creation_time = pygame.time.get_ticks()
        self.duration = 1750
        self.y_speed = -2

    def create_image(self):
        outline_surface = self.font.render(self.text, True, self.outline_color)
        outline_rect = outline_surface.get_rect()
        self.image = pygame.Surface(
            (outline_rect.width + self.outline_width * 2, outline_rect.height + self.outline_width * 2), pygame.SRCALPHA
        )
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.image.blit(outline_surface, (self.outline_width + dx, self.outline_width + dy))
        text_surface = self.font.render(self.text, True, self.color)
        self.image.blit(text_surface, (self.outline_width, self.outline_width))

    def update(self):
        self.rect.y += self.y_speed

        if pygame.time.get_ticks() - self.creation_time > self.duration:
            self.kill()


def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(pos, grid_size):
    x, y = pos
    neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [(nx, ny) for nx, ny in neighbors if 0 <= nx < grid_size[0] and 0 <= ny < grid_size[1]]


def render_upgrade_panel():
    overlay = pygame.Surface((CONSTANTS['WIDTH'], CONSTANTS['HEIGHT']))
    overlay.fill(CONSTANTS['BLACK'])
    screen.blit(overlay, (0, 0))

    panel_width = 900
    panel_height = 450
    panel_x = (CONSTANTS['WIDTH'] - panel_width) // 2
    panel_y = (CONSTANTS['HEIGHT'] - panel_height) // 2

    render_text('Choose an Upgrade', font, CONSTANTS['WHITE'], panel_x + (panel_width // 2) - 100, panel_y - 50)

    option_rects = []
    for i, option in enumerate(UPGRADE_OPTIONS):
        x = panel_x + (i % 3) * 300 + 25
        y = panel_y + (i // 3) * 150
        rect = pygame.Rect(x, y, 250, 100)
        pygame.draw.rect(screen, CONSTANTS['WHITE'], rect, 2)
        render_text(option, font, CONSTANTS['WHITE'], x + 10, y + 40)
        option_rects.append(rect)

    return option_rects


def apply_upgrade(index):
    global player_xp_multiplier  # Make sure this is declared as a global variable

    if index == 0:  # Increase Health
        player.health *= 1.1
    elif index == 1:  # Increase Speed
        player.speed *= 1.1
    elif index == 2:  # Increase Damage
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.damage *= 1.1
    elif index == 3:  # Faster Reload
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.reload_time *= 0.9
    elif index == 4:  # Increase Ammo Capacity
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.max_ammo = int(weapon.max_ammo * 1.2)
                weapon.ammo = weapon.max_ammo
    elif index == 5:  # Increase Fire Rate
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.fire_rate *= 0.9
    elif index == 6:  # Improve Accuracy
        for category in weapon_categories:
            for weapon in category.weapons:
                weapon.spread_angle *= 0.9
    elif index == 7:  # Increase XP Gain
        player_xp_multiplier *= 100
    elif index == 8:  # Unlock Random Weapon
        unlock_random_weapon()

    print(f'Applied upgrade: {UPGRADE_OPTIONS[index]}')


def create_weapon(
    name, projectile_speed, fire_rate, damage, spread_angle, ammo, reload_time, penetration, locked, blast_radius=0
):
    return Weapon(
        name, projectile_speed, fire_rate, damage, spread_angle, ammo, reload_time, penetration, locked, blast_radius
    )


def display_damage_text(damage, position, color):
    damage_text = font.render(f'-{int(damage)}', True, color)
    damage_rect = damage_text.get_rect(center=position)
    screen.blit(damage_text, damage_rect)


def line_collision(start, end, zombie):
    return zombie.hitbox.clipline(start, end)


def render_text(text, font, color, x, y):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))


def manage_waves():
    global current_wave, zombies_to_spawn, wave_start_time, chest

    current_wave += 1
    print(f'Starting Wave {current_wave}')

    zombie_distribution = calculate_zombies(current_wave)
    random.shuffle(zombie_distribution)

    zombies_to_spawn = []
    for zombie_type, count in zombie_distribution:
        while count > 0:
            spawn_count = min(count, CONSTANTS['MAX_ALIVE_ZOMBIES'])
            zombies_to_spawn.append((zombie_type, spawn_count))
            count -= spawn_count

    pygame.time.set_timer(SPAWN_ZOMBIE, CONSTANTS['SPAWN_INTERVAL'])
    wave_start_time = pygame.time.get_ticks() + CONSTANTS['WAVE_DELAY']

    if current_wave > 1:
        chest = Chest(CONSTANTS['VIRTUAL_WIDTH'] // 2, CONSTANTS['VIRTUAL_HEIGHT'] // 2)
        all_sprites.add(chest)
    else:
        chest = None


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
    zombie_types = min(26, wave)  # Limit to 26 types (a-z)
    return [(chr(97 + i), base_zombies // zombie_types) for i in range(zombie_types)]


def spawn_zombie(zombie_type):
    spawn_side = random.choice(['top', 'bottom', 'left', 'right'])
    if spawn_side == 'top':
        x, y = random.randint(50, CONSTANTS['VIRTUAL_WIDTH']), 50
    elif spawn_side == 'bottom':
        x, y = random.randint(50, CONSTANTS['VIRTUAL_WIDTH']), CONSTANTS['VIRTUAL_HEIGHT']
    elif spawn_side == 'left':
        x, y = 0, random.randint(50, CONSTANTS['VIRTUAL_HEIGHT'])
    else:
        x, y = CONSTANTS['VIRTUAL_WIDTH'], random.randint(50, CONSTANTS['VIRTUAL_HEIGHT'])
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
    all_sprites.add(zombie)
    zombies.add(zombie)


def restart_game():
    global current_wave, player_level, player_xp
    CONSTANTS['SCORE'] = 0
    CONSTANTS['BLOOD'] = 0
    CONSTANTS['TOTAL_KILLS'] = 0
    current_wave = 0
    player.health = CONSTANTS['PLAYER_HEALTH']
    player.rect.center = (CONSTANTS['VIRTUAL_WIDTH'] // 2, CONSTANTS['VIRTUAL_HEIGHT'] // 2)
    all_sprites.empty()
    energy_orbs.empty()
    projectiles.empty()
    blood_particles.empty()
    zombies.empty()
    small_circles.empty()
    all_sprites.add(player)
    floating_texts.empty()
    player.set_initial_weapon()
    player_level = 1
    player_xp = 0

    for category in weapon_categories:
        for weapon in category.weapons:
            weapon.locked = True
    weapon_categories[0].weapons[0].locked = False
    player.current_weapon = weapon_categories[0].weapons[0]
    player.current_category_index = 0
    for category in weapon_categories:
        category.current_index = category.find_first_unlocked_weapon()


def update_player_level_and_xp(xp_gained):
    global player_level, player_xp, show_upgrade_panel

    player_xp += xp_gained

    while player_xp >= LEVEL_THRESHOLDS[player_level + 1]:
        player_level += 1
        player_xp -= LEVEL_THRESHOLDS[player_level]
        show_upgrade_panel = True


def draw_progress_bar(surface, x, y, width, height, progress, color):
    bar_rect = pygame.Rect(x, y, width, height)
    fill_rect = pygame.Rect(x, y, int(width * progress), height)
    pygame.draw.rect(surface, CONSTANTS['WHITE'], bar_rect, 2)
    pygame.draw.rect(surface, color, fill_rect)
    level_text = font.render(f'Brain Power: {player_level}', True, CONSTANTS['WHITE'])
    level_text_rect = level_text.get_rect(midleft=(x + 10, y + height // 2))
    surface.blit(level_text, level_text_rect)
    xp_text = font.render(f'{player_xp}/{LEVEL_THRESHOLDS[player_level + 1]}', True, CONSTANTS['WHITE'])
    xp_text_rect = xp_text.get_rect(midright=(x + width - 10, y + height // 2))
    surface.blit(xp_text, xp_text_rect)


def render_how_to_play():
    screen.fill(CONSTANTS['BLACK'])
    render_text('How to Play', font, CONSTANTS['WHITE'], CONSTANTS['WIDTH'] // 2 - 100, 25)
    render_text('WASD - Move', font, CONSTANTS['WHITE'], 100, 100)
    render_text('Left Mouse Button - Shoot', font, CONSTANTS['WHITE'], 100, 150)
    render_text('Right Mouse Button - Auto-fire', font, CONSTANTS['WHITE'], 100, 200)
    render_text('R - Reload', font, CONSTANTS['WHITE'], 100, 250)
    render_text('1-7 - Switch weapon category', font, CONSTANTS['WHITE'], 100, 300)
    render_text('Mouse Wheel - Cycle weapons in category', font, CONSTANTS['WHITE'], 100, 350)
    render_text('ESC - Pause game', font, CONSTANTS['WHITE'], 100, 400)
    render_text(
        'Press ESC to return to main menu',
        font,
        CONSTANTS['WHITE'],
        CONSTANTS['WIDTH'] // 2 - 200,
        CONSTANTS['HEIGHT'] - 100,
    )


def render_credits():
    screen.fill(CONSTANTS['BLACK'])
    render_text('Credits', font, CONSTANTS['WHITE'], CONSTANTS['WIDTH'] // 2 - 50, 50)
    render_text("Game Developer: Some dude living in his mom's basement", font, CONSTANTS['WHITE'], 100, 150)
    render_text('GraphicSFX: Me', font, CONSTANTS['WHITE'], 100, 200)
    render_text('SoundFX: Me', font, CONSTANTS['WHITE'], 100, 250)
    render_text('Programming: Me', font, CONSTANTS['WHITE'], 100, 300)
    render_text('Special Thanks: Coffee', font, CONSTANTS['WHITE'], 100, 350)
    render_text(
        'Press ESC to return to main menu',
        font,
        CONSTANTS['WHITE'],
        CONSTANTS['WIDTH'] // 2 - 200,
        CONSTANTS['HEIGHT'] - 100,
    )


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


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((CONSTANTS['WIDTH'], CONSTANTS['HEIGHT']))
    pygame.display.set_caption('TBBP Game')

    font1 = pygame.font.Font('ps2.ttf', 15)
    font = pygame.font.Font('ps2.ttf', 15)
    scorefont = pygame.font.Font('ps2.ttf', 20)
    bloodfont = pygame.font.Font('bloody.ttf', 20)
    fps_font = pygame.font.Font('ps2.ttf', 20)
    fps_color = CONSTANTS['GAMMA']
    clock = pygame.time.Clock()

    zombie_images = [pygame.image.load(f'zombie{i}.png').convert_alpha() for i in range(1, 10)]
    background_image = pygame.image.load('zombies.png').convert()

    all_zombies_group = pygame.sprite.Group()
    weapon_font = pygame.font.Font('ps2.ttf', 17)
    version_font = pygame.font.Font('ps2.ttf', 15)
    muzzle_flashes = pygame.sprite.Group()

    pygame.mixer.init()
    fire_sound_ak47 = pygame.mixer.Sound('bullet.mp3')
    fire_sound_beretta = pygame.mixer.Sound('glock.mp3')
    fire_sound_mossberg = pygame.mixer.Sound('mossberg.mp3')
    hit_sound = pygame.mixer.Sound('splat.mp3')
    reload_sound = pygame.mixer.Sound('reload.mp3')
    fire_sound_mosin = pygame.mixer.Sound('mosin.mp3')
    firing_sound_mosin = pygame.mixer.Sound('mosinshot.mp3')
    fire_sound_PKM = pygame.mixer.Sound('pkm.mp3')
    fire_sound_skorpian = pygame.mixer.Sound('skorpian.mp3')

    pistol = WeaponCategory(
        'pistols',
        [
            Weapon('Glock(PDW)', 20, 200, 24, 0.080, 15, 1900, 1, locked=False),
        ],
    )
    # Rifles
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

    camera = Camera(CONSTANTS['WIDTH'], CONSTANTS['HEIGHT'])

    blood_particles = pygame.sprite.Group()
    small_circles = pygame.sprite.Group()
    player = Player(CONSTANTS['VIRTUAL_WIDTH'] // 2, CONSTANTS['VIRTUAL_HEIGHT'] // 2)
    all_sprites = pygame.sprite.Group(player)
    projectiles = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    floating_texts = pygame.sprite.Group()
    energy_orbs = pygame.sprite.Group()
    SPAWN_ZOMBIE = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ZOMBIE, CONSTANTS['SPAWN_INTERVAL'])
    current_wave = 1
    zombies_to_spawn = []

    CURSOR_IMG = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(CURSOR_IMG, pygame.Color('white'), (20, 20), 20, 2)
    pygame.draw.circle(CURSOR_IMG, pygame.Color('white'), (20, 20), 2)
    pygame.draw.circle(CURSOR_IMG, pygame.Color('red'), (20, 20), 2)
    cursor_rect = CURSOR_IMG.get_rect()
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
    score = 0
    total_kills = 0
    player_level = 1
    player_xp = 0
    auto_firing = False
    show_upgrade_panel = False
    player_xp_multiplier = 1.0

    while running:
        adjusted_mouse_pos = get_adjusted_mouse_pos(camera)
        keys = pygame.key.get_pressed()
        dt = clock.tick(CONSTANTS['FPS']) / 1000.0
        current_time = pygame.time.get_ticks()
        time_since_last_shot = current_time - last_fired_time[player.current_weapon.name]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                cursor_rect.center = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == CONSTANTS['MOUSE_BUTTON_RIGHT']:
                    auto_firing = not auto_firing
                    print('Auto-firing mode enabled' if auto_firing else 'Auto-firing mode disabled')
                elif event.button == CONSTANTS['MOUSE_BUTTON_LEFT'] and show_upgrade_panel:
                    mouse_pos = pygame.mouse.get_pos()

                    panel_width = 1600
                    panel_height = 900
                    panel_x = (1920 - panel_width) // 2
                    panel_y = (1080 - panel_height) // 2

                    option_width = 450
                    option_height = 200
                    options_per_row = 3
                    horizontal_padding = 50
                    vertical_padding = 50

                    for i, option in enumerate(UPGRADE_OPTIONS):
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
                    if current_time - last_spawn_time >= CONSTANTS['SPAWN_INTERVAL']:
                        if zombies_to_spawn and len(zombies) < CONSTANTS['MAX_ALIVE_ZOMBIES']:  # Add this check
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
                render_upgrade_panel()
                screen.blit(CURSOR_IMG, cursor_rect)
                pygame.display.flip()
                continue

            # Update game objects and check collisions
            for orb in energy_orbs:
                if pygame.sprite.collide_rect(player, orb):
                    orb.kill()
                    update_player_level_and_xp(1)

            if chest and pygame.sprite.collide_rect(player, chest):
                chest.open()
                unlock_random_weapon()
                chest = None

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

            # Update and draw game objects
            energy_orbs.update()
            muzzle_flashes.update()
            player.update(keys, adjusted_mouse_pos)
            player.update_shake()
            blood_particles.update()
            projectiles.update()
            zombies.update()
            small_circles.update()
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
                            zombie.rect.centerx, zombie.rect.top, int(current_damage), damage_color
                        )
                        floating_texts.add(damage_text)
                        projectile.reduce_penetration(zombie)

                        for _ in range(CONSTANTS['BLOOD_SPRAY_PARTICLES']):
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(0.7, 1.5)
                            blood_particle = BloodParticle(zombie.rect.center, angle, speed)
                            blood_particles.add(blood_particle)

                        if projectile.penetration <= 0:
                            projectile.kill()

            # Draw background and other visual elements
            bg_x = -camera.rect.x
            bg_y = -camera.rect.y
            scaled_background = pygame.transform.scale(
                background_image, (CONSTANTS['VIRTUAL_WIDTH'], CONSTANTS['VIRTUAL_HEIGHT'])
            )
            screen_rect = pygame.Rect(0, 0, CONSTANTS['VIRTUAL_WIDTH'], CONSTANTS['VIRTUAL_HEIGHT'])
            image_rect = scaled_background.get_rect()
            image_rect.topleft = (bg_x, bg_y)
            cropped_image = scaled_background.subsurface(screen_rect.clip(image_rect))
            screen.blit(cropped_image, (0, 0))
            screen.blit(CURSOR_IMG, cursor_rect)

            progress = player_xp / LEVEL_THRESHOLDS[player_level + 1]
            draw_progress_bar(
                screen, 10, CONSTANTS['HEIGHT'] - 30, CONSTANTS['WIDTH'] - 20, 20, progress, CONSTANTS['RED']
            )

            for orb in energy_orbs:
                screen.blit(orb.image, camera.apply(orb))

            for particle in blood_particles:
                screen.blit(particle.image, camera.apply(particle))

            for sprite in all_sprites:
                screen.blit(sprite.image, camera.apply(sprite))

            for circle in small_circles:
                screen.blit(circle.image, camera.apply(circle))

            for flash in muzzle_flashes:
                screen.blit(flash.image, camera.apply(flash))

            for projectile in projectiles:
                screen.blit(projectile.image, camera.apply(projectile))

            for text in floating_texts:
                screen.blit(text.image, camera.apply(text))

            for zombie in zombies:
                zombie.draw_health_bar(camera)
                if pygame.sprite.collide_mask(player, zombie):
                    player.take_damage(25)
                    if player.health <= 0:
                        start_time = pygame.time.get_ticks()
                        restart_game()
                        game_state = 'main_menu'

            elapsed_time = (current_time - start_time) / 1000
            render_text(f'Time: {elapsed_time:.2f} s', font, CONSTANTS['WHITE'], 475, 10)
            render_text(f'Wave: {current_wave}', font, CONSTANTS['WHITE'], 700, 10)
            render_text(f'Score: {score}', scorefont, CONSTANTS['WHITE'], 875, 10)
            render_text(f'FPS: {int(clock.get_fps())}', fps_font, CONSTANTS['GAMMA'], CONSTANTS['WIDTH'] - 140, 10)
            render_text(f'Total Kills: {total_kills} (Remaining: {len(zombies)})', font, CONSTANTS['WHITE'], 10, 10)

            version_text = 'Alpha 1.02'
            version_surface = version_font.render(version_text, True, CONSTANTS['WHITE'])
            version_rect = version_surface.get_rect()
            version_rect.bottomright = (CONSTANTS['WIDTH'] - 10, CONSTANTS['HEIGHT'] - 40)
            screen.blit(version_surface, version_rect)

            player_pos = camera.apply(player).topleft
            weapon_text = f'{player.current_weapon.name}'
            ammo_text = f'| {player.current_weapon.ammo} |'
            weapon_text_surface = font1.render(weapon_text, True, CONSTANTS['WHITE'])
            ammo_text_surface = font1.render(ammo_text, True, CONSTANTS['YELLOW'])

            weapon_text_pos = (player_pos[0], player_pos[1] - -60)
            ammo_text_pos = (player_pos[0], player_pos[1] - -80)

            screen.blit(weapon_text_surface, weapon_text_pos)
            screen.blit(ammo_text_surface, ammo_text_pos)

            if auto_firing:
                auto_fire_text = font1.render('Auto-Fire: ON', True, CONSTANTS['YELLOW'])
                auto_fire_text_pos = (player_pos[0], player_pos[1] - -100)
                screen.blit(auto_fire_text, auto_fire_text_pos)

            player.draw_health_bar(camera)
            if reloading[player.current_weapon.name]:
                reload_text = 'Reloading...'
                reload_text_surface = font1.render(reload_text, True, CONSTANTS['YELLOW'])
                reload_text_pos = (player_pos[0], player_pos[1] - -120)
                screen.blit(reload_text_surface, reload_text_pos)
        elif game_state == 'main_menu':
            screen.fill(CONSTANTS['BLACK'])
            render_text(
                'The Black Box Project',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 200,
                CONSTANTS['HEIGHT'] // 2 - 150,
            )
            render_text(
                'Press ENTER to Play',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 200,
                CONSTANTS['HEIGHT'] // 2 - 50,
            )
            render_text(
                'Press H for How to Play',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 200,
                CONSTANTS['HEIGHT'] // 2,
            )
            render_text(
                'Press C for Credits',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 200,
                CONSTANTS['HEIGHT'] // 2 + 50,
            )
            render_text(
                'Press ESC to Quit',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 200,
                CONSTANTS['HEIGHT'] // 2 + 100,
            )
        elif game_state == 'paused':
            screen.fill(CONSTANTS['BLACK'])
            render_text(
                'Game Paused', font, CONSTANTS['WHITE'], CONSTANTS['WIDTH'] // 2 - 150, CONSTANTS['HEIGHT'] // 2 - 100
            )
            render_text(
                'Press ENTER to Resume',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 250,
                CONSTANTS['HEIGHT'] // 2,
            )
            render_text(
                'Press ESC to Main Menu',
                font,
                CONSTANTS['WHITE'],
                CONSTANTS['WIDTH'] // 2 - 250,
                CONSTANTS['HEIGHT'] // 2 + 50,
            )
        elif game_state == 'how_to_play':
            render_how_to_play()
        elif game_state == 'credits':
            render_credits()

        screen.blit(CURSOR_IMG, cursor_rect)
        pygame.display.flip()

    pygame.quit()
    sys.exit()
