"""Extract only labeled proxy traces and a normal PCAP from MineShark.

The Zenodo archive remains untouched under data/raw. Selected files retain their
original relative names, and a SHA-256 manifest records every extracted file.
"""

from hashlib import sha256
from pathlib import Path
import csv
import re
import shutil
import tarfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/MineShark_AE.tar.gz"
DEST = ROOT / "data/raw/mineshark_subset"
PREFIX = "AE/dataset/obfuscated/"
CHOICES = {"ssr", "trojan", "v2ray"}


def wanted(name: str) -> bool:
    if name in {"AE/README.md", "AE/LICENSE", "AE/detector/pcap/normal.pcap"}:
        return True
    if not name.startswith(PREFIX) or not name.endswith(".tsv"):
        return False
    path = Path(name)
    return any(part in CHOICES for part in path.parts)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or not wanted(member.name):
                continue
            # Original Linux filenames contain ':' and '*', invalid on Windows.
            relative = Path(*[re.sub(r'[:*?"<>|]', '_', part) for part in Path(member.name).parts[1:]])
            output = DEST / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            digest = sha256()
            with archive.extractfile(member) as inp, output.open("wb") as out:
                while chunk := inp.read(1 << 20):
                    out.write(chunk)
                    digest.update(chunk)
            records.append((member.name, str(relative).replace("\\", "/"), member.size, digest.hexdigest()))
            if len(records) % 25 == 0:
                print(f"extracted {len(records)}", flush=True)
    with (DEST / "extracted_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archive_path", "extracted_relative_path", "bytes", "sha256"])
        w.writerows(records)
    print(f"extracted {len(records)} files; total {sum(x[2] for x in records)} bytes", flush=True)


if __name__ == "__main__":
    main()
