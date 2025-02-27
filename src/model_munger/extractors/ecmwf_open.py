import datetime
import re
from collections import defaultdict
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Iterable

import netCDF4
import numpy as np
import numpy.typing as npt
import pygrib
from numpy import ma

from model_munger.utils import (
    EARTH_RADIUS,
    HPA_TO_PA,
    M_TO_KM,
)
from model_munger.version import __version__


@dataclass
class Level:
    time: int
    level: int
    variable: str
    values: npt.NDArray


def _find_closest_gridpoints(
    grb,
    latitudes: npt.NDArray,
    longitudes: npt.NDArray,
) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray, npt.NDArray, float]:
    if grb.gridType not in ("regular_gg", "regular_ll", "reduced_gg", "reduced_ll"):
        raise NotImplementedError(f"Not implemented for grid type {grb.gridType}")
    grid_lats = grb.distinctLatitudes
    grid_lons = grb.distinctLongitudes
    lat_ind = np.argmin(np.abs(grid_lats - latitudes[:, np.newaxis]), axis=1)
    lon_ind = np.argmin(np.abs(grid_lons - longitudes[:, np.newaxis]), axis=1)
    res = grb.iDirectionIncrementInDegrees / 360 * 2 * np.pi * EARTH_RADIUS
    return (grid_lats[lat_ind], grid_lons[lon_ind], lat_ind, lon_ind, res)


def extract_profiles(
    input_files: Iterable[str | PathLike],
    sites: list[dict],
    output_directory: str | PathLike,
) -> list[Path]:
    """Extract profiles from ECMWF open data GRIB files.

    Args:
        input_files: List of GRIB files from a single run.
        sites: List of sites from Cloudnet API.
        output_directory: Directory where output files are written.

    Returns:
        List of output files.
    """
    time = []
    output: list[dict] = [defaultdict(list) for site in sites]
    latitudes = np.array([site["latitude"] for site in sites])
    longitudes = np.array([site["longitude"] for site in sites])

    lat = None
    lon = None
    lat_idx = None
    lon_idx = None
    res = None

    units = {
        "latitude": "degree_north",
        "longitude": "degree_east",
        "horizontal_resolution": "km",
    }
    long_names = {
        "latitude": "Latitude of model gridpoint",
        "longitude": "Longitude of model gridpoint",
        "horizontal_resolution": "Horizontal resolution of model",
    }
    dimensions: dict[str, tuple[str, ...]] = {
        "latitude": (),
        "longitude": (),
        "horizontal_resolution": (),
    }
    standard_names = {"latitude": "latitude", "longitude": "longitude"}
    parameters = {}

    start_dt = None
    sfc_levels = []
    pressure_levels = []
    soil_levels = []

    for time_idx, input_file in enumerate(input_files):
        path = Path(input_file)

        m = re.match(r"^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)-(\d+)h-", path.name)
        if m is None:
            raise ValueError(f"Invalid filename: {path.name}")
        new_dt = datetime.datetime(
            year=int(m[1]),
            month=int(m[2]),
            day=int(m[3]),
            hour=int(m[4]),
            minute=int(m[5]),
            second=int(m[6]),
            tzinfo=datetime.timezone.utc,
        )
        if start_dt is None:
            start_dt = new_dt
        elif new_dt != start_dt:
            raise ValueError(f"Files from different runs: {new_dt} vs {start_dt}")
        hour = int(m[7])
        time.append(hour)

        print(f"Opening {path}")
        with pygrib.open(path) as grbs:
            for grb in grbs:
                if lat is None:
                    lat, lon, lat_idx, lon_idx, res = _find_closest_gridpoints(
                        grb,
                        latitudes,
                        longitudes,
                    )
                    for output_idx in range(len(lat)):
                        output[output_idx]["latitude"] = lat[output_idx]
                        output[output_idx]["longitude"] = lon[output_idx]
                        output[output_idx]["horizontal_resolution"] = np.round(
                            res * M_TO_KM,
                        )
                units[grb.cfVarName] = grb.units
                long_names[grb.cfVarName] = grb.name
                parameters[grb.cfVarName] = grb.paramId
                if "cfName" in grb.keys() and grb.cfName != "unknown":  # noqa: SIM118
                    standard_names[grb.cfVarName] = grb.cfName
                values = grb.values[(lat_idx, lon_idx)]
                if grb.levtype == "sfc":
                    dimensions[grb.cfVarName] = ("time",)
                    sfc_levels.append(Level(time_idx, 0, grb.cfVarName, values))
                elif grb.levtype == "pl":
                    dimensions[grb.cfVarName] = ("time", "level")
                    pressure = grb.level
                    if grb.pressureUnits == "hPa":
                        pressure *= HPA_TO_PA
                    elif grb.pressureUnits != "Pa":
                        raise ValueError(f"Invalid pressure units: {grb.pressureUnits}")
                    pressure_levels.append(
                        Level(time_idx, pressure, grb.cfVarName, values),
                    )
                elif grb.levtype == "sol":
                    dimensions[grb.cfVarName] = ("time", "soil_level")
                    soil_levels.append(
                        Level(time_idx, grb.level, grb.cfVarName, values),
                    )

    pressures = sorted({level.level for level in pressure_levels}, reverse=True)
    n_time = len(time)
    n_pressure = len(pressures)
    n_soil = max((level.level for level in soil_levels), default=0)

    for output_idx, data in enumerate(output):
        for level in soil_levels:
            if level.variable not in data:
                data[level.variable] = ma.masked_all((n_time, n_soil))
            data[level.variable][level.time, level.level - 1] = level.values[output_idx]
        for level in sfc_levels:
            if level.variable not in data:
                data[level.variable] = ma.masked_all(n_time)
            data[level.variable][level.time] = level.values[output_idx]
        for level in pressure_levels:
            if level.variable not in data:
                data[level.variable] = ma.masked_all((n_time, n_pressure))
            pressure_idx = pressures.index(level.level)
            data[level.variable][level.time, pressure_idx] = level.values[output_idx]

    output_paths = []

    for site, data in zip(sites, output):
        site_id = site["id"]
        filename = f"{start_dt:%Y%m%d%H%M%S}_{site_id}_ecmwf-open.nc"
        output_path = Path(output_directory) / filename
        output_paths.append(output_path)
        print(f"Saving {filename}")
        with netCDF4.Dataset(output_path, "w", format="NETCDF4_CLASSIC") as nc:
            nc.Conventions = "CF-1.8"
            site_name = site["humanReadableName"]
            nc.title = f"ECMWF open data single-site output over {site_name}"
            nc.location = site_name
            nc.source = "ECMWF open data"
            nc.model_munger_version = __version__
            now = datetime.datetime.now(datetime.timezone.utc)
            nc.history = (
                f"{now:%Y-%m-%d %H:%M:%S} +00:00 - "
                f"Model run {start_dt:%H} UTC extracted from ECMWF open data "
                f"using model-munger v{__version__}",
            )

            nc.createDimension("time", len(time))
            nc.createDimension("level", len(pressures))
            if n_soil > 0:
                nc.createDimension("soil_level", n_soil)

            ncvar = nc.createVariable("time", "f4", "time", zlib=True)
            ncvar.long_name = "Hours UTC"
            ncvar.units = f"hours since {start_dt:%Y-%m-%d %H:%M:%S} +00:00"
            ncvar.axis = "T"
            ncvar.calendar = "standard"
            ncvar[:] = time

            ncvar = nc.createVariable("pressure", "f4", "level", zlib=True)
            ncvar.long_name = "Pressure"
            ncvar.units = "Pa"
            ncvar[:] = pressures

            for key in data:
                values = ma.array(data[key])
                data_type = values.dtype.str[1:]
                fill_value = netCDF4.default_fillvals[data_type]
                ncvar = nc.createVariable(
                    key,
                    data_type,
                    dimensions[key],
                    zlib=True,
                    fill_value=fill_value,
                )
                ncvar.units = units[key]
                ncvar.long_name = long_names[key]
                if key in standard_names:
                    ncvar.standard_name = standard_names[key]
                if key in parameters:
                    ncvar.param_id = parameters[key]
                if dimensions[key] == ("time",) and len(values) == 1:
                    values = ma.repeat(values, len(time))
                ncvar[:] = values

    return output_paths
