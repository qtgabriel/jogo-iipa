import turtle

from scr.world_map import WorldMap


class Enemy:

    def __init__(self, world_map: WorldMap, route: list[tuple[int, int]], interval: int = 500) -> None:
        if len(route) < 2:
            raise ValueError("a rota precisa de pelo menos dois waypoints")
        if interval <= 0:
            raise ValueError("o intervalo precisa ser maior que zero")

        self.world = world_map
        self.route = list(route)
        self.interval = interval
        self.path = self._build_path(self.route)
        self.index = 0
        self.direction = 1
        self.row, self.col = self.path[0]
        self.running = False

        self.t = turtle.Turtle()
        self.t.speed(0)
        self.t.shape("square")
        self.t.color("green")
        self.t.penup()
        self.t.shapesize(world_map.sqr_size / 20)
        self.sync()

    def _build_path(self, route: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Expande os waypoints em todas as células do trajeto."""
        if not self.world.is_walkable(*route[0]):
            raise ValueError(f"o primeiro waypoint não é chão: {route[0]}")

        path = [route[0]]
        for start, end in zip(route, route[1:]):
            start_row, start_col = start
            end_row, end_col = end
            delta_row = (end_row > start_row) - (end_row < start_row)
            delta_col = (end_col > start_col) - (end_col < start_col)
            if delta_row and delta_col:
                raise ValueError(f"o trecho {start} -> {end} é diagonal; use trechos retos")

            row, col = start
            while (row, col) != (end_row, end_col):
                row += delta_row
                col += delta_col
                if not self.world.is_walkable(row, col):
                    raise ValueError(f"a rota passa por uma parede: ({row}, {col})")
                path.append((row, col))

        return path

    def sync(self) -> None:
        self.t.goto(*self.world.cell_to_pixel(self.row, self.col))

    def step(self) -> None:
        """Avança uma célula; nas pontas da rota, inverte o sentido."""
        if len(self.path) < 2:
            return

        next_index = self.index + self.direction
        if next_index >= len(self.path) or next_index < 0:
            self.direction = -self.direction
            next_index = self.index + self.direction

        self.index = next_index
        self.row, self.col = self.path[self.index]
        self.sync()

    def start(self) -> None:
        """Começa a patrulhar por conta própria."""
        if self.running:
            return
        self.running = True
        self._schedule()

    def stop(self) -> None:
        self.running = False

    def _schedule(self) -> None:
        self.world.screen.ontimer(self._tick, self.interval)

    def _tick(self) -> None:
        if not self.running:
            return
        self.step()
        self._schedule()
