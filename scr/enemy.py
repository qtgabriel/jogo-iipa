import math
import time
import turtle
from collections import deque

from scr.world_map import WorldMap


class Enemy:

    # (alcance, metade do ângulo do cone, raio da visão periférica)
    NORMAL_VISION = (5, 40, 2)
    ALERT_VISION = (8, 75, 3)
    SEARCH_TIME = 5.0          # segundos procurando depois de perder o alvo
    CHASE_SPEED = 2            # na perseguição anda 2x mais rápido

    COLORS = {
        "patrol": (0.75, 0.75, 0.75),
        "chase": (1.0, 0.45, 0.45),
        "search": (1.0, 0.8, 0.35),
    }

    def __init__(self, world, route, interval=500, target=None, on_touch=None):
        if len(route) < 2:
            raise ValueError("a rota precisa de pelo menos 2 waypoints")
        if not world.is_walkable(*route[0]):
            raise ValueError(f"o primeiro waypoint não é chão: {route[0]}")

        self.world = world
        self.interval = interval
        self.target = target
        self.on_touch = on_touch
        self.path = self._build_path(route)
        self.index = 0
        self.step_dir = 1
        self.row, self.col = self.path[0]
        self.facing = self._facing_to(self.path[1])
        self.state = "patrol"
        self.last_seen = None
        self.search_until = 0
        self.running = False

        self.t = turtle.Turtle()
        self.t.speed(0)
        self.t.shape("square")
        self.t.color("green")
        self.t.penup()
        self.t.shapesize(world.sqr_size / 20)
        self.sync()

        self.vision = turtle.Turtle(visible=False)
        self.vision.speed(0)
        self.vision.penup()
        self.draw_vision()

    def _build_path(self, route):
        """Transforma os waypoints em todas as células do trajeto."""
        path = [route[0]]
        for (r1, c1), (r2, c2) in zip(route, route[1:]):
            d_row = (r2 > r1) - (r2 < r1)
            d_col = (c2 > c1) - (c2 < c1)
            if d_row and d_col:
                raise ValueError(f"trecho diagonal na rota: {(r1, c1)} -> {(r2, c2)}")
            while (r1, c1) != (r2, c2):
                r1, c1 = r1 + d_row, c1 + d_col
                if not self.world.is_walkable(r1, c1):
                    raise ValueError(f"parede na rota: {(r1, c1)}")
                path.append((r1, c1))
        return path

    def _facing_to(self, cell):
        d_row, d_col = cell[0] - self.row, cell[1] - self.col
        return ((d_row > 0) - (d_row < 0), (d_col > 0) - (d_col < 0))

    def _angle(self, d_row, d_col):
        """Ângulo entre o olhar e a célula (0 = bem na frente, 180 = atrás)."""
        f_row, f_col = self.facing
        cosine = (f_row * d_row + f_col * d_col) / math.hypot(d_row, d_col)
        return math.degrees(math.acos(max(-1, min(1, cosine))))

    def _blocked(self, row, col):
        """Anda em linha reta até a célula: qualquer parede no caminho bloqueia."""
        r, c = self.row, self.col
        d_row, d_col = abs(row - r), abs(col - c)
        step_row = 1 if row > r else -1
        step_col = 1 if col > c else -1
        error = d_col - d_row

        while (r, c) != (row, col):
            double = 2 * error
            if double > -d_row:
                error -= d_row
                c += step_col
            if double < d_col:
                error += d_col
                r += step_row
            if (r, c) != (row, col) and not self.world.is_walkable(r, c):
                return True

        return False

    def visible_cells(self):
        reach, half_angle, near = self.NORMAL_VISION if self.state == "patrol" else self.ALERT_VISION
        cells = set()

        for row in range(self.row - reach, self.row + reach + 1):
            for col in range(self.col - reach, self.col + reach + 1):
                d_row, d_col = row - self.row, col - self.col
                distance = math.hypot(d_row, d_col)
                if not 0 < distance <= reach or not self.world.is_walkable(row, col):
                    continue

                angle = self._angle(d_row, d_col)
                in_cone = angle <= half_angle
                in_periphery = distance <= near and angle <= 90   # nada atrás
                if (in_cone or in_periphery) and not self._blocked(row, col):
                    cells.add((row, col))

        return cells

    def sees_target(self):
        return self.target is not None and (self.target.row, self.target.col) in self.visible_cells()

    def draw_vision(self):
        """Desenha a visão atual; o clear() apaga o desenho do tick anterior."""
        screen = self.world.screen
        tracing = screen.tracer()
        screen.tracer(0)

        self.vision.clear()
        self.vision.color(self.COLORS[self.state])
        half = self.world.sqr_size / 2

        for row, col in self.visible_cells():
            x, y = self.world.cell_to_pixel(row, col)
            corners = ((x - half, y - half), (x + half, y - half),
                       (x + half, y + half), (x - half, y + half), (x - half, y - half))
            self.vision.goto(corners[0])
            self.vision.pendown()
            for corner in corners[1:]:
                self.vision.goto(corner)
            self.vision.penup()

        screen.update()
        screen.tracer(tracing)

    def sync(self):
        self.t.goto(*self.world.cell_to_pixel(self.row, self.col))

    def _move_to(self, cell):
        previous = (self.row, self.col)
        self.row, self.col = cell
        self.facing = (cell[0] - previous[0], cell[1] - previous[1])
        self.sync()

    def _next_cell(self, goal):
        """Primeira célula do caminho mais curto até o destino (BFS)."""
        start = (self.row, self.col)
        if start == goal:
            return None
        came_from = {start: None}
        queue = deque([start])

        while queue:
            cell = queue.popleft()
            if cell == goal:
                break
            row, col = cell
            for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbour = (row + d_row, col + d_col)
                if neighbour not in came_from and self.world.is_walkable(*neighbour):
                    came_from[neighbour] = cell
                    queue.append(neighbour)

        if goal not in came_from:
            return None

        cell = goal
        while came_from[cell] != start:
            cell = came_from[cell]
        return cell

    def _go(self, cell):
        if cell is not None:
            next_cell = self._next_cell(cell)
            if next_cell is not None:
                self._move_to(next_cell)

    def _patrol(self):
        if (self.row, self.col) != self.path[self.index]:
            self._go(self.path[self.index])      # voltando de uma perseguição
            return

        next_index = self.index + self.step_dir
        if not 0 <= next_index < len(self.path):
            self.step_dir *= -1
            next_index = self.index + self.step_dir

        self._move_to(self.path[next_index])
        self.index = next_index

    def step(self):
        now = time.monotonic()

        if self.sees_target():
            self.state = "chase"
            self.last_seen = (self.target.row, self.target.col)
            self._go(self.last_seen)
        elif self.state == "chase":
            self.state = "search"
            self.search_until = now + self.SEARCH_TIME
            self._go(self.last_seen)
        elif self.state == "search" and now >= self.search_until:
            self.state = "patrol"
            self._patrol()
        elif self.state == "search":
            self._go(self.last_seen)
        else:
            self._patrol()

        if self.target is not None and (self.row, self.col) == (self.target.row, self.target.col):
            if self.on_touch is not None:
                self.on_touch(self)

        self.draw_vision()

    def start(self):
        if not self.running:
            self.running = True
            self._schedule()

    def stop(self):
        self.running = False

    def _schedule(self):
        delay = self.interval
        if self.state == "chase":
            delay = max(100, self.interval // self.CHASE_SPEED)
        self.world.screen.ontimer(self._tick, delay)

    def _tick(self):
        if self.running:
            self.step()
            self._schedule()
