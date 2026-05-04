import datetime
from typing import Final

import atmoslib
import numpy as np
import numpy.typing as npt
from numpy import ma
from scipy.spatial import geometric_slerp

M_TO_KM: Final = 1e-3
"Multiplicative conversion factor from meter to kilometer"


def calc_vertical_wind(
    height: npt.NDArray,
    sfc_pressure: npt.NDArray,
    pressure: npt.NDArray,
    omega: npt.NDArray,
) -> npt.NDArray:
    """Convert vertical wind from pressure to cartesian coordinates.

    Args:
        height: Height above ground (m)
        sfc_pressure: Surface pressure (Pa)
        pressure: Pressure (Pa)
        omega: Vertical wind (Pa s-1)

    Returns:
        Vertical wind (m s-1)
    """
    dz = np.diff(height, prepend=0, axis=1)
    dp = np.diff(pressure, prepend=sfc_pressure[:, np.newaxis], axis=1)
    return omega * dz / dp


def calc_saturation_vapor_pressure(
    t: npt.NDArray, t_ice: float, t_water: float
) -> npt.NDArray:
    """Calculate saturation vapor pressure over liquid or ice.

    Between t_ice and t_water, the saturation vapor pressure is interpolated
    using a quadratic formula (ECMWF 2024, Eq. 7.99).

    Args:
        t: Temperature (K).
        t_ice: Temperature threshold for ice (K).
        t_water: Temperature threshold for water (K).

    Returns:
        Saturation vapor pressure (Pa).

    References:
        ECMWF (2024). IFS Documentation CY49R1 - Part IV: Physical Processes.
            https://doi.org/10.21957/c731ee1102
    """
    is_ice = t <= t_ice
    is_water = t >= t_water
    is_blend = ~is_ice & ~is_water
    a = np.empty_like(t)
    a[is_ice] = 0
    a[is_blend] = ((t[is_blend] - t_ice) / (t_water - t_ice)) ** 2
    a[is_water] = 1
    es_water = atmoslib.saturation_vapor_pressure(t, "liquid")
    es_ice = atmoslib.saturation_vapor_pressure(t, "ice")
    return a * es_water + (1 - a) * es_ice


def ffill(values: npt.NDArray) -> npt.NDArray:
    """Forward-fills masked values in a 1D NumPy array.

    Args:
        values: Input 1D array, possibly with masked values.

    Returns:
        Array with masked values replaced by the most recent non-masked value.
    """
    mask = ma.getmaskarray(values)
    idx = np.where(mask, 0, np.arange(len(values)))
    np.maximum.accumulate(idx, out=idx)
    return values[idx]


def spherical_to_cartesian(
    latitude: npt.ArrayLike,
    longitude: npt.ArrayLike,
) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:
    latitude = np.radians(latitude)
    longitude = np.radians(longitude)
    x = np.cos(latitude) * np.cos(longitude)
    y = np.cos(latitude) * np.sin(longitude)
    z = np.sin(latitude)
    return x, y, z


def cartesian_to_spherical(x: float, y: float, z: float) -> tuple[float, float]:
    hyp = np.hypot(x, y)
    lat = np.degrees(np.arctan2(z, hyp))
    lon = np.degrees(np.arctan2(y, x))
    return lat, lon


def slerp(
    time: datetime.datetime,
    times: list[datetime.datetime],
    latitudes: list[float],
    longitudes: list[float],
) -> tuple[float, float]:
    """Perform spherical linear interpolation.

    Args:
        time: Interpolate point at this time.
        times: Sorted time array for latitudes and longitudes.
        latitudes: Latitudes (degrees).
        longitudes: Longitudes (degrees).

    Returns:
        Latitude and longitude of interpolated point at given time.
    """
    i = np.searchsorted(times, time)  # type: ignore[call-overload]
    if i == 0:
        return latitudes[0], longitudes[0]
    if i == len(times):
        return latitudes[-1], longitudes[-1]
    t = (time - times[i - 1]) / (times[i] - times[i - 1])
    start = spherical_to_cartesian(latitudes[i - 1], longitudes[i - 1])
    end = spherical_to_cartesian(latitudes[i], longitudes[i])
    new_point = geometric_slerp(start, end, t)  # type: ignore[arg-type]
    return cartesian_to_spherical(*new_point)
