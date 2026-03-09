import re
from enum import Enum


class AccessionType(str, Enum):
    PROJECT = "PRJ"
    SAMPLE = "SAM"
    EXPERIMENT = "EXP"
    RUN = "RUN"
    SUBMISSION = "SUB"


_ACCESSION_PATTERN = re.compile(r"^NFDP-(PRJ|SAM|EXP|RUN|SUB)-\d{6}$")


def generate_accession(acc_type: AccessionType, sequence: int) -> str:
    return f"NFDP-{acc_type.value}-{sequence:06d}"


def validate_accession(accession: str) -> bool:
    return bool(_ACCESSION_PATTERN.match(accession))
