import datetime
from os import PathLike

from model_munger.model import Location, Model, ModelType
from model_munger.readers.arpege import _read_lfa2nc


def read_arome(file: str | PathLike, location: Location) -> Model:
    """Read AROME netCDF generated using lfa2nc."""
    return _read_lfa2nc(file, location, AROME, _get_horizontal_resolution)


def _get_horizontal_resolution(_date: datetime.date) -> float:
    return 1.3


AROME = ModelType(
    id="arome",
    full_name="Application of Research to Operations at MEsoscale (AROME)",
    short_name="AROME",
)
