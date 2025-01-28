import re
from os import PathLike

import netCDF4
import numpy as np
from cftime import num2pydate

from model_munger.model import Location, Model, ModelType
from model_munger.utils import calc_geometric_height

keymap = {
    "asn": "sfc_albedo_snow",
    "d2m": "sfc_dewpoint_temp_2m",
    "fg10": "sfc_wind_gust_10m",
    "latitude": "latitude",
    "longitude": "longitude",
    "lsm": "sfc_land_cover",
    "msl": "sfc_pressure_amsl",
    "pressure": "pressure",
    "q": "q",
    "skt": "sfc_skin_temp",
    "sot": "soil_temperature",
    "sp": "sfc_pressure",
    "t": "temperature",
    "t2m": "sfc_temp_2m",
    "tcw": "total_column_water",
    "tcwv": "total_column_water_vapour",
    "tprate": "sfc_ls_rainrate",
    "u": "uwind",
    "u10": "sfc_wind_u_10m",
    "v": "vwind",
    "v10": "sfc_wind_v_10m",
    "vsw": "soil_moisture",
    "w": "omega",
}


def read_ecmwf_open(file: str | PathLike, location: Location) -> Model:
    """Read ECMWF open data netCDF generated using model-munger."""

    with netCDF4.Dataset(file) as nc:
        data = {}
        units = {}

        for src, dst in keymap.items():
            if src not in nc.variables:
                continue
            var = nc[src]
            data[dst] = var[:]
            units[dst] = _normalize_units(var.units)

        time = nc["time"]
        data["time"] = num2pydate(time[:], units=time.units)

        data["pressure"] = np.tile(data["pressure"], (len(data["time"]), 1))

        if "soil_temperature" in data or "soil_moisture" in data:
            soil_depth = [0.07, 0.21, 0.72, 1.89]
            data["soil_depth"] = np.tile(soil_depth, (len(data["time"]), 1))
            units["soil_depth"] = "m"

        data["height"] = calc_geometric_height(nc["gh"][:])
        units["height"] = "m"

        history = nc.history.splitlines()

        return Model(ECMWF_OPEN, location, data, units, history=history)


def _normalize_units(units: str) -> str:
    if units in ("kg kg**-1", "(0 - 1)"):
        return "1"
    return re.sub(r"\*\*(-?\d+)", r"\1", units)


ECMWF_OPEN = ModelType(
    id="ecmwf-open",
    full_name="ECMWF open data",
    short_name="ECMWF open data",
)
