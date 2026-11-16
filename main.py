import time
import turtle

from scr.enemy import Enemy
from scr.player import Player
from scr.world_map import MAP_1, MAP_2, MAP_3, WorldMap

TILE = 20
MAX_LIVES = 3
MAX_AMMO = 5            # balas atordoantes por partida
INVULNERABLE = 1.5      # segundos sem poder levar outro encosto

# Cada fase é (mapa, [(rota, intervalo em ms), ...]).
PHASES = [
    (MAP_1, [
        ([(2, 8), (2, 2), (6, 2), (6, 8)], 600),
        ([(12, 17), (12, 27), (14, 27), (14, 17)], 450),
    ]),
    (MAP_2, [
        ([(15, 2), (15, 27)], 550),
        ([(11, 2), (11, 27)], 450),
        ([(7, 2), (7, 27)], 650),
    ]),
    (MAP_3, [
        ([(17, 1), (17, 28)], 550),
        ([(15, 5), (15, 24)], 450),
        ([(12, 9), (12, 20)], 650),
    ]),
]


class Game:

    def __init__(self, screen):
        self.screen = screen
        self.world = None
        self.player = None
        self.hud = None
        self.bullet = None
        self.enemies = []
        self.phase = 0
        self.lives = MAX_LIVES
        self.ammo = MAX_AMMO
        self.started = False
        self.resetting = False
        self.protected_until = 0.0

    def run(self):
        self.show_title()
        self.screen.onkeypress(self.start, "p")
        self.screen.onkeypress(self.screen.bye, "q")
        self.screen.listen()
        self.screen.mainloop()

    def show_title(self):
        t = turtle.Turtle(visible=False)
        t.penup()
        t.goto(0, 25)
        t.write("JOGO IIPA", align="center", font=("Arial", 30, "bold"))
        t.goto(0, -30)
        t.write("Pressione P para começar", align="center", font=("Arial", 16))

    def start(self):
        if not self.started:
            self.started = True
            self.lives = MAX_LIVES
            self.ammo = MAX_AMMO
            self.load(0)

    def load(self, index):
        for enemy in self.enemies:
            enemy.stop()
        self.screen.clear()
        self.screen.onkeypress(self.screen.bye, "q")

        map_data, enemy_list = PHASES[index]
        self.world = WorldMap(self.screen, TILE, map_data)
        self.world.draw()
        self.player = Player(self.world, *self.world.spawn())

        self.enemies = [
            Enemy(self.world, route, interval, target=self.player,
                  on_touch=lambda _enemy: self.hit())
            for route, interval in enemy_list
        ]
        for enemy in self.enemies:
            enemy.start()

        self.hud = turtle.Turtle(visible=False)
        self.hud.penup()
        self.bullet = turtle.Turtle(visible=False)
        self.bullet.penup()
        self.draw_hud()

        self.screen.onkeypress(self.shoot, "space")
        self.screen.onkeypress(lambda: self.move(-1, 0), "w")
        self.screen.onkeypress(lambda: self.move(0, -1), "a")
        self.screen.onkeypress(lambda: self.move(1, 0), "s")
        self.screen.onkeypress(lambda: self.move(0, 1), "d")
        self.phase = index

    def draw_hud(self):
        self.hud.clear()
        self.hud.goto(self.world.origin[0], self.world.origin[1] + 16)
        self.hud.write(f"Vida: {self.lives}   Balas: {self.ammo}",
                       align="left", font=("Arial", 14, "bold"))

    def move(self, d_row, d_col):
        self.player.move(d_row, d_col)
        if (self.player.row, self.player.col) == self.world.exit():
            self.next_phase()
        elif any((e.row, e.col) == (self.player.row, self.player.col) and not e.stunned
                 for e in self.enemies):
            self.hit()

    def shoot(self):
        if not self.started or self.ammo <= 0:
            return

        self.ammo -= 1
        self.draw_hud()

        d_row, d_col = self.player.facing
        row, col = self.player.row, self.player.col
        hit = None

        # a bala anda em linha reta até a parede ou até um inimigo
        while True:
            next_row, next_col = row + d_row, col + d_col
            if not self.world.is_walkable(next_row, next_col):
                break
            row, col = next_row, next_col
            hit = next((e for e in self.enemies if (e.row, e.col) == (row, col)), None)
            if hit is not None:
                break

        self.bullet.clear()
        self.bullet.goto(*self.world.cell_to_pixel(self.player.row, self.player.col))
        self.bullet.pendown()
        self.bullet.goto(*self.world.cell_to_pixel(row, col))
        self.bullet.penup()
        self.screen.ontimer(self.bullet.clear, 150)

        if hit is not None:
            hit.stun()

    def hit(self):
        if not self.started or self.resetting:
            return
        now = time.monotonic()
        if now < self.protected_until:
            return

        self.lives -= 1
        self.draw_hud()
        self.protected_until = now + INVULNERABLE

        if self.lives <= 0:
            self.resetting = True
            self.screen.ontimer(self.restart, 0)

    def next_phase(self):
        if self.phase + 1 < len(PHASES):
            self.load(self.phase + 1)
        else:
            self.victory()

    def victory(self):
        for enemy in self.enemies:
            enemy.stop()
        self.screen.clear()
        self.screen.onkeypress(self.screen.bye, "q")

        t = turtle.Turtle(visible=False)
        t.penup()
        t.goto(0, 20)
        t.write("VOCÊ VENCEU!", align="center", font=("Arial", 30, "bold"))
        t.goto(0, -30)
        t.write("Q para sair", align="center", font=("Arial", 16))

    def restart(self):
        """Zerou as vidas: começa de novo na primeira fase."""
        self.resetting = False
        self.lives = MAX_LIVES
        self.ammo = MAX_AMMO
        self.load(0)


def main():
    screen = turtle.Screen()
    screen.title("Jogo IIPA")

    width = len(MAP_1[0]) * TILE
    height = len(MAP_1) * TILE
    margin = 60
    screen.setup(width + 2 * margin, height + 2 * margin)
    screen.update()
    screen.screensize(screen.window_width() - 8, screen.window_height() - 8)
    screen.getcanvas().winfo_toplevel().resizable(False, False)

    Game(screen).run()


if __name__ == "__main__":
    main()
