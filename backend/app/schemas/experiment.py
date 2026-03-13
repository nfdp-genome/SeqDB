from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.models.enums import Platform, LibraryStrategy, LibrarySource, LibraryLayout
from app.services.accession import validate_accession


class ExperimentCreate(BaseModel):
    sample_accession: str
    platform: Platform
    instrument_model: str
    library_strategy: LibraryStrategy
    library_source: LibrarySource
    library_layout: LibraryLayout
    insert_size: Optional[int] = None

    @field_validator("sample_accession")
    @classmethod
    def validate_sample_accession(cls, v):
        if not validate_accession(v):
            raise ValueError(f"Invalid accession format: {v}")
        return v


class ExperimentResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    ncbi_accession: Optional[str] = None
    platform: Platform
    instrument_model: str
    library_strategy: LibraryStrategy
    library_source: LibrarySource
    library_layout: LibraryLayout
    insert_size: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
