import datetime
from pathlib import Path
import sys
from typing import Literal
import requests


def download_ecmwf(
    date: datetime.date, run: Literal[0, 6, 12, 18], directory: Path
) -> list[Path]:
    """Download ECMWF high-resolution forecast model (open data subset).

    Args:
        date: Forecast date (UTC)
        run: Forecast run (0, 6, 12 or 18 UTC hour)
        directory: Directory to save downloaded files.

    Returns:
        Paths to downloaded files
    """
    date_str = date.strftime("%Y%m%d")
    run_str = str(run).zfill(2)
    stream = "oper" if run in (0, 12) else "scda"
    paths = []
    for hour in range(run, 25, 3):
        filename = f"{date_str}{run_str}0000-{hour}h-{stream}-fc.grib2"
        path = directory / filename
        paths.append(path)
        if path.exists():
            continue
        url = f"https://data.ecmwf.int/forecasts/{date_str}/{run_str}z/ifs/0p25/{stream}/{filename}"
        _download_file(url, path)
    return paths


def _download_file(url: str, out: Path):
    with out.open("wb") as f, requests.get(url, stream=True) as res:
        res.raise_for_status()
        total_bytes = res.headers.get("Content-Length")
        if total_bytes is None:
            f.write(res.content)
        else:
            dl_bytes = 0
            total_bytes_int = int(total_bytes)
            for data in res.iter_content(chunk_size=4096):
                dl_bytes += len(data)
                f.write(data)
                percent = round(100 * dl_bytes / total_bytes_int)
                print(f"\r[{percent:3}%] {url}", end="", file=sys.stderr, flush=True)
    print(file=sys.stderr)
