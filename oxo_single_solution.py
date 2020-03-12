# -*- coding: utf-8 -*-
"""OXO Game"""

from time import sleep
import silence_pygame
from pygame import Color
from gui import Gui, GuiHandlers
from oxo_types import Cell, Size


class Oxo():
    gui: Gui = None
    stop_game = False
    board = None
    player_ones_turn = True
    game_over = False

    board_size = Size(3, 3)

    def window_close(self):
        self.stop()

    def click_cell(self, x: int, y: int):
        if self.game_over:
            return

        if self.board[y][x] != Cell.EMPTY:
            return

        if self.player_ones_turn:
            self.board[y][x] = Cell.X
        else:
            self.board[y][x] = Cell.O

        if self.max_same_cell_row_count(x, y) >= 3:
            self.game_over = True
            spelernaam = "één" if self.player_ones_turn else "twee"
            self.gui.draw(self.board, f"Speler {spelernaam} is gewonnen!")
        else:
            self.player_ones_turn = not self.player_ones_turn
            spelernaam = "één" if self.player_ones_turn else "twee"
            self.gui.draw(self.board, f"Speler {spelernaam} is aan zet")

    def max_same_cell_row_count(self, cx: int, cy: int):
        counts = []

        # Iterate top-left, -middle and -right
        for dx in range(-1, 2):
            dy = -1
            counts.append(self.same_cell_row_count(cx, cy, dx, dy))

        # Check left
        dx = -1
        dy = 0
        counts.append(self.same_cell_row_count(cx, cy, dx, dy))

        return max(counts)

    def same_cell_row_count(self, cx: int, cy: int, dx: int, dy: int):
        """Returns the number of same-value cells in a row.

        Checks both the (dx, dy) direction and its oposite.
        """
        return (
            self.directed_same_cell_row_count(cx, cy, dx, dy)
            + 1
            + self.directed_same_cell_row_count(cx, cy, -dx, -dy)
        )

    def directed_same_cell_row_count(self, cx: int, cy: int, dx: int, dy: int):
        """Returns the number of same-value cells in a row.

        Checks the (dx, dy) direction (delta-x, -y).
        """
        center_val = self.board[cy][cx]
        count = 0
        x, y = (cx+dx, cy+dy)
        if not self.is_on_board(x, y):
            return count
        val = self.board[y][x]
        while val == center_val:
            count += 1
            # Delta-extended-x, -y
            dex, dey = (dx*(count+1), dy*(count+1))
            x, y = (cx+dex, cy+dey)
            if not self.is_on_board(x, y):
                break
            val = self.board[y][x]
        return count

    def is_on_board(self, x, y):
        return (
            x >= 0 and x < self.board_size.width
            and y >= 0 and y < self.board_size.height
        )

    def stop(self):
        print("\nExiting...")
        if self.gui is not None:
            self.gui.stop()
        self.stop_game = True

    def start(self):
        self.board = [[Cell.EMPTY for x in range(self.board_size.width)] for y in range(self.board_size.height)]

        size = 500, 500
        self.gui = Gui(size, Color("blue"), Color("white"), GuiHandlers(self.click_cell, self.window_close))
        self.gui.init()
        self.gui.draw(self.board, "Speler één is aan zet")

        while not self.stop_game:
            sleep(0.05)


if __name__ == "__main__":
    oxo = Oxo()
    try:
        oxo.start()
    except KeyboardInterrupt as intr:
        oxo.stop()
