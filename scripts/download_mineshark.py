"""Resume the public MineShark artifact download using HTTP byte ranges.

Source: https://zenodo.org/records/13624058 (CC BY 4.0).
The original Zenodo URL and exact archive are recorded here for provenance.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import md5
from pathlib import Path
from urllib.request import Request, urlopen
import json
import math
import time


URL = "https://zenodo.org/records/13624058/files/MineShark_AE.tar.gz?download=1"
SIZE = 1_411_938_097
MD5 = "6c64268ec35414fc9f483a7a4ed43755"
CHUNK = 8 * 1024 * 1024
DEST = Path("data/raw/MineShark_AE.tar.gz")
PARTS = Path("data/raw/.mineshark_parts")


def fetch(i):
    start = i * CHUNK
    end = min(SIZE, start + CHUNK) - 1
    part = PARTS / f"{i:04d}.bin"
    want = end - start + 1
    if part.exists() and part.stat().st_size == want:
        return i, "cached"
    for attempt in range(5):
        try:
            req = Request(URL, headers={"Range": f"bytes={start}-{end}"})
            with urlopen(req, timeout=90) as response:
                if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{SIZE}":
                    raise ValueError(f"bad range response: {response.status}, {response.headers.get('Content-Range')}")
                data = response.read()
            if len(data) != want:
                raise ValueError(f"short read: {len(data)} != {want}")
            temp = part.with_suffix(".tmp")
            temp.write_bytes(data)
            temp.replace(part)
            return i, "downloaded"
        except Exception:
            if attempt == 4:
                raise
            time.sleep(min(15, 2 ** attempt))


def main():
    PARTS.mkdir(parents=True, exist_ok=True)
    n = math.ceil(SIZE / CHUNK)
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch, i) for i in range(n)]
        for j, future in enumerate(as_completed(futures), 1):
            i, status = future.result()
            if j % 10 == 0 or j == n:
                print(f"{j}/{n} chunks ready; last={i} {status}", flush=True)
    digest = md5()
    with DEST.open("wb") as output:
        for i in range(n):
            with (PARTS / f"{i:04d}.bin").open("rb") as input_file:
                while block := input_file.read(1024 * 1024):
                    output.write(block)
                    digest.update(block)
    actual = digest.hexdigest()
    if actual != MD5:
        raise ValueError(f"MD5 mismatch: {actual} != {MD5}")
    Path("data/raw/mineshark_source.json").write_text(
        json.dumps({"url": URL, "size": SIZE, "md5": actual, "license": "CC BY 4.0"}, indent=2),
        encoding="utf-8",
    )
    print(f"Verified {DEST}: {actual}", flush=True)


if __name__ == "__main__":
    main()
