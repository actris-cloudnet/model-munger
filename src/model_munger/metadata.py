from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Metadata:
    units: str
    long_name: str
    dimensions: tuple[str, ...] = ()
    standard_name: str | None = None
    comment: str | None = None
    axis: Literal["X", "Y", "Z", "T"] | None = None
    positive: Literal["up", "down"] | None = None


ATTRIBUTES = {
    "latitude": Metadata(
        units="degree_north",
        long_name="Latitude of model gridpoint",
        standard_name="latitude",
    ),
    "longitude": Metadata(
        units="degree_east",
        long_name="Longitude of model gridpoint",
        standard_name="longitude",
    ),
    "forecast_time": Metadata(
        units="hours",
        long_name="Time since initialization of forecast",
        comment="For each profile in the file this variable contains the time elapsed since the initialization time of the forecast from which it was taken. Note that the profiles in this file may be taken from more than one forecast.",
        dimensions=("time",),
    ),
    "model_level": Metadata(
        units="1",
        long_name="Model level",
        standard_name="model_level_number",
        axis="Z",
        positive="down",
        dimensions=("level",),
    ),
    "horizontal_resolution": Metadata(
        long_name="Horizontal resolution of model",
        units="km",
    ),
    "sfc_pressure": Metadata(
        units="Pa",
        long_name="Surface pressure",
        standard_name="surface_air_pressure",
        dimensions=("time",),
    ),
    "sfc_pressure_amsl": Metadata(
        long_name="Surface pressure at mean sea level",
        units="Pa",
        dimensions=("time",),
    ),
    "sfc_temp_2m": Metadata(
        units="K", long_name="Temperature at 2m", dimensions=("time",)
    ),
    "sfc_dewpoint_temp_2m": Metadata(
        units="K", long_name="Dew point temperature at 2m", dimensions=("time",)
    ),
    "sfc_wind_u_10m": Metadata(
        long_name="Zonal wind at 10 m",
        units="m s-1",
        dimensions=("time",),
    ),
    "sfc_wind_v_10m": Metadata(
        long_name="Meridional wind at 10 m",
        units="m s-1",
        dimensions=("time",),
    ),
    "pressure": Metadata(
        units="Pa",
        long_name="Pressure",
        standard_name="air_pressure",
        dimensions=("time", "level"),
    ),
    "temperature": Metadata(
        units="K",
        long_name="Temperature",
        standard_name="air_temperature",
        dimensions=("time", "level"),
    ),
    "uwind": Metadata(
        units="m s-1",
        long_name="Zonal wind",
        standard_name="eastward_wind",
        dimensions=("time", "level"),
    ),
    "vwind": Metadata(
        units="m s-1",
        long_name="Meridional wind",
        standard_name="northward_wind",
        dimensions=("time", "level"),
    ),
    "wwind": Metadata(
        units="m s-1",
        long_name="Vertical wind",
        standard_name="upward_air_velocity",
        dimensions=("time", "level"),
        comment="The vertical wind has been calculated from omega (Pa s-1), height and pressure using: w=omega*dz/dp",
    ),
    "omega": Metadata(
        units="Pa s-1",
        long_name="Vertical wind in pressure coordinates",
        standard_name="omega",
        dimensions=("time", "level"),
    ),
    "rh": Metadata(
        units="1",
        long_name="Relative humidity",
        standard_name="relative_humidity",
        dimensions=("time", "level"),
        comment="With respect to liquid above 0 degrees C and with respect to ice below 0 degrees C. Calculated using Goff-Gratch formula.",
    ),
    "q": Metadata(
        units="1",
        long_name="Specific humidity",
        standard_name="specific_humidity",
        dimensions=("time", "level"),
    ),
    "ql": Metadata(
        units="1",
        long_name="Gridbox-mean liquid water mixing ratio",
        standard_name="mass_fraction_of_cloud_liquid_water_in_air",
        dimensions=("time", "level"),
    ),
    "qi": Metadata(
        units="1",
        long_name="Gridbox-mean ice water mixing ratio",
        standard_name="mass_fraction_of_cloud_ice_in_air",
        dimensions=("time", "level"),
    ),
    "sfc_geopotential": Metadata(
        units="m2 s-2",
        long_name="Geopotential",
        standard_name="geopotential",
        dimensions=("time",),
    ),
    "height": Metadata(
        units="m",
        long_name="Height above ground",
        standard_name="height",
        dimensions=("time", "level"),
    ),
    "cloud_fraction": Metadata(
        units="1",
        long_name="Cloud fraction",
        standard_name="cloud_area_fraction",
        dimensions=("time", "level"),
    ),
    "soil_depth": Metadata(
        units="m",
        long_name="Depth below ground",
        standard_name="depth",
        dimensions=("time", "soil_level"),
    ),
    "soil_temperature": Metadata(
        units="K",
        long_name="Soil temperature",
        dimensions=("time", "soil_level"),
    ),
    "soil_moisture": Metadata(
        units="m3 m-3",
        long_name="Soil moisture content",
        dimensions=("time", "soil_level"),
    ),
    "sfc_land_cover": Metadata(
        units="1",
        long_name="Land cover",
        standard_name="land_area_fraction",
        dimensions=("time",),
    ),
}
