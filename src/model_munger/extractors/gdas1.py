import datetime
import os
from collections.abc import Iterator
from typing import BinaryIO

import numpy as np

from model_munger.grid import RegularGrid
from model_munger.level import Level, LevelType
from model_munger.utils import HPA_TO_PA

LONG_NAMES = {
    "PRSS": "Pressure at surface",
    "MSLP": "Pressure reduced to mean sea level",
    "TPP6": "Accumulated precipitation (6 h accumulation)",
    "UMOF": "u-component of momentum flux (3- or 6-h average)",
    "VMOF": "v-component of momentum flux (3- or 6-h average)",
    "SHTF": "Sensible heat net flux at surface (3- or 6-h average)",
    "DSWF": "Downward short wave radiation flux (3- or 6-h average)",
    "RH2M": "Relative Humidity at 2m AGL",
    "U10M": "U-component of wind at 10 m AGL",
    "V10M": "V-component of wind at 10 m AGL",
    "T02M": "Temperature at 2m AGL",
    "TCLD": "Total cloud cover (3- or 6-h average)",
    "SHGT": "Geopotential height",
    "CAPE": "Convective available potential energy",
    "CINH": "Convective inhibition",
    "LISD": "Standard lifted index",
    "LIB4": "Best 4-layer lifted index",
    "PBLH": "Planetary boundary layer height",
    "TMPS": "Temperature at surface",
    "CPP6": "Accumulated convective precipitation (6 h accumulation)",
    "CPPA": "Accumulated convective precipitation (total accumulation)",
    "SOLM": "Volumetric soil moisture content",
    "CSNO": "Categorial snow (yes=1, no=0) (3- or 6-h average)",
    "CICE": "Categorial ice (yes=1, no=0) (3- or 6-h average)",
    "CFZR": "Categorial freezing rain (yes=1, no=0) (3- or 6-h average)",
    "CRAI": "Categorial rain (yes=1, no=0) (3- or 6-h average)",
    "LHTF": "Latent heat net flux at surface (3- or 6-h average)",
    "LCLD": "Low cloud cover (3- or 6-h average)",
    "MCLD": "Middle cloud cover (3- or 6-h average)",
    "HCLD": "High cloud cover (3- or 6-h average)",
    "HGTS": "Geopotential height",
    "TEMP": "Temperature",
    "UWND": "U-component of wind with respect to grid",
    "VWND": "V-component of wind with respect to grid",
    "WWND": "Pressure vertical velocity",
    "RELH": "Relative humidity",
}

UNITS = {
    "PRSS": "hPa",
    "MSLP": "hPa",
    "TPP6": "m",
    "UMOF": "N/m2",
    "VMOF": "N/m2",
    "SHTF": "W/m2",
    "DSWF": "W/m2",
    "RH2M": "%",
    "U10M": "m/s",
    "V10M": "m/s",
    "T02M": "K",
    "TCLD": "%",
    "SHGT": "gpm",
    "CAPE": "J/kg",
    "CINH": "J/kg",
    "LISD": "K",
    "LIB4": "K",
    "PBLH": "m",
    "TMPS": "K",
    "CPP6": "m",
    "CPPA": "m",
    "SOLM": "frac.",
    "LHTF": "W/m2",
    "LCLD": "%",
    "MCLD": "%",
    "HCLD": "%",
    "HGTS": "gpm",
    "TEMP": "K",
    "UWND": "m/s",
    "VWND": "m/s",
    "WWND": "hPa/s",
    "RELH": "%",
}


NOAA_URL = "https://www.ready.noaa.gov/data/archives/gdas1/"
AWS_URL = "https://noaa-oar-arl-hysplit-pds.s3.amazonaws.com/gdas1/"
MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def generate_gdas1_url(date: datetime.date, source: str) -> tuple[str, bool]:
    """Generate URL for a file in GDAS1 archive.

    Args:
        date: Date (UTC)
        source: Location from which to download files ("ecmwf" or "aws").

    Returns:
        Tuple with URL and boolean that indicates whether the file should be
        revalidated if previously downloaded.
    """
    month = MONTHS[date.month - 1]
    year = date.year % 100
    week = (date.day - 1) // 7 + 1
    filename = f"gdas1.{month}{year:02}.w{week}"
    if source == "noaa":
        today = datetime.datetime.now(datetime.timezone.utc).date()
        current_start = datetime.date(
            today.year, today.month, 7 * ((today.day - 1) // 7) + 1
        )
        if date >= current_start:
            filename = "current7days"
            revalidate = True
        else:
            revalidate = False
        url = NOAA_URL + filename
    elif source == "aws":
        url = f"{AWS_URL}{date.year}/{filename}"
        revalidate = False
    else:
        raise ValueError(f"Invalid source: {source}")
    return url, revalidate


def read_gdas1(filename: str | os.PathLike) -> Iterator[Level]:
    with open(filename, "rb") as f:
        yield from _read(f)


GRID = RegularGrid(181, 360, -90.0, 0.0, 90.0, -1.0, 1.0, 1.0)
GRID_DEF = (
    b"90.0000"
    b"359.000"
    b"1.00000"
    b"1.00000"
    b".000000"
    b".000000"
    b".000000"
    b"1.00000"
    b"1.00000"
    b"-90.000"
    b".000000"
    b".000000"
    b"360"
    b"181"
)


def _read(f: BinaryIO) -> Iterator[Level]:
    while True:
        header = f.read(50)
        if len(header) == 0:
            break
        if header[14:18] != b"INDX":
            raise ValueError("Invalid header")

        header = f.read(108)
        if header[9:99] != GRID_DEF:
            raise ValueError("Unexpected grid definition")
        nx = 360
        ny = 181
        nz = int(header[99:102])
        k_flag = int(header[102:104])
        if k_flag != 2:
            raise ValueError("Expected absolute pressure levels")
        lenh = int(header[104:108])

        heights = []
        for _z in range(nz):
            header = f.read(8)
            height = int(float(header[0:6]) * HPA_TO_PA)
            n_vars = int(header[6:8])
            heights.extend([height] * n_vars)
            f.seek(n_vars * 8, os.SEEK_CUR)

        f.seek(nx * ny - lenh, os.SEEK_CUR)
        for height in heights:
            header = f.read(50)
            year = 2000 + int(header[0:2])
            month = int(header[2:4])
            day = int(header[4:6])
            hour = int(header[6:8])
            forecast_hour = int(header[8:10])
            level = int(header[10:12])
            variable = header[14:18].decode()
            exponent = int(header[18:22])
            precision = float(header[22:36])
            value = float(header[36:50])
            compressed = f.read(nx * ny)
            if forecast_hour == -1:
                continue
            values = np.frombuffer(compressed, dtype=np.uint8).reshape((ny, nx))
            values = (values.astype(np.float32) - 127) / 2 ** (7 - exponent)
            assert values[0, 0] == 0
            values[0, 0] = value
            np.cumsum(values[:, 0], out=values[:, 0])
            np.cumsum(values, axis=1, out=values)
            values[np.abs(values) < precision] = 0

            kind = LevelType.SURFACE if level == 0 else LevelType.PRESSURE
            time = datetime.datetime(
                year, month, day, hour, tzinfo=datetime.timezone.utc
            )
            forecast_time = datetime.timedelta(hours=hour % 6)
            attributes = {"long_name": LONG_NAMES[variable]}
            if variable in UNITS:
                attributes["units"] = UNITS[variable]

            yield Level(
                kind=kind,
                level_no=height,
                variable=variable,
                values=np.ravel(values),
                time=time,
                forecast_time=forecast_time,
                grid=GRID,
                attributes=attributes,
            )
