from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import SubmissionStatus


class SubmissionCreate(BaseModel):
    title: str
    project_accession: str
    run_accessions: list[str]


class SubmissionResponse(BaseModel):
    submission_id: str
    title: str
    status: SubmissionStatus
    created_at: datetime

    model_config = {"from_attributes": True}
