import re
from os import PathLike

import atmoslib
import netCDF4
import numpy as np
from cftime import num2pydate

from model_munger.model import Location, Model, ModelType
from model_munger.utils import ffill

keymap = {
    "horizontal_resolution": "horizontal_resolution",
    "latitude": "latitude",
    "longitude": "longitude",
    "pl_q": "q",
    "pl_r": "rh",
    "pl_t": "temperature",
    "pl_u": "uwind",
    "pl_v": "vwind",
    "pl_w": "omega",
    "pressure": "pressure",
    "sfc_asn": "sfc_albedo_snow",
    "sfc_d2m": "sfc_dewpoint_temp_2m",
    "sfc_fg10": "sfc_wind_gust_10m",
    "sfc_lsm": "sfc_land_cover",
    "sfc_msl": "sfc_pressure_amsl",
    "sfc_skt": "sfc_skin_temp",
    "sfc_sp": "sfc_pressure",
    "sfc_t2m": "sfc_temp_2m",
    "sfc_tcw": "total_column_water",
    "sfc_tcwv": "total_column_water_vapour",
    "sfc_tprate": "sfc_ls_rainrate",
    "sfc_u10": "sfc_wind_u_10m",
    "sfc_v10": "sfc_wind_v_10m",
    "sfc_z": "sfc_geopotential",
    "sol_sot": "soil_temperature",
    "sol_vsw": "soil_moisture",
    # Legacy names used by model-munger <= 0.3.10:
    "asn": "sfc_albedo_snow",
    "d2m": "sfc_dewpoint_temp_2m",
    "fg10": "sfc_wind_gust_10m",
    "lsm": "sfc_land_cover",
    "msl": "sfc_pressure_amsl",
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
    # GFS
    "pl_clwmr": "ql",
    "pl_snmr": "qs",
    "pl_icmr": "qi",
    "pl_rwmr": "qr",
    # "pl_tcc": "cloud_fraction",
}

RH_COMMENT = """For temperatures over 0°C (273.15 K) it is calculated for
saturation over water. At temperatures below -23°C it is calculated for
saturation over ice. Between -23°C and 0°C this parameter is calculated by
interpolating between the ice and water values using a quadratic function."""


def read_ecmwf_open(
    file: str | PathLike, location: Location, model: ModelType
) -> Model:
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

        ghvar = nc["pl_gh"] if "pl_gh" in nc.variables else nc["gh"]
        data["height"] = atmoslib.geometric_height(ghvar[:])
        units["height"] = "m"
        sources["height"] = f"ECMWF parameter {ghvar.param_id} converted from gpm to m"

        # # Eq. 4, Xu & Randall (1996)
        # es = atmoslib.saturation_vapor_pressure(data["temperature"])
        # qcon = data["ql"] + data["qi"]
        # qsat = MW_RATIO * es / (data["pressure"] - es)
        # p = 0.25
        # y = 0.49
        # a0 = 100
        # rh = data["rh"]/100
        # data["cloud_fraction"] = rh ** p * (1 - np.exp(-a0 * qcon / ((1 - rh) * qsat) ** y))
        # units["cloud_fraction"] = "1"

        rh0 = 0.8
        rh = data["rh"] / 100
        data["cloud_fraction"] = np.maximum(0, np.minimum(1, (rh - rh0) / (1 - rh0)))
        # data["cloud_fraction"] = (data["ql"]+data["qi"] > 1e-10).filled(0).astype(np.float32)
        units["cloud_fraction"] = "1"

        history = nc.history.splitlines()

        return Model(
            model,
            location,
            data,
            units,
            sources=sources,
            comments=comments,
            history=history,
        )


def _normalize_units(units: str) -> str:
    if units in ("kg kg**-1", "(0 - 1)"):
        return "1"
    return re.sub(r"\*\*(-?\d+)", r"\1", units)


ECMWF_OPEN = ModelType(
    id="ecmwf-open",
    full_name="ECMWF open data",
    short_name="ECMWF open data",
)
