import argparse
import datetime
from pathlib import Path
import sys


from model_munger.cloudnet import get_sites, submit_file
from model_munger.download import download_ecmwf
from model_munger.extractors.ecmwf_open import extract_profiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        type=datetime.date.fromisoformat,
        default=datetime.datetime.now(datetime.timezone.utc).date(),
    )
    parser.add_argument("-r", "--run", type=int, default=0)
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

    input_files = download_ecmwf(
        args.date, run=args.run, steps=list(range(0, 90 + 1, 3)), directory=download_dir
    )
    output_files = extract_profiles(input_files, sites, output_dir)
    if args.submit:
        for site, output_file in zip(sites, output_files):
            submit_file(output_file, site, args.date)


if __name__ == "__main__":
    main()
