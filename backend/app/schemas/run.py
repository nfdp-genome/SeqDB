from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import FileType


class RunResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    file_type: FileType
    file_size: int
    checksum_md5: str
    created_at: datetime

    model_config = {"from_attributes": True}
