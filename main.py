import turtle
from scr.world_map import WorldMap


def main():
    screen = turtle.Screen()
    world_map = WorldMap(screen, 20)
    world_map.draw()

if __name__ == "__main__":
    main()