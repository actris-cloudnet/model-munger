from typing import Final
import numpy.typing as npt
import numpy as np

EARTH_RADIUS: Final = 6_371_229
"Radius of the Earth (m) as assumed in ECMWF IFS"

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
    dz = np.diff(height, prepend=0)
    dp = np.diff(pressure, prepend=sfc_pressure)
    return omega * dz / dp


def calc_saturated_vapor_pressure(temperature: npt.NDArray) -> npt.NDArray:
    """Calculate saturation vapor pressure over liquid above freezing and over
    ice below freezing using Goff-Gratch formulae.

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


def calc_vapor_pressure(
    pressure: npt.NDArray, specific_humidity: npt.NDArray
) -> npt.NDArray:
    """Calculate partial pressure of water vapor from atmospheric pressure and
    specific humidity.

    Args:
        pressure: Air pressure (Pa)
        specific_humidity: Specific humidity (kg kg-1)

    Returns:
        Vapor pressure (Pa)

    References:
        Cai, J. (2019). Humidity Measures.
        https://cran.r-project.org/web/packages/humidity/vignettes/humidity-measures.html
    """
    return (
        specific_humidity * pressure / (MW_RATIO + (1 - MW_RATIO) * specific_humidity)
    )


def calc_relative_humidity(
    pressure: npt.NDArray, temperature: npt.NDArray, specific_humidity: npt.NDArray
) -> npt.NDArray:
    """Calculate relative humidity with respect to liquid above freezing and
    with respect to ice below freezing using Goff-Gratch formulae.

    Args:
        pressure: Pressure (Pa)
        temperature: Temperature (K)
        specific_humidity: Specific humidity (kg kg-1)

    Returns:
        Relative humidity (1)
    """
    vp = calc_vapor_pressure(pressure, specific_humidity)
    svp = calc_saturated_vapor_pressure(temperature)
    return vp / svp
