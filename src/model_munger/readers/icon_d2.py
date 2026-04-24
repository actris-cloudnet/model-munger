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
    "UMFL_S": "sfc_turb_mom_u",
    "V10M": "sfc_wind_v_10m",
    "VIS": "sfc_visibility",
    "VMFL_S": "sfc_turb_mom_v",
    "W_SNOW": "sfc_weq_snow",
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
    "TKVH": "turb_heat_coeff",
    "TKVM": "turb_mom_coeff",
    "U": "uwind",
    "V": "vwind",
    "W": "wwind",
}


units_map = {
    "-": "1",
    "N m-2": "kg m-1 s-2",
    "kg kg-1": "1",
    "kg/kg": "1",
    "m H2O": "m",
    "m**2/s": "m2 s-1",
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
    dimensions = {}

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

        date_values = netCDF4.chartostring(nc["date"][:])
        time_ind = date_values != ""
        data["time"] = np.array(
            [
                datetime.datetime.strptime(value, "%Y%m%dT%H%M%SZ")
                for value in date_values[time_ind]
            ]
        )
        n_time = len(data["time"])

        for src_ind, src_name in enumerate(var_names):
            if src_name not in keymap:
                continue
            dst_name = keymap[src_name]
            nlevs = var_nlevs[src_ind]
            data[dst_name] = nc["values"][time_ind, :nlevs, src_ind, station_ind][
                :, ::-1
            ]
            units[keymap[src_name]] = units_map.get(
                var_units[src_ind], var_units[src_ind]
            )
            sources[keymap[src_name]] = src_name
            dimensions[keymap[src_name]] = (
                "time",
                "level" if nlevs == 65 else "flux_level",
            )
        for src_ind, src_name in enumerate(sfcvar_names):
            if src_name not in sfc_keymap:
                continue
            dst_name = sfc_keymap[src_name]
            data[dst_name] = nc["sfcvalues"][time_ind, src_ind, station_ind]
            units[dst_name] = units_map.get(
                sfcvar_units[src_ind], sfcvar_units[src_ind]
            )
            sources[dst_name] = src_name

        sfc_height = nc["station_hsurf"][station_ind]

        t_ind = var_names.index("T")
        n_level = var_nlevs[t_ind]
        height = nc["heights"][:n_level, t_ind, station_ind][::-1] - sfc_height
        data["height"] = np.tile(height, (n_time, 1))
        units["height"] = "m"
        sources["height"] = "Calculated from HHL - HSURF"

        data["model_level"] = np.arange(n_level, 0, -1, dtype=np.int16)
        units["model_level"] = "1"

        w_ind = var_names.index("W")
        n_flux = var_nlevs[w_ind]
        flx_height = nc["heights"][:n_flux, w_ind, station_ind][::-1] - sfc_height
        data["flx_height"] = np.tile(flx_height, (n_time, 1))
        units["flx_height"] = "m"
        sources["flx_height"] = "Calculated from HHL - HSURF"

        data["flux_level"] = np.arange(n_flux, 0, -1, dtype=np.int16)
        units["flux_level"] = "1"

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
        units,
        sources=sources,
        dimensions=dimensions,
    )


ICON_D2 = ModelType(
    id="icon-d2",
    full_name="ICOsahedral Nonhydrostatic D2 (ICON-D2)",
    short_name="ICON-D2",
)
