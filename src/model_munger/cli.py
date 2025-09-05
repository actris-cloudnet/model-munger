import argparse
import datetime
import sys
from pathlib import Path

from model_munger.cloudnet import api_client, submit_file
from model_munger.download import download_file
from model_munger.extract import (
    Extractor,
    FixedLocation,
    MobileLocation,
    write_netcdf,
)
from model_munger.extractors.ecmwf_open import generate_ecmwf_url, read_ecmwf
from model_munger.extractors.gdas1 import generate_gdas1_url, read_gdas1
from model_munger.readers.ecmwf_open import ECMWF_OPEN
from model_munger.readers.gdas1 import GDAS1


def main() -> None:
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
        required=True,
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
        all_sites = api_client.sites()
        invalid_ids = set(args.sites) - {site.id for site in all_sites}
        if invalid_ids:
            parser.error("Invalid sites: " + ",".join(invalid_ids))
            sys.exit(1)
        sites = [site for site in all_sites if site.id in args.sites]
    else:
        sites = api_client.sites("cloudnet")

    download_dir = Path("data")
    output_dir = Path("output")
    download_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    date = args.start
    while date <= args.stop:
        for run in args.runs:
            locations: list[FixedLocation | MobileLocation] = []
            for site in sites:
                if site.latitude is not None and site.longitude is not None:
                    locations.append(
                        FixedLocation(
                            id=site.id,
                            name=site.human_readable_name,
                            latitude=site.latitude,
                            longitude=site.longitude,
                        )
                    )
                else:
                    locs = []
                    for day_offset in range(-1, args.steps // 24 + 2):
                        loc_date = date + datetime.timedelta(days=day_offset)
                        locs.extend(api_client.moving_site_locations(site.id, loc_date))
                    locations.append(
                        MobileLocation(
                            id=site.id,
                            name=site.human_readable_name,
                            time=[loc.time for loc in locs],
                            latitude=[loc.latitude for loc in locs],
                            longitude=[loc.longitude for loc in locs],
                        )
                    )

            if args.model == "ecmwf-open":
                model = ECMWF_OPEN
                history = f"Model run {run:02} UTC extracted from ECMWF open data"
                steps = list(range(0, args.steps + 1, 3))
                start_time = datetime.datetime.combine(
                    date, datetime.time(run), datetime.timezone.utc
                )
                time = [start_time + datetime.timedelta(hours=step) for step in steps]
                extractor = Extractor(time, locations, model, history)

                date_id = f"{date:%Y%m%d}{run:02}0000"
                source = args.source or "ecmwf"
                for step in steps:
                    url = generate_ecmwf_url(date, run, step, source)
                    path = download_file(url, download_dir)
                    for level in read_ecmwf(path):
                        extractor.add_level(level)
                    if args.no_keep:
                        path.unlink()
            elif args.model == "gdas1":
                model = GDAS1
                source = args.source or "noaa"
                url, revalidate = generate_gdas1_url(date, source)
                filename = url.rsplit("/", maxsplit=1)[-1]
                history = f"GDAS1 data on {date:%Y-%m-%d} extracted from {filename}"
                time = [
                    datetime.datetime.combine(
                        date, datetime.time(hour), datetime.timezone.utc
                    )
                    for hour in range(0, 24, 3)
                ]
                extractor = Extractor(time, locations, model, history)

                date_id = f"{date:%Y%m%d}"
                path = download_file(url, download_dir, revalidate=revalidate)
                for level in read_gdas1(path):
                    if level.time.date() < date:
                        continue
                    if level.time.date() > date:
                        break
                    extractor.add_level(level)

                next_date = date + datetime.timedelta(days=1)
                next_url, _next_revalidate = generate_gdas1_url(next_date, source)
                if args.no_keep and (date == args.stop or url != next_url):
                    path.unlink()

            for raw in extractor.extract_profiles():
                outfile = f"{date_id}_{raw.location.id}_{raw.model.id}.nc"
                outpath = output_dir / outfile
                print(outpath)
                write_netcdf(raw, outpath)
                if args.submit:
                    submit_file(outpath, raw.location, date, raw.model)
                if args.no_keep:
                    outpath.unlink()

        date += datetime.timedelta(days=1)


def utctoday() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


def parse_date(value: str) -> datetime.date:
    if value == "today":
        return utctoday()
    if value == "yesterday":
        return utctoday() - datetime.timedelta(days=1)
    return datetime.date.fromisoformat(value)


if __name__ == "__main__":
    main()
