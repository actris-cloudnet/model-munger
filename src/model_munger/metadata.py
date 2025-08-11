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
        dimensions=("time",),
    ),
    "longitude": Metadata(
        units="degree_east",
        long_name="Longitude of model gridpoint",
        standard_name="longitude",
        dimensions=("time",),
    ),
    "forecast_time": Metadata(
        units="hours",
        long_name="Time since initialization of forecast",
        comment=(
            "For each profile in the file this variable contains the time\n"
            "elapsed since the initialization time of the forecast from which\n"
            "it was taken. Note that the profiles in this file may be taken\n"
            "from more than one forecast."
        ),
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
    "flux_level": Metadata(
        units="1",
        long_name="Flux level",
        standard_name="flux_level_number",
        axis="Z",
        positive="down",
        dimensions=("level",),
    ),
    "height": Metadata(
        units="m",
        long_name="Height above ground",
        standard_name="height",
        dimensions=("time", "level"),
    ),
    "horizontal_resolution": Metadata(
        long_name="Horizontal resolution of model", units="km", dimensions=("time",)
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
    "qs": Metadata(
        units="1",
        long_name="Gridbox-mean snow mixing ratio",
        standard_name="mass_fraction_of_snow_ice_in_air",
        dimensions=("time", "level"),
    ),
    "qr": Metadata(
        units="1",
        long_name="Gridbox-mean rain mixing ratio",
        standard_name="mass_fraction_of_rain_in_air",
        dimensions=("time", "level"),
    ),
    "qg": Metadata(
        units="1",
        long_name="Gridbox-mean graupel mixing ratio",
        standard_name="mass_fraction_of_graupel_in_air",
        dimensions=("time", "level"),
    ),
    "qh": Metadata(
        units="1",
        long_name="Gridbox-mean hail mixing ratio",
        standard_name="mass_fraction_of_hail_in_air",
        dimensions=("time", "level"),
    ),
    "NL": Metadata(
        units="kg-1",
        long_name="Liquid water droplet number concentration",
        dimensions=("time", "level"),
    ),
    "NI": Metadata(
        units="kg-1",
        long_name="Ice particle number concentration",
        dimensions=("time", "level"),
    ),
    "NS": Metadata(
        units="kg-1",
        long_name="Snow particle number concentration",
        dimensions=("time", "level"),
    ),
    "NR": Metadata(
        units="kg-1",
        long_name="Rain drop number concentration",
        dimensions=("time", "level"),
    ),
    "NG": Metadata(
        units="kg-1",
        long_name="Graupel number concentration",
        dimensions=("time", "level"),
    ),
    "NH": Metadata(
        units="kg-1",
        long_name="Hail number concentration",
        dimensions=("time", "level"),
    ),
    "NI_act": Metadata(
        units="kg-1",
        long_name="Activated ice nuclei number concentration",
        dimensions=("time", "level"),
    ),
    "q_diag": Metadata(
        units="1",
        long_name="Total specific humidity (diagnostic)",
        dimensions=("time", "level"),
    ),
    "ql_diag": Metadata(
        units="1",
        long_name="Total specific liquid water (diagnostic)",
        dimensions=("time", "level"),
    ),
    "qi_diag": Metadata(
        units="1",
        long_name="Total specific ice water (diagnostic)",
        dimensions=("time", "level"),
    ),
    "ls_cloud_fraction": Metadata(
        units="1",
        long_name="Large scale cloud fraction",
        standard_name="large_scale_cloud_area_fraction",
        dimensions=("time", "level"),
    ),
    "conv_cloud_fraction": Metadata(
        units="1",
        long_name="Convective cloud fraction",
        standard_name="convective_cloud_area_fraction",
        dimensions=("time", "level"),
    ),
    "cloud_fraction": Metadata(
        units="1",
        long_name="Cloud fraction",
        standard_name="cloud_area_fraction",
        dimensions=("time", "level"),
    ),
    "tke": Metadata(
        units="J m-2",
        long_name="Turbulent kinetic energy",
        dimensions=("time", "level"),
    ),
    "turb_mom_coeff": Metadata(
        units="m2 s-1",
        long_name="Turbulent diffusion coefficients for momentum",
        dimensions=("time", "level"),
    ),
    "turb_heat_coeff": Metadata(
        units="m2 s-1",
        long_name="Turbulent diffusion coefficients for heat",
        dimensions=("time", "level"),
    ),
    "ozone": Metadata(
        units="1",
        long_name="Grid-box mean ozone mixing ratio",
        dimensions=("time", "level"),
    ),
    "mass_flux_up": Metadata(
        units="kg m-2 s-1",
        long_name="Mean updraft mass flux",
        dimensions=("time", "level"),
    ),
    "mass_flux_down": Metadata(
        units="kg m-2 s-1",
        long_name="Mean downdraft mass flux",
        dimensions=("time", "level"),
    ),
    "detrainment_rate_up": Metadata(
        units="kg m-3 s-1",
        long_name="Mean updraft detrainment rate",
        dimensions=("time", "level"),
    ),
    "detrainment_rate_down": Metadata(
        units="kg m-3 s-1",
        long_name="Mean downdraft detrainment rate",
        dimensions=("time", "level"),
    ),
    "total_precipitation_flux": Metadata(
        units="kg m-2 s-1",
        long_name="Mean total precipitation flux",
        dimensions=("time", "level"),
    ),
    "flx_net_sw": Metadata(
        units="W m-2",
        long_name="Net shortwave flux",
        standard_name="net_downward_shortwave_flux_in_air",
        dimensions=("time", "level"),
    ),
    "flx_net_lw": Metadata(
        units="W m-2",
        long_name="Net longwave flux",
        standard_name="net_downward_longwave_flux_in_air",
        dimensions=("time", "level"),
    ),
    "flx_down_sw": Metadata(
        units="W m-2",
        long_name="Downwelling shortwave flux",
        standard_name="downwelling_shortwave_flux_in_air",
        dimensions=("time", "level"),
    ),
    "flx_down_lw": Metadata(
        units="W m-2",
        long_name="Downwelling longwave flux",
        standard_name="downwelling_longwave_flux_in_air",
        dimensions=("time", "level"),
    ),
    "flx_down_sw_cs": Metadata(
        units="W m-2",
        long_name="Downwelling clear sky shortwave flux",
        dimensions=("time", "level"),
    ),
    "flx_down_lw_cs": Metadata(
        units="W m-2",
        long_name="Downwelling clear sky longwave flux",
        dimensions=("time", "level"),
    ),
    "flx_down_sens_heat": Metadata(
        units="W m-2",
        long_name="Sensible heat flux",
        dimensions=("time", "level"),
    ),
    "flx_turb_moist": Metadata(
        units="kg m-2 s-1",
        long_name="Turbulent moisture heat flux",
        dimensions=("time", "level"),
    ),
    "flx_ls_rain": Metadata(
        units="kg m-2 s-1",
        long_name="Large-scale rainfall flux",
        standard_name="large_scale_rainfall_flux",
        dimensions=("time", "level"),
    ),
    "flx_ls_snow": Metadata(
        units="kg m-2 s-1",
        long_name="Large-scale snowfall flux",
        standard_name="large_scale_snowfall_flux",
        dimensions=("time", "level"),
    ),
    "flx_graupel_rain": Metadata(
        units="kg m-2 s-1",
        long_name="Large-scale graupel flux",
        standard_name="large_scale_graupel_flux",
        dimensions=("time", "level"),
    ),
    "flx_conv_rain": Metadata(
        units="kg m-2 s-1",
        long_name="Convective rainfall flux",
        standard_name="convective_rainfall_flux",
        dimensions=("time", "level"),
    ),
    "flx_conv_snow": Metadata(
        units="kg m-2 s-1",
        long_name="Convective snowfall flux",
        standard_name="convective_snowfall_flux",
        dimensions=("time", "level"),
    ),
    "flx_turb_mom_u": Metadata(
        units="kg m-1 s-2",
        long_name="Zonal turbulent momentum flux",
        standard_name="downward_eastward_momentum_flux_in_air",
        dimensions=("time", "level"),
    ),
    "flx_turb_mom_v": Metadata(
        units="kg m-1 s-2",
        long_name="Meridional turbulent momentum flux",
        standard_name="downward_northward_momentum_flux_in_air",
        dimensions=("time", "level"),
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
    "sfc_geopotential": Metadata(
        units="m2 s-2",
        long_name="Geopotential",
        standard_name="geopotential",
        dimensions=("time",),
    ),
    "sfc_height": Metadata(
        units="m",
        long_name="Surface height",
        standard_name="height_above_mean_sea_level",
        dimensions=("time",),
    ),
    "sfc_net_sw": Metadata(
        units="W m-2",
        long_name="Surface net downward shortwave flux",
        standard_name="surface_net_downward_shortwave_flux",
        dimensions=("time",),
    ),
    "sfc_net_sw_cs": Metadata(
        units="W m-2",
        long_name="Surface net clear sky downward shortwave flux",
        dimensions=("time",),
    ),
    "sfc_net_lw": Metadata(
        units="W m-2",
        long_name="Surface net downward longwave flux",
        standard_name="surface_net_downward_longwave_flux",
        dimensions=("time",),
    ),
    "sfc_net_lw_cs": Metadata(
        units="W m-2",
        long_name="Clear sky net downward longwave flux",
        dimensions=("time",),
    ),
    "sfc_net_lat_heat_flx": Metadata(
        units="W m-2",
        long_name="Net latent heat flux at the surface",
        dimensions=("time",),
    ),
    "sfc_up_sw": Metadata(
        units="W m-2",
        long_name="Surface upwelling shortwave flux",
        standard_name="surface_upwelling_shortwave_flux",
        dimensions=("time",),
    ),
    "sfc_up_sw_diffuse": Metadata(
        units="W m-2",
        long_name="Surface diffuse upwelling shortwave flux",
        dimensions=("time",),
    ),
    "sfc_up_lw": Metadata(
        units="W m-2",
        long_name="Surface upwelling longwave flux",
        standard_name="surface_upwelling_longwave_flux",
        dimensions=("time",),
    ),
    "sfc_up_lw_cs": Metadata(
        units="W m-2",
        long_name="Clear sky upwelling longwave flux",
        standard_name="surface_upwelling_longwave_flux_in_air_assuming_clear_sky",
        dimensions=("time",),
    ),
    "sfc_down_sw": Metadata(
        units="W m-2",
        long_name="Surface downwelling shortwave flux",
        standard_name="surface_downwelling_shortwave_flux",
        dimensions=("time",),
    ),
    "sfc_down_sw_diffuse": Metadata(
        units="W m-2",
        long_name="Surface diffuse downwelling shortwave flux",
        standard_name="surface_diffuse_downwelling_shortwave_flux_in_air",
        dimensions=("time",),
    ),
    "sfc_down_sw_direct": Metadata(
        units="W m-2",
        long_name="Surface direct downwelling shortwave flux",
        standard_name="surface_direct_downwelling_shortwave_flux_in_air",
        dimensions=("time",),
    ),
    "sfc_down_sw_cs": Metadata(
        units="W m-2",
        long_name="Surface clear sky downwelling shortwave flux",
        standard_name="surface_downwelling_shortwave_flux_in_air_assuming_clear_sky",
        dimensions=("time",),
    ),
    "sfc_down_sw_direct_normal": Metadata(
        units="W m-2",
        long_name="Surface direct normal downwelling shortwave flux",
        dimensions=("time",),
    ),
    "sfc_down_lw": Metadata(
        units="W m-2",
        long_name="Surface downwelling longwave flux",
        standard_name="surface_downwelling_longwave_flux",
        dimensions=("time",),
    ),
    "sfc_down_lw_cs": Metadata(
        units="W m-2",
        long_name="Surface clear sky downwelling longwave flux",
        standard_name="surface_downwelling_longwave_flux_in_air_assuming_clear_sky",
        dimensions=("time",),
    ),
    "toa_net_sw": Metadata(
        units="W m-2",
        long_name="Top of atmosphere net downward shortwave flux",
        dimensions=("time",),
    ),
    "toa_net_sw_cs": Metadata(
        units="W m-2",
        long_name="Top of atmosphere net clear sky downward shortwave flux",
        dimensions=("time",),
    ),
    "toa_net_lw": Metadata(
        units="W m-2",
        long_name="Top of atmosphere net downward longwave flux",
        dimensions=("time",),
    ),
    "toa_net_lw_cs": Metadata(
        units="W m-2",
        long_name="Top of atmosphere net clear sky downward longwave flux",
        dimensions=("time",),
    ),
    "toa_down_sw": Metadata(
        units="W m-2",
        long_name="Top of atmosphere downwelling shortwave flux",
        dimensions=("time",),
    ),
    "toa_up_sw": Metadata(
        units="W m-2",
        long_name="Top of atmosphere upwelling shortwave flux",
        dimensions=("time",),
    ),
    "toa_up_lw": Metadata(
        units="W m-2",
        long_name="Top of atmosphere upwelling longwave flux",
        dimensions=("time",),
    ),
    "toa_up_lw_cs": Metadata(
        units="W m-2",
        long_name="Top of atmosphere upwelling clear sky longwave flux",
        dimensions=("time",),
    ),
    "toa_brightness_temperature": Metadata(
        units="K",
        long_name="Top of atmosphere brightness temperature",
        standard_name="toa_brightness_temperature",
        dimensions=("time",),
    ),
    "sfc_down_lat_heat_flx": Metadata(
        units="W m-2",
        long_name="Latent heat flux",
        standard_name="surface_downward_latent_heat_flux",
        dimensions=("time",),
    ),
    "sfc_down_sens_heat_flx": Metadata(
        units="W m-2",
        long_name="Sensible heat flux",
        standard_name="surface_downward_sensible_heat_flux",
        dimensions=("time",),
    ),
    "sfc_ls_rain": Metadata(
        units="kg m-2",
        long_name="Large-scale rainfall amount",
        standard_name="large_scale_rainfall_amount",
        dimensions=("time",),
    ),
    "sfc_ls_snow": Metadata(
        units="kg m-2",
        long_name="Large-scale snowfall amount",
        standard_name="large_scale_snowfall_amount",
        dimensions=("time",),
    ),
    "sfc_ls_graupel": Metadata(
        units="kg m-2",
        long_name="Large-scale graupel amount",
        standard_name="stratiform_graupel_fall_amount",
        dimensions=("time",),
    ),
    "sfc_ls_hail": Metadata(
        units="kg m-2",
        long_name="Large-scale hail amount",
        standard_name="hail_fall_amount",
        dimensions=("time",),
    ),
    "sfc_ls_rainrate": Metadata(
        units="kg m-2 s-1",
        long_name="Large-scale rainfall intensity",
        dimensions=("time",),
    ),
    "sfc_ls_snowrate": Metadata(
        units="kg m-2 s-1",
        long_name="Large-scale snowfall intensity",
        dimensions=("time",),
    ),
    "sfc_ls_graupelrate": Metadata(
        units="kg m-2 s-1",
        long_name="Large-scale graupel intensity",
        dimensions=("time",),
    ),
    "sfc_conv_rain": Metadata(
        units="kg m-2",
        long_name="Convective rainfall amount",
        standard_name="convective_rainfall_amount",
        dimensions=("time",),
    ),
    "sfc_conv_snow": Metadata(
        units="kg m-2",
        long_name="Convective snowfall amount",
        standard_name="convective_snowfall_amount",
        dimensions=("time",),
    ),
    "sfc_total_rain": Metadata(
        units="kg m-2",
        long_name="Total rainfall amount",
        dimensions=("time",),
    ),
    "sfc_total_snow": Metadata(
        units="kg m-2",
        long_name="Total snowfall amount",
        dimensions=("time",),
    ),
    "sfc_ls_precip_fraction": Metadata(
        units="1",
        long_name="Large-scale precipitation fraction",
        dimensions=("time",),
    ),
    "sfc_cloud_fraction": Metadata(
        units="1",
        long_name="Surface total cloud fraction",
        dimensions=("time",),
    ),
    "sfc_cloud_fraction_low": Metadata(
        units="1",
        long_name="Surface cloud fraction (low clouds)",
        dimensions=("time",),
    ),
    "sfc_cloud_fraction_medium": Metadata(
        units="1",
        long_name="Surface cloud fraction (mid-level clouds)",
        dimensions=("time",),
    ),
    "sfc_cloud_fraction_high": Metadata(
        units="1",
        long_name="Surface cloud fraction (high clouds)",
        dimensions=("time",),
    ),
    "sfc_conv_cloud_fraction": Metadata(
        units="1",
        long_name="Surface convective cloud fraction",
        dimensions=("time",),
    ),
    "sfc_bl_height": Metadata(
        units="m",
        long_name="Boundary layer height",
        dimensions=("time",),
    ),
    "sfc_bl_dissipation": Metadata(
        units="J m-2",
        long_name="Boundary layer height",
        dimensions=("time",),
    ),
    "sfc_cloud_base_height": Metadata(
        units="m",
        long_name="Cloud base height",
        dimensions=("time",),
    ),
    "sfc_albedo": Metadata(
        units="1",
        long_name="Surface albedo",
        standard_name="surface_albedo",
        dimensions=("time",),
    ),
    "sfc_albedo_snow": Metadata(
        units="1",
        long_name="Surface albedo of snow",
        dimensions=("time",),
    ),
    "sfc_albedo_lw_direct": Metadata(
        units="1",
        long_name="Surface albedo (longwave direct)",
        dimensions=("time",),
    ),
    "sfc_albedo_lw_diffuse": Metadata(
        units="1",
        long_name="Surface albedo (longwave diffuse)",
        dimensions=("time",),
    ),
    "sfc_albedo_sw_direct": Metadata(
        units="1",
        long_name="Surface albedo (shortwavewave direct)",
        dimensions=("time",),
    ),
    "sfc_albedo_sw_diffuse": Metadata(
        units="1",
        long_name="Surface albedo (shortwave diffuse)",
        dimensions=("time",),
    ),
    "sfc_temp": Metadata(
        units="K",
        long_name="Surface temperature",
        dimensions=("time",),
    ),
    "sfc_skin_temp": Metadata(
        units="K",
        long_name="Surface skin temperature",
        dimensions=("time",),
    ),
    "sfc_temp_2m": Metadata(
        units="K",
        long_name="Temperature at 2m",
        dimensions=("time",),
    ),
    "sfc_dewpoint_temp_2m": Metadata(
        units="K",
        long_name="Dew point temperature at 2m",
        dimensions=("time",),
    ),
    "sfc_rh_2m": Metadata(
        units="1",
        long_name="Relative humidity at 2m",
        dimensions=("time",),
    ),
    "sfc_q_2m": Metadata(
        units="1",
        long_name="Specific humidity at 2m",
        dimensions=("time",),
    ),
    "sfc_rough_mom": Metadata(
        units="m",
        long_name="Surface roughness for momentum",
        dimensions=("time",),
    ),
    "sfc_rough_heat": Metadata(
        units="m",
        long_name="Surface roughness for heat",
        dimensions=("time",),
    ),
    "sfc_rough_oro": Metadata(
        units="m",
        long_name="Surface roughness for orography",
        dimensions=("time",),
    ),
    "sfc_friction_velocity": Metadata(
        units="m s-1",
        long_name="Surface friction velocity",
        dimensions=("time",),
    ),
    "sfc_roughness_length": Metadata(
        units="m",
        long_name="Surface roughness length",
        dimensions=("time",),
    ),
    "sfc_drag_coefficient": Metadata(
        units="1",
        long_name="Surface drag coefficient",
        dimensions=("time",),
    ),
    "sfc_temp_snow": Metadata(
        units="K",
        long_name="Surface snow temperature",
        dimensions=("time",),
    ),
    "sfc_snow_density": Metadata(
        units="kg m-3",
        long_name="Surface snow density",
        dimensions=("time",),
    ),
    "sfc_emissivity": Metadata(
        units="1",
        long_name="Surface emissivity",
        dimensions=("time",),
    ),
    "sfc_dissipation": Metadata(
        units="W n-2",
        long_name="Surface dissipation",
        dimensions=("time",),
    ),
    "sfc_soil_moisture": Metadata(
        units="1",
        long_name="Surface soil moisture content",
        dimensions=("time",),
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
    "sfc_wind_gust_10m": Metadata(
        long_name="Wind gust at 10 m",
        units="m s-1",
        dimensions=("time",),
    ),
    "sfc_uwind_gust_10m": Metadata(
        long_name="Zonal wind gust at 10 m",
        units="m s-1",
        dimensions=("time",),
    ),
    "sfc_wwind_gust_10m": Metadata(
        long_name="Meridional wind gust at 10 m",
        units="m s-1",
        dimensions=("time",),
    ),
    "sfc_turb_mom_u": Metadata(
        units="kg m-1 s-2",
        long_name="Surface zonal turbulent momentum flux",
        dimensions=("time",),
    ),
    "sfc_turb_mom_v": Metadata(
        units="kg m-1 s-2",
        long_name="Surface meridional turbulent momentum flux",
        dimensions=("time",),
    ),
    "sfc_eastward_stress": Metadata(
        units="Pa",
        long_name="Surface zonal stress",
        standard_name="surface_downward_eastward_stress",
        dimensions=("time",),
    ),
    "sfc_northward_stress": Metadata(
        units="Pa",
        long_name="Surface meridional stress",
        standard_name="surface_downward_northward_stress",
        dimensions=("time",),
    ),
    "sfc_bt": Metadata(
        units="K",
        long_name="Surface brightness temperature",
        dimensions=("time",),
    ),
    "sfc_global_rad": Metadata(
        units="kg m-2 s-1",
        long_name="Surface global radiation",
        dimensions=("time",),
    ),
    "sfc_lw_heating": Metadata(
        units="kg m-2 s-1",
        long_name="Surface longwave heating",
        dimensions=("time",),
    ),
    "sfc_solar_heating": Metadata(
        units="kg m-2 s-1",
        long_name="Surface solar heating",
        dimensions=("time",),
    ),
    "sfc_conv_heat": Metadata(
        units="kg m-2 s-1",
        long_name="Surface convective heating",
        dimensions=("time",),
    ),
    "sfc_conv_moist": Metadata(
        units="kg m-2 s-1",
        long_name="Surface convective moistening",
        dimensions=("time",),
    ),
    "sfc_vert_diff_accel": Metadata(
        units="kg m-2 s-1",
        long_name="Surface vertical diffusion of acceleration",
        dimensions=("time",),
    ),
    "sfc_vert_diff_moist": Metadata(
        units="kg m-2 s-1",
        long_name="Surface vertical diffusion of moisture",
        dimensions=("time",),
    ),
    "sfc_vert_diff_heat": Metadata(
        units="kg m-2 s-1",
        long_name="Surface vertical diffusion of heat",
        dimensions=("time",),
    ),
    "sfc_visibility": Metadata(
        units="m",
        long_name="Surface visibility",
        dimensions=("time",),
    ),
    "sfc_weg_snow": Metadata(
        units="m",
        long_name="Surface water equivalent snow depth",
        dimensions=("time",),
    ),
    "sfc_qs": Metadata(
        units="1",
        long_name="Gridbox-mean snow mixing ratio at surface",
        dimensions=("time",),
    ),
    "sfc_qg": Metadata(
        units="1",
        long_name="Gridbox-mean graupel mixing ratio at surface",
        dimensions=("time",),
    ),
    "total_column_water_vapour": Metadata(
        units="kg m-2",
        long_name="Total column water vapour",
        dimensions=("time",),
    ),
    "total_column_water": Metadata(
        units="kg m-2",
        long_name="Total column water",
        dimensions=("time",),
    ),
    "total_column_liquid": Metadata(
        units="kg m-2",
        long_name="Total column liquid water",
        dimensions=("time",),
    ),
    "total_column_sc_liquid": Metadata(
        units="kg m-2",
        long_name="Total column supercooled liquid water",
        dimensions=("time",),
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
    "sfc_cape": Metadata(
        units="J kg-1",
        long_name="Convective available potential energy (CAPE)",
        standard_name="atmosphere_convective_available_potential_energy_wrt_surface",
        dimensions=("time",),
    ),
    "sfc_cin": Metadata(
        units="J kg-1",
        long_name="Convective inhibition (CIN)",
        standard_name="atmosphere_convective_inhibition_wrt_surface",
        dimensions=("time",),
    ),
    "standard_lifted_index": Metadata(
        units="K", long_name="Standard lifted index", dimensions=("time",)
    ),
    "best_4layer_lifted_index": Metadata(
        units="K", long_name="Best 4-layer lifted index", dimensions=("time",)
    ),
    "sfc_categorical_snow": Metadata(
        units="1", long_name="Categorical snow", dimensions=("time",)
    ),
    "sfc_categorical_ice": Metadata(
        units="1", long_name="Categorical ice", dimensions=("time",)
    ),
    "sfc_categorical_freezing_rain": Metadata(
        units="1", long_name="Categorical freezing rain", dimensions=("time",)
    ),
    "sfc_categorical_rain": Metadata(
        units="1", long_name="Categorical rain", dimensions=("time",)
    ),
}
