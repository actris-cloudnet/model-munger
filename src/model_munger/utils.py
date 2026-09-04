import datetime
from typing import Any, Final, overload

import atmoslib
import numpy as np
import numpy.typing as npt
from atmoslib.constants import HPA_TO_PA, RS, G
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


def calc_sigma_height(
    ap: npt.NDArray[np.floating],
    b: npt.NDArray[np.floating],
    ps: npt.NDArray[np.floating],
    t: npt.NDArray[np.floating],
    q: npt.NDArray[np.floating],
) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]:
    """Calculate pressure and height in hybrid sigma-pressure coordinate system.

    Args:
        ap: Reference pressure at full level (Pa).
        b: Coefficient at full level (1).
        ps: Surface pressure (Pa).
        t: Temperature at full level (K).
        q: Specific humidity at full level (kg kg-1).

    Returns:
        Pressure (Pa) and geopotential height above ground (gpm) at full level.
    """
    n_level = len(ap)
    ap_half = np.empty(n_level + 1)
    ap_half[n_level] = 0
    b_half = np.empty(n_level + 1)
    b_half[n_level] = 1
    for i in range(n_level - 1, -1, -1):
        ap_half[i] = 2 * ap[i] - ap_half[i + 1]
        b_half[i] = 2 * b[i] - b_half[i + 1]

    p_half = ap_half + b_half * ps[:, np.newaxis]
    p = (p_half[:, 1:] + p_half[:, :-1]) / 2
    tv = atmoslib.virtual_temperature(t, q)

    z_half = np.zeros_like(p_half)
    for i in range(n_level - 1, 0, -1):
        z_half[:, i] = z_half[:, i + 1] + (RS * tv[:, i] / G) * np.log(
            p_half[:, i + 1] / p_half[:, i]
        )

    z = (z_half[:, 1:] + z_half[:, :-1]) / 2
    z[:, 0] = z_half[:, 1] + (RS * tv[:, 0] / G) * np.log(2)
    return p, z


class LCC:
    """Lambert conformal conic projection."""

    def __init__(
        self,
        standard_parallel: tuple[float, float],
        origin_latitude: float,
        central_meridian: float,
        earth_radius: float,
    ) -> None:
        """Initialize Lambert conformal conic projection.

        Args:
            standard_parallel: Standard parallels (degrees).
            origin_latitude: Latitude of projection origin (degrees).
            central_meridian: Longitude of central meridian (degrees).
            earth_radius: Earth radius (m).
        """
        if standard_parallel[0] != standard_parallel[1]:
            msg = "Only one standard parallel is supported"
            raise ValueError(msg)
        self.R = earth_radius
        self.lambda0 = central_meridian
        phi0 = np.deg2rad(origin_latitude)
        phi1 = np.deg2rad(standard_parallel[0])
        self.n = np.sin(phi1)
        self.F = np.cos(phi1) * np.tan(np.pi / 4 + phi1 / 2) ** self.n / self.n
        self.rho0 = self.R * self.F / np.tan(np.pi / 4 + phi0 / 2) ** self.n

    @overload
    def project(self, lat: float, lon: float) -> tuple[Any, Any]: ...
    @overload
    def project(
        self, lat: npt.ArrayLike, lon: npt.ArrayLike
    ) -> tuple[npt.NDArray, npt.NDArray]: ...

    def project(self, lat, lon):
        """Project latitude and longitude.

        Args:
            lat: Latitude (degrees).
            lon: Longitude (degrees).

        Return:
            Tuple of y and x coordinates.
        """
        phi = np.deg2rad(lat)
        rho = self.R * self.F / np.tan(np.pi / 4 + phi / 2) ** self.n
        theta = self.theta(lon)
        x = rho * np.sin(theta)
        y = self.rho0 - rho * np.cos(theta)
        return y, x

    @overload
    def theta(self, lon: float) -> Any: ...
    @overload
    def theta(self, lon: npt.ArrayLike) -> npt.NDArray: ...

    def theta(self, lon):
        """Calculate grid convergence angle.

        Args:
            lon: Longitude (degrees).

        Returns:
            Grid convergence angle (radians).
        """
        return self.n * np.deg2rad(lon - self.lambda0)


def convert_units(
    key: str,
    values: npt.NDArray,
    units_from: str,
    units_to: str,
) -> npt.NDArray:
    """Convert array values from one unit to another.

    Args:
        key: Name of the variable being converted.
        values: Array of values to convert.
        units_from: Source units .
        units_to: Target units.

    Returns:
        Array of converted values.

    Raises:
        ValueError: If the unit conversion is not supported.
    """
    if units_from == units_to:
        return values
    if units_from == "hPa" and units_to == "Pa":
        return values * HPA_TO_PA
    if units_from == "hPa s-1" and units_to == "Pa s-1":
        return values * HPA_TO_PA
    if units_from == "%" and units_to == "1":
        return values / 100
    msg = f"Cannot convert '{key}' from '{units_from}' to '{units_to}'"
    raise ValueError(msg)
