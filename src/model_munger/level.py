import datetime
from dataclasses import dataclass
from enum import Enum

import numpy.typing as npt

from model_munger.grid import Grid


class LevelType(Enum):
    SURFACE = 1
    PRESSURE = 2
    SOIL = 3
    MODEL = 4


@dataclass
class Level:
    kind: LevelType
    level_no: int
    variable: str
    values: npt.NDArray
    time: datetime.datetime
    forecast_time: datetime.timedelta | None
    grid: Grid
    attributes: dict[str, str]
