import turtle


class Player:

    def __init__(self, world, row, col):
        self.world = world
        self.row = row
        self.col = col
        self.facing = (0, 1)
        self.t = turtle.Turtle()
        self.t.shape("square")
        self.t.color("blue")
        self.t.penup()
        self.t.shapesize(world.sqr_size / 20)
        self.sync()

    def sync(self):
        self.t.goto(*self.world.cell_to_pixel(self.row, self.col))

    def move(self, d_row, d_col):
        self.facing = (d_row, d_col)
        row, col = self.row + d_row, self.col + d_col
        if self.world.is_walkable(row, col):
            self.row, self.col = row, col
            self.sync()
