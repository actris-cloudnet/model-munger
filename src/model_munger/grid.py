import numpy as np
import numpy.typing as npt

from model_munger.utils import EARTH_RADIUS


class RegularGrid:
    def __init__(
        self,
        nlat: int,
        nlon: int,
        first_lat: float,
        first_lon: float,
        last_lat: float,
        last_lon: float,
        delta_lat: float,
        delta_lon: float,
    ):
        self.nlat = nlat
        self.nlon = nlon
        self.first_lat = first_lat
        self.first_lon = first_lon
        self.last_lat = last_lat
        self.last_lon = last_lon
        self.delta_lat = delta_lat
        self.delta_lon = delta_lon

    def find_closest(
        self,
        latitudes: npt.ArrayLike,
        longitudes: npt.ArrayLike,
    ) -> tuple[
        npt.NDArray[np.intp],
        npt.NDArray[np.intp],
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
    ]:
        """Finds closest grid points to given coordinates.

        Args:
            latitudes: Latitudes (degrees).
            longitudes: Longitudes (degrees).

        Returns:
            Tuple with latitudinal indices, longitudinal indices, latitudes
            (degrees), longitudes (degrees) and horizontal resolutions (m) of
            the closest grid points.
        """
        latitudes = np.atleast_1d(latitudes)
        longitudes = np.atleast_1d(longitudes)

        i = (
            np.round((latitudes - self.first_lat) / self.delta_lat).astype(np.intp)
            % self.nlat
        )
        j = (
            np.round((longitudes - self.first_lon) / self.delta_lon).astype(np.intp)
            % self.nlon
        )
        closest_lat = self.first_lat + i * self.delta_lat
        closest_lon = self.first_lon + j * self.delta_lon
        closest_lon[closest_lon > 180] -= 360

        res = (
            np.radians(np.abs(self.delta_lon))
            * EARTH_RADIUS
            * np.cos(np.radians(closest_lat))
        )

        return i, j, closest_lat, closest_lon, res
