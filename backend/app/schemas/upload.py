from pydantic import BaseModel
from app.models.enums import FileType


class UploadInitiate(BaseModel):
    experiment_accession: str
    filename: str
    file_size: int
    checksum_md5: str
    file_type: FileType


class UploadInitiateResponse(BaseModel):
    upload_id: str
    presigned_url: str
    expires_in: int


class UploadComplete(BaseModel):
    upload_id: str
    checksum_md5: str


class UploadCompleteResponse(BaseModel):
    run_accession: str
    qc_job_id: str
    status: str
