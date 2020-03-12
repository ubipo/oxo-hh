"""

"""

import threading
import time
from typing import Tuple, List, NamedTuple, Callable

import pygame

from oxo_types import Cell


class GuiHandlers(NamedTuple):
    """Data class for Gui's event handlers"""

    cell_click: Callable[[int, int], None]
    window_close: Callable[[], None]


class Gui():
    """Handles the pygame GUI for the OXO game"""

    size: Tuple[int, int]
    fg_color: pygame.Color
    bg_color: pygame.Color

    _surface: pygame.Surface = None
    _screen_padding = lambda self: min(self.size) // 20
    _gutter_size = lambda self: min(self.size) // 50
    _text_height = lambda self: min(self.size) // 25
    _font_size = lambda self: min(self.size) // 25
    _rectangles: List[pygame.Rect]
    _last_board: List[List[Cell]] # Used for screen-resize updates
    _last_text: str = ""
    _event_thread: threading.Thread
    _stop_event_thread = False
    _handlers: GuiHandlers

    def __init__(self,
                 size: Tuple[int, int],
                 fg_color: pygame.Color,
                 bg_color: pygame.Color,
                 handlers: GuiHandlers):
        self.size = size
        self.fg_color = fg_color
        self.bg_color = bg_color
        self._handlers = handlers

        pygame.init()


    def init(self):
        self._surface = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        pygame.display.set_caption('OXO')
        icon = pygame.image.load('oxo.png')
        pygame.display.set_icon(icon)
        self._event_thread = threading.Thread(target=self._pygame_event_loop, daemon=True)
        self._event_thread.start()


    def draw(self, board: List[List[Cell]], text: str):
        self._last_board = board
        self._last_text = text

        grid_rows = len(board)
        grid_columns = len(board[0])
        screen_padding = self._screen_padding()
        gutter_size = self._gutter_size()
        text_height = self._text_height()
        max_width = self.size[0]-screen_padding
        max_height = self.size[1]-screen_padding*2-text_height

        block_size = Gui._calc_block_size(max_width, max_height, grid_columns, grid_rows, gutter_size)

        grid_size = ((grid_columns*(block_size+gutter_size))+gutter_size,
                     (grid_rows*(block_size+gutter_size))+gutter_size)
        x_start = int((self.size[0] / 2) - (grid_size[0] / 2))
        y_start = int((self.size[1] / 2) - (grid_size[1] / 2) - (text_height / 2))

        bg_rect = pygame.Rect(x_start, y_start, grid_size[0], grid_size[1] + text_height)
        pygame.draw.rect(self._surface, self.fg_color, bg_rect)

        self._rectangles = []
        for y in range(grid_rows):
            if len(board[y]) != grid_columns:
                raise IndexError("Board has incorrect dimensions! Does every row have the same number of columns?")
            row = []
            self._rectangles.append(row)
            for x in range(grid_columns):
                rect_x = x_start+gutter_size+x*(block_size+gutter_size)
                rect_y = y_start+gutter_size+y*(block_size+gutter_size)
                rect = pygame.Rect(rect_x, rect_y, block_size, block_size)
                row.append(rect)
                pygame.draw.rect(self._surface, self.bg_color, rect)
                circle_center = (int(rect_x+block_size/2), int(rect_y+block_size/2))
                cell = board[y][x]
                if cell is Cell.X:
                    self._draw_x(int(block_size*(2/3)), circle_center, int(block_size*(1/20)))
                elif cell is Cell.O:
                    self._draw_o(int(block_size*(2/3)), circle_center, int(block_size*(1/20)))

        font = pygame.font.Font('freesansbold.ttf', self._font_size())
        text = font.render(text, True, self.bg_color, self.fg_color)
        text_rect = text.get_rect()
        text_rect.center = (x_start+grid_size[1]//2, y_start+grid_size[1]+text_height//2)
        self._surface.blit(text, text_rect)

        pygame.display.flip()


    def stop(self):
        self._stop_event_thread = True


    def _pygame_event_loop(self):
        while not self._stop_event_thread:
            time.sleep(0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._handlers.window_close()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        pos = pygame.mouse.get_pos()
                        if self._rectangles is not None:
                            for y, row in enumerate(self._rectangles):
                                for x, rect in enumerate(row):
                                    if rect.collidepoint(pos):
                                        self._handlers.cell_click(x, y)
                                        break
                elif event.type == pygame.VIDEORESIZE:
                    self.size = (event.w, event.h)
                    self._surface = pygame.display.set_mode(self.size, pygame.RESIZABLE)
                    self.draw(self._last_board, self._last_text)


    def _draw_o(self, size, center, thickness):
        pygame.draw.circle(self._surface, self.fg_color, center, int(size/2), thickness)


    def _draw_x(self, length, center, thickness):
        self._draw_rotated_rect((length, thickness), center, 45)
        self._draw_rotated_rect((length, thickness), center, 135)


    def _draw_rotated_rect(self, size, center, angle):
        rect1 = Gui._gen_rotated_rectangle_img(size, angle, self.fg_color, self.bg_color)
        rect1_bbox = rect1.get_rect()
        rect1_bbox.center = center
        self._surface.blit(rect1, rect1_bbox)


    @staticmethod
    def _calc_block_size(max_width, max_height, grid_columns, grid_rows, gutter_size):
        field_size = min(max_width, max_height)
        block_width = int((field_size-((grid_columns-1)*gutter_size))/grid_columns)
        block_height = int((field_size-((grid_rows-1)*gutter_size))/grid_rows)
        return min(block_width, block_height)


    @staticmethod
    def _gen_rotated_rectangle_img(dim, angle, fg_color, bg_color):
        rect = pygame.Surface(dim)
        rect.set_colorkey(bg_color)
        rect.fill(fg_color)
        rect_rotated = pygame.transform.rotate(rect, angle)
        return rect_rotated
