import enum


class Platform(str, enum.Enum):
    ILLUMINA = "ILLUMINA"
    OXFORD_NANOPORE = "OXFORD_NANOPORE"
    PACBIO_SMRT = "PACBIO_SMRT"
    SNP_CHIP = "SNP_CHIP"
    HI_C = "HI_C"


class LibraryStrategy(str, enum.Enum):
    WGS = "WGS"
    WXS = "WXS"
    RNA_SEQ = "RNA-Seq"
    AMPLICON = "AMPLICON"
    TARGETED = "TARGETED"
    OTHER = "OTHER"


class LibrarySource(str, enum.Enum):
    GENOMIC = "GENOMIC"
    TRANSCRIPTOMIC = "TRANSCRIPTOMIC"
    METAGENOMIC = "METAGENOMIC"
    OTHER = "OTHER"


class LibraryLayout(str, enum.Enum):
    PAIRED = "PAIRED"
    SINGLE = "SINGLE"


class FileType(str, enum.Enum):
    FASTQ = "FASTQ"
    BAM = "BAM"
    CRAM = "CRAM"
    VCF = "VCF"
    IDAT = "IDAT"
    BED_BIM_FAM = "BED_BIM_FAM"
    PED_MAP = "PED_MAP"
    CSV = "CSV"
    OTHER = "OTHER"


class ProjectType(str, enum.Enum):
    WGS = "WGS"
    METAGENOMICS = "Metagenomics"
    GENOTYPING = "Genotyping"
    TRANSCRIPTOMICS = "Transcriptomics"
    AMPLICON = "Amplicon"
    OTHER = "Other"


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    DEPOSITED = "deposited"
    PUBLISHED = "published"
    FAILED = "failed"


class QCStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUBMITTER = "submitter"
    VIEWER = "viewer"
    EXTERNAL_CLIENT = "external_client"


class UploadMethod(str, enum.Enum):
    BROWSER = "browser"
    FTP = "ftp"


class StagedFileStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    LINKED = "linked"
    EXPIRED = "expired"


class Archive(str, enum.Enum):
    ENA = "ENA"
    NCBI = "NCBI"


class ArchiveSubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    PUBLIC = "public"
    FAILED = "failed"


class OntologyType(str, enum.Enum):
    NCBI_TAXONOMY = "ncbi_taxonomy"
    GAZ = "gaz"
    EFO = "efo"
    LBO = "lbo"
    ENVO = "envo"
