import datetime

import numpy as np
from numpy.testing import assert_array_equal

from model_munger.merge import merge_models
from model_munger.model import Location, Model, ModelType

SNARK = ModelType(
    id="snark",
    short_name="SNARK",
    full_name="System for Numerical Atmospheric Research and Kinetics (SNARK)",
)
HELSINKI = Location(id="helsinki", name="Helsinki")


def test_merge():
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
    latitude = 60.25
    longitude = 25.0
    model1 = Model(
        SNARK,
        HELSINKI,
        {
            "time": time1,
            "height": height,
            "pressure": pressure1,
            "latitude": latitude,
            "longitude": longitude,
        },
        history=["model 1 was created"],
    )
    model2 = Model(
        SNARK,
        HELSINKI,
        {
            "time": time2,
            "height": height,
            "pressure": pressure2,
            "latitude": latitude,
            "longitude": longitude,
        },
        history=["model 2 was created"],
    )
    merged = merge_models([model1, model2])
    assert merged.type == SNARK
    assert merged.location == HELSINKI
    assert merged.history == ["model 1 was created", "model 2 was created"]
    assert merged.data["latitude"] == latitude
    assert merged.data["longitude"] == longitude
    assert_array_equal(merged.data["time"], np.array(time1[:12] + time2))
    assert_array_equal(merged.data["pressure"], pressure1[:12] + pressure2)
    assert_array_equal(merged.data["height"], [[10, 100, 1000]] * (12 + 25))
    assert_array_equal(
        merged.data["forecast_time"], np.concatenate([np.arange(12), np.arange(25)])
    )
