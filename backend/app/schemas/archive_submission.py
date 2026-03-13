from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import Archive, ArchiveSubmissionStatus


class ArchiveSubmissionResponse(BaseModel):
    id: int
    entity_type: str
    entity_accession: str
    archive: Archive
    archive_accession: Optional[str] = None
    status: ArchiveSubmissionStatus
    submitted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
