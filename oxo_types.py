from typing import List, Tuple, NamedTuple
from enum import Enum, unique

@unique
class Cell(Enum):
    """Game board cell values"""

    EMPTY = None
    X = "x"
    O = "O"


class Size(NamedTuple):
    width: int
    height: int
