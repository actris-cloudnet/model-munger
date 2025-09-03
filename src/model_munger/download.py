import datetime
import email.utils
import os
import sys
import time
from pathlib import Path

import requests


def download_file(
    url: str, outdir: Path, retries: int = 10, revalidate: bool = False
) -> Path:
    """Downloads a file from a URL with cache and retry logic.

    Args:
        url: The URL from which to download the file.
        outdir: The local filesystem path where the downloaded file will be saved.
        retries: Maximum number of retry attempts on failure.
        revalidate: If True, the cached file is revalidated based on
            modification time. Defaults to False.

    Raises:
        requests.HTTPError: If the download fails after all retries.
    """
    filename = url.rsplit("/", maxsplit=1)[-1]
    out = outdir / filename
    attempt = 0
    while True:
        try:
            _download_file(url, out, revalidate)
            break
        except requests.HTTPError as e:
            print(
                f"Failed to download file on attempt {attempt + 1}: {e}",
                file=sys.stderr,
            )
            out.unlink(missing_ok=True)
            if attempt >= retries:
                raise
            time.sleep(2**attempt)
        attempt += 1
    return out


def _download_file(url: str, out: Path, revalidate: bool) -> None:
    try:
        pending_output = False
        print_progress = sys.stdout.isatty()
        if not print_progress:
            print(f"Download {url}", file=sys.stderr)
        headers = {}
        if out.exists():
            if not revalidate:
                return
            mtime = os.path.getmtime(out)
            headers["If-Modified-Since"] = email.utils.formatdate(mtime, usegmt=True)
        with requests.get(url, headers=headers, stream=True) as res:
            res.raise_for_status()
            # GDAS1 redirects missing files to a page that returns 200.
            if res.url.endswith("/notfound.php"):
                raise Exception("Page not found")
            if res.status_code == 304:
                return
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
            if "Last-Modified" in res.headers:
                last_modified = res.headers["Last-Modified"]
                try:
                    new_mtime = email.utils.parsedate_to_datetime(
                        last_modified
                    ).timestamp()
                    new_atime = datetime.datetime.now().timestamp()
                    os.utime(out, (new_atime, new_mtime))
                except ValueError:
                    pass
    finally:
        if pending_output:
            print(file=sys.stderr)
