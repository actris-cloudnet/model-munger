import json
import sys

import netCDF4
import numpy as np
import pygrib

from model_munger.utils import LCC

if sys.argv[1] == "icon-d2":
    grbs = pygrib.open(
        "/home/tuomas/Downloads/icon-d2_germany_icosahedral_time-invariant_2026082700_000_0_clat.grib2"
    )
    lat = next(grbs).values
    grbs = pygrib.open(
        "/home/tuomas/Downloads/icon-d2_germany_icosahedral_time-invariant_2026082700_000_0_clon.grib2"
    )
    lon = next(grbs).values

    min_lat = lat[0]
    max_lat = lat[0]
    min_lon = lon[0]
    max_lon = lon[0]
    for i in range(1, len(lat)):
        min_lat = min(min_lat, lat[i])
        max_lat = max(max_lat, lat[i])
        min_lon = min(min_lon, lon[i])
        max_lon = max(max_lon, lon[i])
    min_lat = min_lat - 5
    max_lat = max_lat + 5
    min_lon = min_lon - 5
    max_lon = max_lon + 5

    def find_closest(my_lat, my_lon):
        closest_dist = None
        closest_lat = None
        closest_lon = None
        for i in range(len(lat)):
            dist = (lat[i] - my_lat) ** 2 + (lon[i] - my_lon) ** 2
            if closest_dist is None or dist < closest_dist:
                closest_lat = lat[i]
                closest_lon = lon[i]
                closest_dist = dist
        return closest_lat, closest_lon

    points = []
    nx = 2
    ny = 10
    for xi in np.linspace(min_lat, max_lat, nx):
        points.append(find_closest(xi, min_lon))
    for yi in np.linspace(min_lon, max_lon, ny):
        points.append(find_closest(max_lat, yi))
    for xi in np.linspace(max_lat, min_lat, nx):
        points.append(find_closest(xi, max_lon))
    for yi in np.linspace(max_lon, min_lon, ny):
        points.append(find_closest(min_lat, yi))
    print(json.dumps([[round(lat, 3), round(lon, 3)] for lat, lon in points]))
    exit()
if sys.argv[1] == "arome":
    grbs = pygrib.open("arome.grib")
    grb = next(grbs)

    is_valid = np.ravel(~np.ma.getmaskarray(grb.values))
    lat = grb.latitudes[is_valid]
    lon = grb.longitudes[is_valid]

    min_lat = lat[0]
    max_lat = lat[0]
    min_lon = lon[0]
    max_lon = lon[0]
    for i in range(1, len(lat)):
        min_lat = min(min_lat, lat[i])
        max_lat = max(max_lat, lat[i])
        min_lon = min(min_lon, lon[i])
        max_lon = max(max_lon, lon[i])
    min_lat = min_lat - 5
    max_lat = max_lat + 5
    min_lon = min_lon - 5
    max_lon = max_lon + 5

    def find_closest(my_lat, my_lon):
        closest_dist = None
        closest_lat = None
        closest_lon = None
        for i in range(len(lat)):
            dist = (lat[i] - my_lat) ** 2 + (lon[i] - my_lon) ** 2
            if closest_dist is None or dist < closest_dist:
                closest_lat = lat[i]
                closest_lon = lon[i]
                closest_dist = dist
        return closest_lat, closest_lon

    points = []
    nx = 2
    ny = 10
    for xi in np.linspace(min_lat, max_lat, nx):
        points.append(find_closest(xi, min_lon))
    for yi in np.linspace(min_lon, max_lon, ny):
        points.append(find_closest(max_lat, yi))
    for xi in np.linspace(max_lat, min_lat, nx):
        points.append(find_closest(xi, max_lon))
    for yi in np.linspace(max_lon, min_lon, ny):
        points.append(find_closest(min_lat, yi))

    points_unique = []
    for lat, lon in points:
        p = round(lat, 3), round(lon, 3)
        if p not in points_unique:
            points_unique.append(p)
    print(json.dumps(points_unique))
    exit()
if sys.argv[1] == "arome-arctic":
    url = "https://thredds.met.no/thredds/dodsC/aromearcticarchive/2026/01/01/arome_arctic_det_sfc_20260101T00Z.ncml"
elif sys.argv[1] == "meps":
    url = "https://thredds.met.no/thredds/dodsC/meps25epsarchive/2026/01/01/meps_det_sfc_20260101T00Z.ncml"
with netCDF4.Dataset(url) as nc:
    x = nc["x"][:]
    y = nc["y"][:]
    lam = nc["projection_lambert"]
    bert = LCC(
        standard_parallel=lam.standard_parallel,
        origin_latitude=lam.latitude_of_projection_origin,
        central_meridian=lam.longitude_of_central_meridian,
        earth_radius=lam.earth_radius,
    )
    min_x = np.min(x)
    max_x = np.max(x)
    min_y = np.min(y)
    max_y = np.max(y)
    points = []
    nx = 10
    ny = 10
    for xi in np.linspace(min_x, max_x, nx):
        points.append(bert.inverse(xi, min_y))
    for yi in np.linspace(min_y, max_y, ny):
        points.append(bert.inverse(max_x, yi))
    for xi in np.linspace(max_x, min_x, nx):
        points.append(bert.inverse(xi, max_y))
    for yi in np.linspace(max_y, min_y, ny):
        points.append(bert.inverse(min_x, yi))
    print(json.dumps([[round(lat, 3), round(lon, 3)] for lat, lon in points]))
