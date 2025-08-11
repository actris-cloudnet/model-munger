import datetime

import netCDF4
from numpy.testing import assert_allclose, assert_array_equal

from model_munger.extract import RawLocation, extract_profiles, write_netcdf
from model_munger.extractors.ecmwf_open import read_ecmwf
from model_munger.level import Level
from model_munger.readers.ecmwf_open import ECMWF_OPEN


def test_extract_profiles(tmp_path):
    input_files = [
        "tests/data/20250115000000-0h-oper-fc.grib2",
        "tests/data/20250115000000-3h-oper-fc.grib2",
    ]
    locations = [
        RawLocation(
            id="hyytiala",
            name="Hyytiälä",
            time=None,
            latitude=61.844,
            longitude=24.287,
        ),
        RawLocation(
            id="boaty",
            name="Boaty McBoatface",
            time=[
                datetime.datetime(2025, 1, 14, 23, 59),
                datetime.datetime(2025, 1, 15, 3, 1),
            ],
            latitude=[59.446, 59.801],
            longitude=[24.772, 24.839],
        ),
    ]
    levels: list[Level] = []
    for input_file in input_files:
        levels.extend(read_ecmwf(input_file))
    for raw in extract_profiles(levels, locations, ECMWF_OPEN):
        write_netcdf(raw, tmp_path / f"{raw.location.id}.nc")
    with netCDF4.Dataset(tmp_path / "hyytiala.nc") as nc:
        assert nc["time"].units == "hours since 2025-01-15 00:00:00 +00:00"
        assert_array_equal(nc["time"][:], [0, 3])
        assert_array_equal(nc["latitude"][:], 61.75)
        assert_array_equal(nc["longitude"][:], 24.25)
        assert_array_equal(nc["pressure"][:], [100_000, 10_000])
        assert_allclose(
            nc["t"][:],
            [[273.766754, 214.335098], [271.976425, 213.248489]],
        )
        assert_allclose(nc["t2m"][:], [273.366211, 270.937653])
        assert_allclose(
            nc["sot"][:],
            [[273.004318, 272.756409], [272.97612, 272.759644]],
        )
    with netCDF4.Dataset(tmp_path / "boaty.nc") as nc:
        assert nc["time"].units == "hours since 2025-01-15 00:00:00 +00:00"
        assert_array_equal(nc["time"][:], [0, 3])
        assert_array_equal(nc["latitude"][:], [59.5, 59.75])
        assert_array_equal(nc["longitude"][:], [24.75, 24.75])
        assert_array_equal(nc["pressure"][:], [100_000, 10_000])
        assert_allclose(
            nc["t"][:], [[275.423004, 213.647598], [275.007675, 213.435989]]
        )
        assert_allclose(nc["t2m"][:], [275.584961, 276.343903])
        assert_allclose(
            nc["sot"][:], [[274.848068, 274.912659], [277.22612, 277.228394]]
        )
