import datetime
from os import PathLike

import netCDF4
import numpy as np

from model_munger.model import Location, Model, ModelType

sfc_keymap = {
    "CLCH": "sfc_cloud_fraction_high",
    "CLCL": "sfc_cloud_fraction_low",
    "CLCM": "sfc_cloud_fraction_medium",
    "CLCT": "sfc_cloud_fraction",
    "P_SFC": "sfc_pressure",
    "QV_S": "sfc_q",
    "T2M": "sfc_temp_2m",
    "TD2M": "sfc_dewpoint_temp_2m",
    "T_S": "sfc_temp",
    "T_SNOW": "sfc_temp_snow",
    "U10M": "sfc_wind_u_10m",
    "V10M": "sfc_wind_v_10m",
    "VIS": "sfc_visibility",
    "W_SNOW": "sfc_weg_snow",
}

keymap = {
    "CLC": "cloud_fraction",
    "P": "pressure",
    "QC": "ql",
    "QG": "qg",
    "QI": "qi",
    "QR": "qr",
    "QS": "qs",
    "QV": "q",
    "REL_HUM": "rh",
    "T": "temperature",
    "TKE": "tke",
    "U": "uwind",
    "V": "vwind",
    "W": "wwind",
}


units_map = {
    "-": "1",
    "kg kg-1": "1",
    "kg/kg": "1",
    "m H2O": "m",
    "m/s": "m s-1",
    "m^2/s^2": "m2 s-2",
}


class StationMissingError(Exception):
    pass


def read_icon_d2(file: str | PathLike, station_name: str, location: Location) -> Model:
    """Read ICON meteogram file.

    Args:
        file: Path to ICON meteogram file.
        station_name: Station name to extract from the meteogram file.
        location: Location to use for the given station name.

    Returns:
        Model data.

    Raises:
        StationMissingError: If given station doesn't exist.

    References:
        Reinert et al. (2026). DWD Database Reference for the Global and
            Regional ICON and ICON-EPS Forecasting System. Version 2.5.4.
            https://www.dwd.de/SharedDocs/downloads/DE/modelldokumentationen/nwv/icon/icon_dbbeschr_aktuell.pdf

        Prill et al. (2024). Working with the ICON Model.
            https://www.dwd.de/DE/leistungen/nwv_icon_tutorial/pdf_einzelbaende/icon_tutorial2024.pdf
    """
    data = {}
    units = {}
    sources = {}

    with netCDF4.Dataset(file) as nc:
        station_names = netCDF4.chartostring(nc["station_name"][:]).tolist()
        var_names = netCDF4.chartostring(nc["var_name"][:]).tolist()
        var_units = netCDF4.chartostring(nc["var_unit"][:]).tolist()
        var_nlevs = nc["var_nlevs"][:]
        sfcvar_names = netCDF4.chartostring(nc["sfcvar_name"][:]).tolist()
        sfcvar_units = netCDF4.chartostring(nc["sfcvar_unit"][:]).tolist()
        try:
            station_ind = station_names.index(station_name)
        except ValueError as err:
            msg = f"Station {station_name} not in file"
            raise StationMissingError(msg) from err
        for src_ind, src_name in enumerate(var_names):
            if src_name not in keymap:
                continue
            dst_name = keymap[src_name]
            nlevs = var_nlevs[src_ind]
            data[dst_name] = nc["values"][:, :nlevs, src_ind, station_ind][:, ::-1]
            units[keymap[src_name]] = units_map.get(
                var_units[src_ind], var_units[src_ind]
            )
            sources[keymap[src_name]] = src_name
        for src_ind, src_name in enumerate(sfcvar_names):
            if src_name not in sfc_keymap:
                continue
            dst_name = sfc_keymap[src_name]
            data[dst_name] = nc["sfcvalues"][:, src_ind, station_ind]
            units[dst_name] = units_map.get(
                sfcvar_units[src_ind], sfcvar_units[src_ind]
            )
            sources[dst_name] = src_name

        for key in ("wwind", "tke"):
            data[key] = (data[key][:, :-1] + data[key][:, 1:]) / 2
            sources[key] += " interpolated from half to full levels"

        data["time"] = np.array(
            [
                datetime.datetime.strptime(value, "%Y%m%dT%H%M%SZ")
                for value in netCDF4.chartostring(nc["date"][:])
            ]
        )
        n_time = len(data["time"])

        t_ind = var_names.index("T")
        n_level = var_nlevs[t_ind]
        sfc_height = nc["station_hsurf"][station_ind]
        height = nc["heights"][:n_level, t_ind, station_ind][::-1] - sfc_height
        data["height"] = np.tile(height, (n_time, 1))
        units["height"] = "m"
        sources["height"] = "Calculated from HHL - HSURF"

        data["model_level"] = np.arange(n_level, 0, -1, dtype=np.int32)
        units["model_level"] = "1"

        data["latitude"] = np.repeat(nc["station_lat"][station_ind], n_time)
        units["latitude"] = "degree_north"
        sources["latitude"] = "CLAT"

        data["longitude"] = np.repeat(nc["station_lon"][station_ind], n_time)
        units["longitude"] = "degree_east"
        sources["longitude"] = "CLON"

        data["sfc_height"] = np.repeat(sfc_height, n_time)
        units["sfc_height"] = "m"
        sources["sfc_height"] = "HSURF"

    return Model(
        ICON_D2,
        location,
        data,
        units=units,
        sources=sources,
    )


ICON_D2 = ModelType(
    id="icon-d2",
    full_name="ICOsahedral Nonhydrostatic D2 (ICON-D2)",
    short_name="ICON-D2",
)
