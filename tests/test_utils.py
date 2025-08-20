import numpy as np
import pytest
from numpy import ma
from numpy.testing import assert_array_equal

from model_munger import utils


def test_bin_data():
    x = np.arange(-5.0, 11.0)
    y = np.arange(0.0, 6.0, 5.0)
    bins, is_valid = utils.bin_data(x, y)
    assert_array_equal(bins, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    assert_array_equal(is_valid, [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0])


def test_average_coordinates():
    time = np.array([8, 9, 10, 11, 20])
    model_time = np.array([10, 20])
    lat = np.array([5, 5, 4, 4, 4])
    lon = np.array([2, 1, 1, 2, 2])
    avg_lat, avg_lon = utils.average_coordinates(time, lat, lon, model_time)
    assert ma.allclose(avg_lat, [4.5, 4.0], atol=1e-3)
    assert ma.allclose(avg_lon, [1.5, 2.0], atol=1e-3)


def test_average_coordinates_exception():
    time = np.array([8, 9, 10, 11])
    model_time = np.array([0, 10, 20])
    lat = np.array([5, 5, 4, 4])
    lon = np.array([2, 1, 1, 2])
    with pytest.raises(ValueError, match="Empty bin found"):
        utils.average_coordinates(time, lat, lon, model_time)


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
def test_fill_masked(test_input, expected):
    actual = utils.ffill(test_input)
    assert_array_equal(actual, expected)
    assert_array_equal(ma.getmaskarray(actual), ma.getmaskarray(expected))
