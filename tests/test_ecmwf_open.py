import netCDF4
import numpy as np
from numpy.testing import assert_allclose

from model_munger.extractors.ecmwf_open import extract_profiles


def test_extract_profiles(tmp_path):
    input_files = [
        "tests/data/20250115000000-0h-oper-fc.grib2",
        "tests/data/20250115000000-3h-oper-fc.grib2",
    ]
    sites = [
        {
            "id": "hyytiala",
            "humanReadableName": "Hyytiälä",
            "latitude": 61.844,
            "longitude": 24.287,
        },
    ]
    output_files = extract_profiles(input_files, sites, tmp_path)
    assert len(output_files) == len(sites)
    assert output_files[0].name == "20250115000000_hyytiala_ecmwf-open.nc"
    with netCDF4.Dataset(output_files[0]) as nc:
        assert nc["time"].units == "hours since 2025-01-15 00:00:00 +00:00"
        assert_allclose(nc["time"][:], [0, 3])
        assert_allclose(
            nc["latitude"][:],
            np.array(sites[0]["latitude"]),
            rtol=0,
            atol=0.25 / 2,
        )
        assert_allclose(
            nc["longitude"][:],
            np.array(sites[0]["longitude"]),
            rtol=0,
            atol=0.25 / 2,
        )
        assert_allclose(nc["pressure"][:], [100_000, 10_000])
        assert_allclose(
            nc["t"][:],
            [[273.766754, 214.335098], [271.976425, 213.248489]],
        )
        assert_allclose(nc["t2m"][:], [273.366211, 270.937653])
        assert_allclose(
            nc["sot"][:],
            [[273.004318, 272.756409], [272.97612, 272.759644]],
        )
