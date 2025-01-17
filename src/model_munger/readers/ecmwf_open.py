from os import PathLike
import re

import netCDF4
from cftime import num2pydate
import numpy as np

from model_munger.model import Location, Model, ModelType
from model_munger.utils import calc_geometric_height


keymap = {
    "d2m": "sfc_dewpoint_temp_2m",
    "latitude": "latitude",
    "longitude": "longitude",
    "msl": "sfc_pressure_amsl",
    "pressure": "pressure",
    "q": "q",
    "sot": "soil_temperature",
    "sp": "sfc_pressure",
    "t": "temperature",
    "t2m": "sfc_temp_2m",
    "u": "uwind",
    "u10": "sfc_wind_u_10m",
    "v": "vwind",
    "v10": "sfc_wind_v_10m",
    "vsw": "soil_moisture",
    "w": "omega",
}


def read_ecmwf_open(file: str | PathLike, location: Location) -> Model:
    with netCDF4.Dataset(file) as nc:
        data = {}
        units = {}

        for src, dst in keymap.items():
            var = nc[src]
            data[dst] = var[:]
            units[dst] = _normalize_units(var.units)

        time = nc["time"]
        data["time"] = num2pydate(time[:], units=time.units)

        data["pressure"] = np.tile(data["pressure"], (len(data["time"]), 1))

        soil_depth = [0.07, 0.21, 0.72, 1.89]
        data["soil_depth"] = np.tile(soil_depth, (len(data["time"]), 1))
        units["soil_depth"] = "m"

        data["height"] = calc_geometric_height(nc["gh"][:])
        units["height"] = "m"

        history = nc.history.splitlines()

        return Model(ECMWF_OPEN, location, data, units, history=history)


def _normalize_units(units: str) -> str:
    if units == "kg kg**-1":
        return "1"
    return re.sub(r"\*\*(-?\d+)", r"\1", units)


ECMWF_OPEN = ModelType(
    id="ecmwf-open",
    full_name="ECMWF open data",
    short_name="ECMWF open data",
)
