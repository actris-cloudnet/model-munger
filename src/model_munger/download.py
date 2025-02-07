import datetime
import sys
import time
from pathlib import Path
from typing import Literal

import requests

SOURCES = {
    "ecmwf": "https://data.ecmwf.int/forecasts",
    "aws": "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
}


def download_ecmwf(
    date: datetime.date,
    run: Literal[0, 6, 12, 18],
    steps: list[int],
    directory: Path,
    source: Literal["ecmwf", "aws"],
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
    base_url = SOURCES[source]
    for step in steps:
        filename = f"{date_str}{run_str}0000-{step}h-{stream}-fc.grib2"
        path = directory / filename
        paths.append(path)
        if path.exists():
            continue
        url = f"{base_url}/{date_str}/{run_str}z/ifs/0p25/{stream}/{filename}"
        _download_file_with_retry(url, path)
    return paths


def _download_file_with_retry(url: str, out: Path):
    attempt = 0
    while True:
        try:
            _download_file(url, out)
            break
        except requests.HTTPError as e:
            print(
                f"Failed to download file on attempt {attempt+1}: {e}", file=sys.stderr
            )
            out.unlink(missing_ok=True)
            if attempt > 10:
                raise
            time.sleep(2**attempt)
        attempt += 1


def _download_file(url: str, out: Path):
    try:
        pending_output = False
        print_progress = sys.stdout.isatty()
        if not print_progress:
            print(f"Download {url}", file=sys.stderr)
        with requests.get(url, stream=True) as res:
            res.raise_for_status()
            total_bytes = res.headers.get("Content-Length")
            with out.open("wb") as f:
                if total_bytes is None:
                    f.write(res.content)
                else:
                    dl_bytes = 0
                    total_bytes_int = int(total_bytes)
                    for data in res.iter_content(chunk_size=4096):
                        dl_bytes += len(data)
                        f.write(data)
                        if print_progress:
                            percent = round(100 * dl_bytes / total_bytes_int)
                            print(
                                f"\r[{percent:3}%] {url}",
                                end="",
                                file=sys.stderr,
                                flush=True,
                            )
                            pending_output = True
    finally:
        if pending_output:
            print(file=sys.stderr)
