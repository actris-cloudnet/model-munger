import datetime
from pathlib import Path

import netCDF4
import numpy as np
from numpy.testing import assert_array_equal

from model_munger.model import Model

from .common import HELSINKI, SNARK


def test_model_latlon_scalar(tmp_path: Path) -> None:
    time = np.array(
        [
            datetime.datetime(2024, 1, 22, 0, 0, 0) + datetime.timedelta(hours=i)
            for i in range(25)
        ]
    )
    height = np.array([[10, 100, 1000]] * 25, dtype="f4")
    latitude = np.array(60.25, dtype="f4")
    longitude = np.array(25.0, dtype="f4")
    model = Model(
        SNARK,
        HELSINKI,
        {"time": time, "height": height, "latitude": latitude, "longitude": longitude},
    )
    model.screen_forecast_time(0, 12)
    assert model.data["time"].shape == (13,)
    assert model.data["height"].shape == (13, 3)
    assert model.data["latitude"].shape == (13,)
    assert model.data["longitude"].shape == (13,)

    filename = tmp_path / "model.nc"
    model.write_netcdf(filename)
    with netCDF4.Dataset(filename) as nc:
        assert_array_equal(nc["time"][:], np.arange(13, dtype="f4"), strict=True)
        assert_array_equal(nc["latitude"][:], latitude, strict=True)
        assert_array_equal(nc["longitude"][:], longitude, strict=True)


def test_model_latlon_array(tmp_path: Path) -> None:
    time = np.array(
        [
            datetime.datetime(2024, 1, 22, 0, 0, 0) + datetime.timedelta(hours=i)
            for i in range(25)
        ]
    )
    height = np.array([[10, 100, 1000]] * 25, dtype="f4")
    latitude = np.round(np.linspace(60, 61, 25, dtype="f4") / 0.25) * 0.25
    longitude = np.round(np.linspace(25, 26, 25, dtype="f4") / 0.25) * 0.25
    model = Model(
        SNARK,
        HELSINKI,
        {"time": time, "height": height, "latitude": latitude, "longitude": longitude},
    )
    model.screen_forecast_time(0, 12)
    assert model.data["time"].shape == (13,)
    assert model.data["height"].shape == (13, 3)
    assert model.data["latitude"].shape == (13,)
    assert model.data["longitude"].shape == (13,)

    filename = tmp_path / "model.nc"
    model.write_netcdf(filename)
    with netCDF4.Dataset(filename) as nc:
        assert_array_equal(nc["time"][:], np.arange(13, dtype="f4"), strict=True)
        assert_array_equal(nc["latitude"][:], latitude[:13], strict=True)
        assert_array_equal(nc["longitude"][:], longitude[:13], strict=True)
