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
from app.models.enums import Archive, ArchiveSubmissionStatus, OntologyType
from app.models.archive_submission import ArchiveSubmission
from app.models.domain_schema import DomainSchema
from app.models.ontology_term import OntologyTerm
import sqlalchemy as sa


def test_new_enums_archive():
    assert Archive.ENA.value == "ENA"
    assert Archive.NCBI.value == "NCBI"


def test_new_enums_archive_submission_status():
    assert ArchiveSubmissionStatus.DRAFT.value == "draft"
    assert ArchiveSubmissionStatus.SUBMITTED.value == "submitted"
    assert ArchiveSubmissionStatus.PROCESSING.value == "processing"
    assert ArchiveSubmissionStatus.PUBLIC.value == "public"
    assert ArchiveSubmissionStatus.FAILED.value == "failed"


def test_new_enums_ontology_type():
    assert OntologyType.NCBI_TAXONOMY.value == "ncbi_taxonomy"
    assert OntologyType.GAZ.value == "gaz"
    assert OntologyType.EFO.value == "efo"
    assert OntologyType.LBO.value == "lbo"
    assert OntologyType.ENVO.value == "envo"


def test_project_ncbi_accession_column():
    cols = {c.name for c in Project.__table__.columns}
    assert "ncbi_accession" in cols


def test_sample_ncbi_accession_column():
    cols = {c.name for c in Sample.__table__.columns}
    assert "ncbi_accession" in cols


def test_sample_domain_schema_id_column():
    cols = {c.name for c in Sample.__table__.columns}
    assert "domain_schema_id" in cols


def test_experiment_ncbi_accession_column():
    cols = {c.name for c in Experiment.__table__.columns}
    assert "ncbi_accession" in cols


def test_run_ncbi_accession_column():
    cols = {c.name for c in Run.__table__.columns}
    assert "ncbi_accession" in cols


def test_archive_submission_table():
    assert ArchiveSubmission.__tablename__ == "archive_submissions"
    cols = {c.name for c in ArchiveSubmission.__table__.columns}
    assert "id" in cols
    assert "entity_type" in cols
    assert "entity_accession" in cols
    assert "archive" in cols
    assert "archive_accession" in cols
    assert "status" in cols
    assert "submitted_at" in cols
    assert "response_data" in cols
    assert "created_at" in cols


def test_domain_schema_table():
    assert DomainSchema.__tablename__ == "domain_schemas"
    cols = {c.name for c in DomainSchema.__table__.columns}
    assert "id" in cols
    assert "display_name" in cols
    assert "ena_checklist" in cols
    assert "ncbi_package" in cols


def test_ontology_term_table():
    assert OntologyTerm.__tablename__ == "ontology_terms"
    cols = {c.name for c in OntologyTerm.__table__.columns}
    assert "id" in cols
    assert "ontology" in cols
    assert "term_id" in cols
    assert "label" in cols
    assert "synonyms" in cols
    assert "parent_id" in cols
    assert "is_obsolete" in cols
    assert "last_updated" in cols


def test_ontology_term_unique_constraint():
    constraint_names = {
        c.name for c in OntologyTerm.__table__.constraints
        if hasattr(c, "name") and c.name is not None
    }
    assert "uq_ontology_term" in constraint_names


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
