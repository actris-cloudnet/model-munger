import datetime
import os.path
import sys
import time
from collections.abc import Iterable
from typing import Literal

import netCDF4
import numpy as np
import numpy.typing as npt
from numpy import ma

from model_munger.extract import FixedLocation, MobileLocation, RawModel
from model_munger.readers.arome_arctic import AROME_ARCTIC
from model_munger.utils import LCC
from model_munger.version import __version__ as model_munger_version


def download_arome_arctic(
    date: datetime.date,
    run: Literal[0, 3, 6, 9, 12, 15, 18, 21],
    kind: Literal["sfc", "pl", "ml", "hl"],
    locations: Iterable[FixedLocation | MobileLocation],
) -> list[RawModel]:
    """Extract AROME-Arctic data from MET Norway THREDDS server.

    Args:
        date: Forecast date (UTC)
        run: Forecast run (0, 3, 6, 9, 12, 15 or 18 UTC hour)
        kind: Level type (sfc, pl, ml or hl)
        locations: Locations to extract
    """
    loc_list = []
    lat_list = []
    lon_list = []
    for loc in locations:
        if isinstance(loc, MobileLocation):
            msg = "Mobile locations are not implemented"
            raise NotImplementedError(msg)
        loc_list.append(loc)
        lat_list.append(loc.latitude)
        lon_list.append(loc.longitude)
    locs = np.array(loc_list)
    lats = np.array(lat_list)
    lons = np.array(lon_list)

    data: dict[str, npt.NDArray | list[npt.NDArray]] = {}
    dimensions = {}
    attributes = {}
    history = None
    in_path = _generate_arome_arctic_url(date, run, kind)

    with netCDF4.Dataset(in_path) as nc_in:
        grid_x = _get_data(nc_in["x"])
        grid_y = _get_data(nc_in["y"])
        res = ma.median(np.diff(grid_x))
        min_x = np.min(grid_x) - res / 2
        max_x = np.max(grid_x) + res / 2
        min_y = np.min(grid_y) - res / 2
        max_y = np.max(grid_y) + res / 2

        lambert_var = nc_in["projection_lambert"]
        lambert = LCC(
            standard_parallel=lambert_var.standard_parallel,
            origin_latitude=lambert_var.latitude_of_projection_origin,
            central_meridian=lambert_var.longitude_of_central_meridian,
            earth_radius=lambert_var.earth_radius,
        )
        site_y, site_x = lambert.project(lats, lons)

        is_valid = (
            (site_x >= min_x)
            & (site_x <= max_x)
            & (site_y >= min_y)
            & (site_y <= max_y)
        )
        locs = locs[is_valid]
        site_y = site_y[is_valid]
        site_x = site_x[is_valid]

        for loc in locs:
            print(f"{loc.name}: {loc.latitude}, {loc.longitude}")

        closest_y = np.argmin(np.abs(grid_y[:, np.newaxis] - site_y), axis=0)
        closest_x = np.argmin(np.abs(grid_x[:, np.newaxis] - site_x), axis=0)

        now = datetime.datetime.now(datetime.timezone.utc)
        filename = os.path.basename(in_path)
        history_lines = getattr(nc_in, "history", "").splitlines()
        history_lines.append(
            f"{now:%Y-%m-%d %H:%M:%S} +00:00 - Extracted from {filename} "
            f"using model-munger v{model_munger_version}"
        )
        history = "\n".join(history_lines)

        n_var = len(nc_in.variables)
        for i, key in enumerate(nc_in.variables):
            print(f"{i + 1}/{n_var}", key)
            var_in = nc_in[key]
            if "x" in var_in.dimensions or "y" in var_in.dimensions:
                data[key] = [
                    _get_data(var_in, _make_index(var_in.dimensions, y=y, x=x))
                    for y, x in zip(closest_y, closest_x, strict=True)
                ]
            else:
                data[key] = _get_data(var_in)
            dimensions[key] = var_in.dimensions
            attributes[key] = {
                attr: var_in.getncattr(attr)
                for attr in var_in.ncattrs()
                if attr not in ("_FillValue", "_ChunkSizes")
            }

    return [
        RawModel(
            location=loc,
            model=AROME_ARCTIC,
            data={
                key: value[i] if isinstance(value, list) else value
                for key, value in data.items()
            },
            dimensions={
                key: tuple(d for d in value if d not in ("x", "y"))
                for key, value in dimensions.items()
            },
            attributes=attributes,
            history=history,
        )
        for i, loc in enumerate(locs)
    ]


def _generate_arome_arctic_url(date: datetime.date, run: int, kind: str) -> str:
    return f"https://thredds.met.no/thredds/dodsC/aromearcticarchive/{date:%Y/%m/%d}/arome_arctic_det_{kind}_{date:%Y%m%d}T{run:02}Z.ncml"


def _make_index(dims: list[str], **kwargs: int) -> tuple[int | slice, ...]:
    return tuple(kwargs.get(key, slice(None)) for key in dims)


def _get_data(
    ncvar: netCDF4.Variable,
    ind: slice | tuple[int | slice, ...] = slice(None),
    retries: int = 10,
) -> npt.NDArray:
    """Get data with retry.

    Args:
        ncvar: NetCDF variable.
        ind: Index to data.
        retries: Maximum number of retry attempts on failure.

    Returns:
        Data at given index.
    """
    attempt = 0
    while True:
        try:
            return ncvar[ind]
        except RuntimeError as err:
            print(
                f"Failed to get data on attempt {attempt + 1}: {err}", file=sys.stderr
            )
            if attempt >= retries:
                raise
            time.sleep(2**attempt)
        attempt += 1
