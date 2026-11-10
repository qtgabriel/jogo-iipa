import turtle

from scr.enemy import Enemy
from scr.player import Player
from scr.world_map import WorldMap


def main():
    screen = turtle.Screen()
    screen.title("Jogo IIPA")

    world_map = WorldMap(screen, 20)

    # Janela do tamanho do mapa + margem: o mapa inteiro sempre cabe.
    margin = 60
    screen.setup(
        world_map.pixel_width + 2 * margin,
        world_map.pixel_height + 2 * margin,
    )
    screen.update()

    # A área de desenho passa a coincidir com a janela visível, então o
    # (0, 0) fica no centro e o mapa aparece centralizado e inteiro,
    # sem precisar de câmera.
    screen.screensize(screen.window_width() - 8, screen.window_height() - 8)
    screen.getcanvas().winfo_toplevel().resizable(False, False)

    world_map.draw()

    player = Player(world_map, *world_map.spawn)

    # Cada inimigo tem a sua rota (waypoints), cor e velocidade.
    enemies = [
        Enemy(world_map, [(2, 8), (2, 2), (6, 2), (6, 8)], interval=600),
        Enemy(world_map, [(12, 17), (12, 27), (14, 27), (14, 17)], interval=450),
    ]
    for enemy in enemies:
        enemy.start()

    screen.listen()
    screen.onkeypress(player.move_up, "w")
    screen.onkeypress(player.move_left, "a")
    screen.onkeypress(player.move_down, "s")
    screen.onkeypress(player.move_right, "d")

    screen.mainloop()


if __name__ == "__main__":
    main()
