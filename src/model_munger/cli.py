import argparse
import datetime
import sys
from pathlib import Path

from model_munger.cloudnet import get_sites, submit_file
from model_munger.download import download_ecmwf
from model_munger.extractors.ecmwf_open import extract_profiles


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
        "-s",
        "--sites",
        type=lambda x: x.split(","),
        help="Comma-separated list of Cloudnet sites (e.g. hyytiala) to extract.",
    )
    parser.add_argument(
        "--source",
        choices=["ecmwf", "aws"],
        default="ecmwf",
        help="Where to download ECMWF open data from.",
    )
    parser.add_argument(
        "--submit", action="store_true", help="Submit files to Cloudnet."
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

    sites = get_sites()
    if args.sites:
        if invalid_sites := set(args.sites) - {site["id"] for site in sites}:
            parser.error("Invalid sites: " + ",".join(invalid_sites))
            sys.exit(1)
        sites = [site for site in sites if site["id"] in args.sites]

    download_dir = Path("data")
    output_dir = Path("output")
    download_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    date = args.start
    while date <= args.stop:
        for run in args.runs:
            input_files = download_ecmwf(
                date,
                run=run,
                steps=list(range(0, 90 + 1, 3)),
                directory=download_dir,
                source=args.source,
            )
            output_files = extract_profiles(input_files, sites, output_dir)
            if args.submit:
                for site, output_file in zip(sites, output_files):
                    submit_file(output_file, site, date)
            if args.no_keep:
                for file in input_files + output_files:
                    file.unlink()
        date += datetime.timedelta(days=1)


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
