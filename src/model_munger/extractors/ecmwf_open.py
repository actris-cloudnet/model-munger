import datetime
import logging
import os.path
import re
from collections.abc import Iterable
from typing import Any, Literal

import numpy as np
import pygrib

from model_munger.grid import RegularGrid
from model_munger.level import Level, LevelType
from model_munger.utils import HPA_TO_PA

SOURCES = {
    "ecmwf": "https://data.ecmwf.int/forecasts",
    "aws": "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
}
_unsupported_levtypes = set()


def generate_ecmwf_url(
    date: datetime.date,
    run: Literal[0, 6, 12, 18],
    step: int,
    source: str,
) -> str:
    """Generate URL for ECMWF high-resolution forecast model (open data subset).

    Args:
        date: Forecast date (UTC)
        run: Forecast run (0, 6, 12 or 18 UTC hour)
        step: Forecast step (0, 1, 2, ...)
        source: Location from which to download files ("ecmwf" or "aws").

    Returns:
        URL for GRIB files
    """
    date_str = date.strftime("%Y%m%d")
    run_str = str(run).zfill(2)
    stream = "oper" if run in (0, 12) else "scda"
    if source not in SOURCES:
        raise ValueError(f"Invalid source: {source}")
    base_url = SOURCES[source]
    filename = f"{date_str}{run_str}0000-{step}h-{stream}-fc.grib2"
    return f"{base_url}/{date_str}/{run_str}z/ifs/0p25/{stream}/{filename}"


def read_ecmwf(filename: str | os.PathLike) -> Iterable[Level]:
    basename = os.path.basename(filename)
    m = re.match(r"^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)-(\d+)h-", basename)
    if m is None:
        raise ValueError(f"Invalid filename: {basename}")
    start_time = datetime.datetime(
        year=int(m[1]),
        month=int(m[2]),
        day=int(m[3]),
        hour=int(m[4]),
        minute=int(m[5]),
        second=int(m[6]),
        tzinfo=datetime.timezone.utc,
    )
    forecast_time = datetime.timedelta(hours=int(m[7]))
    time = start_time + forecast_time
    with pygrib.open(filename) as grbs:
        for grb in grbs:
            level = grb.level
            if grb.levtype == "sfc":
                kind = LevelType.SURFACE
            elif grb.levtype == "pl":
                kind = LevelType.PRESSURE
                if grb.pressureUnits == "hPa":
                    level *= HPA_TO_PA
                elif grb.pressureUnits != "Pa":
                    raise ValueError(f"Invalid pressure units: {grb.pressureUnits}")
            elif grb.levtype == "sol":
                kind = LevelType.SOIL
            else:
                if grb.levtype not in _unsupported_levtypes:
                    logging.warning("Unsupported level type: %s", grb.levtype)
                    _unsupported_levtypes.add(grb.levtype)
                continue
            attributes = {
                "long_name": grb.name,
                "units": grb.units,
                "param_id": grb.paramId,
            }
            if "cfName" in grb.keys() and grb.cfName != "unknown":  # noqa: SIM118
                attributes["standard_name"] = grb.cfName
            time_invariant = grb.shortName in ("z", "slor", "sdor")
            yield Level(
                kind=kind,
                level_no=level,
                variable=grb.cfVarName,
                values=np.ravel(grb.values),
                grid=_make_grid(grb),
                time=time,
                forecast_time=forecast_time if not time_invariant else None,
                attributes=attributes,
            )


def _make_grid(grb: Any) -> RegularGrid:
    if grb.gridType != "regular_ll":
        raise ValueError(f"Invalid grid type: {grb.gridType}")
    delta_lat = grb.jDirectionIncrementInDegrees
    if not grb.jScansPositively:
        delta_lat = -delta_lat
    delta_lon = grb.iDirectionIncrementInDegrees
    if grb.iScansNegatively:
        delta_lon = -delta_lon
    return RegularGrid(
        grb.Nj,
        grb.Ni,
        grb.latitudeOfFirstGridPointInDegrees,
        grb.longitudeOfFirstGridPointInDegrees,
        grb.latitudeOfLastGridPointInDegrees,
        grb.longitudeOfLastGridPointInDegrees,
        delta_lat,
        delta_lon,
    )
