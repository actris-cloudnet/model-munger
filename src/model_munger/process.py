import datetime
from pathlib import Path
import pygrib
import numpy as np
import numpy.typing as npt
from dataclasses import dataclass
import netCDF4
from model_munger.metadata import ATTRIBUTES
from model_munger.utils import (
    EARTH_RADIUS,
    HPA_TO_PA,
    M_TO_KM,
    calc_geometric_height,
    calc_vertical_wind,
    calc_relative_humidity,
)
from model_munger.version import __version__


@dataclass
class Level:
    pressure: int
    variable: str
    values: npt.NDArray


GRIB_UNITS = {
    "10u": "m s**-1",
    "10v": "m s**-1",
    "2d": "K",
    "2t": "K",
    "gh": "gpm",
    "msl": "Pa",
    "q": "kg kg**-1",
    "sp": "Pa",
    "st": "K",
    "t": "K",
    "u": "m s**-1",
    "v": "m s**-1",
    "w": "Pa s**-1",
}
NC_NAMES = {
    "10u": "sfc_wind_u_10m",
    "10v": "sfc_wind_v_10m",
    "2d": "sfc_dewpoint_temp_2m",
    "2t": "sfc_temp_2m",
    "gh": "_gh",
    "msl": "sfc_pressure_amsl",
    "q": "q",
    "sp": "sfc_pressure",
    "st": "soil_temperature",
    "t": "temperature",
    "u": "uwind",
    "v": "vwind",
    "w": "omega",
}


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
    paths: list[Path],
    date: datetime.date,
    latitudes: npt.NDArray,
    longitudes: npt.NDArray,
) -> list[dict]:
    pressures = None

    output = []

    for i in range(len(latitudes)):
        data: dict = {key: [] for key in NC_NAMES.values() if not key.startswith("_")}
        data["time"] = []
        data["pressure"] = []
        data["height"] = []
        data["wwind"] = []
        data["rh"] = []
        output.append(data)

    lat = None
    lon = None
    lat_idx = None
    lon_idx = None
    res = None

    for i, path in enumerate(paths):
        print(f"Opening {path}")
        grbs = pygrib.open(path)

        hour = 3 * i

        surface = {}
        levels = []

        for grb in grbs:
            if grb.shortName not in NC_NAMES or grb.typeOfLevel not in (
                "surface",
                "meanSea",
                "heightAboveGround",
                "depthBelowLandLayer",
                "isobaricInPa",
                "isobaricInhPa",
            ):
                continue
            if lat is None:
                lat, lon, lat_idx, lon_idx, res = _find_closest_gridpoints(
                    grb, latitudes, longitudes
                )
                for i in range(len(lat)):
                    output[i]["latitude"] = lat[i]
                    output[i]["longitude"] = lon[i]
                    output[i]["horizontal_resolution"] = np.around(res * M_TO_KM)
            if (
                grb.year != date.year
                or grb.month != date.month
                or grb.day != date.day
                or grb.forecastTime != hour
            ):
                raise ValueError("Invalid time")
            if grb.units != GRIB_UNITS[grb.shortName]:
                raise ValueError(
                    f"Expected {grb.shortName} to have units {GRIB_UNITS[grb.shortName]} but received {grb.units}"
                )
            values = grb.values[(lat_idx, lon_idx)]
            if grb.typeOfLevel in (
                "surface",
                "meanSea",
                "heightAboveGround",
                "depthBelowLandLayer",
            ):
                surface[NC_NAMES[grb.shortName]] = values
            else:
                pressure = grb.level
                if grb.pressureUnits == "hPa":
                    pressure *= HPA_TO_PA
                levels.append(Level(pressure, NC_NAMES[grb.shortName], values))

        if pressures is None:
            pressures = list(
                sorted(set(level.pressure for level in levels), reverse=True)
            )

        for j, data in enumerate(output):
            profile: dict = {
                v: np.full(len(pressures), np.nan)
                for v in NC_NAMES.values()
                if v not in surface
            }
            for level in levels:
                pressure_idx = pressures.index(level.pressure)
                profile[level.variable][pressure_idx] = level.values[j]
            for key in surface:
                profile[key] = surface[key][j]
            profile["pressure"] = np.array(pressures)
            profile["height"] = calc_geometric_height(profile["_gh"])
            profile["wwind"] = calc_vertical_wind(
                profile["height"],
                profile["sfc_pressure"],
                profile["pressure"],
                profile["omega"],
            )
            profile["rh"] = calc_relative_humidity(
                profile["pressure"], profile["temperature"], profile["q"]
            )
            profile["time"] = hour
            for key, values in profile.items():
                if not key.startswith("_"):
                    data[key].append(values)

    return output


def save_netcdf(
    date: datetime.date, station_id: str, station_name: str, data: dict, directory: Path
) -> Path:
    filename = directory / f"{date:%Y%m%d}_{station_id}_ecmwf-open.nc"
    print(f"Saving {filename}")
    with netCDF4.Dataset(filename, "w", format="NETCDF4_CLASSIC") as nc:
        nc.Conventions = "CF-1.8"
        nc.title = f"Model data from {station_name}"
        nc.location = station_name
        nc.cloudnet_file_type = "model"
        nc.year = str(date.year)
        nc.month = str(date.month).zfill(2)
        nc.day = str(date.day).zfill(2)
        nc.source = "ECMWF open data"
        nc.model_munger_version = __version__

        nc.createDimension("time", len(data["time"]))
        nc.createDimension("level", len(data["pressure"][0]))

        ncvar = nc.createVariable("time", "f4", "time")
        ncvar.long_name = "Hours UTC"
        ncvar.units = f"hours since {date:%Y-%m-%d} 00:00:00 +00:00"
        ncvar.standard_name = "time"
        ncvar.axis = "T"
        ncvar.calendar = "standard"
        ncvar[:] = data["time"]

        for key, meta in ATTRIBUTES.items():
            ncvar = nc.createVariable(key, "f4", meta.dimensions)
            ncvar.units = meta.units
            ncvar.long_name = meta.long_name
            if meta.standard_name:
                ncvar.standard_name = meta.standard_name
            if meta.comment:
                ncvar.comment = meta.comment
            values = data[key]
            ncvar[:] = values
    return filename
