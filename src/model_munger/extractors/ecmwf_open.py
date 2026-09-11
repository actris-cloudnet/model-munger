import datetime
import json
import logging
import os.path
from collections.abc import Iterable
from typing import Any, Literal

import numpy as np
import pygrib
from atmoslib.constants import HPA_TO_PA

from model_munger.grid import RegularGrid
from model_munger.level import Level, LevelType

SOURCES = {
    "ecmwf": "https://data.ecmwf.int/forecasts",
    "aws": "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
    "google": "https://storage.googleapis.com/ecmwf-open-data",
    "azure": "https://ai4edataeuwest.blob.core.windows.net/ecmwf",
}
_unsupported_levtypes: set[str] = set()

logger = logging.getLogger(__name__)

DATE_CYCLE_50R1 = datetime.date(2026, 5, 12)


def generate_ecmwf_url(
    date: datetime.date,
    run: Literal[0, 6, 12, 18],
    step: int,
    source: str,
    extension: Literal["grib2", "index"],
) -> str:
    """Generate URL for ECMWF high-resolution forecast model (open data subset).

    Args:
        date: Forecast date (UTC)
        run: Forecast run (0, 6, 12 or 18 UTC hour)
        step: Forecast step (0, 1, 2, ...)
        source: Location from which to download files ("ecmwf" or "aws").
        extension: File extension ("grib2" or "index")

    Returns:
        URL for GRIB files
    """
    date_str = date.strftime("%Y%m%d")
    run_str = str(run).zfill(2)
    stream = "scda" if date < DATE_CYCLE_50R1 and run in (6, 18) else "oper"
    if source not in SOURCES:
        msg = f"Invalid source: {source}"
        raise ValueError(msg)
    base_url = SOURCES[source]
    filename = f"{date_str}{run_str}0000-{step}h-{stream}-fc.{extension}"
    return f"{base_url}/{date_str}/{run_str}z/ifs/0p25/{stream}/{filename}"


def read_ecmwf_index(filename: str | os.PathLike) -> list[dict]:
    with open(filename) as f:
        return [json.loads(line) for line in f]


def read_ecmwf(
    filename: str | os.PathLike, start_time: datetime.datetime, forecast_time: int
) -> Iterable[Level]:
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
                    msg = f"Invalid pressure units: {grb.pressureUnits}"
                    raise ValueError(msg)
            elif grb.levtype == "sol":
                kind = LevelType.SOIL
            else:
                if grb.levtype not in _unsupported_levtypes:
                    logger.warning("Unsupported level type: %s", grb.levtype)
                    _unsupported_levtypes.add(grb.levtype)
                continue
            attributes = {
                "long_name": grb.name,
                "units": grb.units,
                "param_id": grb.paramId,
            }
            if "cfName" in grb.keys() and grb.cfName != "unknown":  # noqa: SIM118
                attributes["standard_name"] = grb.cfName
            time_invariant = grb.levtype == "sfc" and grb.shortName in (
                "z",
                "slor",
                "sdor",
            )
            yield Level(
                kind=kind,
                level_no=level,
                variable=grb.levtype + "_" + grb.cfVarName,
                values=np.ravel(grb.values),
                grid=_make_grid(grb),
                time=time,
                forecast_time=forecast_time if not time_invariant else None,
                attributes=attributes,
            )


def _make_grid(grb: Any) -> RegularGrid:
    if grb.gridType != "regular_ll":
        msg = f"Invalid grid type: {grb.gridType}"
        raise ValueError(msg)
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
