from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import Archive, ArchiveSubmissionStatus


class ArchiveSubmission(Base):
    __tablename__ = "archive_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_accession: Mapped[str] = mapped_column(String(20), index=True)
    archive: Mapped[Archive] = mapped_column(SAEnum(Archive))
    archive_accession: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[ArchiveSubmissionStatus] = mapped_column(
        SAEnum(ArchiveSubmissionStatus), default=ArchiveSubmissionStatus.DRAFT
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
