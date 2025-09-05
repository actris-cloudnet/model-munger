import datetime

import numpy as np
import numpy.typing as npt
import pytest
from numpy import ma
from numpy.testing import assert_allclose, assert_array_equal

from model_munger import utils


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (np.array([1, 2, 3]), [1, 2, 3]),
        (ma.array([]), []),
        (ma.array([1, 2, 3]), [1, 2, 3]),
        (ma.array([1, 2, 3], mask=[0, 0, 0]), [1, 2, 3]),
        (ma.array([1, 2, 3], mask=[1, 0, 0]), ma.array([1, 2, 3], mask=[1, 0, 0])),
        (ma.array([1, 2, 3], mask=[0, 1, 0]), [1, 1, 3]),
        (ma.array([1, 2, 3], mask=[0, 1, 1]), [1, 1, 1]),
        (ma.array([1, 2, 3], mask=[1, 1, 1]), ma.array([1, 2, 3], mask=[1, 1, 1])),
    ],
)
def test_fill_masked(test_input: npt.NDArray, expected: npt.NDArray) -> None:
    actual = utils.ffill(test_input)
    assert_array_equal(actual, expected)
    assert_array_equal(ma.getmaskarray(actual), ma.getmaskarray(expected))


@pytest.mark.parametrize(
    "time,expected",
    [
        # Before
        (datetime.datetime(2025, 9, 10, 10, 0), (59.0, 23.0)),
        # Exact
        (datetime.datetime(2025, 9, 10, 11, 0), (59.0, 23.0)),
        (datetime.datetime(2025, 9, 10, 12, 0), (60.0, 24.0)),
        (datetime.datetime(2025, 9, 10, 13, 0), (61.0, 25.0)),
        # Between
        (datetime.datetime(2025, 9, 10, 11, 30), (59.500954, 23.492592)),
        (datetime.datetime(2025, 9, 10, 12, 30), (60.500935, 24.492287)),
        # After
        (datetime.datetime(2025, 9, 10, 14, 0), (61.0, 25.0)),
    ],
)
def test_slerp(
    time: datetime.datetime, expected: tuple[npt.NDArray, npt.NDArray]
) -> None:
    times = [
        datetime.datetime(2025, 9, 10, 11, 0),
        datetime.datetime(2025, 9, 10, 12, 0),
        datetime.datetime(2025, 9, 10, 13, 0),
    ]
    latitudes = [59.0, 60.0, 61.0]
    longitudes = [23.0, 24.0, 25.0]
    actual = utils.slerp(time, times, latitudes, longitudes)
    assert_allclose(actual, expected)


@pytest.mark.parametrize(
    "time,expected",
    [
        (datetime.datetime(2025, 9, 10, 12, 0), (0.0, 179.0)),
        (datetime.datetime(2025, 9, 10, 12, 15), (0.0, 179.5)),
        (datetime.datetime(2025, 9, 10, 12, 30), (0.0, 180.0)),
        (datetime.datetime(2025, 9, 10, 12, 45), (0.0, -179.5)),
        (datetime.datetime(2025, 9, 10, 13, 0), (0.0, -179.0)),
    ],
)
def test_slerp_antimeridian(
    time: datetime.datetime, expected: tuple[npt.NDArray, npt.NDArray]
) -> None:
    times = [
        datetime.datetime(2025, 9, 10, 12, 0),
        datetime.datetime(2025, 9, 10, 13, 0),
    ]
    latitudes = [0.0, 0.0]
    longitudes = [179.0, -179.0]
    actual = utils.slerp(time, times, latitudes, longitudes)
    assert_allclose(actual, expected)
