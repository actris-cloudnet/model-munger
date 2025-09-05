from model_munger.grid import RegularGrid


def test_gdas1_grid() -> None:
    grid = RegularGrid(181, 360, -90.0, 0.0, 90.0, -1.0, 1.0, 1.0)
    idx, lat, lon, res = grid.find_closest(-89.9, 0.1)
    assert idx == 0
    assert lat == -90
    assert lon == 0


def test_ecmwf_open_grid() -> None:
    grid = RegularGrid(721, 1440, 90.0, 180.0, -90.0, 179.75, -0.25, 0.25)
    idx, lat, lon, res = grid.find_closest(89.9, 179.9)
    assert idx == 0
    assert lat == 90
    assert lon == 180
