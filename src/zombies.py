import heapq
import math
import random
from collections import defaultdict
from typing import ClassVar, Self, Sequence

import pygame

from Launcher import BASE_DIR, HealthBar, Player, ZombieClass
from src.constants import COLORS, GAME_AREA
from src.energy_orb import EnergyOrb
from src.floating_text import FloatingText

GridLocation = tuple[int, int]


class Zombie(pygame.sprite.Sprite):
    AVOIDANCE_RADIUS: ClassVar = 5
    FADE_DURATION: ClassVar = 150
    HEALTH_BAR_VISIBLE_DURATION: ClassVar = 120
    MAX_ALIVE_COUNT: ClassVar = 100
    SPAWN_INTERVAL: ClassVar = 450
    WAVE_DELAY: ClassVar = 10000

    def __init__(self, x: int, y: int, player: Player, zombie_image: pygame.Surface, zombie_class: str) -> None:
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
        self.grid_size = (GAME_AREA['WIDTH'] // 16, GAME_AREA['HEIGHT'] // 16)
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
        self.flash_active = False
        self.flash_start_time = 0

    def get_class_name(self, zombie_class: str) -> str:
        for name, cls in vars(ZombieClass).items():
            if isinstance(cls, dict) and cls == zombie_class:
                return name
        return 'a'

    def get_new_roaming_target(self) -> GridLocation:
        return random.randint(0, GAME_AREA['WIDTH']), random.randint(0, GAME_AREA['HEIGHT'])

    def update(self) -> None:
        self.last_damage_time = pygame.time.get_ticks()
        self.flash()
        if self.fading:
            self.fade_out()
        elif not self.fading:
            current_time = pygame.time.get_ticks()
            if self.show_health_bar and current_time - self.last_damage_time > self.HEALTH_BAR_VISIBLE_DURATION:
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

    def play_random_groan(self) -> None:
        if not self.killed and not self.fading:
            groan_sound = random.choice(self.groan_sounds)
            groan_sound.play()

            self.last_groan_time = pygame.time.get_ticks()
            self.next_groan_interval = random.randint(1000, 30000)

    def update_path(self) -> None:
        start = (self.rect.centerx // 32, self.rect.centery // 32)
        goal = (self.player.rect.centerx // 32, self.player.rect.centery // 32)
        self.path = self.a_star(start, goal)

    def get_neighbors(self, pos: GridLocation) -> list[GridLocation]:
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

    def manhattan_distance(self, a: GridLocation, b: GridLocation) -> int:
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def a_star(self, start: GridLocation, goal: GridLocation) -> list[GridLocation]:
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

    def avoid_other_zombies(self, zombies: Sequence[Self]) -> None:
        avoidance_force = pygame.math.Vector2(0, 0)
        for other_zombie in zombies:
            if other_zombie != self:
                distance = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(other_zombie.rect.center)
                if 0 < distance.length() < self.AVOIDANCE_RADIUS:
                    avoidance_force += distance.normalize()

        if avoidance_force.length() > 0:
            avoidance_force = avoidance_force.normalize() * self.speed * 0.6
            self.rect.x += avoidance_force.x
            self.rect.y += avoidance_force.y

    def check_boundaries(self) -> None:
        self.rect.clamp_ip(pygame.Rect(0, 0, GAME_AREA['WIDTH'], GAME_AREA['HEIGHT']))

    def rotate_to_target(self) -> None:
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

    def draw_health_bar(self) -> None:
        current_time = pygame.time.get_ticks()
        if self.health < self.max_health and not self.killed:
            time_since_last_damage = current_time - self.last_damage_time
            if time_since_last_damage < self.HEALTH_BAR_VISIBLE_DURATION:
                HealthBar(self)

    def take_damage(self, amount: int) -> None:
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

    def start_fading(self) -> None:
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

    def get_score_value(self) -> int:
        score_table = {'a': 5, 'b': 10, 'c': 15, 'd': 20, 'e': 25, 'f': 30, 'g': 35, 'h': 40, 'i': 45, 'j': 50, 'k': 55}
        return score_table.get(self.zombie_class_name, 5)

    def blood(self) -> None:
        bloodline_table = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9, 'j': 10, 'k': 11}
        return bloodline_table.get(self.zombie_class_name, 1)

    def flash(self) -> None:
        self.image.fill(COLORS['WHITE'], special_flags=pygame.BLEND_ADD)
        self.flash_active = True
        self.flash_start_time = pygame.time.get_ticks()

    def update_flash(self) -> None:
        if self.flash_active:
            elapsed_time = pygame.time.get_ticks() - self.flash_start_time
            if elapsed_time > 50:
                self.image = self.original_image.copy()
                self.flash_active = False

    def fade_out(self) -> None:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.fade_start_time
        if elapsed_time < self.FADE_DURATION:
            alpha = 255 - (elapsed_time / self.FADE_DURATION) * 255
            self.image.set_alpha(alpha)
        else:
            self.kill()
            pygame.mixer.Sound.play(hit_sound)
