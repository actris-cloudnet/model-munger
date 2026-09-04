import datetime

from numpy.testing import assert_allclose

from model_munger.model import Location
from model_munger.readers.metno import MEPS, read_meps

KUMPULA = Location(id="kumpula", name="Kumpula")


def test_read_meps_basic() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert model.type == MEPS
    assert model.location == KUMPULA
    assert len(model.data["time"]) == 1
    assert model.data["time"][0] == datetime.datetime(2026, 9, 1, 0, 0)


def test_read_meps_profile_variables() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert model.data["temperature"].shape == (1, 65)
    assert model.data["pressure"].shape == (1, 65)
    assert model.data["uwind"].shape == (1, 65)
    assert model.data["vwind"].shape == (1, 65)
    assert model.data["wwind"].shape == (1, 65)
    assert model.data["q"].shape == (1, 65)
    assert model.data["height"].shape == (1, 65)
    assert model.data["cloud_fraction"].shape == (1, 65)
    assert model.data["tke"].shape == (1, 65)
    assert model.data["temperature"].shape[0] == len(model.data["time"])


def test_read_meps_surface_variables() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert model.data["sfc_pressure"].shape == (1,)
    assert model.data["sfc_pressure_amsl"].shape == (1,)
    assert model.data["sfc_temp"].shape == (1,)
    assert model.data["sfc_temp_2m"].shape == (1,)
    assert model.data["sfc_q_2m"].shape == (1,)
    assert model.data["sfc_rh_2m"].shape == (1,)
    assert model.data["sfc_wind_u_10m"].shape == (1,)
    assert model.data["sfc_wind_v_10m"].shape == (1,)
    assert model.data["sfc_cape"].shape == (1,)
    assert model.data["sfc_cin"].shape == (1,)
    assert model.data["sfc_cloud_fraction"].shape == (1,)
    assert model.data["sfc_land_cover"].shape == (1,)
    assert model.data["sfc_visibility"].shape == (1,)
    assert model.data["sfc_geopotential"].shape == (1,)
    assert model.data["sfc_height"].shape == (1,)


def test_read_meps_profile_specific_values() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert_allclose(model.data["temperature"][0, 0], 289.5845, rtol=1e-6)
    assert_allclose(model.data["temperature"][0, 4], 288.69714, rtol=1e-6)
    assert_allclose(model.data["pressure"][0, 0], 100468.21335487138, rtol=1e-6)
    assert_allclose(model.data["pressure"][0, 4], 99229.41620681644, rtol=1e-6)
    assert_allclose(model.data["uwind"][0, 0], 4.23499894, rtol=1e-6)
    assert_allclose(model.data["vwind"][0, 0], 2.774505991824751, rtol=1e-6)
    assert_allclose(model.data["height"][0, 0], 12.642278070976843, rtol=1e-6)


def test_read_meps_surface_specific_values() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert_allclose(model.data["sfc_pressure"][0], 100617.164, rtol=1e-6)
    assert_allclose(model.data["sfc_temp_2m"][0], 289.38422, rtol=1e-6)
    assert_allclose(model.data["sfc_q_2m"][0], 0.01000006, rtol=1e-6)
    assert_allclose(model.data["sfc_wind_u_10m"][0], 3.97135849, rtol=1e-6)
    assert_allclose(model.data["sfc_wind_v_10m"][0], 2.6019355676593188, rtol=1e-6)


def test_read_meps_ql_calculation() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "ql" in model.data
    assert model.data["ql"].shape == (1, 65)
    assert_allclose(model.data["ql"][0, 0], 0.0, atol=1e-10)
    assert_allclose(model.data["ql"][0, 3], 5.1684870e-09, rtol=1e-6)


def test_read_meps_hydrometeor_variables() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "qi" in model.data
    assert "qs" in model.data
    assert "qr" in model.data
    assert "qg" in model.data
    assert model.data["qi"].shape == (1, 65)
    assert model.data["qs"].shape == (1, 65)
    assert model.data["qr"].shape == (1, 65)
    assert model.data["qg"].shape == (1, 65)


def test_read_meps_location_coordinates() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "latitude" in model.data
    assert "longitude" in model.data
    assert "horizontal_resolution" in model.data
    assert model.data["latitude"].shape == (1,)
    assert model.data["longitude"].shape == (1,)
    assert model.data["horizontal_resolution"].shape == (1,)
    assert_allclose(model.data["latitude"][0], 60.19546423, rtol=1e-6)
    assert_allclose(model.data["longitude"][0], 24.97593848, rtol=1e-6)
    assert_allclose(model.data["horizontal_resolution"][0], 2.5, rtol=1e-6)


def test_read_meps_model_level() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "model_level" in model.data
    assert model.data["model_level"].shape == (65,)


def test_read_meps_sources() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "air_temperature_ml" in model.sources.get("temperature", "")
    assert "specific_humidity_ml" in model.sources.get("q", "")
    assert "surface_air_pressure" in model.sources.get("sfc_pressure", "")
    assert "air_temperature_2m" in model.sources.get("sfc_temp_2m", "")
    assert "Calculated from" in model.sources.get("pressure", "")
    assert "Calculated from" in model.sources.get("ql", "")


def test_read_meps_wind_rotation() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "rotated by" in model.sources.get("uwind", "")
    assert "rotated by" in model.sources.get("vwind", "")
    assert "rotated by" in model.sources.get("sfc_wind_u_10m", "")
    assert "rotated by" in model.sources.get("sfc_wind_v_10m", "")


def test_read_meps_history() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert len(model.history) >= 1
    assert any("model-munger" in h for h in model.history)


def test_read_meps_sources_consistency() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert model.sources.get("tke") == "turbulent_kinetic_energy_ml"
    assert model.sources.get("cloud_fraction") == "cloud_area_fraction_ml"
    assert model.sources.get("temperature") == "air_temperature_ml"
    assert model.sources.get("q") == "specific_humidity_ml"


def test_read_meps_gust_wind() -> None:
    model = read_meps(
        "tests/data/20260901000000_kumpula_meps_sfc.nc",
        "tests/data/20260901000000_kumpula_meps_ml.nc",
        KUMPULA,
    )
    assert "sfc_uwind_gust_10m" in model.data
    assert "sfc_vwind_gust_10m" in model.data
    assert model.data["sfc_uwind_gust_10m"].shape == (1,)
    assert model.data["sfc_vwind_gust_10m"].shape == (1,)
