import datetime
import hashlib
import os
from pathlib import Path

import requests

from model_munger.extract import RawLocation
from model_munger.model import ModelType

BASE_URL = os.environ.get("MM_CLOUDNET_URL", "http://localhost:3000")
AUTH = (
    os.environ.get("MM_CLOUDNET_USERNAME", "admin"),
    os.environ.get("MM_CLOUDNET_PASSWORD", "admin"),
)


def get_sites(type: str | None = None) -> list[dict]:
    params = {"type": type} if type is not None else None
    res = requests.get(f"{BASE_URL}/api/sites", params)
    res.raise_for_status()
    return [site for site in res.json()]


def get_locations(
    site_id: str, date: datetime.date
) -> tuple[list[datetime.datetime], list[float], list[float]]:
    res = requests.get(
        f"{BASE_URL}/api/sites/{site_id}/locations",
        params={"date": date.isoformat(), "raw": "1"},
    )
    res.raise_for_status()
    data = res.json()
    return (
        [
            datetime.datetime.strptime(d["date"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc
            )
            for d in data
        ],
        [d["latitude"] for d in data],
        [d["longitude"] for d in data],
    )


def submit_file(
    filename: Path, location: RawLocation, date: datetime.date, model: ModelType
):
    print(f"Submit {filename.name}")
    md5_hash = hashlib.md5()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    checksum = md5_hash.hexdigest()
    payload = {
        "measurementDate": date.isoformat(),
        "model": model.id,
        "filename": filename.name,
        "checksum": checksum,
        "site": location.id,
    }
    res = requests.post(f"{BASE_URL}/model-upload/metadata/", json=payload, auth=AUTH)
    if res.status_code == 409:
        return
    res.raise_for_status()
    with open(filename, "rb") as f:
        res = requests.put(
            f"{BASE_URL}/model-upload/data/{checksum}",
            data=f,
            auth=AUTH,
        )
        res.raise_for_status()
