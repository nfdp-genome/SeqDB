from app.services.storage import StorageService


def test_bucket_names():
    assert StorageService.BUCKET_RAW == "nfdp-raw"
    assert StorageService.BUCKET_QC == "nfdp-qc"
    assert StorageService.BUCKET_PROCESSED == "nfdp-processed"
    assert StorageService.BUCKET_SNPCHIP == "nfdp-snpchip"
    assert StorageService.BUCKET_STAGING == "nfdp-staging"


def test_all_buckets():
    assert len(StorageService.ALL_BUCKETS) == 5


def test_build_object_path():
    path = StorageService.build_object_path(
        "NFDP-PRJ-000001", "NFDP-SAM-000001", "NFDP-RUN-000001", "sample_R1.fastq.gz"
    )
    assert path == "NFDP-PRJ-000001/NFDP-SAM-000001/NFDP-RUN-000001/sample_R1.fastq.gz"


def test_build_object_path_snpchip():
    path = StorageService.build_object_path(
        "NFDP-PRJ-000002", "NFDP-SAM-000010", "NFDP-RUN-000050", "raw.idat"
    )
    assert path == "NFDP-PRJ-000002/NFDP-SAM-000010/NFDP-RUN-000050/raw.idat"
