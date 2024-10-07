import datetime
import hashlib
from pathlib import Path
import requests

BASE_URL = "http://localhost:3000"
AUTH = ("admin", "admin")


def get_sites() -> list[dict]:
    res = requests.get(f"{BASE_URL}/api/sites", params={"type": "cloudnet"})
    res.raise_for_status()
    return [
        site
        for site in res.json()
        if site["latitude"] is not None and site["longitude"] is not None
    ]


def submit_file(filename: Path, site: dict, date: datetime.date):
    print(f"Submit {filename}")
    md5_hash = hashlib.md5()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    checksum = md5_hash.hexdigest()
    payload = {
        "measurementDate": date.isoformat(),
        "model": "ecmwf-open",
        "filename": filename.name,
        "checksum": checksum,
        "site": site["id"],
    }
    res = requests.post(f"{BASE_URL}/model-upload/metadata/", json=payload, auth=AUTH)
    if res.status_code == 409:
        return
    res.raise_for_status()
    with open(filename, "rb") as f:
        res = requests.put(
            f"{BASE_URL}/model-upload/data/{checksum}", data=f, auth=AUTH
        )
        res.raise_for_status()
