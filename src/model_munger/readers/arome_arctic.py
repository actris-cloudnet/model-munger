from os import PathLike

import atmoslib
import netCDF4
import numpy as np
import numpy.typing as npt
from cftime import num2pydate

from model_munger.model import Location, Model, ModelType
from model_munger.utils import LCC, calc_sigma_height

sfc_keymap = {
    "land_area_fraction": "sfc_land_cover",
    "visibility_in_air": "sfc_visibility",
    "air_temperature_0m": "sfc_temp",
    "surface_geopotential": "sfc_geopotential",
    "surface_air_pressure": "sfc_pressure",
    "air_temperature_2m": "sfc_temp_2m",
    "specific_humidity_2m": "sfc_q_2m",
    "x_wind_10m": "sfc_wind_u_10m",
    "y_wind_10m": "sfc_wind_v_10m",
    "cloud_area_fraction": "sfc_cloud_fraction",
    "specific_convective_available_potential_energy": "sfc_cape",
    "atmosphere_convective_inhibition": "sfc_cin",
    "x_wind_gust_10m": "sfc_uwind_gust_10m",
    "y_wind_gust_10m": "sfc_vwind_gust_10m",
    "air_pressure_at_sea_level": "sfc_pressure_amsl",
}

ml_keymap = {
    "specific_humidity_ml": "q",
    "mass_fraction_of_cloud_condensed_water_in_air_ml": "qc",
    "mass_fraction_of_cloud_ice_in_air_ml": "qi",
    "mass_fraction_of_snow_in_air_ml": "qs",
    "mass_fraction_of_rain_in_air_ml": "qr",
    "mass_fraction_of_graupel_in_air_ml": "qg",
    "turbulent_kinetic_energy_ml": "tke",
    "cloud_area_fraction_ml": "cloud_fraction",
    "air_temperature_ml": "temperature",
    "x_wind_ml": "uwind",
    "y_wind_ml": "vwind",
    "upward_air_velocity_ml": "wwind",
}


units_map = {
    "kg/kg": "1",
    "m^2/s^2": "m2 s-2",
    "m/s": "m s-1",
    "N/m^2": "kg m-1 s-2",
    "J/kg": "J kg-1",
}

override_units = {
    "cloud_area_fraction_ml": "1"  # given incorrectly as %
}


def read_arome_arctic(
    sfc_file: str | PathLike, ml_file: str | PathLike, location: Location
) -> Model:
    """Read AROME-Arctic netCDF subset.

    Args:
        sfc_file: Path to surface data.
        ml_file: Path to model level data.
        location: Location metadata.

    Returns:
        Model data.
    """
    data = {}
    units = {}
    sources = {}
    history = []

    with netCDF4.Dataset(sfc_file) as nc_sfc, netCDF4.Dataset(ml_file) as nc_ml:
        for key in ("x", "y", "latitude", "longitude", "time", "surface_air_pressure"):
            if not np.array_equal(nc_sfc[key][:], nc_ml[key][:]):
                msg = f"Variable {key} in sfc and ml files do not match"
                raise ValueError(msg)

        # sfc variables
        for src, dst in sfc_keymap.items():
            if src not in nc_sfc.variables:
                continue
            var = nc_sfc[src]
            data[dst] = var[:, 0]
            units[dst] = units_map.get(var.units, var.units)
            sources[dst] = src

        time = nc_sfc["time"]
        n_time = len(time)
        data["time"] = num2pydate(time[:], units=time.units)

        lat = nc_sfc["latitude"]
        data["latitude"] = lat[:]
        units["latitude"] = lat.units

        lon = nc_sfc["longitude"]
        data["longitude"] = lon[:]
        units["longitude"] = lon.units

        history.extend(nc_sfc.history.splitlines())

        # ml variables
        for src, dst in ml_keymap.items():
            if src not in nc_ml.variables:
                continue
            var = nc_ml[src]
            data[dst] = var[:, ::-1]
            units[dst] = override_units.get(src, units_map.get(var.units, var.units))
            sources[dst] = src

        lambert_var = nc_sfc["projection_lambert"]
        lambert = LCC(
            standard_parallel=lambert_var.standard_parallel,
            origin_latitude=lambert_var.latitude_of_projection_origin,
            central_meridian=lambert_var.longitude_of_central_meridian,
            earth_radius=lambert_var.earth_radius,
        )
        alpha = lambert.theta(data["longitude"])
        alpha_deg = round(np.rad2deg(alpha), 2)
        for ukey, vkey in [
            ("uwind", "vwind"),
            ("sfc_wind_u_10m", "sfc_wind_v_10m"),
            ("sfc_uwind_gust_10m", "sfc_vwind_gust_10m"),
        ]:
            data[ukey], data[vkey] = _rotate_clockwise(data[ukey], data[vkey], alpha)
            sources[ukey] += f" rotated by {alpha_deg} deg"
            sources[vkey] += f" rotated by {alpha_deg} deg"

        p, z = calc_sigma_height(
            nc_ml["ap"][:],
            nc_ml["b"][:],
            data["sfc_pressure"],
            data["temperature"][:, ::-1],
            data["q"][:, ::-1],
        )

        data["pressure"] = p[:, ::-1]
        units["pressure"] = "Pa"
        sources["pressure"] = "Calculated from ap, b and sfc_pressure"

        data["height"] = atmoslib.geometric_height(z[:, ::-1])
        units["height"] = "m"
        sources["height"] = "Calculated pressure, temperature and q"

        data["model_level"] = np.arange(z.shape[1], 0, -1, dtype=np.int16)
        units["model_level"] = "1"

        data["horizontal_resolution"] = np.repeat(2.5, n_time)
        units["horizontal_resolution"] = "km"

        history.extend(nc_ml.history.splitlines())

    return Model(
        AROME_ARCTIC,
        location,
        data,
        units,
        sources=sources,
        history=history,
    )


def _rotate_clockwise(
    uwind: npt.NDArray, vwind: npt.NDArray, alpha: float
) -> tuple[npt.NDArray, npt.NDArray]:
    """Rotate wind clockwise.

    Args:
        uwind: Zonal wind speed.
        vwind: Meridian wind speed.
        alpha: Angle (radians)

    Returns:
        Tuple of rotated zonal and meridian wind speeds.
    """
    cos_alpha = np.cos(alpha)
    sin_alpha = np.sin(alpha)
    uwind_rot = uwind * cos_alpha + vwind * sin_alpha
    vwind_rot = -uwind * sin_alpha + vwind * cos_alpha
    return uwind_rot, vwind_rot


AROME_ARCTIC = ModelType(
    id="arome-arctic",
    full_name="AROME-Arctic",
    short_name="AROME-Arctic",
)
