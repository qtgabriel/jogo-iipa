import turtle
from scr.world_map import WorldMap

class Player:

    def __init__(self, world_map: WorldMap, row: int, col: int) -> None:
        self.world = world_map
        self.row = row
        self.col = col
        self.t = turtle.Turtle()
        self.t.speed(0)
        self.t.shape("square")
        self.t.color("blue")
        self.t.penup()
        self.t.shapesize(world_map.sqr_size / 20)
        self.sync()

    def sync(self) -> None:
        self.t.goto(*self.world.cell_to_pixel(self.row, self.col))

    def move(self, delta_row: int, delta_col: int) -> None:
        target_row = self.row + delta_row
        target_col = self.col + delta_col
        if not self.world.is_walkable(target_row, target_col):
            return

        self.row = target_row
        self.col = target_col
        self.sync()

    def execute_path(self):
        pass

    def move_up(self) -> None:
        self.move(-1, 0)

    def move_down(self) -> None:
        self.move(1, 0)

    def move_left(self) -> None:
        self.move(0, -1)

    def move_right(self) -> None:
        self.move(0, 1)
