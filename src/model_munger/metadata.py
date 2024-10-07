from dataclasses import dataclass


@dataclass(frozen=True)
class Metadata:
    units: str
    long_name: str
    dimensions: tuple[str, ...] = ()
    standard_name: str | None = None
    comment: str | None = None


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
    "height": Metadata(
        units="m",
        long_name="Height above ground",
        dimensions=("time", "level"),
        comment="Calculated from geopotential height",
    ),
}
