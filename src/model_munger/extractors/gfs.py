import datetime
from dataclasses import dataclass
from os import PathLike
from typing import Literal


@dataclass
class GfsIndex:
    number: int
    offset: int
    date: str
    param: str
    lvl: str
    fcst: str


def generate_gfs_url(
    date: datetime.date,
    run: Literal[0, 6, 12, 18],
    step: int,
    resolution: Literal["0p25", "0p5"],
    params: Literal["pgrb2", "pgrb2b"],
    extension: Literal["", ".idx"] = "",
) -> str:
    # base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
    base_url = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
    path = f"gfs.{date:%Y%m%d}/{run:02}/atmos"
    filename = f"gfs.t{run:02}z.{params}.{resolution}.f{step:03}{extension}"
    return f"{base_url}/{path}/{filename}"


def read_gfs_index(filename: str | PathLike) -> list[GfsIndex]:
    lvls = []
    with open(filename) as f:
        for line in f:
            parts = line.split(":")
            lvls.append(
                GfsIndex(
                    number=int(parts[0]),
                    offset=int(parts[1]),
                    date=parts[2],
                    param=parts[3],
                    lvl=parts[4],
                    fcst=parts[5],
                )
            )
    return lvls
