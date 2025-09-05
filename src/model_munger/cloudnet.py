import datetime
import hashlib
import os
from pathlib import Path

import requests
from cloudnet_api_client import APIClient

from model_munger.extract import FixedLocation, MobileLocation
from model_munger.model import ModelType

BASE_URL = os.environ.get("MM_CLOUDNET_URL", "http://localhost:3000").rstrip("/")
AUTH = (
    os.environ.get("MM_CLOUDNET_USERNAME", "admin"),
    os.environ.get("MM_CLOUDNET_PASSWORD", "admin"),
)

api_client = APIClient(BASE_URL + "/api")


def submit_file(
    filename: Path,
    location: FixedLocation | MobileLocation,
    date: datetime.date,
    model: ModelType,
) -> None:
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
