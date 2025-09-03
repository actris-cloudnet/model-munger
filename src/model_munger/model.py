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
from model_munger.utils import (
    HPA_TO_PA,
    MW_RATIO,
    G,
    calc_geometric_height,
    calc_saturated_vapor_pressure,
    calc_vertical_wind,
)
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
        data: dict[str, npt.NDArray],
        units: dict[str, str] | None = None,
        sources: dict[str, str] | None = None,
        comments: dict[str, str] | None = None,
        history: list[str] | None = None,
    ) -> None:
        self.type = type
        self.location = location
        self.history = history if history is not None else []
        self.sources = sources.copy() if sources is not None else {}
        self.comments = comments if comments is not None else {}
        self.data: dict[str, npt.NDArray] = {}
        n_time = len(data["time"])
        for key, raw_value in data.items():
            if key != "time" and key not in ATTRIBUTES:
                logging.info("Unsupported key %s", key)
                continue
            value = raw_value
            if key != "time" and units and units[key] != ATTRIBUTES[key].units:
                value = _convert_units(key, value, units[key], ATTRIBUTES[key].units)
                if key in self.sources:
                    self.sources[key] = (
                        self.sources[key]
                        + f" converted from {units[key]} to {ATTRIBUTES[key].units}"
                    )
            if key in ("latitude", "longitude") and np.ndim(value) == 0:
                self.data[key] = np.repeat(value, n_time)
            else:
                self.data[key] = value
        if "forecast_time" not in self.data:
            init_time = self.data["time"][0]
            hour = timedelta(hours=1)
            self.data["forecast_time"] = np.array(
                [(t - init_time) / hour for t in self.data["time"]],
            )
        if "wwind" not in self.data and "omega" in self.data:
            self.data["wwind"] = calc_vertical_wind(
                self.data["height"],
                self.data["sfc_pressure"],
                self.data["pressure"],
                self.data["omega"],
            )
            self.sources["wwind"] = (
                "Calculated from omega, height and pressure using: w=omega*dz/dp"
            )
        self._calculate_q("q", "rh", "pressure", "temperature")
        self._calculate_q("sfc_q_2m", "sfc_rh_2m", "sfc_pressure", "sfc_temp_2m")
        self._calculate_rh("q", "rh", "pressure", "temperature")
        self._calculate_rh("sfc_q_2m", "sfc_rh_2m", "sfc_pressure", "sfc_temp_2m")
        if "cloud_fraction" in self.data:
            frac = self.data["cloud_fraction"]
            frac[frac < 1e-4] = 0
        if "sfc_height" not in self.data and "sfc_geopotential" in self.data:
            geopotential_height = self.data["sfc_geopotential"] / G
            self.data["sfc_height"] = calc_geometric_height(geopotential_height)
            self.sources["sfc_height"] = "Calculated from sfc_geopotential"

    def _calculate_q(
        self, q_key: str, rh_key: str, pressure_key: str, temperature_key: str
    ) -> None:
        """Calculate specific humidity if missing.

        References:
            Cai, J. (2019). Humidity Measures.
            https://cran.r-project.org/web/packages/humidity/vignettes/humidity-measures.html
        """
        if (
            q_key in self.data
            or rh_key not in self.data
            or pressure_key not in self.data
            or temperature_key not in self.data
        ):
            return
        es = calc_saturated_vapor_pressure(self.data[temperature_key])
        e = self.data[rh_key] * es
        p = self.data[pressure_key]
        self.data[q_key] = (MW_RATIO * e) / (p - (1 - MW_RATIO) * e)
        self.sources[q_key] = (
            f"Calculated from {rh_key}, {temperature_key} and {pressure_key}"
        )

    def _calculate_rh(
        self, q_key: str, rh_key: str, pressure_key: str, temperature_key: str
    ) -> None:
        """Calculate relative humidity if missing.

        References:
            Cai, J. (2019). Humidity Measures.
            https://cran.r-project.org/web/packages/humidity/vignettes/humidity-measures.html
        """
        if (
            rh_key in self.data
            or q_key not in self.data
            or pressure_key not in self.data
            or temperature_key not in self.data
        ):
            return
        p = self.data[pressure_key]
        q = self.data[q_key]
        e = q * p / (MW_RATIO + (1 - MW_RATIO) * q)
        es = calc_saturated_vapor_pressure(self.data[temperature_key])
        self.data[rh_key] = e / es
        self.sources[rh_key] = (
            f"Calculated from {q_key}, {temperature_key} and {pressure_key}"
        )

    def screen_time(self, date: datetime.date) -> None:
        """Screen time to given date (0th and 24th hour included)."""
        next_date = date + datetime.timedelta(days=1)
        t_min = datetime.datetime.combine(date, datetime.time())
        t_max = datetime.datetime.combine(next_date, datetime.time())
        time = self.data["time"]
        mask = (time >= t_min) & (time <= t_max)
        self._screen_data(mask)

    def screen_forecast_time(self, t_min: int, t_max: int) -> None:
        """Screen forecast time to given range (inclusive)."""
        time = self.data["forecast_time"]
        mask = (time >= t_min) & (time <= t_max)
        self._screen_data(mask)

    def _screen_data(self, mask: npt.NDArray[np.bool]) -> None:
        for key, values in self.data.items():
            if key == "time" or "time" in ATTRIBUTES[key].dimensions:
                self.data[key] = values[mask]

    def write_netcdf(self, filename: PathLike | str) -> None:
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
                f"{now:%Y-%m-%d %H:%M:%S} +00:00 - "
                f"Cloudnet model file generated using model-munger v{__version__}",
                *self.history,
            ]
            nc.history = "\n".join(history)

            n_time, n_level = self.data["height"].shape
            nc.createDimension("time", n_time)
            nc.createDimension("level", n_level)
            if "soil_depth" in self.data:
                n_time, n_soil = self.data["soil_depth"].shape
                nc.createDimension("soil_level", n_soil)

            ncvar = nc.createVariable("time", "f4", "time", zlib=True)
            ncvar.long_name = "Hours UTC"
            ncvar.units = f"hours since {date:%Y-%m-%d} 00:00:00 +00:00"
            ncvar.standard_name = "time"
            ncvar.axis = "T"
            ncvar.calendar = "standard"
            ncvar[:] = date2num(
                self.data["time"],
                units=ncvar.units,
                calendar=ncvar.calendar,
            )

            for key, meta in ATTRIBUTES.items():
                if key not in self.data:
                    continue
                data_type = self.data[key].dtype.str[1:]
                if data_type == "f8":
                    data_type = "f4"
                fill_value = netCDF4.default_fillvals[data_type]
                values = self.data[key]
                dimensions = meta.dimensions
                if key in ("latitude", "longitude") and np.all(values == values[0]):
                    values = values[0]
                    dimensions = ()
                ncvar = nc.createVariable(
                    key,
                    data_type,
                    dimensions,
                    zlib=True,
                    fill_value=fill_value,
                )
                ncvar.units = meta.units
                ncvar.long_name = meta.long_name
                if meta.standard_name:
                    ncvar.standard_name = meta.standard_name
                if key in self.comments:
                    ncvar.comment = self.comments[key]
                elif meta.comment is not None:
                    ncvar.comment = meta.comment
                if meta.axis:
                    ncvar.axis = meta.axis
                if meta.positive:
                    ncvar.positive = meta.positive
                if key in self.sources:
                    ncvar.source = self.sources[key]
                ncvar[:] = values


def _convert_units(
    key: str, values: npt.NDArray, units_from: str, units_to: str
) -> npt.NDArray:
    if units_from == "hPa" and units_to == "Pa":
        return values * HPA_TO_PA
    if units_from == "hPa s-1" and units_to == "Pa s-1":
        return values * HPA_TO_PA
    if units_from == "%" and units_to == "1":
        return values / 100
    raise ValueError(f"Cannot convert '{key}' from '{units_from}' to '{units_to}'")
