from __future__ import annotations

import hashlib
from pathlib import Path

SEQUENCE_EXTENSIONS = {
    ".fastq", ".fq", ".fastq.gz", ".fq.gz",
    ".bam", ".cram", ".vcf", ".vcf.gz",
    ".idat", ".bed", ".bim", ".fam", ".ped", ".map", ".csv",
}


def compute_md5(path: Path, chunk_size: int = 8192) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def discover_sequence_files(directory: Path) -> list[Path]:
    files = []
    for p in sorted(directory.iterdir()):
        if not p.is_file():
            continue
        suffixes = "".join(p.suffixes)
        if suffixes in SEQUENCE_EXTENSIONS or p.suffix in SEQUENCE_EXTENSIONS:
            files.append(p)
    return files
