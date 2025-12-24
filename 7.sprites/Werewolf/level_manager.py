import pygame


class LevelManager:
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        fade_out_ms: int = 700,
        fade_in_ms: int = 400,
        breather_ms: int = 3000,
        spawn_min_dist: int = 250,
        spawn_max_dist: int = 450,
        edge_margin: int = 90,
    ):
        self.screen_w = int(screen_width)
        self.screen_h = int(screen_height)

        self.fade_out_ms = int(fade_out_ms)
        self.fade_in_ms = int(fade_in_ms)
        self.breather_ms = int(breather_ms)

        self.spawn_min_dist = int(spawn_min_dist)
        self.spawn_max_dist = int(spawn_max_dist)
        self.edge_margin = int(edge_margin)

        self.level = 1
        self.state = "spawning"

        self._state_started_at = 0
        self._spawn_queue = []

        self._fade_surface = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        self._fade_alpha = 0

        self._game_over = False
        self._reached_level = 1

    def is_transition_locked(self) -> bool:
        return self.state in ("fading_out", "breather", "fading_in")

    def is_game_over(self) -> bool:
        return self._game_over

    def reached_level(self) -> int:
        return self._reached_level

    def trigger_game_over(self):
        if self._game_over:
            return
        self._game_over = True
        self._reached_level = self.level

    def begin_level_if_needed(self, now_ms: int, player_x: float):
        if self._game_over:
            return

        if self.state == "spawning":
            self._spawn_queue = self._compute_spawn_positions(player_x, self.level)
            self.state = "playing"
            self._state_started_at = now_ms

    def notify_level_clear_if_ready(self, now_ms: int, wraiths) -> bool:
        if self._game_over:
            return False
        if self.state != "playing":
            return False
        if not wraiths:
            return False

        for w in wraiths:
            if getattr(w, "alive", True):
                return False
            if not getattr(w, "death_anim_finished", False):
                return False

        self.state = "fading_out"
        self._state_started_at = now_ms
        self._fade_alpha = 0
        return True

    def update(self, now_ms: int):
        if self._game_over:
            return

        if self.state == "fading_out":
            elapsed = now_ms - self._state_started_at
            t = 1.0 if self.fade_out_ms <= 0 else max(0.0, min(1.0, elapsed / self.fade_out_ms))
            self._fade_alpha = int(255 * t)
            if t >= 1.0:
                self.state = "breather"
                self._state_started_at = now_ms

        elif self.state == "breather":
            elapsed = now_ms - self._state_started_at
            self._fade_alpha = 255
            if elapsed >= self.breather_ms:
                self.level += 1
                self.state = "fading_in"
                self._state_started_at = now_ms

        elif self.state == "fading_in":
            elapsed = now_ms - self._state_started_at
            t = 1.0 if self.fade_in_ms <= 0 else max(0.0, min(1.0, elapsed / self.fade_in_ms))
            self._fade_alpha = int(255 * (1.0 - t))
            if t >= 1.0:
                self._fade_alpha = 0
                self.state = "spawning"

    def consume_spawn_queue(self):
        out = list(self._spawn_queue)
        self._spawn_queue.clear()
        return out

    def draw_fade(self, screen):
        if self._fade_alpha <= 0:
            return
        self._fade_surface.fill((0, 0, 0, self._fade_alpha))
        screen.blit(self._fade_surface, (0, 0))

    def _compute_spawn_positions(self, player_x: float, count: int):
        count = max(1, int(count))

        left_bound = self.edge_margin
        right_bound = self.screen_w - self.edge_margin

        player_x = float(player_x)
        min_d = self.spawn_min_dist
        max_d = self.spawn_max_dist

        candidates = []

        if count == 1:
            candidates = [player_x + max_d]
        else:
            span = right_bound - left_bound
            step = span / (count + 1)
            candidates = [left_bound + step * (i + 1) for i in range(count)]

        def clamp(x):
            if x < left_bound:
                return left_bound
            if x > right_bound:
                return right_bound
            return x

        out = []
        for x in candidates:
            x = clamp(x)

            dx = abs(x - player_x)
            if dx < min_d:
                direction = -1 if x >= player_x else 1
                x = clamp(player_x + direction * min_d)

            dx = abs(x - player_x)
            if dx > max_d:
                direction = 1 if x >= player_x else -1
                x = clamp(player_x + direction * max_d)

            out.append(int(x))

        for i in range(1, len(out)):
            if out[i] <= out[i - 1] + 40:
                out[i] = clamp(out[i - 1] + 60)

        return out