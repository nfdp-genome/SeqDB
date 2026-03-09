from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import ProjectType


class ProjectCreate(BaseModel):
    title: str
    description: str
    project_type: ProjectType
    release_date: Optional[date] = None
    license: str = "CC-BY"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[date] = None
    license: Optional[str] = None


class ProjectResponse(BaseModel):
    accession: str
    ena_accession: Optional[str] = None
    title: str
    description: str
    project_type: ProjectType
    release_date: Optional[date] = None
    license: str
    created_at: datetime

    model_config = {"from_attributes": True}
