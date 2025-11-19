import datetime
from os import PathLike
from pathlib import Path

import netCDF4
import numpy as np
from cftime import num2pydate
from numpy import ma

from model_munger.model import Location, Model, ModelType
from model_munger.utils import G, calc_geometric_height

keymap = {
    "cc": "cloud_fraction",
    "h_soil": "soil_depth",
    "height_f": "height",
    "lsm": "sfc_land_cover",
    "nlev": "model_level",
    "omega": "omega",
    "orog": "sfc_geopotential",
    "pressure_f": "pressure",
    "ps": "sfc_pressure",
    "q": "q",
    "q2m": "sfc_q_2m",
    "q_soil": "soil_moisture",
    "qi": "qi",
    "ql": "ql",
    "snow": "sfc_weg_snow",
    "t": "temperature",
    "t2m": "sfc_temp_2m",
    "t_soil": "soil_temperature",
    "u": "uwind",
    "u10m": "sfc_wind_u_10m",
    "v": "vwind",
    "v10m": "sfc_wind_v_10m",
}

units_map = {
    "0-1": "1",
    "Pa/s": "Pa s-1",
    "Pascal": "Pa",
    "count": "1",
    "deg E": "degree_east",
    "deg N": "degree_north",
    "kg/kg": "1",
    "m, liquid equivalent": "m",
    "m/s": "m s-1",
    "m2/s2": "m2 s-2",
    "m^3/m^3": "m3 m-3",
}


def read_arpege(file: str | PathLike, location: Location) -> Model:
    """Read ARPEGE netCDF generated using lfa2nc."""
    with netCDF4.Dataset(file) as nc:
        data = {}
        units = {}

        for src, dst in keymap.items():
            var = nc[src]
            values = var[:]
            values = ma.masked_where(values == -999, values)
            if "nlev" in var.dimensions:
                values = np.flip(values, var.dimensions.index("nlev"))
            data[dst] = values
            units[dst] = _normalize_units(var.units)

        # Height in the input files appears to be geometric height above sea
        # level. Convert this to geometric height above ground based on surface
        # geopotential.
        ground = calc_geometric_height(data["sfc_geopotential"] / G)
        data["height"] = data["height"] - ground[:, np.newaxis]

        time = nc["time"]
        if time.units == "seconds":
            date_int = nc["date"][0]
            year, month_day = divmod(date_int, 10000)
            month, day = divmod(month_day, 100)
            epoch = datetime.datetime(year, month, day) + datetime.timedelta(
                seconds=int(nc["second"][0])
            )
            data["time"] = np.array(
                [epoch + datetime.timedelta(seconds=int(t)) for t in time]
            )
        else:
            data["time"] = num2pydate(time[:], units=time.units)

        data["latitude"] = nc["lat"][0]
        units["latitude"] = _normalize_units(nc["lat"].units)

        data["longitude"] = nc["lon"][0]
        units["longitude"] = _normalize_units(nc["lon"].units)

        data["soil_depth"] = np.tile(data["soil_depth"], (len(data["time"]), 1))

        history = [
            f"{nc.NetCdf_creation_date} - {Path(file).name} created by {nc.creator}",
        ]

        return Model(ARPEGE, location, data, units, history=history)


def _normalize_units(units: str) -> str:
    return units_map.get(units, units)


ARPEGE = ModelType(
    id="arpege",
    full_name="Action de Recherche Petite Echelle Grande Echelle (ARPEGE)",
    short_name="ARPEGE",
)
