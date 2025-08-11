from os import PathLike

import netCDF4
import numpy as np
from cftime import num2pydate

from model_munger.model import Location, Model, ModelType
from model_munger.utils import calc_geometric_height

keymap = {
    "PRSS": "sfc_pressure",
    "MSLP": "sfc_pressure_amsl",
    "TPP6": "sfc_total_rain",
    "UMOF": "sfc_turb_mom_v",
    "VMOF": "sfc_turb_mom_u",
    "SHTF": "sfc_down_sens_heat_flx",
    "DSWF": "sfc_net_sw",
    "RH2M": "sfc_rh_2m",
    "U10M": "sfc_wind_u_10m",
    "V10M": "sfc_wind_v_10m",
    "T02M": "sfc_temp_2m",
    "TCLD": "sfc_cloud_fraction",
    "CAPE": "sfc_cape",
    "CINH": "sfc_cin",
    "LISD": "standard_lifted_index",
    "LIB4": "best_4layer_lifted_index",
    "PBLH": "sfc_bl_height",
    "TMPS": "sfc_temp",
    "CPP6": "sfc_conv_rain",
    "CPPA": "sfc_conv_rain",
    "SOLM": "sfc_soil_moisture",
    "CSNO": "sfc_categorical_snow",
    "CICE": "sfc_categorical_ice",
    "CFZR": "sfc_categorical_freezing_rain",
    "CRAI": "sfc_categorical_rain",
    "LHTF": "sfc_net_lat_heat_flx",
    "LCLD": "sfc_cloud_fraction_low",
    "MCLD": "sfc_cloud_fraction_medium",
    "HCLD": "sfc_cloud_fraction_high",
    "TEMP": "temperature",
    "UWND": "uwind",
    "VWND": "vwind",
    "WWND": "omega",
    "RELH": "rh",
    "pressure": "pressure",
    "forecast_time": "forecast_time",
    "latitude": "latitude",
    "longitude": "longitude",
    "horizontal_resolution": "horizontal_resolution",
}

units_map = {
    "J/kg": "J kg-1",
    "N/m2": "kg m-1 s-2",
    "W/m2": "W m-2",
    "frac.": "1",
    "hPa/s": "hPa s-1",
    "m/s": "m s-1",
}


RH_COMMENT = (
    "With respect to water for temperatures greater than or equal to zero\n"
    "degrees Celsius (0C), with respect to ice for temperatures less than\n"
    "-20C, and a blend between -20C and 0C"
)

WATER_DENSITY = 1000
"Approximate density of water (kg m-3)"


def read_gdas1(file: str | PathLike, location: Location) -> Model:
    """Read GDAS1 netCDF generated using model-munger."""
    with netCDF4.Dataset(file) as nc:
        data = {}
        units = {}
        sources = {}
        comments = {"rh": RH_COMMENT, "sfc_rh_2m": RH_COMMENT}

        for src, dst in keymap.items():
            if src not in nc.variables:
                continue
            ncvar = nc[src]
            values = ncvar[:]
            if src in ("TPP6", "CPP6", "CPPA") and ncvar.units == "m":
                data[dst] = values * WATER_DENSITY
                units[dst] = "kg m-2"
                sources[dst] = f"{src} converted from {ncvar.units} to {units[dst]}"
            elif src in ("CSNO", "CICE", "CFZR", "CRAI"):
                data[dst] = values.astype(np.int16)
                units[dst] = "1"
                sources[dst] = src
            else:
                data[dst] = values
                units[dst] = units_map.get(ncvar.units, ncvar.units)
                if len(src) == 4:
                    sources[dst] = src

        nctime = nc["time"]
        data["time"] = num2pydate(nctime[:], units=nctime.units)

        data["pressure"] = np.tile(data["pressure"], (len(data["time"]), 1))

        data["height"] = calc_geometric_height(nc["HGTS"][:])
        units["height"] = "m"
        sources["height"] = "HGTS converted from gpm to m"

        data["sfc_height"] = calc_geometric_height(nc["SHGT"][:])
        units["sfc_height"] = "m"
        sources["sfc_height"] = "SHGT converted from gpm to m"

        history = nc.history.splitlines()

        return Model(
            GDAS1,
            location,
            data,
            units=units,
            sources=sources,
            comments=comments,
            history=history,
        )


GDAS1 = ModelType(
    id="gdas1",
    full_name="Global Data Assimilation System (GDAS1)",
    short_name="GDAS1",
)
