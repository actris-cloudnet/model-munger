import re
from os import PathLike

import netCDF4
import numpy as np
from cftime import num2pydate

from model_munger.model import Location, Model, ModelType
from model_munger.utils import calc_geometric_height, ffill

keymap = {
    "asn": "sfc_albedo_snow",
    "d2m": "sfc_dewpoint_temp_2m",
    "fg10": "sfc_wind_gust_10m",
    "horizontal_resolution": "horizontal_resolution",
    "latitude": "latitude",
    "longitude": "longitude",
    "lsm": "sfc_land_cover",
    "msl": "sfc_pressure_amsl",
    "pressure": "pressure",
    "q": "q",
    "r": "rh",
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
    "z": "sfc_geopotential",
}

RH_COMMENT = """For temperatures over 0°C (273.15 K) it is calculated for
saturation over water. At temperatures below -23°C it is calculated for
saturation over ice. Between -23°C and 0°C this parameter is calculated by
interpolating between the ice and water values using a quadratic function."""


def read_ecmwf_open(file: str | PathLike, location: Location) -> Model:
    """Read ECMWF open data netCDF generated using model-munger."""
    with netCDF4.Dataset(file) as nc:
        data = {}
        units = {}
        sources = {}
        comments = {"rh": RH_COMMENT}

        for src, dst in keymap.items():
            if src not in nc.variables:
                continue
            var = nc[src]
            data[dst] = var[:]
            units[dst] = _normalize_units(var.units)
            if hasattr(var, "param_id"):
                sources[dst] = f"ECMWF parameter {var.param_id}"

        # Forward-fill values that are available only in the first time step.
        for key in ("sfc_geopotential",):
            if key in data:
                data[key] = ffill(data[key])

        time = nc["time"]
        data["time"] = num2pydate(time[:], units=time.units)

        data["pressure"] = np.tile(data["pressure"], (len(data["time"]), 1))

        if "soil_temperature" in data or "soil_moisture" in data:
            soil_depth = [0.07, 0.21, 0.72, 1.89]
            data["soil_depth"] = np.tile(soil_depth, (len(data["time"]), 1))
            units["soil_depth"] = "m"

        data["height"] = calc_geometric_height(nc["gh"][:])
        units["height"] = "m"
        sources["height"] = (
            f"ECMWF parameter {nc['gh'].param_id} converted from gpm to m"
        )

        history = nc.history.splitlines()

        return Model(ECMWF_OPEN, location, data, units, sources, comments, history)


def _normalize_units(units: str) -> str:
    if units in ("kg kg**-1", "(0 - 1)"):
        return "1"
    return re.sub(r"\*\*(-?\d+)", r"\1", units)


ECMWF_OPEN = ModelType(
    id="ecmwf-open",
    full_name="ECMWF open data",
    short_name="ECMWF open data",
)
