from app.models.enums import (
    Platform, LibraryStrategy, LibrarySource, LibraryLayout,
    FileType, ProjectType, SubmissionStatus, QCStatus, UserRole,
)
from app.models.project import Project
from app.models.sample import Sample
from app.models.experiment import Experiment
from app.models.run import Run
from app.models.submission import Submission
from app.models.user import User
from app.models.qc_report import QCReport


def test_enums_exist():
    assert Platform.ILLUMINA.value == "ILLUMINA"
    assert Platform.OXFORD_NANOPORE.value == "OXFORD_NANOPORE"
    assert Platform.PACBIO_SMRT.value == "PACBIO_SMRT"
    assert Platform.SNP_CHIP.value == "SNP_CHIP"
    assert Platform.HI_C.value == "HI_C"
    assert FileType.FASTQ.value == "FASTQ"
    assert SubmissionStatus.DRAFT.value == "draft"
    assert UserRole.ADMIN.value == "admin"


def test_project_table_name():
    assert Project.__tablename__ == "projects"


def test_sample_table_name():
    assert Sample.__tablename__ == "samples"


def test_experiment_table_name():
    assert Experiment.__tablename__ == "experiments"


def test_run_table_name():
    assert Run.__tablename__ == "runs"


def test_submission_table_name():
    assert Submission.__tablename__ == "submissions"


def test_user_table_name():
    assert User.__tablename__ == "users"


def test_qc_report_table_name():
    assert QCReport.__tablename__ == "qc_reports"
