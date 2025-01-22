import datetime
import logging
from dataclasses import dataclass
from datetime import timedelta
from os import PathLike

import netCDF4
import numpy as np
import numpy.typing as npt
from cftime import date2num

from model_munger.metadata import ATTRIBUTES
from model_munger.utils import calc_relative_humidity, calc_vertical_wind
from model_munger.version import __version__


@dataclass
class ModelType:
    id: str
    full_name: str
    short_name: str


@dataclass
class Location:
    id: str
    name: str


class Model:
    def __init__(
        self,
        type: ModelType,
        location: Location,
        data: dict,
        units: dict | None = None,
        history: list[str] = [],
    ):
        self.type = type
        self.location = location
        self.history = history
        self.data = {}
        for key, value in data.items():
            if key != "time" and key not in ATTRIBUTES.keys():
                logging.info("Unsupported key %s", key)
                continue
            if key != "time" and units and units[key] != ATTRIBUTES[key].units:
                raise ValueError(
                    f"Excepted '{key}' to have units '{ATTRIBUTES[key].units}' but received '{units[key]}'"
                )
            self.data[key] = value
        if "forecast_time" not in self.data:
            init_time = self.data["time"][0]
            hour = timedelta(hours=1)
            self.data["forecast_time"] = np.array(
                [(t - init_time) / hour for t in self.data["time"]]
            )
        if "wwind" not in self.data:
            self.data["wwind"] = calc_vertical_wind(
                self.data["height"],
                self.data["sfc_pressure"],
                self.data["pressure"],
                self.data["omega"],
            )
        if "rh" not in self.data:
            self.data["rh"] = calc_relative_humidity(
                self.data["pressure"], self.data["temperature"], self.data["q"]
            )
        if "cloud_fraction" in self.data:
            frac = self.data["cloud_fraction"]
            frac[frac < 1e-4] = 0

    def screen_time(self, date: datetime.date):
        """Screen time to given date (0th and 24th hour included)."""
        next_date = date + datetime.timedelta(days=1)
        t_min = datetime.datetime.combine(date, datetime.time())
        t_max = datetime.datetime.combine(next_date, datetime.time())
        time = self.data["time"]
        mask = (time >= t_min) & (time <= t_max)
        self._screen_data(mask)

    def screen_forecast_time(self, t_min: int, t_max: int):
        """Screen forecast time to given range (inclusive)."""
        time = self.data["forecast_time"]
        mask = (time >= t_min) & (time <= t_max)
        self._screen_data(mask)

    def _screen_data(self, mask: npt.NDArray[np.bool]):
        for key, values in self.data.items():
            if key == "time" or "time" in ATTRIBUTES[key].dimensions:
                self.data[key] = values[mask]

    def write_netcdf(self, filename: PathLike | str):
        with netCDF4.Dataset(filename, "w", format="NETCDF4_CLASSIC") as nc:
            nc.Conventions = "CF-1.8"
            nc.title = (
                f"{self.type.short_name} single-site output over {self.location.name}"
            )
            nc.location = self.location.name
            nc.cloudnet_file_type = "model"
            date = self.data["time"][0].date()
            nc.year = str(date.year)
            nc.month = str(date.month).zfill(2)
            nc.day = str(date.day).zfill(2)
            nc.source = self.type.full_name
            nc.model_munger_version = __version__
            now = datetime.datetime.now(datetime.timezone.utc)
            history = [
                f"{now:%Y-%m-%d %H:%M:%S} +00:00 - Cloudnet model file generated using model-munger v{__version__}",
                *self.history,
            ]
            nc.history = "\n".join(history)

            nc.createDimension("time", len(self.data["time"]))
            nc.createDimension("level", self.data["height"].shape[1])
            if "soil_depth" in self.data:
                nc.createDimension("soil_level", self.data["soil_depth"].shape[1])

            ncvar = nc.createVariable("time", "f4", "time", zlib=True)
            ncvar.long_name = "Hours UTC"
            ncvar.units = f"hours since {date:%Y-%m-%d} 00:00:00 +00:00"
            ncvar.standard_name = "time"
            ncvar.axis = "T"
            ncvar.calendar = "standard"
            ncvar[:] = date2num(
                self.data["time"], units=ncvar.units, calendar=ncvar.calendar
            )

            for key, meta in ATTRIBUTES.items():
                if key not in self.data:
                    continue
                data_type = self.data[key].dtype.str[1:]
                if data_type == "f8":
                    data_type = "f4"
                fill_value = netCDF4.default_fillvals[data_type]
                ncvar = nc.createVariable(
                    key, data_type, meta.dimensions, zlib=True, fill_value=fill_value
                )
                ncvar.units = meta.units
                ncvar.long_name = meta.long_name
                if meta.standard_name:
                    ncvar.standard_name = meta.standard_name
                if meta.comment:
                    ncvar.comment = meta.comment
                if meta.axis:
                    ncvar.axis = meta.axis
                if meta.positive:
                    ncvar.positive = meta.positive
                values = self.data[key]
                ncvar[:] = values
