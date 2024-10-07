import argparse
import datetime
from pathlib import Path
import sys

import numpy as np

from model_munger.cloudnet import get_sites, submit_file
from model_munger.download import download_ecmwf
from model_munger.process import extract_profiles, save_netcdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        type=datetime.date.fromisoformat,
        default=datetime.datetime.now(datetime.timezone.utc).date(),
    )
    parser.add_argument("-s", "--sites", type=lambda x: x.split(","))
    parser.add_argument("--submit", action="store_true")

    args = parser.parse_args()
    sites = get_sites()
    if args.sites:
        if invalid_sites := set(args.sites) - {site["id"] for site in sites}:
            print("Invalid sites: " + ",".join(invalid_sites), file=sys.stderr)
            sys.exit(1)
        sites = [site for site in sites if site["id"] in args.sites]

    download_dir = Path("data")
    output_dir = Path("output")
    download_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    latitudes = np.array([site["latitude"] for site in sites])
    longitudes = np.array([site["longitude"] for site in sites])
    files = download_ecmwf(args.date, run=0, directory=download_dir)
    output = extract_profiles(files, args.date, latitudes, longitudes)
    for site, data in zip(sites, output):
        filename = save_netcdf(
            args.date, site["id"], site["humanReadableName"], data, output_dir
        )
        if args.submit:
            submit_file(filename, site, args.date)


if __name__ == "__main__":
    main()
