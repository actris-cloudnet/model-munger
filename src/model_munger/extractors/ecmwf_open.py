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

from model_munger.utils import (
    EARTH_RADIUS,
    HPA_TO_PA,
    M_TO_KM,
)
from model_munger.version import __version__


@dataclass
class Level:
    level: int
    variable: str
    values: npt.NDArray


def _find_closest_gridpoints(
    grb, latitudes: npt.NDArray, longitudes: npt.NDArray
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
    """Extract profiles from ECMWF open data GRIB files and output them in
    netCDF files.

    Args:
        input_files: List of GRIB files from a single run.
        sites: List of sites from Cloudnet API.
        output_directory: Directory where output files are written.

    Returns:
        List of output files.
    """

    pressures = None
    n_soil_levels = 0

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

    for i, input_file in enumerate(input_files):
        # if i > 1:
        #     break

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
        grbs = pygrib.open(path)

        levels = []
        soil_levels = []

        for grb in grbs:
            if lat is None:
                lat, lon, lat_idx, lon_idx, res = _find_closest_gridpoints(
                    grb, latitudes, longitudes
                )
                for i in range(len(lat)):
                    output[i]["latitude"] = lat[i]
                    output[i]["longitude"] = lon[i]
                    output[i]["horizontal_resolution"] = np.around(res * M_TO_KM)
            units[grb.cfVarName] = grb.units
            long_names[grb.cfVarName] = grb.name
            parameters[grb.cfVarName] = grb.paramId
            if "cfName" in grb.keys() and grb.cfName != "unknown":
                standard_names[grb.cfVarName] = grb.cfName
            values = grb.values[(lat_idx, lon_idx)]
            if grb.levtype == "sfc":
                dimensions[grb.cfVarName] = ("time",)
                for i in range(len(lat)):
                    output[i][grb.cfVarName].append(values[i])
            elif grb.levtype == "pl":
                dimensions[grb.cfVarName] = ("time", "level")
                pressure = grb.level
                if grb.pressureUnits == "hPa":
                    pressure *= HPA_TO_PA
                elif grb.pressureUnits != "Pa":
                    raise ValueError(f"Invalid pressure units: {grb.pressureUnits}")
                levels.append(Level(pressure, grb.cfVarName, values))
            elif grb.levtype == "sol":
                dimensions[grb.cfVarName] = ("time", "soil_level")
                if grb.level > n_soil_levels:
                    n_soil_levels = grb.level
                soil_levels.append(Level(grb.level, grb.cfVarName, values))

        if pressures is None:
            pressures = list(sorted(set(level.level for level in levels), reverse=True))

        for j, data in enumerate(output):
            profile: dict = {
                v: np.full(len(pressures), np.nan)
                for v in [level.variable for level in levels]
            }
            for level in levels:
                pressure_idx = pressures.index(level.level)
                profile[level.variable][pressure_idx] = level.values[j]
            for level in soil_levels:
                if level.variable not in profile:
                    profile[level.variable] = np.full(n_soil_levels, np.nan)
                profile[level.variable][level.level - 1] = level.values[j]
            for key, values in profile.items():
                data[key].append(values)

    # from numpy import ma
    # for item in output:
    #     for key in item:
    #         if isinstance(item[key], list) and item[key][0]
    #             item[key] = ma.concatenate(item[key])

    assert pressures is not None

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
                f"{now:%Y-%m-%d %H:%M:%S} +00:00 - Model run {start_dt:%H} UTC extracted from ECMWF open data using model-munger v{__version__}",
            )

            nc.createDimension("time", len(time))
            nc.createDimension("level", len(pressures))
            if n_soil_levels > 0:
                nc.createDimension("soil_level", n_soil_levels)

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

            for key, values in data.items():
                dtype = "f4"  # TODO???
                fill_value = netCDF4.default_fillvals[dtype]
                ncvar = nc.createVariable(
                    key, dtype, dimensions[key], zlib=True, fill_value=fill_value
                )
                ncvar.units = units[key]
                ncvar.long_name = long_names[key]
                if key in standard_names:
                    ncvar.standard_name = standard_names[key]
                if key in parameters:
                    ncvar.param_id = parameters[key]
                if dimensions[key] == ("time",) and len(values) == 1:
                    values = np.repeat(values, len(time))
                ncvar[:] = values

    return output_paths
