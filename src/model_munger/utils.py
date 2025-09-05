import datetime
from typing import Final

import numpy as np
import numpy.typing as npt
from numpy import ma
from scipy.spatial import geometric_slerp

EARTH_RADIUS: Final = 6_371_229
"Radius of the Earth (m) as assumed in ECMWF IFS"

G: Final = 9.80665
"Earth's gravitational acceleration (m s-2)"

MW_RATIO: Final = 0.62198
"Ratio of the molecular weight of water vapor to dry air"

T0: Final = 273.16
"Triple point of water (K)"

HPA_TO_PA: Final = 100
"Multiplicative conversion factor from hehtopascal to pascal"

M_TO_KM: Final = 1e-3
"Multiplicative conversion factor from meter to kilometer"


def calc_geometric_height(height: npt.NDArray) -> npt.NDArray:
    """Convert geopotential height to geometric height.

    Args:
        height: Geopotential height (m)

    Returns:
        Geometric height (m)

    References:
        ECMWF (2023). ERA5: compute pressure and geopotential on model levels,
        geopotential height and geometric height. https://confluence.ecmwf.int/x/JJh0CQ
    """
    return EARTH_RADIUS * height / (EARTH_RADIUS - height)


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


def calc_saturated_vapor_pressure(temperature: npt.NDArray) -> npt.NDArray:
    """Calculate saturation vapor pressure over liquid or ice.

    Based on the given temperature, the saturated vapor pressure is calculated
    over liquid above freezing and over ice below freezing using Goff-Gratch
    formulae.

    Args:
        temperature: Temperature (K).

    Returns:
        Saturation vapor pressure (Pa).

    References:
        Vömel, H. (2016). Saturation vapor pressure formulations.
        http://cires1.colorado.edu/~voemel/vp.html
    """
    ratio = T0 / temperature
    inv_ratio = temperature / T0
    liquid = HPA_TO_PA * 10 ** (
        10.79574 * (1 - ratio)
        - 5.02800 * np.log10(inv_ratio)
        + 1.50475e-4 * (1 - 10 ** (-8.2969 * (inv_ratio - 1)))
        + 0.42873e-3 * (10 ** (4.76955 * (1 - ratio)) - 1)
        + 0.78614
    )
    ice = HPA_TO_PA * 10 ** (
        -9.09718 * (ratio - 1)
        - 3.56654 * np.log10(ratio)
        + 0.876793 * (1 - inv_ratio)
        + np.log10(6.1071)
    )
    return np.where(temperature < T0, ice, liquid)


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
    latitude: npt.ArrayLike, longitude: npt.ArrayLike
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
    i = np.searchsorted(times, time)  # type: ignore
    if i == 0:
        return latitudes[0], longitudes[0]
    if i == len(times):
        return latitudes[-1], longitudes[-1]
    t = (time - times[i - 1]) / (times[i] - times[i - 1])
    start = spherical_to_cartesian(latitudes[i - 1], longitudes[i - 1])
    end = spherical_to_cartesian(latitudes[i], longitudes[i])
    new_point = geometric_slerp(start, end, t)  # type: ignore
    return cartesian_to_spherical(*new_point)
