import datetime
from dataclasses import dataclass
from os import PathLike

import netCDF4
import numpy as np
import numpy.typing as npt
from numpy import ma

from model_munger.grid import Grid
from model_munger.level import Level, LevelType
from model_munger.model import ModelType
from model_munger.utils import M_TO_KM, slerp
from model_munger.version import __version__ as model_munger_version


@dataclass
class FixedLocation:
    id: str
    name: str
    latitude: float
    longitude: float


@dataclass
class MobileLocation:
    id: str
    name: str
    time: list[datetime.datetime]
    latitude: list[float]
    longitude: list[float]


@dataclass
class RawModel:
    location: FixedLocation | MobileLocation
    model: ModelType
    data: dict[str, npt.NDArray]
    dimensions: dict[str, tuple[str, ...]]
    attributes: dict[str, dict[str, str]]
    history: str | None = None


def write_netcdf(raw: RawModel, filename: str | PathLike) -> None:
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
            fill_value = (
                netCDF4.default_fillvals[data_type] if ma.is_masked(values) else None
            )
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


class Extractor:
    def __init__(
        self,
        time: list[datetime.datetime],
        locations: list[FixedLocation | MobileLocation],
        model: ModelType,
        history: str | None = None,
    ) -> None:
        self.time = time
        self.forecast_time = ma.masked_all(len(self.time), dtype=np.float32)
        self.time_unit = datetime.timedelta(hours=1)
        self.locations = locations
        self.model = model
        self.history = history
        self.idx: npt.NDArray | None = None
        self.lat: npt.NDArray | None = None
        self.lon: npt.NDArray | None = None
        self.res: npt.NDArray | None = None
        self.time_data: dict[tuple[str, int], npt.NDArray] = {}
        self.time_level_data: dict[tuple[str, int, int], npt.NDArray] = {}
        self.time_soil_data: dict[tuple[str, int, int], npt.NDArray] = {}
        self.level_data: dict[tuple[str, int], npt.NDArray] = {}
        self.attributes = {
            "forecast_time": {
                "long_name": "Time since initialization of forecast",
                "units": "hours",
            },
            "latitude": {
                "long_name": "Latitude of model gridpoint",
                "standard_name": "latitude",
                "units": "degree_north",
            },
            "longitude": {
                "long_name": "Longitude of model gridpoint",
                "standard_name": "longitude",
                "units": "degree_east",
            },
            "horizontal_resolution": {
                "long_name": "Horizontal resolution of model",
                "units": "km",
            },
        }
        self.dimensions: dict[str, tuple[str, ...]] = {
            "time": ("time",),
            "forecast_time": ("time",),
            "latitude": ("time",),
            "longitude": ("time",),
            "horizontal_resolution": ("time",),
        }
        self.is_pressure: bool | None = None

    def _set_grid(self, grid: Grid) -> None:
        shape = (len(self.locations), len(self.time))
        self.idx = np.empty(shape, dtype=np.intp)
        self.lat = np.empty(shape, dtype=np.float32)
        self.lon = np.empty(shape, dtype=np.float32)
        self.res = np.empty(shape, dtype=np.float32)
        for loc_ind, loc in enumerate(self.locations):
            lat: float | list[float]
            lon: float | list[float]
            if isinstance(loc, MobileLocation):
                lat, lon = [], []
                for time in self.time:
                    tlat, tlon = slerp(time, loc.time, loc.latitude, loc.longitude)
                    lat.append(tlat)
                    lon.append(tlon)
            else:
                lat, lon = loc.latitude, loc.longitude
            (
                self.idx[loc_ind],
                self.lat[loc_ind],
                self.lon[loc_ind],
                self.res[loc_ind],
            ) = grid.find_closest(lat, lon)

    def add_level(self, level: Level) -> None:
        self.attributes[level.variable] = level.attributes

        if self.idx is None:
            self._set_grid(level.grid)
        time_idx = self.time.index(level.time)
        idx = self.idx[:, time_idx]  # type: ignore

        if level.forecast_time is not None:
            self.forecast_time[time_idx] = level.forecast_time / self.time_unit

        if level.kind == LevelType.SURFACE:
            times = (
                list(range(len(self.time)))
                if level.forecast_time is None
                else [time_idx]
            )
            values = level.values[idx]
            for t in times:
                self.time_data[(level.variable, t)] = values
            self.dimensions[level.variable] = ("time",)
        elif level.kind in (LevelType.MODEL, LevelType.PRESSURE):
            is_pressure = level.kind == LevelType.PRESSURE
            if self.is_pressure is None:
                self.is_pressure = is_pressure
            elif self.is_pressure != is_pressure:
                raise ValueError("Cannot have both pressure and model levels")
            if level.forecast_time is not None:
                self.time_level_data[(level.variable, time_idx, level.level_no)] = (
                    level.values[idx]
                )
                self.dimensions[level.variable] = ("time", "level")
            else:
                self.level_data[(level.variable, level.level_no)] = level.values[idx]
                self.dimensions[level.variable] = ("level",)
        elif level.kind == LevelType.SOIL:
            self.time_soil_data[(level.variable, time_idx, level.level_no)] = (
                level.values[idx]
            )
            self.dimensions[level.variable] = ("time", "soil_level")
        else:
            raise RuntimeError(f"Invalid level type: {level.kind}")

    def extract_profiles(self) -> list[RawModel]:
        if self.idx is None:
            return []
        time_vars = set()
        time_level_vars = set()
        time_soil_vars = set()
        level_vars = set()
        uniq_level = set()
        uniq_soil = set()
        for var, _time_ind in self.time_data:
            time_vars.add(var)
        for var, _time_ind, level in self.time_level_data:
            time_level_vars.add(var)
            uniq_level.add(level)
        for var, _time_ind, level in self.time_soil_data:
            time_soil_vars.add(var)
            uniq_soil.add(level)
        for var, _level in self.level_data:
            level_vars.add(var)
        model_levels = sorted(uniq_level, reverse=True)
        soil_levels = sorted(uniq_soil)
        n_time = len(self.time)
        n_level = len(model_levels)
        n_soil = len(soil_levels)
        n_location = len(self.locations)

        start_time = self.time[0]
        time = [(t - start_time) / self.time_unit for t in self.time]
        self.attributes["time"] = {
            "long_name": "Time UTC",
            "standard_name": "time",
            "units": f"hours since {start_time:%Y-%m-%d %H:%M:%S} +00:00",
            "axis": "T",
            "calendar": "standard",
        }
        common_data = {
            "time": np.array(time, dtype=np.float32),
            "forecast_time": self.forecast_time,
        }
        hres = np.round(self.res * M_TO_KM)  # type: ignore

        if self.is_pressure:
            common_data["pressure"] = np.array(model_levels, dtype=np.float32)
            self.dimensions["pressure"] = ("level",)
            self.attributes["pressure"] = {
                "long_name": "Pressure",
                "standard_name": "air_pressure",
                "units": "Pa",
            }
        else:
            common_data["model_level"] = np.array(model_levels, dtype=np.int16)
            self.dimensions["model_level"] = ("level",)
            self.attributes["model_level"] = {
                "long_name": "Model level",
                "standard_name": "model_level_number",
                "units": "1",
            }

        time_data = {
            var: ma.masked_all((n_location, n_time), dtype=np.float32)
            for var in time_vars
        }
        for (var, time_ind), values in self.time_data.items():
            time_data[var][:, time_ind] = values

        time_level_data = {
            var: ma.masked_all((n_location, n_time, n_level), dtype=np.float32)
            for var in time_level_vars
        }
        for (var, time_ind, level), values in self.time_level_data.items():
            z = model_levels.index(level)
            time_level_data[var][:, time_ind, z] = values

        time_soil_data = {
            var: ma.masked_all((n_location, n_time, n_soil), dtype=np.float32)
            for var in time_soil_vars
        }
        for (var, time_ind, level), values in self.time_soil_data.items():
            z = soil_levels.index(level)
            time_soil_data[var][:, time_ind, z] = values

        level_data = {
            var: ma.masked_all((n_location, n_level), dtype=np.float32)
            for var in level_vars
        }
        for (var, level), values in self.level_data.items():
            z = model_levels.index(level)
            level_data[var][:, z] = values

        now = datetime.datetime.now(datetime.timezone.utc)
        history = (
            f"{now:%Y-%m-%d %H:%M:%S} +00:00 - {self.history} "
            f"using model-munger v{model_munger_version}"
        )

        raws = []
        for loc_idx, loc in enumerate(self.locations):
            merged = _merge_dicts(
                common_data,
                {key: values[loc_idx] for key, values in time_data.items()},
                {key: values[loc_idx] for key, values in time_level_data.items()},
                {key: values[loc_idx] for key, values in time_soil_data.items()},
                {key: values[loc_idx] for key, values in level_data.items()},
                {
                    "latitude": self.lat[loc_idx],  # type: ignore
                    "longitude": self.lon[loc_idx],  # type: ignore
                    "horizontal_resolution": hres[loc_idx],
                },
            )
            raw = RawModel(
                location=loc,
                model=self.model,
                data=merged,
                dimensions=self.dimensions,
                attributes=self.attributes,
                history=history,
            )
            raws.append(raw)

        return raws


def _merge_dicts(*dicts: dict) -> dict:
    output: dict = {}
    for d in dicts:
        conflicted = output.keys() & d.keys()
        if conflicted:
            raise KeyError("Conflicting keys: " + ", ".join(conflicted))
        output.update(d)
    return output
