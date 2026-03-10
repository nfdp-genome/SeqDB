from pathlib import Path
from seqdb_cli.utils import compute_md5, discover_sequence_files


def test_compute_md5(tmp_path):
    f = tmp_path / "test.fastq.gz"
    f.write_bytes(b"ACGTACGT")
    md5 = compute_md5(f)
    assert len(md5) == 32
    assert md5 == "cc0af3a4fedb18378b4b57b98068e69f"


def test_discover_fastq_files(tmp_path):
    (tmp_path / "sample_R1.fastq.gz").write_bytes(b"read1")
    (tmp_path / "sample_R2.fastq.gz").write_bytes(b"read2")
    (tmp_path / "readme.txt").write_bytes(b"ignore")
    files = discover_sequence_files(tmp_path)
    assert len(files) == 2
    assert all(f.suffix == ".gz" for f in files)


def test_discover_bam_files(tmp_path):
    (tmp_path / "aligned.bam").write_bytes(b"bam")
    (tmp_path / "variants.vcf").write_bytes(b"vcf")
    files = discover_sequence_files(tmp_path)
    assert len(files) == 2
