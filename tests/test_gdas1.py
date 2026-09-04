import datetime

from numpy.testing import assert_allclose

from model_munger.model import Location
from model_munger.readers.gdas1 import GDAS1, read_gdas1

KUMPULA = Location(id="kumpula", name="Kumpula")


def test_read_gdas1_basic() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert model.type == GDAS1
    assert model.location == KUMPULA
    assert len(model.data["time"]) == 8
    assert model.data["time"][0] == datetime.datetime(2026, 1, 1, 0, 0)
    assert model.data["time"][-1] == datetime.datetime(2026, 1, 1, 21, 0)
    assert len(model.data["forecast_time"]) == 8


def test_read_gdas1_profile_variables() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert model.data["temperature"].shape == (8, 23)
    assert model.data["pressure"].shape == (8, 23)
    assert model.data["uwind"].shape == (8, 23)
    assert model.data["vwind"].shape == (8, 23)
    assert model.data["rh"].shape == (8, 23)
    assert model.data["omega"].shape == (8, 23)
    assert model.data["q"].shape == (8, 23)
    assert model.data["height"].shape == (8, 23)
    assert model.data["wwind"].shape == (8, 23)
    assert_allclose(model.data["temperature"][0, 0], 266.624298, rtol=1e-6)
    assert_allclose(model.data["temperature"][0, -1], 197.869202, rtol=1e-6)
    assert_allclose(model.data["pressure"][0, 0], 100000.0, rtol=1e-6)
    assert_allclose(model.data["pressure"][0, -1], 2000.0, rtol=1e-6)
    assert model.data["pressure"].shape[0] == len(model.data["time"])


def test_read_gdas1_surface_variables() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert model.data["sfc_pressure"].shape == (8,)
    assert model.data["sfc_pressure_amsl"].shape == (8,)
    assert model.data["sfc_temp"].shape == (8,)
    assert model.data["sfc_temp_2m"].shape == (8,)
    assert model.data["sfc_rh_2m"].shape == (8,)
    assert model.data["sfc_wind_u_10m"].shape == (8,)
    assert model.data["sfc_wind_v_10m"].shape == (8,)
    assert model.data["sfc_cape"].shape == (8,)
    assert model.data["sfc_cin"].shape == (8,)
    assert model.data["sfc_bl_height"].shape == (8,)
    assert model.data["sfc_height"].shape == (8,)
    assert model.data["sfc_total_rain"].shape == (8,)
    assert_allclose(model.data["sfc_pressure"][0], 100319.9829, rtol=1e-6)
    assert_allclose(model.data["sfc_temp_2m"][0], 267.416199, rtol=1e-6)
    assert_allclose(model.data["sfc_rh_2m"][0], 0.683000, rtol=1e-6)
    assert_allclose(model.data["sfc_wind_u_10m"][0], 2.689220, rtol=1e-6)
    assert_allclose(model.data["sfc_wind_v_10m"][0], -4.421106, rtol=1e-6)


def test_read_gdas1_specific_humidity() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "q" in model.data
    assert "sfc_q_2m" in model.data
    assert_allclose(model.data["q"][0, 0], 0.0014348316, rtol=1e-6)
    assert_allclose(model.data["sfc_q_2m"][0], 0.0033800671, rtol=1e-6)
    assert "q" in model.comments
    assert "sfc_q_2m" in model.comments
    assert "Calculated from temperature, pressure and rh" in model.comments["q"]
    assert (
        "Calculated from sfc_temp, sfc_pressure and sfc_rh_2m"
        in model.comments["sfc_q_2m"]
    )
    assert "PRSS converted from hPa to Pa" in model.sources.get("sfc_pressure", "")
    assert "converted from hPa to Pa" in model.sources.get("sfc_pressure_amsl", "")


def test_read_gdas1_height_conversion() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert_allclose(model.data["height"][0, 0], 21.690778, rtol=1e-6)
    assert_allclose(model.data["height"][0, -1], 24796.129711, rtol=1e-6)
    assert_allclose(model.data["sfc_height"][0], 0.0, atol=1e-6)
    assert model.sources.get("height") == "HGTS converted from gpm to m"
    assert model.sources.get("sfc_height") == "SHGT converted from gpm to m"


def test_read_gdas1_categorical_variables() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "sfc_categorical_snow" in model.data
    assert "sfc_categorical_ice" in model.data
    assert "sfc_categorical_freezing_rain" in model.data
    assert "sfc_categorical_rain" in model.data
    assert model.data["sfc_categorical_snow"].shape == (8,)
    assert model.data["sfc_categorical_ice"].shape == (8,)
    assert model.data["sfc_categorical_freezing_rain"].shape == (8,)
    assert model.data["sfc_categorical_rain"].shape == (8,)


def test_read_gdas1_cloud_fraction() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "sfc_cloud_fraction" in model.data
    assert "sfc_cloud_fraction_low" in model.data
    assert "sfc_cloud_fraction_medium" in model.data
    assert "sfc_cloud_fraction_high" in model.data
    assert model.data["sfc_cloud_fraction"].shape == (8,)
    assert model.data["sfc_cloud_fraction_low"].shape == (8,)
    assert model.data["sfc_cloud_fraction_medium"].shape == (8,)
    assert model.data["sfc_cloud_fraction_high"].shape == (8,)


def test_read_gdas1_precipitation() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "sfc_total_rain" in model.data
    assert "sfc_conv_rain" in model.data
    assert model.data["sfc_total_rain"].shape == (8,)
    assert model.data["sfc_conv_rain"].shape == (8,)
    assert "converted from m to kg m-2" in model.sources.get("sfc_total_rain", "")


def test_read_gdas1_location_coordinates() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "latitude" in model.data
    assert "longitude" in model.data
    assert "horizontal_resolution" in model.data
    assert model.data["latitude"].shape == (8,)
    assert model.data["longitude"].shape == (8,)
    assert model.data["horizontal_resolution"].shape == (8,)
    assert_allclose(model.data["latitude"][0], 60.0, rtol=1e-6)
    assert_allclose(model.data["longitude"][0], 25.0, rtol=1e-6)


def test_read_gdas1_lifted_index() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "standard_lifted_index" in model.data
    assert "best_4layer_lifted_index" in model.data
    assert model.data["standard_lifted_index"].shape == (8,)
    assert model.data["best_4layer_lifted_index"].shape == (8,)


def test_read_gdas1_flux_variables() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "sfc_down_sens_heat_flx" in model.data
    assert "sfc_net_lat_heat_flx" in model.data
    assert "sfc_net_sw" in model.data
    assert "sfc_turb_mom_u" in model.data
    assert "sfc_turb_mom_v" in model.data
    assert model.data["sfc_down_sens_heat_flx"].shape == (8,)
    assert model.data["sfc_net_lat_heat_flx"].shape == (8,)
    assert model.data["sfc_net_sw"].shape == (8,)
    assert model.data["sfc_turb_mom_u"].shape == (8,)
    assert model.data["sfc_turb_mom_v"].shape == (8,)


def test_read_gdas1_history() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert len(model.history) >= 1
    assert any("model-munger" in h for h in model.history)


def test_read_gdas1_sources() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "TEMP" in model.sources.get("temperature", "")
    assert "UWND" in model.sources.get("uwind", "")
    assert "VWND" in model.sources.get("vwind", "")
    assert "RELH" in model.sources.get("rh", "")
    assert "PRSS" in model.sources.get("sfc_pressure", "")


def test_read_gdas1_rh_comment() -> None:
    model = read_gdas1("tests/data/20260101_kumpula_gdas1.nc", KUMPULA)
    assert "rh" in model.comments
    assert "sfc_rh_2m" in model.comments
    assert "With respect to water" in model.comments["rh"]
    assert "With respect to water" in model.comments["sfc_rh_2m"]
