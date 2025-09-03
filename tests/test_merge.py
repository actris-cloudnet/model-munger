import datetime

import numpy as np
from numpy import ma
from numpy.testing import assert_array_equal

from model_munger.merge import merge_models
from model_munger.model import Model

from .common import HELSINKI, SNARK


def test_merge() -> None:
    time1 = [
        datetime.datetime(2024, 1, 22, 0, 0, 0) + datetime.timedelta(hours=i)
        for i in range(25)
    ]
    time2 = [
        datetime.datetime(2024, 1, 22, 12, 0, 0) + datetime.timedelta(hours=i)
        for i in range(25)
    ]
    height = [[10, 100, 1000]] * 25
    pressure1 = [[101205, 100129, 89875]] * 25
    pressure2 = [[101212, 100136, 89880]] * 25
    latitude = [60.25] * 25
    longitude = [25.0] * 25
    model1 = Model(
        SNARK,
        HELSINKI,
        {
            "time": np.array(time1),
            "height": np.array(height),
            "pressure": np.array(pressure1),
            "latitude": np.array(latitude),
            "longitude": np.array(longitude),
        },
        history=["model 1 was created"],
    )
    model2 = Model(
        SNARK,
        HELSINKI,
        {
            "time": np.array(time2),
            "height": np.array(height),
            "pressure": np.array(pressure2),
            "latitude": np.array(latitude),
            "longitude": np.array(longitude),
        },
        history=["model 2 was created"],
    )
    merged = merge_models([model1, model2])
    assert merged.type == SNARK
    assert merged.location == HELSINKI
    assert merged.history == ["model 1 was created", "model 2 was created"]
    assert_array_equal(merged.data["latitude"], latitude[:12] + latitude)
    assert_array_equal(merged.data["longitude"], longitude[:12] + longitude)
    assert_array_equal(merged.data["time"], np.array(time1[:12] + time2))
    assert_array_equal(merged.data["pressure"], pressure1[:12] + pressure2)
    assert_array_equal(merged.data["height"], [[10, 100, 1000]] * (12 + 25))
    assert_array_equal(
        merged.data["forecast_time"],
        np.concatenate([np.arange(12), np.arange(25)]),
    )


def test_missing_variable_is_masked() -> None:
    time1 = [
        datetime.datetime(2024, 1, 22, 0, 0, 0) + datetime.timedelta(hours=i)
        for i in range(25)
    ]
    time2 = [
        datetime.datetime(2024, 1, 22, 12, 0, 0) + datetime.timedelta(hours=i)
        for i in range(25)
    ]
    height = np.array([[10, 100, 1000]] * 25)
    pressure1 = np.array([[101205, 100129, 89875]] * 25)
    latitude = [60.25] * 25
    longitude = [25.0] * 25
    model1 = Model(
        SNARK,
        HELSINKI,
        {
            "time": np.array(time1),
            "height": np.array(height),
            "pressure": np.array(pressure1),
            "latitude": np.array(latitude),
            "longitude": np.array(longitude),
        },
        history=["model 1 was created"],
    )
    model2 = Model(
        SNARK,
        HELSINKI,
        {
            "time": np.array(time2),
            "height": np.array(height),
            "latitude": np.array(latitude),
            "longitude": np.array(longitude),
        },
        history=["model 2 was created"],
    )
    merged = merge_models([model1, model2])
    assert merged.type == SNARK
    assert merged.location == HELSINKI
    assert merged.history == ["model 1 was created", "model 2 was created"]
    assert_array_equal(merged.data["latitude"], latitude[:12] + latitude)
    assert_array_equal(merged.data["longitude"], longitude[:12] + longitude)
    assert_array_equal(merged.data["time"], np.array(time1[:12] + time2))
    assert_array_equal(
        merged.data["pressure"],
        ma.concatenate([pressure1[:12], ma.masked_all_like(pressure1)]),
    )
    assert_array_equal(merged.data["height"], [[10, 100, 1000]] * (12 + 25))
    assert_array_equal(
        merged.data["forecast_time"],
        np.concatenate([np.arange(12), np.arange(25)]),
    )
