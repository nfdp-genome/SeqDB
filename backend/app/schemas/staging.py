from datetime import datetime

from pydantic import BaseModel

from app.models.enums import UploadMethod, StagedFileStatus


class StagingInitiateRequest(BaseModel):
    filename: str
    file_size: int


class StagingInitiateResponse(BaseModel):
    staged_file_id: int
    presigned_url: str
    staging_path: str
    expires_in: int


class StagedFileResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    checksum_md5: str
    upload_method: UploadMethod
    status: StagedFileStatus
    uploaded_at: datetime

    model_config = {"from_attributes": True}
