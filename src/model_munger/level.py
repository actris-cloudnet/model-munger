import datetime
from dataclasses import dataclass
from enum import Enum

import numpy.typing as npt

from model_munger.grid import RegularGrid


class LevelType(Enum):
    SURFACE = 1
    PRESSURE = 2
    SOIL = 3


@dataclass
class Level:
    kind: LevelType
    level_no: int
    variable: str
    values: npt.NDArray
    time: datetime.datetime
    forecast_time: datetime.timedelta
    grid: RegularGrid
    attributes: dict[str, str]
