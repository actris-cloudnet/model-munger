import datetime
from collections import defaultdict
from dataclasses import dataclass
from os import PathLike

import netCDF4
import numpy as np
import numpy.typing as npt
from numpy import ma

from model_munger.level import Level, LevelType
from model_munger.model import ModelType
from model_munger.utils import M_TO_KM, average_coordinates
from model_munger.version import __version__ as model_munger_version


@dataclass
class RawLocation:
    id: str
    name: str
    time: list[datetime.datetime] | None
    latitude: float | list[float]
    longitude: float | list[float]


@dataclass
class RawModel:
    location: RawLocation
    model: ModelType
    data: dict[str, npt.NDArray]
    dimensions: dict[str, tuple[str, ...]]
    attributes: dict[str, dict[str, str]]
    history: str | None = None


def extract_profiles(
    levels: list[Level],
    locations: list[RawLocation],
    model: ModelType,
    history: str | None = None,
) -> list[RawModel]:
    time_unit = datetime.timedelta(hours=1)
    start_time = levels[0].time
    model_time = []
    forecast_map = {}
    surface_vars = []
    pressure_lvls = []
    pressure_vars = []
    soil_lvls = []
    soil_vars = []

    for level in levels:
        time_hours = (level.time - start_time) / time_unit
        if time_hours not in model_time:
            model_time.append(time_hours)
        forecast_map[time_hours] = level.forecast_time / time_unit
        if level.kind == LevelType.SURFACE:
            if level.variable not in surface_vars:
                surface_vars.append(level.variable)
        elif level.kind == LevelType.PRESSURE:
            if level.level_no not in pressure_lvls:
                pressure_lvls.append(level.level_no)
            if level.variable not in pressure_vars:
                pressure_vars.append(level.variable)
        elif level.kind == LevelType.SOIL:
            if level.level_no not in soil_lvls:
                soil_lvls.append(level.level_no)
            if level.variable not in soil_vars:
                soil_vars.append(level.variable)

    model_time = sorted(model_time)
    pressure_lvls = sorted(pressure_lvls, reverse=True)
    soil_lvls = sorted(soil_lvls)
    forecast_time = [forecast_map[time] for time in model_time]

    surface_data = {
        var: ma.masked_all((len(model_time), len(locations)), dtype=np.float32)
        for var in surface_vars
    }
    pressure_data = {
        var: ma.masked_all(
            (len(model_time), len(pressure_lvls), len(locations)), dtype=np.float32
        )
        for var in pressure_vars
    }
    soil_data = {
        var: ma.masked_all(
            (len(model_time), len(soil_lvls), len(locations)), dtype=np.float32
        )
        for var in soil_vars
    }

    lat_idx = np.empty((len(model_time), len(locations)), dtype=np.intp)
    lon_idx = np.empty((len(model_time), len(locations)), dtype=np.intp)
    latitudes = np.empty((len(model_time), len(locations)), dtype=np.float32)
    longitudes = np.empty((len(model_time), len(locations)), dtype=np.float32)
    resolutions = np.empty((len(model_time), len(locations)), dtype=np.float32)

    for loc_idx, loc in enumerate(locations):
        if loc.time is not None:
            site_time = np.array([(t - start_time) / time_unit for t in loc.time])
            site_lat, site_lon = average_coordinates(
                site_time,
                np.array(loc.latitude),
                np.array(loc.longitude),
                np.array(model_time),
            )
        else:
            site_lat = np.array(loc.latitude)
            site_lon = np.array(loc.longitude)
        (
            lat_idx[:, loc_idx],
            lon_idx[:, loc_idx],
            latitudes[:, loc_idx],
            longitudes[:, loc_idx],
            resolutions[:, loc_idx],
        ) = levels[0].grid.find_closest(site_lat, site_lon)

    common_attributes = defaultdict(
        dict,
        time={
            "long_name": "Time UTC",
            "standard_name": "time",
            "units": f"hours since {start_time:%Y-%m-%d %H:%M:%S} +00:00",
            "axis": "T",
            "calendar": "standard",
        },
        forecast_time={
            "long_name": "Time since initialization of forecast",
            "units": "hours",
        },
        pressure={
            "long_name": "Pressure",
            "standard_name": "air_pressure",
            "units": "Pa",
        },
        latitude={
            "long_name": "Latitude of model gridpoint",
            "standard_name": "latitude",
            "units": "degree_north",
        },
        longitude={
            "long_name": "Longitude of model gridpoint",
            "standard_name": "longitude",
            "units": "degree_east",
        },
        horizontal_resolution={
            "long_name": "Horizontal resolution of model",
            "units": "km",
        },
    )

    for level in levels:
        time_hours = (level.time - start_time) / time_unit
        time_idx = model_time.index(time_hours)
        level_data = level.values[(lat_idx[time_idx], lon_idx[time_idx])]
        if level.kind == LevelType.SURFACE:
            surface_data[level.variable][time_idx] = level_data
        elif level.kind == LevelType.PRESSURE:
            pressure_idx = pressure_lvls.index(level.level_no)
            pressure_data[level.variable][time_idx, pressure_idx] = level_data
        elif level.kind == LevelType.SOIL:
            soil_idx = soil_lvls.index(level.level_no)
            soil_data[level.variable][time_idx, soil_idx] = level_data
        common_attributes[level.variable].update(level.attributes)

    common_dimensions = {
        **{key: ("time",) for key in surface_data},
        **{key: ("time", "level") for key in pressure_data},
        **{key: ("time", "soil_level") for key in soil_data},
        "time": ("time",),
        "forecast_time": ("time",),
        "pressure": ("level",),
        "latitude": ("time",),
        "longitude": ("time",),
        "horizontal_resolution": ("time",),
    }

    raws = []
    for loc_idx, loc in enumerate(locations):
        raw = RawModel(
            location=loc,
            model=model,
            data={
                **{key: values[:, loc_idx] for key, values in surface_data.items()},
                **{key: values[:, :, loc_idx] for key, values in pressure_data.items()},
                **{key: values[:, :, loc_idx] for key, values in soil_data.items()},
                "time": np.array(model_time, dtype=np.float32),
                "forecast_time": np.array(forecast_time, dtype=np.float32),
                "pressure": np.array(pressure_lvls, dtype=np.float32),
                "latitude": latitudes[:, loc_idx],
                "longitude": longitudes[:, loc_idx],
                "horizontal_resolution": np.round(resolutions[:, loc_idx] * M_TO_KM),
            },
            dimensions=common_dimensions,
            attributes=common_attributes,
            history=history,
        )
        raws.append(raw)

    return raws


def write_netcdf(raw: RawModel, filename: str | PathLike):
    with netCDF4.Dataset(filename, "w", format="NETCDF4_CLASSIC") as nc:
        nc.Conventions = "CF-1.8"
        nc.title = f"{raw.model.short_name} single-site output over {raw.location.name}"
        nc.location = raw.location.name
        nc.source = raw.model.full_name
        nc.model_munger_version = model_munger_version
        if raw.history is not None:
            nc.history = raw.history

        for key in raw.data:
            values = raw.data[key]
            data_type = values.dtype.str[1:]
            has_masked = np.any(ma.getmaskarray(values))
            fill_value = netCDF4.default_fillvals[data_type] if has_masked else None
            for dimension, size in zip(raw.dimensions[key], values.shape, strict=True):
                if dimension not in nc.dimensions:
                    nc.createDimension(dimension, size)
            ncvar = nc.createVariable(
                key,
                data_type,
                raw.dimensions[key],
                zlib=True,
                fill_value=fill_value,
            )
            if key in raw.attributes:
                for attr, value in raw.attributes[key].items():
                    setattr(ncvar, attr, value)
            ncvar[:] = values
