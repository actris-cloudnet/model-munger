import argparse
import datetime
import sys
from pathlib import Path

from model_munger.cloudnet import get_locations, get_sites, submit_file
from model_munger.download import download_file
from model_munger.extract import RawLocation, extract_profiles, write_netcdf
from model_munger.extractors.ecmwf_open import generate_ecmwf_url, read_ecmwf
from model_munger.extractors.gdas1 import generate_gdas1_url, read_gdas1
from model_munger.level import Level
from model_munger.readers.ecmwf_open import ECMWF_OPEN
from model_munger.readers.gdas1 import GDAS1
from model_munger.version import __version__ as model_munger_version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        type=parse_date,
        help="Fetch ECMWF open data for this date. Default is today.",
    )
    parser.add_argument(
        "--start",
        type=parse_date,
        help="Fetch ECMWF open data starting from this date. Default is today.",
    )
    parser.add_argument(
        "--stop",
        type=parse_date,
        help="Fetch ECMWF open data until this date. Default is today.",
    )
    parser.add_argument(
        "-r",
        "--runs",
        type=lambda x: [int(y) for y in x.split(",")],
        default=[0],
        help="Comma-separated list of model runs to download.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=90,
        help="Maximum time step. Default is 90 hours.",
    )
    parser.add_argument(
        "-s",
        "--sites",
        type=lambda x: x.split(","),
        help="Comma-separated list of Cloudnet sites (e.g. hyytiala) to extract.",
    )
    parser.add_argument(
        "-m",
        "--model",
        choices=["ecmwf-open", "gdas1"],
        help="Which model to download and process.",
    )
    parser.add_argument(
        "--source",
        choices=["ecmwf", "noaa", "aws"],
        help="Where to download ECMWF open data from.",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit files to Cloudnet.",
    )
    parser.add_argument(
        "--no-keep",
        action="store_true",
        help="Don't keep downloaded and processed files.",
    )

    args = parser.parse_args()

    if args.date and (args.start or args.stop):
        parser.error("Cannot use --date with --start and --stop")
    if args.date:
        args.start = args.date
        args.stop = args.date
    else:
        if not args.start:
            args.start = utctoday()
        if not args.stop:
            args.stop = utctoday()
        if args.start > args.stop:
            parser.error("--start should be before --stop")
    del args.date

    if args.sites:
        all_sites = get_sites()
        if invalid_sites := set(args.sites) - {site["id"] for site in all_sites}:
            parser.error("Invalid sites: " + ",".join(invalid_sites))
            sys.exit(1)
        sites = [site for site in all_sites if site["id"] in args.sites]
    else:
        sites = get_sites("cloudnet")

    download_dir = Path("data")
    output_dir = Path("output")
    download_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    current_files: set[Path] = set()
    last_files: set[Path] = set()

    def _remove_unused_files():
        if args.no_keep:
            unused_files = last_files - current_files
            for file in unused_files:
                print("Remove", file)
                file.unlink()
        last_files.clear()
        last_files.update(current_files)
        current_files.clear()

    date = args.start
    while date <= args.stop:
        for run in args.runs:
            locations = []
            for site in sites:
                if "mobile" in site["type"]:
                    one_day = datetime.timedelta(days=1)
                    time_prev, lat_prev, lon_prev = get_locations(
                        site["id"], date - one_day
                    )
                    time_curr, lat_curr, lon_curr = get_locations(site["id"], date)
                    time_next, lat_next, lon_next = get_locations(
                        site["id"], date + one_day
                    )
                    time = time_prev + time_curr + time_next
                    latitude = lat_prev + lat_curr + lat_next
                    longitude = lon_prev + lon_curr + lon_next
                else:
                    time = None
                    latitude = site["latitude"]
                    longitude = site["longitude"]
                locations.append(
                    RawLocation(
                        id=site["id"],
                        name=site["humanReadableName"],
                        time=time,
                        latitude=latitude,
                        longitude=longitude,
                    )
                )

            levels: list[Level] = []

            if args.model == "ecmwf-open":
                model = ECMWF_OPEN
                history = f"Model run {run:02} UTC extracted from ECMWF open data"
                date_id = f"{date:%Y%m%d}{run:02}0000"
                source = args.source or "ecmwf"
                for step in range(0, args.steps + 1, 3):
                    url = generate_ecmwf_url(date, run, step, source)
                    path = download_file(url, download_dir)
                    levels.extend(read_ecmwf(path))
                    current_files.add(path)
            elif args.model == "gdas1":
                model = GDAS1
                source = args.source or "noaa"
                url, revalidate = generate_gdas1_url(date, source)
                filename = url.rsplit("/", maxsplit=1)[-1]
                history = f"GDAS1 data on {date:%Y-%m-%d} extracted from {filename}"
                date_id = f"{date:%Y%m%d}"
                path = download_file(url, download_dir, revalidate=revalidate)
                for level in read_gdas1(path):
                    if level.time.date() < date:
                        continue
                    if level.time.date() > date:
                        break
                    levels.append(level)
                current_files.add(path)

            now = datetime.datetime.now(datetime.timezone.utc)
            history_line = (
                f"{now:%Y-%m-%d %H:%M:%S} +00:00 - {history} "
                f"using model-munger v{model_munger_version}"
            )

            for raw in extract_profiles(levels, locations, model, history_line):
                outfile = f"{date_id}_{raw.location.id}_{raw.model.id}.nc"
                outpath = output_dir / outfile
                print(outpath)
                write_netcdf(raw, outpath)
                if args.submit:
                    submit_file(outpath, raw.location, date, raw.model)

            _remove_unused_files()

        date += datetime.timedelta(days=1)

    _remove_unused_files()


def utctoday():
    return datetime.datetime.now(datetime.timezone.utc).date()


def parse_date(value: str) -> datetime.date:
    if value == "today":
        return utctoday()
    if value == "yesterday":
        return utctoday() - datetime.timedelta(days=1)
    return datetime.date.fromisoformat(value)


if __name__ == "__main__":
    main()
