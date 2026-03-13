from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.services.accession import validate_accession


class SampleCreate(BaseModel):
    project_accession: str
    checklist_id: str
    organism: str
    tax_id: int
    collection_date: Optional[date] = None
    geographic_location: Optional[str] = None
    breed: Optional[str] = None
    host: Optional[str] = None
    tissue: Optional[str] = None
    developmental_stage: Optional[str] = None
    sex: Optional[str] = None
    custom_fields: Optional[dict] = None
    domain_schema_id: Optional[str] = None

    @field_validator("project_accession")
    @classmethod
    def validate_project_accession(cls, v):
        if not validate_accession(v):
            raise ValueError(f"Invalid accession format: {v}")
        return v


class SampleUpdate(BaseModel):
    organism: Optional[str] = None
    breed: Optional[str] = None
    tissue: Optional[str] = None
    host: Optional[str] = None
    sex: Optional[str] = None
    custom_fields: Optional[dict] = None


class SampleResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    ncbi_accession: Optional[str] = None
    domain_schema_id: Optional[str] = None
    organism: str
    tax_id: int
    breed: Optional[str] = None
    collection_date: Optional[date] = None
    geographic_location: Optional[str] = None
    checklist_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
